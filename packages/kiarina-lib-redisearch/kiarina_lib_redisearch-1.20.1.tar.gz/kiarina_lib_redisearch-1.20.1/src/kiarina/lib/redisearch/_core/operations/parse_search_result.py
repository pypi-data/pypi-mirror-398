from redis.commands.search.result import Result

from kiarina.lib.redisearch_schema import RedisearchSchema

from ..schemas.document import Document
from ..utils.calc_score import calc_score
from ..views.search_result import SearchResult


def parse_search_result(
    *,
    key_prefix: str,
    schema: RedisearchSchema,
    return_fields: list[str] | None,
    result: Result,
) -> SearchResult:
    documents: list[Document] = []

    for doc in result.docs:
        # key
        key: str = doc.id

        if not key.startswith(key_prefix):
            raise ValueError(
                f"Document ID {doc.id} does not start with key prefix {key_prefix}"
            )

        # id
        id = key[len(key_prefix) :]

        # mapping
        mapping = doc.__dict__

        if "id" in mapping:
            if "id" in (return_fields or []):
                mapping["id"] = id
            else:
                mapping.pop("id")

        mapping.pop("payload", None)

        # score
        score = 0.0

        if distance := mapping.pop("distance", None):
            score = calc_score(
                float(distance),
                datatype=schema.vector_field.datatype,
                distance_metric=schema.vector_field.distance_metric,
            )

        documents.append(Document(key=key, id=id, score=score, mapping=mapping))

    return SearchResult(
        total=result.total,
        duration=result.duration,
        documents=documents,
    )
