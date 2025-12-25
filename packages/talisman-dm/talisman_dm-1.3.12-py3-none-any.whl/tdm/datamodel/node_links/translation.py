from dataclasses import dataclass
from typing import Callable, Optional

from tdm.abstract.datamodel import AbstractNodeLink, AbstractNodeMention, Identifiable
from tdm.abstract.json_schema import generate_model


@generate_model(label='translation')
@dataclass(frozen=True)
class TranslationNodeLink(Identifiable, AbstractNodeLink[AbstractNodeMention, AbstractNodeMention]):
    """
    Represents a link between two node mentions where one is a translation of the other.

    Attributes
    --------
    language:
        The language of the translation. Default is None.
    """

    language: Optional[str] = None

    @staticmethod
    def lang_filter(language: str) -> Callable[['TranslationNodeLink'], bool]:
        """
        Returns a filter function based on the translation language
        :param language: The language to filter by
        :return: The filter function for TranslationNodeLink objects
        """

        def _filter(link: TranslationNodeLink) -> bool:
            return link.language == language

        return _filter
