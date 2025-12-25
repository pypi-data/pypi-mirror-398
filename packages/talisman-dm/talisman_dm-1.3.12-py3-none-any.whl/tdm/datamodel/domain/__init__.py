__all__ = [
    'Domain', 'DomainManager',
    'set_default_domain', 'get_default_domain',
    'AccountType', 'AtomValueType', 'CompositeValueType', 'ConceptType', 'DocumentType', 'PlatformType', 'PropertyType',
    'RelationPropertyType', 'RelationType', 'ComponentValueType'
]

from typing import Callable, Optional

from ._impl import Domain
from ._manager import DomainManager
from .types import AccountType, AtomValueType, ComponentValueType, CompositeValueType, ConceptType, DocumentType, PlatformType, \
    PropertyType, RelationPropertyType, RelationType

DEFAULT_DOMAIN_MANAGER = DomainManager()

set_default_domain: Callable[[Optional[Domain]], None] = DEFAULT_DOMAIN_MANAGER.set
get_default_domain: Callable[[], Domain] = DEFAULT_DOMAIN_MANAGER.get
