# eval_type_backport

[![Build Status](https://github.com/alexmojaki/eval_type_backport/workflows/Tests/badge.svg)](https://github.com/alexmojaki/eval_type_backport/actions) [![Coverage Status](https://coveralls.io/repos/github/alexmojaki/eval_type_backport/badge.svg)](https://coveralls.io/github/alexmojaki/eval_type_backport) [![Supports Python versions 3.7+, including PyPy](https://img.shields.io/pypi/pyversions/eval_type_backport.svg)](https://pypi.python.org/pypi/eval_type_backport)

This is a tiny package providing a replacement for `typing._eval_type` to support newer typing features in older Python versions.

Yes, that's very specific, and yes, `typing._eval_type` is a protected function that you shouldn't normally be using. Really this package is specifically made for https://github.com/pydantic/pydantic/issues/7873.

Currently, it allows unions to be written like `int | str` which is normally only supported in Python 3.10+.
