from dataclasses import replace
from typing import Sequence, TypeVar
from unittest import TestCase

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractFact, AbstractLinkFact, FactStatus
from tdm.datamodel.facts import AtomValueFact, MentionFact
from tdm.datamodel.mentions import TextNodeMention
from tdm.datamodel.nodes import TextNode
from tdm.datamodel.values import StringValue


def create_mention(node: TextNode, start, end, label) -> MentionFact:
    return MentionFact(
        FactStatus.APPROVED,
        TextNodeMention(node, start, end),
        AtomValueFact(FactStatus.APPROVED, label, StringValue(node.content[start:end]))
    )


def assert_equal_for_docs(case: TestCase, expected: Sequence[TalismanDocument], actual: Sequence[TalismanDocument]):
    case.assertEqual(len(expected), len(actual))
    for e, a in zip(expected, actual):
        assert_equal_for_facts(case, tuple(e.get_facts()), tuple(a.get_facts()))
        e = e.without_facts(e.get_facts())
        a = a.without_facts(a.get_facts())
        case.assertEqual(e, a)


def assert_equal_for_facts(case: TestCase, expected: Sequence[AbstractFact], actual: Sequence[AbstractFact]):
    case.assertEqual(len(expected), len(actual))
    case.assertSetEqual(set(map(remove_id_from_fact, expected)), set(map(remove_id_from_fact, actual)))


_Fact = TypeVar('_Fact', bound=AbstractFact)


def remove_id_from_fact(fact: _Fact) -> _Fact:
    if isinstance(fact, MentionFact):
        return replace(fact, id='', value=remove_id_from_fact(fact.value))
    if isinstance(fact, AbstractLinkFact):
        return replace(fact, id='', source=remove_id_from_fact(fact.source), target=remove_id_from_fact(fact.target))
    return replace(fact, id='')
