import pytest

from . import SafeMode, safe_mode


class CustomException(BaseException):
    pass


def test_no_safe_mode_no_exception():
    @safe_mode()
    def foo():
        return "foo"

    assert foo() == "foo"


def test_no_safe_mode_exception():
    @safe_mode(None)
    def foo():
        raise CustomException()

    with pytest.raises(CustomException):
        foo()


def test_safe_mode_no_exception():
    safe_params = SafeMode((CustomException,), 1)

    @safe_mode(safe_params)
    def foo():
        return "foo"

    assert foo() == "foo"


def test_safe_mode_exception():
    safe_params = SafeMode((CustomException,), 1)

    @safe_mode(safe_params)
    def foo():
        raise CustomException()

    assert foo() is None


def test_safe_mode_other_exception():
    safe_params = SafeMode((CustomException,), 1)

    @safe_mode(safe_params)
    def foo():
        raise Exception()

    with pytest.raises(Exception):
        foo()


def test_safe_mode_exception_default():
    safe_params = SafeMode((CustomException,), 1)

    @safe_mode(safe_params, lambda: "default")
    def foo():
        raise CustomException()

    assert foo() == "default"


def test_safe_mode_max_exception():
    safe_params = SafeMode((CustomException,), 2)

    @safe_mode(safe_params, lambda: "default")
    def foo():
        raise CustomException()

    assert foo() == "default"
    assert foo() == "default"
    with pytest.raises(CustomException):
        foo()
    assert len(safe_params.errors_caught) == 2


def test_safe_mode_max_no_decorator():
    safe_params = SafeMode((CustomException,), 2)

    def foo(arg1):
        return arg1

    def bar():
        return safe_mode(safe_params)(foo)("bar")

    assert bar() == "bar"


def test_safe_mode_max_no_decorator_exception():
    safe_params = SafeMode((CustomException,), 2)

    def foo():
        raise CustomException()

    def bar():
        default = lambda: "default"
        return safe_mode(safe_params, default)(foo)()

    assert bar() == "default"
    assert bar() == "default"
    with pytest.raises(CustomException):
        bar()
    assert len(safe_params.errors_caught) == 2
