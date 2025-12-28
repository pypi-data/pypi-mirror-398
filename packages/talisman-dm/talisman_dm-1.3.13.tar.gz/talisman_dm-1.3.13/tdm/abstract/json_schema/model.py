import dataclasses
from dataclasses import fields
from typing import Any, Dict, Generic, Optional, Type, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model
from typing_extensions import Literal, Self

from tdm.helper import cache_result, generics_mapping, register_in_module
from .serializers import AbstractElementModel, AbstractElementSerializer, get_serializer

_Element = TypeVar('_Element')


def remove_serializers(schema: Dict[str, Any]):
    for prop in schema.get('properties', {}).values():
        prop.pop('_serializer', None)


class ElementModel(BaseModel, AbstractElementModel[_Element], Generic[_Element]):
    # TODO[pydantic]: do not include serializers into model and remove dataclass from AbstractElementSerializer
    model_config = ConfigDict(extra='forbid', json_schema_extra=remove_serializers)

    def deserialize(self, typed_id2element: Dict[type, Dict[str, Any]]) -> _Element:
        raise NotImplementedError

    @classmethod
    def serialize(cls, element: _Element) -> Self:
        kwargs = {}
        for key, value in element.__dict__.items():
            name = key[1:] if key.startswith('_') else key
            kwargs[name] = cls.model_fields[name].json_schema_extra['_serializer'].serialize(value)
        return cls(**kwargs)


def _wrap_deserializer(coll_type: type, serializer: AbstractElementSerializer):
    def deserialize(values, *args):
        return coll_type(serializer.deserialize(v, *args) for v in values)

    return deserialize


_BaseType = TypeVar('_BaseType', bound=type)


@cache_result()
def create_model_for_type(type_: Type[_Element], label: Optional[str] = None) -> Type[ElementModel[_Element]]:
    type_vars = generics_mapping(type_)

    model_fields = {}

    for field in fields(type_):
        name = field.name
        if name.startswith('_'):
            name = name[1:]
        default_value = field.default if field.default is not dataclasses.MISSING else ...

        field_type, serializer = get_serializer(field.type, type_vars)

        if hasattr(field_type, '__metadata__'):  # field type is already Annotated
            metadata = field_type.__metadata__
            if isinstance(metadata, tuple):
                metadata = metadata[0]
            discriminator = metadata.discriminator
            model_fields[name] = (field_type.__origin__, Field(default_value, discriminator=discriminator, _serializer=serializer))
        else:
            model_fields[name] = (field_type, Field(default_value, _serializer=serializer))
    if label:
        model_fields['type'] = (Literal[label], label)

    model = register_in_module(create_model(f"{type_.__name__}Model", __base__=ElementModel, **model_fields))

    def deserialize(self: model, typed_id2element: Dict[type, Dict[str, Any]]) -> type_:
        kwargs = {}
        for f, info in type_.__dataclass_fields__.items():
            if not info.init:
                continue
            n = f[1:] if f.startswith('_') else f
            if n not in self.__dict__:
                continue
            kwargs[f] = self.model_fields[n].json_schema_extra['_serializer'].deserialize(getattr(self, n), typed_id2element)
        return type_(**kwargs)

    model.deserialize = deserialize

    return model
