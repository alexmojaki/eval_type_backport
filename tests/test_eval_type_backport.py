import sys
import typing as t

from eval_type_backport import eval_type_backport, eval_type_backport_direct


def check_eval(code: str, expected: t.Any):
    ref = t.ForwardRef(code)
    assert eval_type_backport(ref, globals(), locals()) == expected
    assert eval_type_backport_direct(ref, globals(), locals()) == expected
    if sys.version_info >= (3, 10):
        assert eval(code) == expected
        assert t._eval_type(ref, globals(), locals()) == expected  # type: ignore


def test_eval_type_backport():
    check_eval('int', int)
    check_eval('int | str', t.Union[int, str])
    check_eval('int | str | float', t.Union[int, str, float])
    check_eval('int | None', t.Optional[int])
    check_eval('int | None | str', t.Optional[t.Union[int, str]])
    check_eval('t.List[int | str]', t.List[t.Union[int, str]])
    check_eval('t.List[int | str] | None', t.Optional[t.List[t.Union[int, str]]])
    check_eval(
        't.List[int | str] | t.List[float | str]',
        t.Union[
            t.List[t.Union[int, str]],
            t.List[t.Union[float, str]],
        ],
    )
    check_eval(
        't.List[int | str] | t.List[float | str] | None',
        t.Optional[
            t.Union[
                t.List[t.Union[int, str]],
                t.List[t.Union[float, str]],
            ]
        ],
    )
    check_eval(
        't.List[t.List[int | str] | None] | t.List[float | str] | None',
        t.Optional[
            t.Union[
                t.List[t.Optional[t.List[t.Union[int, str]]]],
                t.List[t.Union[float, str]],
            ]
        ],
    )
    check_eval(
        't.List[t.List[int | str] | None] | t.List[float | str] | None | t.List[None]',
        t.Optional[
            t.Union[
                t.List[t.Optional[t.List[t.Union[int, str]]]],
                t.List[t.Union[float, str]],
                t.List[None],
            ]
        ],
    )
