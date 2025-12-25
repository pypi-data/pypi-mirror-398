from typing import Dict

from ._view import AbstractView, generate_dataclass_view


def pack_view_state(id2view: Dict[str, AbstractView]) -> dict:
    result = {
        id_: (_orig_type(view), view.__dict__)
        for id_, view in id2view.items()
    }
    return result


def _orig_type(view: AbstractView) -> type:
    if isinstance(view, AbstractView):
        return view.orig_type()
    return type(view)


def unpack_view_state(state: dict) -> Dict[str, AbstractView]:
    result = {
        id_: generate_dataclass_view(cls)[0](**data)
        for id_, (cls, data) in state.items()
    }
    return result
