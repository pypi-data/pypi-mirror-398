from typing import Literal

from redis.commands.search.field import TextField

from .base_field_schema import BaseFieldSchema


class TextFieldSchema(BaseFieldSchema):
    """
    Schema for text fields
    """

    type: Literal["text"] = "text"

    weight: float = 1
    """Weight"""

    no_stem: bool = False
    """Flag to indicate if stemming is disabled"""

    phonetic_matcher: str | None = None
    """Phonetic matcher"""

    withsuffixtrie: bool = False
    """Flag to indicate if suffix trie is used"""

    no_index: bool = False
    """Flag to prevent index creation"""

    sortable: bool | None = False
    """Flag to indicate if the field is sortable"""

    def to_field(self) -> TextField:
        """
        Convert the field schema to a Redisearch field
        """
        return TextField(
            self.name,
            weight=self.weight,
            no_stem=self.no_stem,
            phonetic_matcher=self.phonetic_matcher,  # type: ignore
            sortable=self.sortable,
            no_index=self.no_index,
        )
