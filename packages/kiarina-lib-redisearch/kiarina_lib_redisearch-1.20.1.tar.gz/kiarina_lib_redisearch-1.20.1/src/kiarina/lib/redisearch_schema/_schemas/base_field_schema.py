from pydantic import BaseModel, Field, field_validator


class BaseFieldSchema(BaseModel):
    """
    Base class of the field schema
    """

    name: str = Field(...)
    """
    RediSearch field name

    The field names `payload` and `distance` cannot be used.
    If `id` is used as a field name, it will be treated as the same value as the document ID.
    """

    @field_validator("name")
    @classmethod
    def forbid_reserved_names(cls, v: str) -> str:
        reserved = {"payload", "distance"}

        if v in reserved:
            raise ValueError(f'"{v}" is a reserved name and cannot be used.')

        return v
