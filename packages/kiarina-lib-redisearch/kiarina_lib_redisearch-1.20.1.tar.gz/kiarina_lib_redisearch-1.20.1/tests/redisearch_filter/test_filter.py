import pytest

import kiarina.lib.redisearch_filter as rf
from kiarina.lib.redisearch_filter._utils.escape_token import escape_token
from kiarina.lib.redisearch_schema import RedisearchSchema


# fmt: off
@pytest.mark.parametrize(
    "filter, query",
    [
        # Tag filters
        (rf.Tag("color") == "blue", "@color:{blue}"),
        (rf.Tag("color") == ["blue", "red"], "@color:{blue|red}"),
        (rf.Tag("color") != "blue", "(-@color:{blue})"),
        (rf.Tag("color") != ["blue", "red"], "(-@color:{blue|red})"),

        # Numeric filters
        (rf.Numeric("price") == 100, "@price:[100 100]"),
        (rf.Numeric("price") != 100, "(-@price:[100 100])"),
        (rf.Numeric("price") > 100, "@price:[(100 +inf]"),
        (rf.Numeric("price") < 100, "@price:[-inf (100]"),
        (rf.Numeric("price") >= 100, "@price:[100 +inf]"),
        (rf.Numeric("price") <= 100, "@price:[-inf 100]"),

        # Text filters
        (rf.Text("title") == "hello", '@title:("hello")'),
        (rf.Text("title") != "hello", '(-@title:"hello")'),
        (rf.Text("title") % "*hello*", "@title:(*hello*)"),

        # Combined filters
        (
            (rf.Tag("color") == "blue") & (rf.Numeric("price") < 100),
            "(@color:{blue} @price:[-inf (100])"
        ),
        (
            (rf.Tag("color") == "blue") | (rf.Numeric("price") < 100),
            "(@color:{blue} | @price:[-inf (100])"
        ),
    ],
)
# fmt: on
def test_redisearch_filter(filter, query):
    assert str(filter) == query


# fmt: off
@pytest.mark.parametrize(
    "conditions, expected",
    [
        # Single conditions
        ([["color", "==", "blue"]], "@color:{blue}"),
        ([["color", "!=", "blue"]], "(-@color:{blue})"),
        ([["color", "in", ["blue", "red"]]], "@color:{blue|red}"),
        ([["color", "not in", ["blue", "red"]]], "(-@color:{blue|red})"),

        ([["price", "==", 100]], "@price:[100 100]"),
        ([["price", "!=", 100]], "(-@price:[100 100])"),
        ([["price", ">", 100]], "@price:[(100 +inf]"),
        ([["price", "<", 100]], "@price:[-inf (100]"),
        ([["price", ">=", 100]], "@price:[100 +inf]"),
        ([["price", "<=", 100]], "@price:[-inf 100]"),

        ([["title", "==", "hello"]], '@title:("hello")'),
        ([["title", "!=", "hello"]], '(-@title:"hello")'),
        ([["title", "like", "*hello*"]], "@title:(*hello*)"),

        # Multiple conditions (combined with &)
        (
            [["color", "in", ["blue", "red"]], ["price", "<", 1000], ["title", "like", "*hello*"]],
            "((@color:{blue|red} @price:[-inf (1000]) @title:(*hello*))"
        ),
    ],
)
# fmt: on
def test_create_redisearch_filter(conditions, expected):
    schema = RedisearchSchema.model_validate(
        {
            "fields": [
                {
                    "type": "tag",
                    "name": "color",
                },
                {
                    "type": "numeric",
                    "name": "price",
                    "sortable": True,
                },
                {
                    "type": "text",
                    "name": "title",
                },
            ]
        }
    )

    assert (
        str(rf.create_redisearch_filter(filter=conditions, schema=schema)) == expected
    )


# fmt: off
@pytest.mark.parametrize(
    "input_str, expected",
    [
        # If no special characters are present → Return as is
        ("hello", "hello"),
        ("abc123", "abc123"),

        # Characters that need escaping
        ("hello world", "hello\\ world"),
        ("price:100", "price\\:100"),
        ("(test)", "\\(test\\)"),
        ("path/to/file", "path\\/to\\/file"),
        ("email@example.com", "email\\@example\\.com"),

        # Containing multiple special characters
        ("a+b=c", "a\\+b\\=c"),
        ("sum<total>", "sum\\<total\\>"),
        ("{key:value}", "\\{key\\:value\\}"),

        # All special characters
        (".,!$", "\\.\\,\\!\\$"),
    ],
)
# fmt: on
def test_escape_token(input_str, expected):
    assert escape_token(input_str) == expected
