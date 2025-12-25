from typing import Callable, Dict, Tuple, Type

from tdm.abstract.datamodel.value import AbstractValue
from tdm.abstract.json_schema import ElementModel, get_model_generator


def register_value_models() -> Tuple[Dict[Type[AbstractValue], Type[ElementModel]], Callable[[AbstractValue], ElementModel]]:
    import tdm.datamodel.values as values
    values

    # TODO: add plugins here

    return get_model_generator(AbstractValue).generate_union_model()


VALUE_MODELS, serialize_value = register_value_models()
