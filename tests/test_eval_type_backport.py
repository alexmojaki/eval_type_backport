from __future__ import annotations

import collections
import contextlib
import re
import sys
import typing as t

import pytest

from eval_type_backport import ForwardRef, eval_type_backport
from eval_type_backport.eval_type_backport import new_generic_types

str((collections, contextlib, re))  # mark these as used (by eval calls)


eval_type = t._eval_type  # type: ignore[attr-defined]


def eval_kwargs(code: str):
    result = []
    for globalns in (None, globals(), {'t': t}, {}):
        for localns in (None, locals(), {'t': t}, {}):
            for try_default in (True, False):
                kwargs = t.cast(
                    t.Dict[str, t.Any],
                    dict(globalns=globalns, localns=localns, try_default=try_default),
                )
                try:
                    eval_type_backport(t.ForwardRef(code), **kwargs)
                except NameError:
                    continue
                except Exception:
                    pass
                result.append(kwargs)
    assert len(result) >= 8
    return result


def check_eval(code: str, expected: t.Any):
    if sys.version_info[:2] < (3, 9):
        code_with_list = code.replace('t.List', 'list')
        if code_with_list != code:
            check_eval(code_with_list, expected)
    typing_ref = t.ForwardRef(code)
    backport_ref = ForwardRef(code)
    for kwargs in eval_kwargs(code):
        for ref in typing_ref, backport_ref:
            assert eval_type_backport(ref, **kwargs) == expected
            if sys.version_info >= (3, 10):
                assert eval(code) == expected
                assert (
                    eval_type(
                        ref,
                        globalns=kwargs['globalns'],
                        localns=kwargs['localns'],
                    )
                    == expected
                )


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
    if hasattr(t, 'Literal'):
        check_eval('t.Literal[1]', t.Literal[1])
        check_eval('t.Literal[1] | t.Literal[2]', t.Union[t.Literal[1], t.Literal[2]])
        check_eval(
            't.List[t.Literal[1] | t.Literal[2]]',
            t.List[t.Union[t.Literal[1], t.Literal[2]]],
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
        with pytest.raises(TypeError):
            eval_type(ForwardRef(code), None, None)


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


class BarMeta(type):
    def __or__(self, other):
        return t.Dict[self, other]  # type: ignore

    def __ror__(self, other):
        return t.Dict[other, self]  # type: ignore


class Bar(metaclass=BarMeta):
    pass


def test_working_or():
    check_eval(
        't.List[(Bar | t.List[int]) | (str | Bar)] | float | t.List[Bar]',
        t.Union[
            t.List[t.Union[t.Dict[Bar, t.List[int]], t.Dict[str, Bar]]],
            float,
            t.List[Bar],
        ],
    )


def check_subscript(code: str, expected_old: t.Any):
    typing_ref = t.ForwardRef(code)
    backport_ref = ForwardRef(code)
    for kwargs in eval_kwargs(code):
        for ref in typing_ref, backport_ref:
            if sys.version_info >= (3, 9):
                expected_new = eval(code)
                assert str(expected_new) == code
                assert eval_type_backport(ref, **kwargs) == expected_new
                args = t.get_args(expected_old)
                origin = t.get_origin(expected_old)
                assert args == t.get_args(expected_new)
                assert origin == t.get_origin(expected_new)
                assert origin[args] == expected_new != expected_old
                assert t.get_origin(getattr(t, new_generic_types[origin])) == origin
            else:
                assert eval_type_backport(ref, **kwargs) == expected_old


def test_subscript():
    check_subscript(
        'tuple[int]',
        t.Tuple[int],
    )
    check_subscript(
        'tuple[int, int]',
        t.Tuple[int, int],
    )
    check_subscript(
        'tuple[int, str]',
        t.Tuple[int, str],
    )
    check_subscript(
        'tuple[int, ...]',
        t.Tuple[int, ...],
    )
    check_subscript(
        'list[int]',
        t.List[int],
    )
    check_subscript(
        'dict[int, str]',
        t.Dict[int, str],
    )
    check_subscript(
        'set[int]',
        t.Set[int],
    )
    check_subscript(
        'frozenset[int]',
        t.FrozenSet[int],
    )
    check_subscript(
        'type[int]',
        t.Type[int],
    )
    check_subscript(
        'collections.deque[int]',
        t.Deque[int],
    )
    check_subscript(
        'collections.defaultdict[int, str]',
        t.DefaultDict[int, str],
    )
    check_subscript(
        'collections.abc.Set[int]',
        t.AbstractSet[int],
    )
    # Python 3.13 added a second type parameter to typing.ContextManager which defaults to bool | None.
    check_subscript(
        'contextlib.AbstractContextManager[int]'
        if sys.version_info < (3, 13)
        else 'contextlib.AbstractContextManager[int, bool | None]',
        t.ContextManager[int],
    )
    check_subscript(
        'contextlib.AbstractAsyncContextManager[int]'
        if sys.version_info < (3, 13)
        else 'contextlib.AbstractAsyncContextManager[int, bool | None]',
        t.AsyncContextManager[int],
    )
    check_subscript(
        'collections.OrderedDict[int, str]',
        t.OrderedDict[int, str],
    )
    check_subscript(
        'collections.Counter[int]',
        t.Counter[int],
    )
    check_subscript(
        'collections.ChainMap[int, str]',
        t.ChainMap[int, str],
    )
    check_subscript(
        'collections.abc.Awaitable[int]',
        t.Awaitable[int],
    )
    check_subscript(
        'collections.abc.Coroutine[int, str, float]',
        t.Coroutine[int, str, float],
    )
    check_subscript(
        'collections.abc.AsyncIterable[int]',
        t.AsyncIterable[int],
    )
    check_subscript(
        'collections.abc.AsyncIterator[int]',
        t.AsyncIterator[int],
    )
    check_subscript(
        'collections.abc.AsyncGenerator[int, str]',
        t.AsyncGenerator[int, str],
    )
    check_subscript(
        'collections.abc.Iterable[int]',
        t.Iterable[int],
    )
    check_subscript(
        'collections.abc.Iterator[int]',
        t.Iterator[int],
    )
    check_subscript(
        'collections.abc.Generator[int, str, float]',
        t.Generator[int, str, float],
    )
    check_subscript(
        'collections.abc.Reversible[int]',
        t.Reversible[int],
    )
    check_subscript(
        'collections.abc.Container[int]',
        t.Container[int],
    )
    check_subscript(
        'collections.abc.Collection[int]',
        t.Collection[int],
    )
    check_subscript(
        'collections.abc.Callable[[int], str]',
        t.Callable[[int], str],
    )
    check_subscript(
        'collections.abc.MutableSet[int]',
        t.MutableSet[int],
    )
    check_subscript(
        'collections.abc.Mapping[int, str]',
        t.Mapping[int, str],
    )
    check_subscript(
        'collections.abc.MutableMapping[int, str]',
        t.MutableMapping[int, str],
    )
    check_subscript(
        'collections.abc.Sequence[int]',
        t.Sequence[int],
    )
    check_subscript(
        'collections.abc.MutableSequence[int]',
        t.MutableSequence[int],
    )
    check_subscript(
        'collections.abc.MappingView[int]',
        t.MappingView[int],  # type: ignore
    )
    check_subscript(
        'collections.abc.KeysView[int]',
        t.KeysView[int],
    )
    check_subscript(
        'collections.abc.ItemsView[int, str]',
        t.ItemsView[int, str],
    )
    check_subscript(
        'collections.abc.ValuesView[int]',
        t.ValuesView[int],
    )
    check_subscript(
        're.Pattern[str]',
        t.Pattern[str],
    )
    check_subscript(
        're.Match[str]',
        t.Match[str],
    )


def test_copy_forward_ref_attrs():
    ref = t.ForwardRef(
        't.ClassVar[int | str]',
        is_argument=False,
        **({} if sys.version_info < (3, 9, 8) else {'is_class': True}),
    )
    eval_type_backport(ref, globalns=globals(), localns=locals())
