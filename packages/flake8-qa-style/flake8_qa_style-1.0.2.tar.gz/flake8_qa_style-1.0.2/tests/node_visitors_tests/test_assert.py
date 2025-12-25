from flake8_plugin_utils import assert_error, assert_not_error

from flake8_qa_style.checkers.node_visitors import AssertVisitor
from flake8_qa_style.errors import (
    AssertSameObjectsForEquality,
    AssertWithConstant
)


def test_assert_same_constants():
    code = """
    assert 1 == 1
    """
    assert_error(AssertVisitor, code, AssertSameObjectsForEquality)


def test_assert_constants():
    code = """
    assert 1 == 2
    """
    assert_not_error(AssertVisitor, code)


def test_assert_same_variables():
    code = """
    assert var == var
    """
    assert_error(AssertVisitor, code, AssertSameObjectsForEquality)


def test_assert_different_variables():
    code = """
    assert var == foo
    """
    assert_not_error(AssertVisitor, code)


def test_assert_with_string():
    code = """
    assert var == 'string'
    """
    assert_error(AssertVisitor, code, AssertWithConstant)


def test_assert_with_number():
    code = """
    assert var == 2
    """
    assert_error(AssertVisitor, code, AssertWithConstant)


def test_assert_with_string_in_variable():
    code = """
    foo = 'string'
    assert var == foo
    """
    assert_not_error(AssertVisitor, code)


def test_assert_with_fstring():
    code = """
    assert var == f'string'
    """
    assert_not_error(AssertVisitor, code)


def test_assert_in_scenario():
    code = """
    class Scenario:
        def when(): pass
        def then(): assert self.foo == self.foo
    """
    assert_error(AssertVisitor, code, AssertSameObjectsForEquality)


def test_correct_assert_in_scenario():
    code = """
    class Scenario:
        def when(): pass
        def then(): assert self.foo == self.var
    """
    assert_not_error(AssertVisitor, code)


def test_assert_with_bool():
    code = """
    assert True
    """
    assert_not_error(AssertVisitor, code)
