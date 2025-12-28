from enum import Enum
from typing import Union

from pydantic import BaseModel
from typing_extensions import Literal


class DirectiveType(str, Enum):
    CREATE_ACCOUNT = 'create_account'
    CREATE_PLATFORM = 'create_platform'


class AbstractDirectiveModel(BaseModel):
    directive_type: DirectiveType


class CreateAccountDirectiveModel(AbstractDirectiveModel):
    key: str
    platform_key: str
    name: str
    url: str

    directive_type: Literal[DirectiveType.CREATE_ACCOUNT] = DirectiveType.CREATE_ACCOUNT

    def __hash__(self):
        return hash((self.directive_type, self.key))


class CreatePlatformDirectiveModel(AbstractDirectiveModel):
    key: str
    platform_type: str
    name: str
    url: str

    directive_type: Literal[DirectiveType.CREATE_PLATFORM] = DirectiveType.CREATE_PLATFORM

    def __hash__(self):
        return hash((self.directive_type, self.key))


DirectiveModel = Union[CreateAccountDirectiveModel, CreatePlatformDirectiveModel]
