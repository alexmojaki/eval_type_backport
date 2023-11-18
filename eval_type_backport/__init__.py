from .eval_type_backport import eval_type_backport

try:
    from .version import __version__
except ImportError:  # pragma: no cover
    # version.py is auto-generated with the git tag when building
    __version__ = '???'

__all__ = ['eval_type_backport', '__version__']
