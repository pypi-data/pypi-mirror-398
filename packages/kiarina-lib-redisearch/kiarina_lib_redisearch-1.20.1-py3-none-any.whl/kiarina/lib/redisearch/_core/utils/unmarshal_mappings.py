from typing import Any

import numpy as np

from kiarina.lib.redisearch_schema import RedisearchSchema


def unmarshal_mappings(
    *,
    schema: RedisearchSchema,
    mapping: dict[bytes, bytes],
) -> dict[str, Any]:
    """
    Convert the mapping from the appropriate format based on the schema
    """
    unmarshaled: dict[str, Any] = {}

    for bkey, value in mapping.items():
        key = bkey.decode("utf-8")

        field = schema.get_field(key)

        if not field:
            try:
                unmarshaled[key] = _decode_numeric(value)
            except ValueError:
                unmarshaled[key] = value.decode("utf-8")

        elif field.type == "tag":
            if field.multiple:
                unmarshaled[key] = value.decode("utf-8").split(field.separator)
            else:
                unmarshaled[key] = value.decode("utf-8").split(field.separator).pop(0)

        elif field.type == "numeric":
            unmarshaled[key] = _decode_numeric(value)

        elif field.type == "text":
            unmarshaled[key] = value.decode("utf-8")

        elif field.type == "vector":
            unmarshaled[key] = np.frombuffer(value, dtype=field.dtype).tolist()

    return unmarshaled


def _decode_numeric(value: bytes) -> float | int:
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass

    raise ValueError(f"Cannot decode numeric value: {value.decode('utf-8')}")
