from typing import Any, Literal

from pydantic import Field
from redis.commands.search.field import VectorField

from .base_vector_field_schema import BaseVectorFieldSchema


class HNSWVectorFieldSchema(BaseVectorFieldSchema):
    """
    Schema for HNSW vector fields
    """

    algorithm: Literal["HNSW"] = "HNSW"

    m: int = Field(default=16)

    ef_construction: int = Field(default=200)

    ef_runtime: int = Field(default=10)

    epsilon: float = Field(default=0.01)

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

        attributes.update(
            {
                "M": self.m,
                "EF_CONSTRUCTION": self.ef_construction,
                "EF_RUNTIME": self.ef_runtime,
                "EPSILON": self.epsilon,
            }
        )

        return attributes
