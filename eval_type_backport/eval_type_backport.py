from __future__ import annotations

import ast
import typing
import uuid
from typing import Any


def is_unsupported_types_for_union_error(e: TypeError) -> bool:
    return str(e).startswith('unsupported operand type(s) for |: ')


class UnionTransformer(ast.NodeTransformer):
    """
    Transforms `X | Y` into `Union[X, Y]` if `X | Y` is not supported.
    """

    def __init__(self, globalns: dict[str, Any] | None, localns: dict[str, Any] | None):
        # This logic for handling Nones is copied from typing.ForwardRef._evaluate
        if globalns is None and localns is None:
            globalns = localns = {}
        elif globalns is None:
            # apparently pyright doesn't infer this automatically
            assert localns is not None
            globalns = localns
        elif localns is None:
            # apparently pyright doesn't infer this automatically
            assert globalns is not None
            localns = globalns

        self.typing_name = f'typing_{uuid.uuid4().hex}'
        self.globalns = globalns
        self.localns = {**localns, self.typing_name: typing}

    def eval_type(self, node: ast.AST) -> Any:
        if not isinstance(node, ast.Expression):
            node = ast.copy_location(ast.Expression(node), node)
        ref = typing.ForwardRef(ast.dump(node))
        ref.__forward_code__ = compile(node, '<node>', 'eval')
        return typing._eval_type(  # type: ignore
            ref, self.globalns, self.localns
        )

    def visit_BinOp(self, node) -> ast.BinOp | ast.Subscript:
        if isinstance(node.op, ast.BitOr):
            left_node = self.visit(node.left)
            right_node = self.visit(node.right)
            left_val = self.eval_type(left_node)
            right_val = self.eval_type(right_node)
            try:
                _ = left_val | right_val
            except TypeError as e:
                if not is_unsupported_types_for_union_error(e):
                    raise
                # Replace `left | right` with `typing.Union[left, right]`
                replacement = ast.Subscript(
                    value=ast.Attribute(
                        value=ast.Name(id=self.typing_name, ctx=ast.Load()),
                        attr='Union',
                        ctx=ast.Load(),
                    ),
                    slice=ast.Index(value=ast.Tuple(elts=[left_node, right_node], ctx=ast.Load())),
                    ctx=ast.Load(),
                )
                return ast.fix_missing_locations(replacement)

        return node


def _eval_direct(
    value: typing.ForwardRef,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
):
    tree = ast.parse(value.__forward_arg__, mode='eval')
    transformer = UnionTransformer(globalns, localns)
    tree = transformer.visit(tree)
    return transformer.eval_type(tree)


def eval_type_backport(
    value: Any,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
    try_default: bool = True,
) -> Any:
    """
    Like `typing._eval_type`, but lets older Python versions use newer typing features.
    Currently this just means that `X | Y` is converted to `Union[X, Y]` if `X | Y` is not supported.
    This would also be the place to add support for `list[int]` instead of `List[int]` etc.
    """
    if not try_default:
        return _eval_direct(value, globalns, localns)
    try:
        return typing._eval_type(  # type: ignore
            value, globalns, localns
        )
    except TypeError as e:
        if not (isinstance(value, typing.ForwardRef) and is_unsupported_types_for_union_error(e)):
            raise
        return _eval_direct(value, globalns, localns)
