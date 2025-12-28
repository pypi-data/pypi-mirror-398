from typing import Any, Dict, Iterator, Optional, Sequence

from tdm import TalismanDocument
from tdm.abstract.datamodel import AbstractDomain, AbstractDomainType, AbstractFact, FactStatus
from tdm.datamodel.domain import AtomValueType, PropertyType, RelationType
from tdm.datamodel.domain.types import DocumentType
from tdm.datamodel.facts import AtomValueFact, ConceptFact, KBConceptValue, PropertyFact, RelationFact


def get_metadata_facts(
        doc: TalismanDocument, metadata: Dict[str, Any], domain: Optional[AbstractDomain], metadata_map: Dict[str, str]
) -> Iterator[AbstractFact]:
    document_fact = doc.get_fact(doc.id)
    if not isinstance(document_fact, ConceptFact) or not isinstance(document_fact.type_id, DocumentType):
        raise ValueError

    if not metadata:
        return
    for key, value in metadata.items():
        if key not in metadata_map:
            continue  # maybe log
        domain_types = tuple(domain.related_types(document_fact.type_id, filter_=AbstractDomainType.name_filter(metadata_map[key])))
        if len(domain_types) != 1:
            raise ValueError
        domain_type = domain_types[0]
        if isinstance(domain_type, PropertyType):
            value_type: AtomValueType = domain_type.target
            if not isinstance(value, str) and isinstance(value, Sequence):
                values = tuple(value_type.value_type(v) for v in value)
            else:
                values = (value_type.value_type(value),)
            for v in values:
                yield PropertyFact(FactStatus.APPROVED, domain_type, document_fact, AtomValueFact(FactStatus.APPROVED, value_type, v))
        elif isinstance(domain_type, RelationType):
            yield RelationFact(
                FactStatus.APPROVED, domain_type, document_fact,
                ConceptFact(FactStatus.APPROVED, domain_type.target, KBConceptValue(value))
            )
        else:
            raise ValueError
