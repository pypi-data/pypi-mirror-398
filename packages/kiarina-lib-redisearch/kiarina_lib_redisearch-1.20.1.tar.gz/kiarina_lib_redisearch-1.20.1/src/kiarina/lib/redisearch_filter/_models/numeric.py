from .._decorators.check_operator_misuse import check_operator_misuse
from .._enums.redisearch_filter_operator import RedisearchFilterOperator
from .base_field_filter import BaseFieldFilter
from .redisearch_filter import RedisearchFilter


class Numeric(BaseFieldFilter):
    """
    Filter for numeric fields.
    """

    # --------------------------------------------------
    # Class Variables
    # --------------------------------------------------

    OPERATORS: dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: "==",
        RedisearchFilterOperator.NE: "!=",
        RedisearchFilterOperator.LT: "<",
        RedisearchFilterOperator.GT: ">",
        RedisearchFilterOperator.LE: "<=",
        RedisearchFilterOperator.GE: ">=",
    }
    """Supported operators"""

    OPERATOR_MAP: dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: "@%s:[%s %s]",
        RedisearchFilterOperator.NE: "(-@%s:[%s %s])",
        RedisearchFilterOperator.GT: "@%s:[(%s +inf]",
        RedisearchFilterOperator.LT: "@%s:[-inf (%s]",
        RedisearchFilterOperator.GE: "@%s:[%s +inf]",
        RedisearchFilterOperator.LE: "@%s:[-inf %s]",
    }
    """Operator and query mapping"""

    SUPPORTED_VALUE_TYPES = (int, float, type(None))
    """Supported value types"""

    # --------------------------------------------------
    # Magic Methods
    # --------------------------------------------------

    def __str__(self) -> str:
        """
        Stringification

        Converting filter expressions into query strings
        """
        if self._value is None:
            return "*"

        if (
            self._operator == RedisearchFilterOperator.EQ
            or self._operator == RedisearchFilterOperator.NE
        ):
            return self.OPERATOR_MAP[self._operator] % (
                self._field_name,
                self._value,
                self._value,
            )
        else:
            return self.OPERATOR_MAP[self._operator] % (self._field_name, self._value)

    @check_operator_misuse
    def __eq__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical equivalence filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("zipcode") == 90210
        """
        self._set(
            operator=RedisearchFilterOperator.EQ,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    @check_operator_misuse
    def __ne__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical inequality filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("zipcode") != 90210
        """
        self._set(
            operator=RedisearchFilterOperator.NE,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    def __gt__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical "greater than" filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("age") > 18
        """
        self._set(
            operator=RedisearchFilterOperator.GT,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    def __lt__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical "less than" filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("age") < 18
        """
        self._set(
            operator=RedisearchFilterOperator.LT,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    def __ge__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical "greater than or equal to" filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("age") >= 18
        """
        self._set(
            operator=RedisearchFilterOperator.GE,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    def __le__(self, other: int | float) -> RedisearchFilter:
        """
        Create a numerical "less than or equal to" filter expression.

        Args:
            other (int | float): Value to filter by

        Example:
            >>> import kiarina.lib.redisearch.field as rf
            >>> filter = rf.Numeric("age") <= 18
        """
        self._set(
            operator=RedisearchFilterOperator.LE,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))
