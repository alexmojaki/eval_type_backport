import sys
import typing as t

import pytest

from eval_type_backport import install_patch


runtime_node_class: t.Optional[t.Type[t.Any]]
if sys.version_info[:2] >= (3, 9):

    class RuntimeNode:
        children: list['RuntimeNode']

    runtime_node_class = RuntimeNode
else:
    runtime_node_class = None


def test_install_patch_supports_get_type_hints_for_pep585_forward_refs():
    if runtime_node_class is None:
        pytest.skip('PEP 585 generic aliases were added in Python 3.9')
    runtime_node = t.cast(t.Any, runtime_node_class)

    original_evaluate = t.ForwardRef._evaluate
    original_eval_type = t._eval_type  # type: ignore[attr-defined]
    try:
        install_patch()
        assert t.get_type_hints(runtime_node) == {'children': list[runtime_node]}
    finally:
        t.ForwardRef._evaluate = original_evaluate
        t._eval_type = original_eval_type  # type: ignore[attr-defined]
