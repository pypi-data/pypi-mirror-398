import ast
from typing import List

from flake8_plugin_utils import Error

from flake8_qa_style.checkers.node_visitors.function_call_visitor import (
    Checker,
    Context,
    FunctionCallVisitor
)
from flake8_qa_style.errors import SleepWithConstantArgument


@FunctionCallVisitor.register_checker
class SleepChecker(Checker):

    def check(self, call_node: ast.Call, context: Context) -> List[Error]:
        if (
            context.sleep_function_name
            and isinstance(call_node.func, ast.Name)
            and call_node.func.id == context.sleep_function_name
        ) or (
            context.is_imported_module_time
            and isinstance(call_node.func, ast.Attribute)
            and call_node.func.attr == 'sleep'
            and call_node.func.value.id == 'time'
        ):
            if call_node.args:
                if isinstance(call_node.args[0], ast.Constant):
                    return [SleepWithConstantArgument(call_node.lineno, call_node.col_offset)]
            else:
                if (
                    call_node.keywords
                    and call_node.keywords[0].arg == 'secs'
                    and isinstance(call_node.keywords[0].value, ast.Constant)
                ):
                    return [SleepWithConstantArgument(call_node.lineno, call_node.col_offset)]

        return []
