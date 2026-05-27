from .eval_type_backport import ForwardRef, eval_type_backport, install_patch

try:
    from .version import __version__
except ImportError:  # pragma: no cover
    # version.py is auto-generated with the git tag when building
    __version__ = '???'

__all__ = ['install_patch', 'ForwardRef', 'eval_type_backport', '__version__']
