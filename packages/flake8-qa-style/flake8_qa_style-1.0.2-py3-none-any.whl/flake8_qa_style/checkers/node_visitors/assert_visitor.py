import ast

from flake8_qa_style.checkers.node_visitors._visitor_with_filename import (
    VisitorWithFilename
)
from flake8_qa_style.errors import (
    AssertSameObjectsForEquality,
    AssertWithConstant
)


class AssertVisitor(VisitorWithFilename):

    def visit_Assert(self, node: ast.Assert):
        if isinstance(node.test, ast.Compare):

            left = node.test.left
            right = node.test.comparators[0]

            # assert 1 == 2
            if isinstance(left, ast.Constant) and isinstance(right, ast.Constant):

                if left.value == right.value:
                    self.error_from_node(AssertSameObjectsForEquality, node)

            # assert var == var
            elif isinstance(left, ast.Name) and isinstance(right, ast.Name):
                if left.id == right.id:
                    self.error_from_node(AssertSameObjectsForEquality, node)

            # assert var == 'string' or assert var == 1
            elif isinstance(right, ast.Constant):
                self.error_from_node(AssertWithConstant, node)

            # assert self.foo == self.foo
            elif isinstance(left, ast.Attribute) and isinstance(right, ast.Attribute):
                if left.attr == right.attr:  # foo == foo
                    if (
                        isinstance(left.value, ast.Name) and isinstance(right.value, ast.Name)
                        and left.value.id == right.value.id
                    ):
                        self.error_from_node(AssertSameObjectsForEquality, node)
