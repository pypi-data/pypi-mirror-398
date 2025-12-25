"""
Plugin to fix the type of certain methods on ``Just`` and ``Nothing`` objects.
"""

import typing as t

from mypy.checkmember import analyze_member_access
from mypy.plugin import MethodContext, Plugin
from mypy.types import Instance, LiteralType, Type


def attr_callback(ctx: MethodContext) -> Type:
    """Callback to determine type for a ``.attr`` call on a ``Maybe``."""
    ((attr,),) = ctx.arg_types
    attr_maybe_value: t.Optional[Type] = attr
    if isinstance(attr, Instance):
        attr_maybe_value = attr.last_known_value

    if not isinstance(attr_maybe_value, LiteralType):
        ctx.api.fail(
            'The attr to Maybe.attr should be a literal',
            ctx.context,
        )
        return ctx.default_return_type

    attr_value = attr_maybe_value.value

    if not isinstance(attr_value, str):  # pragma: no cover
        return ctx.default_return_type

    assert isinstance(ctx.type, Instance)
    (base,) = ctx.type.args
    if not (
        isinstance(base, Instance)
        and base.type.has_readable_member(attr_value)
    ):
        ctx.api.fail(
            'The {} has no attribute named {}'.format(base, attr_value),
            ctx.context,
        )
        return ctx.default_return_type

    checker = ctx.api.expr_checker  # type: ignore

    member = analyze_member_access(
        attr_value,
        base,
        ctx.context,
        is_lvalue=False,
        is_super=False,
        is_operator=False,
        msg=checker.msg,
        original_type=base,
        chk=checker.chk,
        in_literal_context=checker.is_literal_context(),
    )
    assert isinstance(ctx.default_return_type, Instance)
    return ctx.default_return_type.copy_modified(args=[member])


class CgMaybePlugin(Plugin):
    """Mypy plugin definition."""

    def get_method_hook(
        self,
        fullname: str,
    ) -> t.Optional[t.Callable[[MethodContext], Type]]:
        """Get the function to be called by mypy."""
        if fullname in (
            'cg_maybe._just.Just.attr',
            'cg_maybe._nothing._Nothing.attr',
        ):
            return lambda ctx: attr_callback(ctx)
        return None


def plugin(_: str) -> t.Type[CgMaybePlugin]:
    """Get the mypy plugin definition."""
    # ignore version argument if the plugin works with all mypy versions.
    return CgMaybePlugin
