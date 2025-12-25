from typing import Callable, Iterable, Tuple, Type, Union

from pydantic import Field, create_model
from typing_extensions import Annotated

from tdm.abstract.datamodel import AbstractNode, TalismanDocument
from tdm.abstract.json_schema import ElementModel, get_model_generator
from tdm.helper import register_in_module, unfold_union


def register_node_models() -> Tuple[Type[ElementModel[AbstractNode]], Callable[[AbstractNode], ElementModel[AbstractNode]]]:
    import tdm.datamodel.nodes as nodes  # we need this import for serializers registration
    nodes

    # TODO: here plugin for extra document nodes could be added

    models, serialize = get_model_generator(AbstractNode).generate_union_model()

    # add children field to all node models. serialize function doesn't generate value for children field
    kwargs = {
        'children': (Tuple[str, ...], ...)
    }

    model_mapping = {}
    tree_models = []

    for model in unfold_union(models[AbstractNode]):
        tree_model = register_in_module(create_model(f"Tree{model.__name__}", __base__=model, **kwargs))
        model_mapping[model] = tree_model
        tree_models.append(tree_model)

    NodeModel_ = Annotated[Union[tuple(tree_models)], Field(discriminator='type')]  # noqa N806

    # wrap serialize to generate tree node instead of node
    def serialize_node(node: AbstractNode) -> ElementModel[AbstractNode]:
        serialized = serialize(node)
        return model_mapping[type(serialized)].model_construct(**serialized.__dict__)

    return NodeModel_, serialize_node


NodeModel, serialize_node = register_node_models()


def fill_children(node_models: Iterable[NodeModel], document: TalismanDocument) -> None:
    for node in node_models:
        children = tuple(n.id for n in document.child_nodes(node.id))
        node.children = children
