from collections import defaultdict
from functools import singledispatch
from typing import Dict, List

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractFact
from tdm.datamodel.facts import AtomValueFact, ComponentFact, CompositeValueFact, ConceptFact, MentionFact, PropertyFact, RelationFact
from tdm.datamodel.mentions import TextNodeMention
from tdm.datamodel.nodes import TextNode


@singledispatch
def get_mentions(fact: AbstractFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    raise NotImplementedError


@get_mentions.register
def _(fact: AtomValueFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    result = defaultdict(list)
    for mention in document.related_facts(fact, MentionFact):
        result[mention.mention.node].append(mention.mention)
    return result


@get_mentions.register
def _(fact: CompositeValueFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    result = defaultdict(list)
    for component in document.related_facts(fact, ComponentFact):
        for node, mentions in get_mentions(component.target, document).items():
            result[node].extend(mentions)
    return result


@get_mentions.register
def _(fact: ConceptFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    result = defaultdict(list)
    for prop in document.related_facts(fact, PropertyFact, filter_=lambda pf: pf.type_id.isIdentifying):
        prop: PropertyFact
        for node, mentions in get_mentions(prop.target, document).items():
            result[node].extend(mentions)
    return result


@get_mentions.register
def _(fact: RelationFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    result = defaultdict(list)
    for concept in [fact.source, fact.target]:
        for node, mentions in get_mentions(concept, document).items():
            result[node].extend(mentions)
    return result


@get_mentions.register
def _(fact: PropertyFact, document: TalismanDocument) -> Dict[TextNode, List[TextNodeMention]]:
    result = defaultdict(list)

    for node, mentions in get_mentions(fact.target, document).items():
        result[node].extend(mentions)
    return result
