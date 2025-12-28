from typing import Any, Literal

import numpy as np
from pydantic import Field

from .base_field_schema import BaseFieldSchema


class BaseVectorFieldSchema(BaseFieldSchema):
    """
    Base class for vector field schemas
    """

    type: Literal["vector"] = "vector"

    dims: int = Field(...)
    """Dimensionality"""

    datatype: Literal["FLOAT32", "FLOAT64"] = "FLOAT32"
    """Data type"""

    distance_metric: Literal["L2", "COSINE", "IP"] = "COSINE"
    """Distance metric"""

    initial_cap: int | None = None
    """Initial capacity"""

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def dtype(self) -> Any:
        """
        Get the numpy data type
        """
        if self.datatype == "FLOAT32":
            return np.float32
        elif self.datatype == "FLOAT64":
            return np.float64
        else:
            raise ValueError(f"Unsupported datatype: {self.datatype}")

    # --------------------------------------------------
    # Protected Methods
    # --------------------------------------------------

    def _get_attributes(self) -> dict[str, Any]:
        """
        Get attributes for the vector field
        """
        attributes = {
            "TYPE": self.datatype,
            "DIM": self.dims,
            "DISTANCE_METRIC": self.distance_metric,
        }

        if self.initial_cap is not None:
            attributes["INITIAL_CAP"] = self.initial_cap

        return attributes
