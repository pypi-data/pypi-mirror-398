import re

ESCAPED_CHARACTERS: str = r"[,.<>{}\[\]\\\"\':;!@#$%^&*()\-+=~\/ ]"
"""
Regular expression patterns

for characters requiring escaping in Redisearch queries
"""

ESCAPED_CHARACTERS_RE: re.Pattern[str] = re.compile(ESCAPED_CHARACTERS)
"""Compiled regular expression for escaped characters"""


def escape_token(value: str) -> str:
    """
    Escape special characters in a Redisearch query token.
    """
    return ESCAPED_CHARACTERS_RE.sub(r"\\\g<0>", value)
