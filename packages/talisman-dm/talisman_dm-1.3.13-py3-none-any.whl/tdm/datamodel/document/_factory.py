import uuid
from typing import Dict, Iterable, Optional, Tuple

from tdm.abstract.datamodel import AbstractDocumentFactory, AbstractDomain, AbstractFact, AbstractNode, \
    AbstractNodeLink, FactStatus, TalismanDocument
from tdm.datamodel.common import TypedIdsContainer
from tdm.datamodel.domain import get_default_domain
from tdm.datamodel.domain.types import DocumentType
from tdm.datamodel.facts import ConceptFact, KBConceptValue
from ._impl import TalismanDocumentImpl
from ._structure import NodesStructure


class TalismanDocumentFactory(AbstractDocumentFactory):
    """
    Factory class for TalismanDocument construction
    """

    def __init__(self, domain: Optional[AbstractDomain] = None):
        self._domain = domain if domain is not None else get_default_domain()

    def create_document(self, *, id_: Optional[str] = None, doc_type: Optional[str] = None) -> TalismanDocument:
        doc = TalismanDocumentImpl(
            id2view={},
            dependencies={},
            structure=NodesStructure(),
            containers={
                AbstractNode: TypedIdsContainer(AbstractNode, ()),
                AbstractNodeLink: TypedIdsContainer(AbstractNodeLink, ()),
                AbstractFact: TypedIdsContainer(AbstractFact, ())
            },
            hash2ids={},
            id2hash={},
            duplicate2id={},
            id2duplicates={},
            id_=id_ or self.generate_id(),
            domain=self._domain
        )
        if doc_type is not None:
            if self._domain is not None:
                doc_type = self._domain.get_type(doc_type)
                if not isinstance(doc_type, DocumentType):
                    raise ValueError(f"Invalid document type: expected `DocumentType`, but got `{doc_type.pretty()}`.")
            return doc.with_facts([ConceptFact(FactStatus.APPROVED, doc_type, KBConceptValue.build(doc.id), id=doc.id)])
        return doc

    def construct(
            self,
            content: Iterable[AbstractNode] = (),
            structure: Dict[str, Tuple[str, ...]] = None,
            root: Optional[str] = None,
            node_links: Iterable[AbstractNodeLink] = (),
            facts: Iterable[AbstractFact] = (),
            *, id_: Optional[str] = None
    ) -> TalismanDocument:
        """
        Construct TalismanDocument with specified objects.

        :param content: document content nodes
        :param structure: document content nodes structural links
        :param root: document main root node identifier
        :param node_links: document node semantic links
        :param facts: document facts
        :param id_: document identifier
        :return: new TalismanDocument object filled with specified content and structure
        """
        doc: TalismanDocumentImpl = self.create_document(id_=id_)
        doc = doc.with_elements((*content, *node_links, *facts)) \
            .with_structure(structure) \
            .with_main_root(root)
        return doc

    @staticmethod
    def generate_id():
        return str(uuid.uuid4())
