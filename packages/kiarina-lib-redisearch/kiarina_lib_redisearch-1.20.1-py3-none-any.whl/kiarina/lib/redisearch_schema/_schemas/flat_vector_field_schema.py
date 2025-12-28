from typing import Any, Literal

from redis.commands.search.field import VectorField

from .base_vector_field_schema import BaseVectorFieldSchema


class FlatVectorFieldSchema(BaseVectorFieldSchema):
    """
    Schema for FLAT vector fields
    """

    algorithm: Literal["FLAT"] = "FLAT"

    block_size: int | None = None

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def to_field(self) -> VectorField:
        """
        Convert field schema to Redisearch field
        """
        return VectorField(self.name, self.algorithm, self._get_attributes())

    # --------------------------------------------------
    # Protected Methods
    # --------------------------------------------------

    def _get_attributes(self) -> dict[str, Any]:
        """
        Get attributes for the vector field
        """
        attributes = super()._get_attributes()

        if self.block_size is not None:
            attributes["BLOCK_SIZE"] = self.block_size

        return attributes
