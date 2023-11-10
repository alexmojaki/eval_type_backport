import sys
import typing

from eval_type_backport import eval_type_backport


def check_eval(code: str, expected: typing.Any):
    assert eval_type_backport(typing.ForwardRef(code)) == expected
    if sys.version_info >= (3, 10):
        assert eval(code) == expected


def test_eval_type_backport():
    assert eval_type_backport(typing.ForwardRef('int')) == int
    assert eval_type_backport(typing.ForwardRef('int | str')) == typing.Union[int, str]
