from immutabledict import immutabledict
from pydantic import BaseModel

from tdm.helper import freeze_dict


class AbstractMarkupModel(BaseModel):
    """
    The most base class for node markup serialization
    """

    def immutabledict(self) -> immutabledict:
        return freeze_dict(self.model_dump(exclude_none=True, exclude_defaults=True))
