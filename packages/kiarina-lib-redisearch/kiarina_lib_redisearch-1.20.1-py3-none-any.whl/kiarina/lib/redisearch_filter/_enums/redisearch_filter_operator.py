from enum import Enum


class RedisearchFilterOperator(Enum):
    """
    Filter operator enumeration type
    """

    EQ = 1
    """Equal"""
    NE = 2
    """Not Equal"""
    LT = 3
    """Less Than"""
    GT = 4
    """Greater Than"""
    LE = 5
    """Less Than or Equal"""
    GE = 6
    """Greater Than or Equal"""
    OR = 7
    """Logical OR"""
    AND = 8
    """Logical AND"""
    LIKE = 9
    """LIKE"""
    IN = 10
    """IN"""
