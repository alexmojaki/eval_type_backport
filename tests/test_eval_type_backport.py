import sys
import typing as t

import pytest

from eval_type_backport import eval_type_backport


def check_eval(code: str, expected: t.Any):
    ref = t.ForwardRef(code)
    for globalns in (None, globals(), {'t': t}, {}):
        for localns in (None, locals(), {'t': t}, {}):
            ns = dict(globalns=globalns, localns=localns)
            try:
                assert eval_type_backport(ref, **ns, try_default=True) == expected
            except NameError:
                continue
            assert eval_type_backport(ref, **ns, try_default=False) == expected
            if sys.version_info >= (3, 10):
                assert eval(code) == expected
                assert t._eval_type(ref, **ns) == expected  # type: ignore


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


def test_other_type_error():
    for code in [
        'int + str',
        '(int | str) + float',
        'int | (str + float)',
        '(int + str) | float',
        'int + (str | float)',
        '(int | str) + (float | None)',
        '(int + str) | (float + None)',
    ]:
        with pytest.raises(TypeError):
            check_eval(code, None)


class FooMeta(type):
    def __or__(self, other):
        raise TypeError('foo')


class Foo(metaclass=FooMeta):
    pass


def test_other_or_type_error():
    for code in [
        'Foo | (int | str)',
    ]:
        with pytest.raises(TypeError) as e:
            check_eval(code, None)
        assert str(e.value) == 'foo'
