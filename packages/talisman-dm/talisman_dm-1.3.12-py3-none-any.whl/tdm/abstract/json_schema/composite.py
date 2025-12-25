from abc import abstractmethod
from collections import defaultdict
from typing import Callable, Dict, Generic, Iterable, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, Field, create_model
from typing_extensions import Annotated, Self

from tdm.abstract.datamodel import AbstractNode
from .model import ElementModel, create_model_for_type

_ElementType = TypeVar('_ElementType')
_DATA = TypeVar('_DATA')


class AbstractLabeledModel(Generic[_ElementType]):

    @abstractmethod
    def deserialize(self, nodes: Dict[str, AbstractNode]) -> Iterable[_ElementType]:
        pass

    @classmethod
    @abstractmethod
    def serialize(cls, elements: Dict[Type[_ElementType], Iterable[_ElementType]]) -> Self:
        pass


class ModelsGenerator(Generic[_DATA]):
    __slots__ = (
        '_base_type', '_include_label',
        '_finalized', '_label2model', '_cls2label_model', '_cls_hierarchy'
    )

    def __init__(self, base_type: Type[_DATA], include_label: bool = False):
        self._base_type = base_type
        self._include_label = include_label

        self._finalized = False
        self._label2model: Dict[str, Type[ElementModel[_DATA]]] = {}
        self._cls2label_model: Dict[Type[_DATA], Tuple[str, Type[ElementModel[_DATA]]]] = {}
        self._cls_hierarchy: Dict[Type[_DATA], List[Type[_DATA]]] = defaultdict(list)

    def generate_model(self, cls: Type[_DATA] = None, *, label: str = None):
        def wrap(cls: Type[_DATA]):
            label_ = label if label is not None else cls.__name__
            if label_ in self._label2model or cls in self._cls2label_model:
                raise ValueError(f"Label '{label_}' or class '{cls}' is already registered.")
            self._register(label_, cls)
            return cls

        if cls is None:
            return wrap

        return wrap(cls)

    def _register(self, label: str, cls: Type[_DATA]) -> None:
        if self._finalized:
            raise Exception(f"Model for {self} has already been generated.")
        model = create_model_for_type(cls, label if self._include_label else None)
        self._label2model[label] = model
        self._cls2label_model[cls] = label, model
        for t in cls.mro():
            if issubclass(t, self._base_type):
                self._cls_hierarchy[t].append(cls)

    def generate_labeled_model(self, name: str) -> Type[AbstractLabeledModel[_DATA]]:
        if self._finalized:
            raise Exception(f"Model for {self} has already been generated.")
        self._finalized = True
        deserialization_order = tuple(self._label2model)

        base_type = self._base_type

        class LabeledModel(BaseModel, AbstractLabeledModel[_DATA]):

            def deserialize(self, nodes: Dict[str, AbstractNode]) -> Iterable[_ElementType]:
                id2element: Dict[str, _DATA] = {}
                elements = {
                    AbstractNode: nodes,
                    base_type: id2element
                }
                for label in deserialization_order:
                    for model in self.__dict__.get(label) or tuple():
                        model: ElementModel
                        element = model.deserialize(elements)
                        id2element[element.id] = element
                return id2element.values()

            @classmethod
            def serialize(cls, elements: Dict[Type[_ElementType], Iterable[_ElementType]]) -> Self:
                kwargs = {}
                for type_, els in elements.items():
                    label, model = self._cls2label_model[type_]
                    kwargs[label] = tuple(model.serialize(element) for element in els)
                return cls.model_construct(**kwargs)

        model_fields = {label: (Optional[Tuple[model, ...]], None) for label, model in self._label2model.items()}
        model = create_model(name, __base__=LabeledModel, **model_fields)
        return model

    def generate_union_model(self, discriminator: str = None) \
            -> Tuple[Dict[Type[_DATA], Type[ElementModel[_DATA]]], Callable[[_DATA], ElementModel[_DATA]]]:
        if self._finalized:
            raise ValueError(f"Model for {self} has already been generated.")
        self._finalized = True

        result = {}
        for cls, clss in self._cls_hierarchy.items():
            if len(clss) == 1:
                result[cls] = self._cls2label_model[clss[0]][1]
            else:
                types = tuple(map(lambda cls_: self._cls2label_model[cls_][1], clss))
                result[cls] = Annotated[Union[types], Field(discriminator=discriminator)] if discriminator is not None else Union[types]

        def serialize(element: _DATA) -> ElementModel[_DATA]:
            if type(element) not in result:
                try:
                    supertype = next(filter(lambda t: t in result, type(element).mro()))
                except StopIteration:
                    raise ValueError(f"There is no applicable serializers for {type(element)} type (object: {element})")
                result[type(element)] = result[supertype]
            return result[type(element)].serialize(element)

        return result, serialize
