from functools import singledispatch
from typing import Dict, Iterable, Set, Tuple, Type, TypeVar, Union

from typing_extensions import Protocol

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractDomainType, AbstractFact, AbstractLinkFact, AbstractNodeMention, AbstractValue, FactStatus
from tdm.datamodel.domain import AtomValueType, ComponentValueType, PropertyType, RelationPropertyType, RelationType
from tdm.datamodel.facts import AtomValueFact, ComponentFact, ConceptFact, KBConceptValue, MentionFact, PropertyFact, \
    RelationFact, RelationPropertyFact
from tdm.utils.copy_value import copy_value


def get_metadata(document: TalismanDocument) -> Dict[str, Union[Tuple[AbstractValue, ...], AbstractValue]]:
    doc_fact = document.get_fact(document.id)
    metadata_property_facts: Set[PropertyFact] = set(document.related_facts(doc_fact, PropertyFact))

    return {property_fact.type_id.name: property_fact.target.value for property_fact in metadata_property_facts}


class MentionedFactsFactory(Protocol):
    def __call__(
            self, mention: AbstractNodeMention,
            status: FactStatus = FactStatus.NEW,
            value: Union[AbstractValue, Iterable[AbstractValue]] = ()
    ) -> Iterable[AbstractFact]:
        ...


@singledispatch
def mentioned_fact_factory(type_: AbstractDomainType) -> MentionedFactsFactory:
    raise NotImplementedError


@mentioned_fact_factory.register(AtomValueType)
def _value_fact_factory(type_: AtomValueType) -> MentionedFactsFactory:
    def create_facts(
            mention: AbstractNodeMention, status: FactStatus, value: Union[Tuple[AbstractValue, ...], AbstractValue] = ()
    ) -> Tuple[AtomValueFact, MentionFact]:
        value_fact = AtomValueFact(status, type_, value)
        return value_fact, MentionFact(status, mention, value_fact)

    return create_facts


@mentioned_fact_factory.register(PropertyType)
def _concept_fact_factory(type_: PropertyType) -> MentionedFactsFactory:
    def create_facts(
            mention: AbstractNodeMention, status: FactStatus, value: Union[Tuple[AbstractValue, ...], AbstractValue] = ()
    ) -> Tuple[ConceptFact, AtomValueFact, PropertyFact, MentionFact]:
        if status is FactStatus.APPROVED:
            concept_fact = ConceptFact(status, type_.source, KBConceptValue(value.value))
        else:
            concept_fact = ConceptFact(status, type_.source)
        value_fact = AtomValueFact(status, type_.target, value)
        return concept_fact, value_fact, PropertyFact(status, type_, concept_fact, value_fact), MentionFact(status, mention, value_fact)

    return create_facts


class LinkFactsFactory(Protocol):
    def __call__(
            self,
            source: AbstractFact,
            target: AbstractFact,
            doc: TalismanDocument,
            status: FactStatus = FactStatus.NEW
    ) -> Iterable[AbstractFact]:
        ...


@singledispatch
def link_fact_factory(type_: AbstractDomainType) -> LinkFactsFactory:
    raise NotImplementedError


@link_fact_factory.register(RelationType)
def _relation_fact_factory(type_: RelationType) -> LinkFactsFactory:
    def create_facts(
            source: AbstractFact, target: AbstractFact, doc: TalismanDocument, status: FactStatus = FactStatus.NEW
    ) -> Tuple[AbstractFact, ...]:
        return RelationFact(status, type_, source, target),

    return create_facts


_PropertyType = TypeVar('_PropertyType', bound=Type[AbstractLinkFact])


def _build_prop_fact_factory(type_: AbstractDomainType, fact_type: _PropertyType) -> LinkFactsFactory:
    def create_facts(source: AbstractFact, target: AbstractFact, doc: TalismanDocument, status=FactStatus.NEW) -> Tuple[AbstractFact, ...]:
        copied = copy_value(target, doc, status)
        return (fact_type(status, type_, source, copied[0]), *copied)

    return create_facts


@link_fact_factory.register(PropertyType)
def _(type_: PropertyType):
    return _build_prop_fact_factory(type_, PropertyFact)


@link_fact_factory.register(RelationPropertyType)
def _(type_: RelationPropertyType):
    return _build_prop_fact_factory(type_, RelationPropertyFact)


@link_fact_factory.register(ComponentValueType)
def _(type_: ComponentValueType):
    return _build_prop_fact_factory(type_, ComponentFact)
