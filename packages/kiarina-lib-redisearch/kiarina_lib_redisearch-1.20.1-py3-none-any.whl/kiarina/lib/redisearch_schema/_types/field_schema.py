from typing import TypeAlias

from .._schemas.numeric_field_schema import NumericFieldSchema
from .._schemas.tag_field_schema import TagFieldSchema
from .._schemas.text_field_schema import TextFieldSchema
from .._schemas.flat_vector_field_schema import FlatVectorFieldSchema
from .._schemas.hnsw_vector_field_schema import HNSWVectorFieldSchema

FieldSchema: TypeAlias = (
    NumericFieldSchema
    | TagFieldSchema
    | TextFieldSchema
    | FlatVectorFieldSchema
    | HNSWVectorFieldSchema
)
