from typing import Literal

from pydantic import Field
from redis.commands.search.field import TagField

from .base_field_schema import BaseFieldSchema


class TagFieldSchema(BaseFieldSchema):
    """
    Schema for tag fields
    """

    type: Literal["tag"] = "tag"

    separator: str = ","
    """Tag separator"""

    case_sensitive: bool = False
    """Flag to indicate if case sensitivity is enabled"""

    no_index: bool = False
    """Flag to prevent index creation"""

    sortable: bool | None = False
    """Flag to indicate if the field is sortable"""

    multiple: bool = Field(False, exclude=True)
    """
    Flag to indicate if multiple tags are allowed

    This field is not a feature of Redisearch and is only used within this library.
    Therefore, it does not affect the migration.
    """

    def to_field(self) -> TagField:
        """
        Convert the field schema to a Redisearch field
        """
        return TagField(
            self.name,
            separator=self.separator,
            case_sensitive=self.case_sensitive,
            sortable=self.sortable,
            no_index=self.no_index,
        )
