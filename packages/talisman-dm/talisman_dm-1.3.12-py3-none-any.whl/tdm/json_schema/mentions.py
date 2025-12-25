from typing import Callable, Dict, Tuple, Type

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import ElementModel, get_model_generator


def register_mention_models() -> \
        Tuple[Dict[Type[AbstractNodeMention], Type[ElementModel]], Callable[[AbstractNodeMention], ElementModel]]:
    import tdm.datamodel.mentions as mentions  # we need mentions models to be registered
    mentions

    # TODO: add plugins support here

    return get_model_generator(AbstractNodeMention).generate_union_model(discriminator='type')


MENTION_MODELS, serialize_mention = register_mention_models()
