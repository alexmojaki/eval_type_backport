# eval_type_backport

[![Build Status](https://github.com/alexmojaki/eval_type_backport/workflows/Tests/badge.svg)](https://github.com/alexmojaki/eval_type_backport/actions) [![Coverage Status](https://coveralls.io/repos/github/alexmojaki/eval_type_backport/badge.svg)](https://coveralls.io/github/alexmojaki/eval_type_backport) [![Supports Python versions 3.7+, including PyPy](https://img.shields.io/pypi/pyversions/eval_type_backport.svg)](https://pypi.python.org/pypi/eval_type_backport) [![Anaconda's conda-forge channel](https://anaconda.org/conda-forge/eval-type-backport/badges/version.svg)](https://anaconda.org/conda-forge/eval-type-backport)

This package makes runtime typing inspection with the `typing` module possible with newer syntax in older Python versions.
Specifically, this transforms `X | Y` into `typing.Union[X, Y]`
and `list[X]` into `typing.List[X]` etc. (for all the types made generic in PEP 585)
if the original syntax is not supported in the current Python version.

For users of Pydantic, merely having this package installed should make Pydantic models with newer syntax work in older Python versions.

Here's an example of how to use it directly:

```python
import typing

from eval_type_backport import install_patch

install_patch()


class Foo:
    a: 'int | str'


print(typing.get_type_hints(Foo))
```

In Python 3.9, without the `install_patch`, the above code will raise `TypeError: unsupported operand type(s) for |: 'type' and 'type'`.
With it, it prints `{'a': typing.Union[int, str]}` as expected.

`install_patch` monkey-patches the `typing` module so that things should 'just work' from wherever. To specifically use the backport where you need it instead of patching globally, you can use the `eval_type_backport.eval_type_backport` function directly instead of `typing._eval_type`. Yes, `typing._eval_type` is a protected function that you shouldn't normally be using. This package was written to support Pydantic, which uses it internally.

## Install

From PyPI:

```shell
pip install eval-type-backport
```

or with Conda:

```shell
conda install -c conda-forge eval-type-backport
```
