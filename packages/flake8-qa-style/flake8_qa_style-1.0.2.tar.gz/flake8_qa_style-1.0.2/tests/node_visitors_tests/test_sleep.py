from flake8_plugin_utils import assert_error, assert_not_error

from flake8_qa_style.checkers.node_visitors import FunctionCallVisitor
from flake8_qa_style.checkers.node_visitors.call_checkers import SleepChecker
from flake8_qa_style.errors import SleepWithConstantArgument


def test_call_sleep():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    from time import sleep
    sleep(1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_no_import():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    def sleep(foo): pass
    sleep(1)
    """
    assert_not_error(FunctionCallVisitor, code)


def test_call_sleep_in_func():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    from time import sleep
    def foo(): sleep(1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_in_class():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    from time import sleep
    class Test:
        def foo(): sleep(1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_with_var():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    from time import sleep
    sleep(var)
    """
    assert_not_error(FunctionCallVisitor, code)


def test_call_sleep_as_name():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    from time import sleep as s
    s(1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_import_time():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    import time
    def f(): time.sleep(1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_import_time_kwargs():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    import time
    def f(): time.sleep(secs=1)
    """
    assert_error(FunctionCallVisitor, code, SleepWithConstantArgument)


def test_call_sleep_import_time_kwargs_not_constant():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    import time
    def f(): time.sleep(secs=a)
    """
    assert_not_error(FunctionCallVisitor, code)


def test_call_not_sleep_import_time():
    FunctionCallVisitor.deregister_all()
    FunctionCallVisitor.register_checker(SleepChecker)
    code = """
    import time
    def f(): time.not_sleep(1)
    """
    assert_not_error(FunctionCallVisitor, code)
