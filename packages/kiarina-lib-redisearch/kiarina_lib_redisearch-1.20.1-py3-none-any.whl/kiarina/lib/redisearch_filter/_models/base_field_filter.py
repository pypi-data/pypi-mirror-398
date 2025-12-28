from typing import Any, Self

from .._enums.redisearch_filter_operator import RedisearchFilterOperator


class BaseFieldFilter:
    """
    Base class for field filters.
    """

    OPERATORS: dict[RedisearchFilterOperator, str] = {}
    """Supported operators"""

    def __init__(self, field_name: str):
        """
        Initialization
        """
        self._field_name: str = field_name
        """Field name"""

        self._operator: RedisearchFilterOperator = RedisearchFilterOperator.EQ
        """Filter operator"""

        self._value: Any = None
        """Filter value"""

    # --------------------------------------------------
    # Public Methods
    # --------------------------------------------------

    def equals(self, other: Self) -> bool:
        """
        Check if another filter field is equal to this one.
        """
        if not isinstance(other, type(self)):
            return False

        return self._field_name == other._field_name and self._value == other._value

    # --------------------------------------------------
    # Protected Methods
    # --------------------------------------------------

    def _set(
        self,
        *,
        operator: RedisearchFilterOperator,
        value: Any,
        value_type: tuple[Any],
    ) -> None:
        # Check if the operator is supported by this class
        if operator not in self.OPERATORS:
            raise ValueError(
                f"Operator {operator} not supported by {self.__class__.__name__}. "
                f"Supported operators are {self.OPERATORS.values()}."
            )

        if not isinstance(value, value_type):
            raise TypeError(
                f"Right side argument passed to operator {self.OPERATORS[operator]} "
                f"with left side "
                f"argument {self.__class__.__name__} must be of type {value_type}, "
                f"received value {value}"
            )

        self._operator = operator
        self._value = value
