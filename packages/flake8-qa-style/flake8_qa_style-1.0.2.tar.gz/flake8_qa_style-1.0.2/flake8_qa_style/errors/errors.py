from flake8_plugin_utils import Error


class SleepWithConstantArgument(Error):
    code = 'CS001'
    message = 'using sleep with constant as argument is prohibited. Use sleep(var) instead'


class Print(Error):
    code = 'CS002'
    message = 'try to avoid printing. If it\'s necessary ignore this warning'


# assert var == var
class AssertSameObjectsForEquality(Error):
    code = 'CS003'
    message = 'comparing same objects in assert doesn\'t make any sense'


# assert var == 'string'
# assert var == 2
class AssertWithConstant(Error):
    code = 'CS004'
    message = 'assert variable with constants is not allowed, move constant to libs'


class ArgAnnotationMissing(Error):
    code = 'CS005'
    message = 'missing annotation for argument "{arg_name}" for function "{func_name}"'


class ReturnAnnotationMissing(Error):
    code = 'CS006'
    message = 'missing return annotation for function "{func_name}"'


class NoBlankFileStart(Error):
    code = 'CS007'
    message = 'file should not start with a blank line'
