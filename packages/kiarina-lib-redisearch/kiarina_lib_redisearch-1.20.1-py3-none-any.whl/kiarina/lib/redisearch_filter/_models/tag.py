from typing import Dict, List, Set, Tuple, Union

from .._decorators.check_operator_misuse import check_operator_misuse
from .._enums.redisearch_filter_operator import RedisearchFilterOperator
from .._utils.escape_token import escape_token
from .base_field_filter import BaseFieldFilter
from .redisearch_filter import RedisearchFilter


class Tag(BaseFieldFilter):
    """
    Filter for tag fields.
    """

    # --------------------------------------------------
    # Class Variables
    # --------------------------------------------------

    OPERATORS: Dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: "==",
        RedisearchFilterOperator.NE: "!=",
        RedisearchFilterOperator.IN: "==",
    }
    """Supported operators"""

    OPERATOR_MAP: Dict[RedisearchFilterOperator, str] = {
        RedisearchFilterOperator.EQ: "@%s:{%s}",
        RedisearchFilterOperator.NE: "(-@%s:{%s})",
        RedisearchFilterOperator.IN: "@%s:{%s}",
    }
    """Operator and query mapping"""

    SUPPORTED_VALUE_TYPES = (list, set, tuple, str, type(None))
    """Supported value types"""

    # --------------------------------------------------
    # Properties
    # --------------------------------------------------

    @property
    def _formatted_tag_value(self) -> str:
        """
        Format the tag value for query representation.
        """
        return "|".join([escape_token(tag) for tag in self._value])

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
            self._formatted_tag_value,
        )

    @check_operator_misuse
    def __eq__(
        self, other: Union[List[str], Set[str], Tuple[str], str]
    ) -> RedisearchFilter:
        """
        Create an equality filter expression for tags.

        Args:
            other (Union[List[str], Set[str], Tuple[str], str]):
                The tags to filter by.

        Example:
            >>> import kiarina.lib.redisearch as rf
            >>> filter = rf.Tag("color") == "blue"
        """
        self._set(
            operator=RedisearchFilterOperator.EQ,
            value=self._normalize_tag_value(other),
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    @check_operator_misuse
    def __ne__(
        self, other: Union[List[str], Set[str], Tuple[str], str]
    ) -> RedisearchFilter:
        """
        Create a not-equal filter expression for tags.

        Args:
            other (Union[List[str], Set[str], Tuple[str], str]):
                The tags to filter by.

        Example:
            >>> import kiarina.lib.redisearch as rf
            >>> filter = rf.Tag("color") != "blue"
        """
        self._set(
            operator=RedisearchFilterOperator.NE,
            value=self._normalize_tag_value(other),
            value_type=self.SUPPORTED_VALUE_TYPES,  # type: ignore
        )

        return RedisearchFilter(str(self))

    # --------------------------------------------------
    # Private Methods
    # --------------------------------------------------

    def _normalize_tag_value(
        self, other: Union[List[str], Set[str], Tuple[str], str]
    ) -> List[str]:
        """
        Normalize the tag value to a list of strings.

        Args:
            other: The tag value to normalize.

        Returns:
            List[str]: Normalized tag values.

        Raises:
            ValueError: If tags within collection cannot be converted to strings.
        """
        if isinstance(other, (list, set, tuple)):
            try:
                return [str(val) for val in other if val]
            except ValueError:
                raise ValueError("All tags within collection must be strings")

        elif not other:
            return []

        elif isinstance(other, str):
            return [other]

        return []
