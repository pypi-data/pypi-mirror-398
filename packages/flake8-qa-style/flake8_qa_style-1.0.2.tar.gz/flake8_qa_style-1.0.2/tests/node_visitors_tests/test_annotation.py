from flake8_plugin_utils import assert_error, assert_not_error

from flake8_qa_style.checkers.node_visitors import AnnotationVisitor
from flake8_qa_style.config import DefaultConfig
from flake8_qa_style.errors import (
    ArgAnnotationMissing,
    ReturnAnnotationMissing
)


def test_func_no_annotation():
    code = """
    def f(var): pass
    """
    assert_error(AnnotationVisitor, code, ArgAnnotationMissing, arg_name='var', func_name='f',
                 config=DefaultConfig())


def test_func_with_annotation():
    code = """
    def f(var: int): pass
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_func_with_partial_annotation():
    code = """
    def f(var_1: int, var_2): pass
    """
    assert_error(AnnotationVisitor, code, ArgAnnotationMissing, arg_name='var_2', func_name='f',
                 config=DefaultConfig())


def test_func_with_annotation_and_defaults():
    code = """
    def f(var_1: int, var_2: bool = True): pass
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_func_without_annotation_and_defaults():
    code = """
    def f(var_1: int, var_2 = True): pass
    """
    assert_error(AnnotationVisitor, code, ArgAnnotationMissing,
                 func_name='f', arg_name='var_2', config=DefaultConfig())


def test_func_self_arg():
    code = """
    def f(self): pass
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_func_cls_arg():
    code = """
    def f(cls): pass
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_func_no_return_annotation():
    code = """
    def f(): return True
    """
    assert_error(AnnotationVisitor, code, ReturnAnnotationMissing, func_name='f',
                 config=DefaultConfig())


def test_func_return_annotation():
    code = """
    def f() -> bool: return True
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_func_no_return_annotation_for_property_skipped():
    code = """
    @property
    def f(): return True
    """
    assert_not_error(AnnotationVisitor, code,
                     config=DefaultConfig(skip_property_return_annotation=True))


def test_func_no_return_annotation_for_property():
    code = """
    @property
    def f(): return True
    """
    assert_error(AnnotationVisitor, code, ReturnAnnotationMissing,
                 func_name='f',
                 config=DefaultConfig(skip_property_return_annotation=False))


def test_dunder_func_without_annotation():
    code = """
    def __init__(self, attribute):
      self.attribute = attribute
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())


def test_dunder_return_func_without_annotation():
    code = """
    def __dict__(self):
      return 'some string'
    """
    assert_not_error(AnnotationVisitor, code, config=DefaultConfig())
