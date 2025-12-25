import pytest
from semantic_search.utils import (
    dict_to_markdown,
    filter_queries,
    build_semantic_summaries,
)


@pytest.mark.parametrize(
    "query,expected_result",
    [
        # should remove all words
        ("water in india", ""),
        # should keep negated words
        ("-test", "-test"),
        # should remove all words except negated
        ("water in india -test", "-test"),
        # should remove words, keep negated phrase
        (
            'water in india -"test 123"',
            '-"test 123"',
        ),
        # should not remove words when OR-ed
        ('water OR "test"', 'water OR "test"'),
        # should keeps a phrase
        ('water AND "test"', '"test"'),
        # should remove AND, group where none of the terms are retained
        (
            "(water AND test)",
            "",
        ),
        # should keep negated term in AND, retain group
        ("(water AND -test)", "( -test)"),
        # should remove NOT (search doesn't yet support NOT), non-negated word
        ("NOT water", ""),
        # should keep phrase, remove NOT
        (
            'NOT "test"',
            '"test"',
        ),
        # all together now
        (
            'title:water water in india -"is a resource" -goats "test"',
            '-"is a resource" -goats "test"',
        ),
        # should handle single quotes at start of search query
        (
            "'water in india'",
            "",
        ),
    ],
)
def test_filter_queries(query, expected_result):
    results = filter_queries([query])
    assert results[0] == expected_result, (
        f"Expected {expected_result}, but got {results}"
    )


@pytest.mark.parametrize(
    "query,expected_result",
    [
        ("-test", ""),
        (
            'title:water water in india -"is a resource" -goats "test"',
            'title:water water in india "test"',
        ),
        (
            "'water in india'",
            "water in india'",
        ),
    ],
)
def test_filter_queries_without_negations(query, expected_result):
    results = filter_queries([query], keep_negations=False)
    assert results[0] == expected_result, (
        f"Expected {expected_result}, but got {results}"
    )


@pytest.mark.parametrize(
    "document_dict,expected_summary",
    [
        ({"title": "Test Document"}, "# title\n\nTest Document\n\n"),
        (
            {"summary": "This is a test document."},
            "# summary\n\nThis is a test document.\n\n",
        ),
        (
            {
                "details": {
                    "author": "John Doe",
                    "date": "2023-10-01",
                }
            },
            "# details\n\n## author\n\nJohn Doe\n\n## date\n\n2023-10-01\n\n\n",
        ),
        ({"tags": ["test", "document"]}, "# tags\n\n* test\n* document\n\n"),
    ],
)
def test_dict_to_markdown(document_dict, expected_summary):
    summaries = dict_to_markdown(document_dict)
    assert summaries == expected_summary, (
        f"Expected {expected_summary}, but got {summaries}"
    )


def test_build_semantic_summaries():
    document_dict = {
        "title": "Test Document",
        "summary": "This is a test document.",
        "details": {
            "author": "John Doe",
            "date": "2023-10-01",
        },
        "tags": ["test", "document"],
    }
    summaries = build_semantic_summaries(document_dict)
    expected_summaries = [
        "# title  \nTest Document",
        "# summary  \nThis is a test document.",
        "# details  \n## author  \nJohn Doe  \n## date  \n2023-10-01",
        "# tags  \n* test\n* document",
    ]
    assert summaries == expected_summaries
