from typing import Any, Self

from pydantic import BaseModel
from pydantic import Field as PydanticField
from redis.commands.search.field import Field as RedisearchField

from .._schemas.flat_vector_field_schema import FlatVectorFieldSchema
from .._schemas.hnsw_vector_field_schema import HNSWVectorFieldSchema
from .._types.field_schema import FieldSchema
from .._types.redisearch_field_dicts import RedisearchFieldDicts


class RedisearchSchema(BaseModel):
    """
    Redisearch index schema
    """

    fields: list[FieldSchema] = PydanticField(default_factory=list)
    """All fields"""

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def field_names(self) -> list[str]:
        """
        Obtain the names of all fields in the schema
        """
        return [field.name for field in self.fields if field.name]

    @property
    def vector_field(self) -> FlatVectorFieldSchema | HNSWVectorFieldSchema:
        """
        Obtain the vector field from the schema

        Even if there are two or more vector fields, the first one is returned.
        The vector field used for vector search is assumed to exist only once,
        if at all, within the schema.
        """
        for field in self.fields:
            if field.type == "vector":
                return field

        raise ValueError("No vector field found")

    # --------------------------------------------------
    # Magic Methods
    # --------------------------------------------------

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RedisearchSchema):
            return False

        # Ignore fields not output by model_dump() when comparing
        return self.model_dump() == other.model_dump()

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def get_field(self, name: str) -> FieldSchema | None:
        """
        Get a field by its name

        Args:
            name (str): Field name

        Returns:
            FieldSchema | None: The field if found, otherwise None
        """
        for field in self.fields:
            if field.name == name:
                return field

        return None

    def to_fields(self) -> list[RedisearchField]:
        """
        Convert the schema model to a list of Redisearch fields
        """
        return [field.to_field() for field in self.fields]

    # --------------------------------------------------
    # Class Methods
    # --------------------------------------------------

    @classmethod
    def from_field_dicts(cls, field_dicts: RedisearchFieldDicts) -> Self:
        return cls.model_validate({"fields": field_dicts})
