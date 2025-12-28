from dataclasses import replace
from operator import attrgetter
from typing import Dict, Iterator, Optional, Sequence, Tuple

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, FactStatus, Identifiable, TalismanDocument
from tdm.datamodel.domain import AtomValueType, PropertyType
from tdm.datamodel.facts import AtomValueFact, ConceptFact, KBConceptValue, MentionFact, PropertyFact, RelationFact, RelationPropertyFact
from tdm.datamodel.mentions import TextNodeMention
from tdm.datamodel.nodes import TextNode
from tdm.datamodel.values import StringValue
from tdm.v0.json_schema.fact import AbstractFactModel, ConceptFactModel, PropertyFactModel, RelationFactModel, ValueFactModel


def _fact_text(fact: AbstractFactModel) -> Optional[str]:
    if fact.metadata is not None and hasattr(fact.metadata, 'text'):
        return ' '.join(fact.metadata.text)
    if fact.mention:
        return ' '.join(map(attrgetter('value'), fact.mention))
    return None


def convert_concept_fact(
        fact: ConceptFactModel, doc: TalismanDocument, domain: AbstractDomain, titles: Dict[str, PropertyType]
) -> Iterator[AbstractFact]:
    status = FactStatus(fact.status.value)
    if isinstance(fact.value, str):
        value = KBConceptValue(fact.value)
    elif isinstance(fact.value, Sequence):
        value = tuple(KBConceptValue(v) for v in fact.value)
    else:
        raise ValueError(f"illegal concept fact value {fact.value}")
    concept_fact = ConceptFact(
        status=status,
        type_id=fact.type_id,
        value=value,
        id=fact.id  # preserve old id
    )
    yield concept_fact
    name = _fact_text(fact)
    if not name:
        return
    name_property = titles[fact.type_id]
    if name_property.target.value_type is not StringValue:
        raise ValueError
    old_fashion_value = ValueFactModel(
        id=Identifiable.generate_id(),
        status=fact.status,
        type_id=name_property.target.id,
        value={'value': name},
        mention=fact.mention,
        metadata=fact.metadata
    )
    value, *other = convert_value_fact(old_fashion_value, doc, domain)
    yield value
    yield from other
    yield PropertyFact(
        status=status,
        type_id=name_property,
        source=concept_fact,
        target=value
    )


def convert_value_fact(fact: ValueFactModel, doc: TalismanDocument, domain: AbstractDomain) -> Iterator[AbstractFact]:
    status = FactStatus(fact.status.value)
    value_type = domain.get_type(fact.type_id)
    if not isinstance(value_type, AtomValueType):
        raise ValueError
    if isinstance(fact.value, dict):
        value = value_type.value_type.from_dict(fact.value)
    elif isinstance(fact.value, Sequence):
        value = tuple(value_type.value_type.from_dict(v) for v in fact.value)
    else:
        raise ValueError
    value = AtomValueFact(
        status=status,
        type_id=value_type,
        value=value,
        id=fact.id
    )
    yield value

    if fact.mention:
        # get only first span of multi-span mention
        node = doc.id2node[fact.mention[0].node_id]
        if not isinstance(node, TextNode):
            return
        mention = TextNodeMention(node, fact.mention[0].start, fact.mention[0].end)
    elif fact.metadata and hasattr(fact.metadata, 'text'):
        # create node
        text = ' '.join(fact.metadata.text)
        mention = TextNodeMention(TextNode(text), 0, len(text))
    else:
        return

    yield MentionFact(
        status=status,
        mention=mention,
        value=value
    )


def convert_relation_fact(fact: RelationFactModel, old2new: Dict[str, AbstractFact]) -> RelationFact:
    status = FactStatus(fact.status.value)
    source = old2new[fact.value.from_fact]
    target = old2new[fact.value.to_fact]
    if not isinstance(source, ConceptFact) or not isinstance(target, ConceptFact):
        raise ValueError
    return RelationFact(
        status=status,
        type_id=fact.type_id,
        source=source,
        target=target,
        id=fact.id
    )


def convert_property_fact(
        fact: PropertyFactModel,
        old2new: Dict[str, AbstractFact],
        value2mention: Dict[str, Tuple[MentionFact, ...]]
) -> Iterator[AbstractFact]:
    status = FactStatus(fact.status.value)
    source = old2new[fact.value.from_fact]
    target = old2new[fact.value.to_fact]
    if not isinstance(target, AtomValueFact):
        raise ValueError

    new_target = replace(target, id=None)

    if isinstance(source, ConceptFact):
        yield PropertyFact(
            status=status,
            type_id=fact.type_id,
            source=source,
            target=new_target,
            id=fact.id
        )
    elif isinstance(source, RelationFact):
        yield RelationPropertyFact(
            status=status,
            type_id=fact.type_id,
            source=source,
            target=new_target,
            id=fact.id
        )
    else:
        raise ValueError

    yield new_target
    for mention in value2mention[fact.value.to_fact]:
        yield replace(mention, id=None, value=new_target)
