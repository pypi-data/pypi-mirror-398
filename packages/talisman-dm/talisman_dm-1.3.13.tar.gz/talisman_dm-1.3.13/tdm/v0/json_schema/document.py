from collections import defaultdict
from typing import ClassVar, Dict, Iterable, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, PrivateAttr

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, TalismanDocument
from tdm.datamodel.document import TalismanDocumentFactory
from tdm.datamodel.domain import PropertyType
from tdm.datamodel.domain.types import AbstractConceptType, AccountType, DocumentType, PlatformType
from .content import TreeDocumentContentModel
from .convert import build_structure, convert_account_directive, convert_concept_fact, convert_platform_directive, convert_property_fact, \
    convert_relation_fact, convert_value_fact, get_metadata_facts
from .directive import DirectiveModel, DirectiveType
from .fact import ConceptFactModel, FactModel, FactType, PropertyFactModel, RelationFactModel, ValueFactModel
from .metadata import DocumentMetadataModel

_T = TypeVar('_T', bound=AbstractConceptType)


def _get_source_type(domain: AbstractDomain, cls: Type[_T], props: Iterable[PropertyType]) -> _T:
    sources = {domain.get_type(p.id).source for p in props}
    if len(sources) > 1:
        raise ValueError
    source = sources.pop()
    if not isinstance(source, cls):
        raise ValueError
    return source


class TalismanDocumentModel(BaseModel):
    _DEFAULT_DOMAIN: ClassVar[AbstractDomain] = None
    _domain: AbstractDomain = PrivateAttr(None)

    id: str
    content: TreeDocumentContentModel
    metadata: Optional[DocumentMetadataModel] = None
    facts: Optional[Tuple[FactModel, ...]] = None  # pydantic fails to serialize FrozenSet[FactModel]
    directives: Optional[Tuple[DirectiveModel, ...]] = None

    @classmethod
    def set_default_domain(cls, domain: Optional[AbstractDomain]) -> None:
        cls._DEFAULT_DOMAIN = domain

    def set_domain(self, domain: Optional[AbstractDomain]) -> None:
        self._domain = domain

    def to_doc(
            self, doc_type: Union[str, DocumentType], concept_titles: Iterable[PropertyType], metadata_map: Dict[str, str],
            platform_props: Dict[str, PropertyType] = None, account_props: Dict[str, PropertyType] = None
    ) -> TalismanDocument:
        domain = self._domain or self._DEFAULT_DOMAIN
        if domain is None:
            raise ValueError('TDM v0 could parse document only with domain')
        titles: Dict[str, PropertyType] = {prop.source.id: prop for prop in concept_titles}

        result = TalismanDocumentFactory(self._domain or self._DEFAULT_DOMAIN).create_document(id_=self.id, doc_type=doc_type)

        nodes, structure, node_links = build_structure(self.content)
        result = result.with_nodes(nodes).with_structure(structure).with_node_links(node_links, update=True).with_main_root(self.content.id)

        # convert document metadata to facts
        if self.metadata:
            result = result.with_facts(get_metadata_facts(result, self.metadata.to_metadata(), self._domain, metadata_map), update=True)

        # now convert facts
        old_facts = defaultdict(set)
        for fact in (self.facts or []):
            old_facts[fact.fact_type].add(fact)

        facts = []
        facts_mapping: dict[str, AbstractFact] = {}
        # convert all CreateAccount and CreateAccount directives into new types
        type2directives = defaultdict(list)
        for d in self.directives or ():
            type2directives[d.directive_type].append(d)
        if DirectiveType.CREATE_PLATFORM in type2directives:
            platform_type = _get_source_type(domain, PlatformType, platform_props.values())
            for d in type2directives[DirectiveType.CREATE_PLATFORM]:
                facts.extend(convert_platform_directive(d, platform_type, platform_props))
        if DirectiveType.CREATE_ACCOUNT in type2directives:
            account_type = _get_source_type(domain, AccountType, account_props.values())
            for d in type2directives[DirectiveType.CREATE_ACCOUNT]:
                facts.extend(convert_account_directive(d, account_type, account_props))

        # start with concept facts
        # old concept fact consists of <status, type_id, value, mention> and should be converted to chain
        # ConceptFact(type_id) <- Property(Name) -> AtomValueFact(value) <-  MentionFact -> TextNodeMention(mention)

        for old_concept_fact in old_facts.get(FactType.CONCEPT, []):
            old_concept_fact: ConceptFactModel
            concept_fact, *other = convert_concept_fact(old_concept_fact, result, domain, titles)
            facts_mapping[old_concept_fact.id] = concept_fact
            facts.extend((concept_fact, *other))
        # then convert ValueFacts
        # old value fact consists of <status, type_id, value, mention> and should be converted to chain
        # AtomValueFact(value) <- MentionFact -> TextNodeMention(mention)
        value2mention = {}
        for old_value_fact in old_facts.get(FactType.VALUE, []):
            old_value_fact: ValueFactModel
            value_fact, *other = convert_value_fact(old_value_fact, result, domain)
            facts_mapping[old_value_fact.id] = value_fact
            value2mention[old_value_fact.id] = other

        # now relations
        # old relations should be mapped to new ones with trivial modifications
        for old_relation_fact in old_facts.get(FactType.RELATION, []):
            old_relation_fact: RelationFactModel
            relation_fact = convert_relation_fact(old_relation_fact, facts_mapping)
            facts_mapping[old_relation_fact.id] = relation_fact
            facts.append(relation_fact)

        # and finally properties and relation properties
        not_hanging_values = set()  # save
        for old_property_fact in old_facts.get(FactType.PROPERTY, []):
            old_property_fact: PropertyFactModel
            not_hanging_values.add(old_property_fact.value.to_fact)
            property_fact, *other = convert_property_fact(old_property_fact, facts_mapping, value2mention)
            facts.extend([property_fact, *other])

        # add to `facts` AtomValueFacts without properties
        for value_id, mentions in value2mention.items():
            if value_id not in not_hanging_values:
                facts.extend([facts_mapping[value_id], *mentions])

        result = result.with_facts(facts, update=True)
        return result
