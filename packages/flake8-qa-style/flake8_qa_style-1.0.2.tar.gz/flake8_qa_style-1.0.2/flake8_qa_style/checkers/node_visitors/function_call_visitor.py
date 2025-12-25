import ast
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from flake8_qa_style.checkers.node_visitors._visitor_with_filename import (
    VisitorWithFilename
)


class Checker(ABC):
    @abstractmethod
    def check(self, call_node, context):
        pass


class Context:
    def __init__(self, sleep_function_name: Optional[str], is_imported_module_time: bool):
        self.sleep_function_name = sleep_function_name
        self.is_imported_module_time = is_imported_module_time


class FunctionCallVisitor(VisitorWithFilename):
    checkers: List[Checker] = []
    is_imported_module_time: bool = False
    sleep_function_name: Optional[str] = None

    @classmethod
    def register_checker(cls, checker: Type[Checker]):
        cls.checkers.append(checker())
        return checker

    @classmethod
    def deregister_all(cls):
        cls.checkers = []

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == 'time':
            for name in node.names:
                if name.name == 'sleep':
                    self.sleep_function_name = name.name if not name.asname else name.asname

    def visit_Import(self, node: ast.ImportFrom):
        for name in node.names:
            if name.name == 'time':
                self.is_imported_module_time = True

    def visit_Call(self, node: ast.Call):
        context = Context(self.sleep_function_name, self.is_imported_module_time)
        try:
            for checker in self.checkers:
                self.errors.extend(checker.check(node, context))
        except Exception as e:
            print(f'Linter failed: checking {self.filename} with {checker.__class__}.\n'
                  f'Exception: {e}')
