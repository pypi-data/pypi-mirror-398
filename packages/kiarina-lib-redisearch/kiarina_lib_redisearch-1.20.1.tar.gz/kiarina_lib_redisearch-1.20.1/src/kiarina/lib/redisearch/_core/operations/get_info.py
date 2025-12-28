from typing import Any, Awaitable, Literal, overload

from kiarina.lib.redisearch_schema import RedisearchSchema

from ..schemas.redisearch_context import RedisearchContext
from ..views.info_result import InfoResult


@overload
def get_info(
    mode: Literal["sync"],
    ctx: RedisearchContext,
) -> InfoResult: ...


@overload
def get_info(
    mode: Literal["async"],
    ctx: RedisearchContext,
) -> Awaitable[InfoResult]: ...


def get_info(
    mode: Literal["sync", "async"],
    ctx: RedisearchContext,
) -> InfoResult | Awaitable[InfoResult]:
    """
    Get index information using FT.INFO command.
    """

    def _after(result: dict[str, Any]) -> InfoResult:
        return InfoResult(
            index_name=str(result.get("index_name", "")),
            num_docs=int(result.get("num_docs", 0)),
            num_terms=int(result.get("num_terms", 0)),
            num_records=int(result.get("num_records", 0)),
            index_schema=_parse_schema(ctx.schema, result),
        )

    def _sync() -> InfoResult:
        result = ctx.redis.ft(index_name=ctx.settings.index_name).info()  # type: ignore[no-untyped-call]
        assert isinstance(result, dict)
        return _after(result)

    async def _async() -> InfoResult:
        result = await ctx.redis_async.ft(index_name=ctx.settings.index_name).info()  # type: ignore[no-untyped-call]
        assert isinstance(result, dict)
        return _after(result)

    if mode == "sync":
        return _sync()
    else:
        return _async()


def _parse_schema(schema: RedisearchSchema, result: dict[str, Any]) -> RedisearchSchema:
    """
    Parse the schema information from the FT.INFO results
    """
    fields: list[dict[str, Any]] = []

    if "attributes" not in result:
        raise ValueError("The FT.INFO results do not contain attributes.")

    for attr in result["attributes"]:
        attr_dict = _parse_attribute(attr)
        field = _parse_field(attr_dict)
        fields.append(field)

    return RedisearchSchema.from_field_dicts(fields)


def _parse_attribute(attr: Any) -> dict[str, Any]:
    attr_dict = {}

    for i in range(0, len(attr), 2):
        key = attr[i].decode("utf-8") if isinstance(attr[i], bytes) else attr[i]

        if i + 1 >= len(attr):
            break

        value = attr[i + 1]

        if isinstance(value, bytes):
            value = value.decode("utf-8")

        elif isinstance(value, list):
            value = [v.decode("utf-8") if isinstance(v, bytes) else v for v in value]

        attr_dict[key] = value

    return attr_dict


def _parse_field(attr_dict: dict[str, Any]) -> dict[str, Any]:
    field_type = _get_field_type(attr_dict)

    field_dict: dict[str, Any] = {}
    field_dict["name"] = str(attr_dict.get("identifier"))

    if field_type == "tag":
        return _parse_tag_field(field_dict, attr_dict)
    elif field_type == "numeric":
        return _parse_numeric_field(field_dict, attr_dict)
    elif field_type == "text":
        return _parse_text_field(field_dict, attr_dict)
    elif field_type == "vector":
        return _parse_vector_field(field_dict, attr_dict)
    else:
        raise ValueError(f"Unknown field type: {field_type}")


def _parse_tag_field(
    field_dict: dict[str, Any], attr_dict: dict[str, Any]
) -> dict[str, Any]:
    field_dict["separator"] = str(attr_dict.get("SEPARATOR", ","))
    field_dict["case_sensitive"] = "CASE_SENSITIVE" in attr_dict
    field_dict["no_index"] = "NO_INDEX" in attr_dict
    field_dict["sortable"] = "SORTABLE" in attr_dict
    return field_dict


def _parse_numeric_field(
    field_dict: dict[str, Any], attr_dict: dict[str, Any]
) -> dict[str, Any]:
    field_dict["no_index"] = "NO_INDEX" in attr_dict
    field_dict["sortable"] = "SORTABLE" in attr_dict
    return field_dict


def _parse_text_field(
    field_dict: dict[str, Any], attr_dict: dict[str, Any]
) -> dict[str, Any]:
    field_dict["weight"] = float(attr_dict.get("WEIGHT", 1.0))
    field_dict["no_stem"] = "NO_STEM" in attr_dict
    field_dict["withsuffixtrie"] = "WITHSUFFIX" in attr_dict
    field_dict["no_index"] = "NO_INDEX" in attr_dict
    field_dict["sortable"] = "SORTABLE" in attr_dict
    return field_dict


def _parse_vector_field(
    field_dict: dict[str, Any], attr_dict: dict[str, Any]
) -> dict[str, Any]:
    field_dict["dims"] = int(attr_dict.get("dim", 0))
    field_dict["algorithm"] = str(attr_dict.get("algorithm", ""))
    field_dict["datatype"] = str(attr_dict.get("data_type", ""))
    field_dict["distance_metric"] = str(attr_dict.get("distance_metric", ""))
    return field_dict


def _get_field_type(attr_dict: dict[str, Any]) -> str:
    if "type" not in attr_dict:
        raise ValueError("The FT.INFO results do not include the field type.")

    return str(attr_dict["type"]).lower()
