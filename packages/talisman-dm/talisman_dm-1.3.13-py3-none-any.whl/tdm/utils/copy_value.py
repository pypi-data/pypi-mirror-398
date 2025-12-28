from dataclasses import replace
from functools import singledispatch
from typing import Optional, Tuple, TypeVar

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractFact, FactStatus
from tdm.datamodel.facts import AtomValueFact, ComponentFact, CompositeValueFact, MentionFact

_Fact = TypeVar('_Fact', bound=AbstractFact)


@singledispatch
def copy_value(value: _Fact, doc: TalismanDocument, status: Optional[FactStatus]) -> Tuple[AbstractFact, ...]:
    """ Recursive copy all value information
        returns:
        - value with new id
        - mentions, components with values with new ids
    """
    raise NotImplementedError


@copy_value.register
def _(value: AtomValueFact, doc: TalismanDocument, status: Optional[FactStatus]) -> Tuple[AbstractFact, ...]:
    status = status or value.status
    new_value = replace(value, id=None, status=status)
    mentions = (replace(m, value=new_value, id=None, status=status) for m in doc.get_facts(MentionFact, filter_=lambda m: m.value == value))
    return (new_value, *mentions)


@copy_value.register
def _(value: CompositeValueFact, doc: TalismanDocument, status=Optional[FactStatus]) -> Tuple[AbstractFact, ...]:
    status = status or value.status
    new_value = replace(value, id=None, status=status)
    components = []
    for component in doc.related_facts(value, ComponentFact):
        new_component_values = copy_value(component.target, doc, status)
        new_component = ComponentFact(status, component.type_id, new_value, new_component_values[0], component.value, id=None)
        components.extend((new_component, *new_component_values))

    return (new_value, *components)
