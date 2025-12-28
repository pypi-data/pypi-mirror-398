from typing import Optional

from tdm.datamodel.domain._impl import Domain


class DomainManager(object):
    def __init__(self):
        self._default = None

    def set(self, domain: Domain) -> None:
        self._default = domain

    def get(self) -> Optional[Domain]:
        return self._default
