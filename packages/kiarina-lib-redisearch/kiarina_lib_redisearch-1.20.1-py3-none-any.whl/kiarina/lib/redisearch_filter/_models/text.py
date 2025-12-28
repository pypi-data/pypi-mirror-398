from .._decorators.check_operator_misuse import check_operator_misuse
from .._enums.redisearch_filter_operator import RedisearchFilterOperator
from .base_field_filter import BaseFieldFilter
from .redisearch_filter import RedisearchFilter


class Text(BaseFieldFilter):
    """
    Field for text fields.
    """

    # --------------------------------------------------
    # Class Variables
    # --------------------------------------------------

    OPERATORS: dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: "==",
        RedisearchFilterOperator.NE: "!=",
        RedisearchFilterOperator.LIKE: "%",
    }
    """Supported operators"""

    OPERATOR_MAP: dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: '@%s:("%s")',
        RedisearchFilterOperator.NE: '(-@%s:"%s")',
        RedisearchFilterOperator.LIKE: "@%s:(%s)",
    }
    """Operator and query mapping"""

    SUPPORTED_VALUE_TYPES = (str, type(None))
    """Supported value types"""

    # --------------------------------------------------
    # Magic Methods
    # --------------------------------------------------

    def __str__(self) -> str:
        """
        Stringification

        Converting filter expressions into query strings
        """
        if not self._value:
            return "*"

        return self.OPERATOR_MAP[self._operator] % (
            self._field_name,
            self._value,
        )

    @check_operator_misuse
    def __eq__(self, other: str) -> RedisearchFilter:
        """
        Create an equality (exact match) filter expression for strings.

        Args:
            other (str): The text value to filter by.

        Example:
            >>> import kiarina.lib.redisearch as rf
            >>> filter = rf.Text("job") == "engineer"
        """
        self._set(
            operator=RedisearchFilterOperator.EQ,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    @check_operator_misuse
    def __ne__(self, other: str) -> RedisearchFilter:
        """
        Create a non-equality (not equal) filter expression for strings.

        Args:
            other (str): The text value to filter by.

        Example:
            >>> import kiarina.lib.redisearch as rf
            >>> filter = rf.Text("job") != "engineer"
        """
        self._set(
            operator=RedisearchFilterOperator.NE,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    def __mod__(self, other: str) -> RedisearchFilter:
        """
        Create a "LIKE" filter expression for strings.

        Args:
            other (str): The text value to filter by.

        Example:
            >>> import kiarina.lib.redisearch as rf
            >>> filter = rf.Text("job") % "engine*"         # Suffix wildcard match
            >>> filter = rf.Text("job") % "%%engine%%"      # Fuzzy match (using edit distance)
            >>> filter = rf.Text("job") % "engineer|doctor" # Contains either term
            >>> filter = rf.Text("job") % "engineer doctor" # Contains both terms
        """
        self._set(
            operator=RedisearchFilterOperator.LIKE,
            value=other,
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))
