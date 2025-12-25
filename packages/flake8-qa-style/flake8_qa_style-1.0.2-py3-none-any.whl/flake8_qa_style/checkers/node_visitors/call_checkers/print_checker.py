import ast
from typing import List

from flake8_plugin_utils import Error

from flake8_qa_style.checkers.node_visitors.function_call_visitor import (
    Checker,
    FunctionCallVisitor
)
from flake8_qa_style.errors import Print


@FunctionCallVisitor.register_checker
class PrintChecker(Checker):

    def check(self, call_node: ast.Call, *args) -> List[Error]:
        if isinstance(call_node.func, ast.Name):
            if call_node.func.id == 'print' or call_node.func.id == 'pp':
                return [Print(call_node.lineno, call_node.col_offset)]
        return []
