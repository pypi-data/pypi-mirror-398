from typing import ClassVar, Dict, Optional, Tuple

from pydantic import BaseModel, PrivateAttr
from typing_extensions import Literal

from .abstract.datamodel import AbstractDomain, AbstractNode, TalismanDocument
from .datamodel.document import TalismanDocumentFactory
from .json_schema.facts import FactsModel
from .json_schema.links import NodeLinksModel
from .json_schema.nodes import NodeModel, fill_children, serialize_node


class TalismanDocumentModel(BaseModel):
    """
    Represents a Pydantic model for serializing and deserializing a Talisman document.
    """

    _DEFAULT_DOMAIN: ClassVar[AbstractDomain] = None
    _domain: AbstractDomain = PrivateAttr(None)

    VERSION: Literal['1.0'] = ...  # should be required in the TDM schema
    id: str
    main_node: str
    content: Tuple[NodeModel, ...]
    links: NodeLinksModel
    facts: FactsModel

    @classmethod
    def set_default_domain(cls, domain: Optional[AbstractDomain]) -> None:
        """
        Set the default domain for the Talisman document.

        :param domain: The default domain to be set.
        """
        cls._DEFAULT_DOMAIN = domain

    def set_domain(self, domain: Optional[AbstractDomain]) -> None:
        """
        Set the domain for the Talisman document.

        :param domain: The domain to be set.
        """
        self._domain = domain

    def deserialize(self) -> TalismanDocument:
        """
        Deserialize the Talisman document from the model.

        :return: The deserialized Talisman document.
        """
        document_factory = TalismanDocumentFactory(self._domain or self._DEFAULT_DOMAIN)
        id2node, structure = self._collect_nodes()

        return document_factory.construct(
            content=id2node.values(),
            structure=structure,
            root=self.main_node,
            node_links=self.links.deserialize(id2node),
            facts=self.facts.deserialize(id2node),
            id_=self.id
        )

    def _collect_nodes(self) -> Tuple[Dict[str, AbstractNode], Dict[str, Tuple[str, ...]]]:
        # try to avoid recursion
        links: Dict[str, Tuple[str, ...]] = {}
        id2node = {}

        for node_model in self.content:
            id2node[node_model.id] = node_model.deserialize({})
            if node_model.children:
                links[node_model.id] = node_model.children
        return id2node, links

    @classmethod
    def serialize(cls, document: TalismanDocument) -> 'TalismanDocumentModel':
        """
        Serialize the Talisman document to the model.

        :param document: The Talisman document to be serialized.
        :return: The serialized TalismanDocumentModel.
        """
        node_models = tuple(serialize_node(node) for node in document.id2node.values())
        fill_children(node_models, document)
        return cls(
            VERSION='1.0',
            id=document.id,
            main_node=document.main_root.id,
            content=node_models,
            links=NodeLinksModel.serialize(document.node_links),
            facts=FactsModel.serialize(document.facts)
        )
