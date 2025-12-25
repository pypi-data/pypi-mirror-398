import ast
from typing import Union

from flake8_qa_style.checkers.node_visitors._visitor_with_filename import (
    VisitorWithFilename
)
from flake8_qa_style.errors import (
    ArgAnnotationMissing,
    ReturnAnnotationMissing
)


class AnnotationVisitor(VisitorWithFilename):

    def check_annotation(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):

        # exclude annotation check for dunder methods
        if node.name.startswith('__') and node.name.endswith('__'):
            return

        for arg in node.args.args:
            if arg.annotation is None and arg.arg != 'self' and arg.arg != 'cls':
                self.error_from_node(ArgAnnotationMissing, node,
                                     arg_name=arg.arg,
                                     func_name=node.name)

        if self.config.skip_property_return_annotation:
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Name) and decorator.id == 'property':
                    return

        for line in node.body:
            if isinstance(line, ast.Return):
                if node.returns is None:
                    self.error_from_node(ReturnAnnotationMissing, node,
                                         func_name=node.name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.check_annotation(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.check_annotation(node)
