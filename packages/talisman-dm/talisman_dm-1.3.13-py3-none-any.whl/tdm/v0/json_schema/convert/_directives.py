from typing import Dict, Iterator

from tdm.abstract.datamodel import AbstractFact, FactStatus
from tdm.datamodel.domain import PropertyType
from tdm.datamodel.domain.types import AbstractConceptType, AccountType, PlatformType
from tdm.datamodel.facts import AtomValueFact, ConceptFact, PropertyFact
from tdm.datamodel.values import StringValue
from tdm.v0.json_schema.directive import AbstractDirectiveModel, CreateAccountDirectiveModel, CreatePlatformDirectiveModel


def _convert_directive(
        d: AbstractDirectiveModel, type_: AbstractConceptType, properties: Dict[str, PropertyType]
) -> Iterator[AbstractFact]:
    fact = ConceptFact(FactStatus.AUTO, type_)
    yield fact
    for f in d.model_fields_set:
        if f not in properties:
            raise ValueError
        prop_type = properties[f]
        yield PropertyFact(FactStatus.AUTO, prop_type, fact, AtomValueFact(FactStatus.AUTO, prop_type.target, StringValue(getattr(d, f))))


def convert_platform_directive(
        d: CreatePlatformDirectiveModel, type_: PlatformType, properties: Dict[str, PropertyType]
) -> Iterator[AbstractFact]:
    return _convert_directive(d, type_, properties)


def convert_account_directive(
        d: CreateAccountDirectiveModel, type_: AccountType, properties: Dict[str, PropertyType]
) -> Iterator[AbstractFact]:
    return _convert_directive(d, type_, properties)
