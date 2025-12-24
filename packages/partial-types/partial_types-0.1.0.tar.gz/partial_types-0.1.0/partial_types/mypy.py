# mypy: ignore-errors

from mypy.nodes import TypeInfo
from mypy.plugin import AnalyzeTypeContext, Plugin
from mypy.types import AnyType, TypedDictType, TypeOfAny, UnionType, get_proper_type


class PydanticPartialPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        if fullname == "autodbg.partial.Partial":
            return partial_type_analyze_hook
        return None


def partial_type_analyze_hook(ctx: AnalyzeTypeContext):
    if not getattr(ctx.type, "args", None):
        return ctx.default_type

    type_arg_expr = ctx.type.args[0]
    analyzed_type = ctx.api.analyze_type(type_arg_expr)
    proper_type = get_proper_type(analyzed_type)

    info: TypeInfo | None = getattr(proper_type, "type", None)
    if info is None or not info.mro:
        return ctx.default_type

    items = {}
    for name, symnode in info.names.items():
        if symnode.node and hasattr(symnode.node, "type"):
            items[name] = symnode.node.type

    dict_str_any = ctx.api.named_type(
        "builtins.dict",
        [ctx.api.named_type("builtins.str"), AnyType(TypeOfAny.explicit)],
    )

    partial_typeddict = TypedDictType(
        items=items,
        required_keys=set(),
        readonly_keys=set(),
        fallback=dict_str_any,
    )

    return UnionType.make_union([proper_type, partial_typeddict])


def plugin(version: str):
    return PydanticPartialPlugin
