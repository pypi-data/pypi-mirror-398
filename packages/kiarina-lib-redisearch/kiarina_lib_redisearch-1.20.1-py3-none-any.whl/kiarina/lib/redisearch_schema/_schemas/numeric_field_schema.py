from typing import Literal

from redis.commands.search.field import NumericField

from .base_field_schema import BaseFieldSchema


class NumericFieldSchema(BaseFieldSchema):
    """
    Schema for numeric fields
    """

    type: Literal["numeric"] = "numeric"

    no_index: bool = False
    """Flag to prevent index creation"""

    sortable: bool | None = False
    """Flag to indicate if the field is sortable"""

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def to_field(self) -> NumericField:
        """
        Convert the field schema to a Redisearch field
        """
        return NumericField(
            self.name,
            sortable=self.sortable,
            no_index=self.no_index,
        )
