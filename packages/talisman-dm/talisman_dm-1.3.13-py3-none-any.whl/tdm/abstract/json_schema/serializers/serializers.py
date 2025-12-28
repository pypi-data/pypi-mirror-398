from typing import Collection, Dict, Mapping, Sequence, Tuple, Type, TypeVar, Union

from tdm.abstract.datamodel import AbstractDomainType, AbstractFact, AbstractMarkup, AbstractNode, AbstractNodeMention, AbstractValue, \
    BaseNodeMetadata
from tdm.helper import unfold_union, uniform_collection
from .abstract import AbstractElementSerializer
from .composite import CompositeElementSerializer
from .dataclass import DataclassSerializer
from .domain import DomainTypeSerializer
from .identifiable import IdSerializer
from .identity import IdentitySerializer
from .markup import MarkupSerializer
from .mention import NodeMentionSerializer
from .type_ import TypeSerializer
from .value import ValueSerializer
from .wrap import MappingElementSerializer, SequenceElementSerializer

_BASE_SERIALIZERS = {
    AbstractNode: IdSerializer(AbstractNode),
    AbstractFact: IdSerializer(AbstractFact),
    AbstractNodeMention: NodeMentionSerializer(),
    BaseNodeMetadata: DataclassSerializer(),
    AbstractValue: ValueSerializer(),
    AbstractMarkup: MarkupSerializer(),
    AbstractDomainType: DomainTypeSerializer()
}

_E = TypeVar('_E')
_S = TypeVar('_S')


def _prepare(serializer: AbstractElementSerializer[_E, _S], arg: Type[_E]) -> Tuple[Type[_S], _E]:
    return serializer.field_type(arg), serializer


def get_serializer(t: Type, type_vars: Dict[TypeVar, Type] = None) -> Tuple[type, AbstractElementSerializer]:
    if isinstance(t, TypeVar) and type_vars is not None and t in type_vars:
        return get_serializer(type_vars[t], type_vars)
    t = unfold_union(t)
    if len(t) > 1:
        field_types, serializers = zip(*map(lambda x: get_serializer(x, type_vars), t))
        return Union[field_types], CompositeElementSerializer.build(serializers)
    else:
        t = t[0]
    real_type, arg = uniform_collection(t)
    if real_type is type:
        return _prepare(TypeSerializer(), arg)
    if real_type is not None:
        if issubclass(real_type, Collection):
            wrapped_type, serializer = get_serializer(arg, type_vars)
            if issubclass(real_type, Mapping):
                serializer = MappingElementSerializer(real_type, serializer)
            elif issubclass(real_type, Sequence):
                serializer = SequenceElementSerializer(real_type, serializer)
            else:
                raise TypeError(f"Unsupported collection type `{real_type.__name__}` for serialization.")
            return _prepare(serializer, wrapped_type)
        raise TypeError(f"Unsupported type `{real_type.__name__}` for serialization.")
    possible_types = set(arg.mro()).intersection(_BASE_SERIALIZERS)
    if len(possible_types) == 1:
        return _prepare(_BASE_SERIALIZERS[possible_types.pop()], arg)
    if hasattr(arg, '__dataclass_fields__'):
        return _prepare(DataclassSerializer(), arg)
    return _prepare(IdentitySerializer(arg), arg)
