from typing import Self

from .._enums.redisearch_filter_operator import RedisearchFilterOperator


class RedisearchFilter:
    """
    A class representing the filter condition expression for a Redisearch query.

    RedisearchFilter can be combined using & and | operators to create
    complex logical expressions that are evaluated in the Redis Query language.

    This interface allows users to construct complex queries without needing to know
    the Redis Query language.

    Filter-based fields are not initialised directly.
    Instead, they are constructed by combining RedisFilterFields
    using the & and | operators.

    Examples:
        >>> import kiarina.lib.redisearch.filter as rf
        >>> filter = (rf.Tag("color") == "blue") & (rf.Numeric("price") < 100)
        >>> print(str(filter))
        (@color:{blue} @price:[-inf (100)])
    """

    def __init__(
        self,
        query: str | None = None,
        *,
        left: Self | None = None,
        operator: RedisearchFilterOperator | None = None,
        right: Self | None = None,
    ):
        """
        Initialization
        """
        self._query: str | None = query
        """Query string"""

        self._left: Self | None = left
        """Left operand"""

        self._operator: RedisearchFilterOperator | None = operator
        """Logical operator"""

        self._right: Self | None = right
        """Right operand"""

    def __and__(self, other: Self) -> Self:
        """
        AND operator for concatenation
        """
        return type(self)(
            left=self,
            operator=RedisearchFilterOperator.AND,
            right=other,
        )

    def __or__(self, other: Self) -> Self:
        """
        OR operator for concatenation
        """
        return type(self)(
            left=self,
            operator=RedisearchFilterOperator.OR,
            right=other,
        )

    def __str__(self) -> str:
        """
        Stringification
        """
        if self._query:
            return self._query

        if self._left and self._operator and self._right:
            operator = " | " if self._operator == RedisearchFilterOperator.OR else " "

            left, right = str(self._left), str(self._right)

            if (left == right) and (right == "*"):
                return "*"

            if (left == "*") and (right != "*"):
                return right

            if (left != "*") and (right == "*"):
                return left

            return f"({left}{operator}{right})"

        raise ValueError("Improperly initialized RedisearchFilter")
