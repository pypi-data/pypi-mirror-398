import luqum.parser
import ply.lex as lex
import ply.yacc as yacc
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from semantic_search.transformers import (
    FilterQueryTransformer,
    WithoutNegationsTransformer,
)


# patch Luqum's error handling to handle unexpected tokens more gracefully
luqum.parser.t_error = lambda t: t.lexer.skip(1)
lexer = lex.lex(module=luqum.parser)
parser = yacc.yacc(module=luqum.parser)

headers_to_split_on = [
    ("#", "Header 1"),
]

token_splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)

max_tokens = 1000
chunk_overlap = 30
encoder_name = "cl100k_base"

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name=encoder_name,
    chunk_size=max_tokens,
    chunk_overlap=chunk_overlap,
)


def filter_queries(qs, keep_negations=True):
    """
    Filters a list of queries to keep only phrases, e.g. "term", and
    negations, and some operators,
    e.g. `title:water water in india -"is a resource" -goats "test"`
    becomes `-"is a resource" -goats "test"`.
    Or just removes negations.
    """

    Transformer = (
        FilterQueryTransformer if keep_negations else WithoutNegationsTransformer
    )

    return [str(Transformer().visit(parser.parse(q))).strip() for q in qs]


def dict_to_markdown(data, level=1):
    markdown = ""
    for key, value in data.items():
        if value:
            markdown += f"{'#' * level} {key}\n\n"
            if isinstance(value, dict):
                markdown += dict_to_markdown(value, level + 1)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        markdown += dict_to_markdown(item, level + 1)
                    else:
                        markdown += f"* {item}\n"
            else:
                markdown += f"{value}\n"
            markdown += "\n"
    return markdown


def batch_queryset(qs, batch_size):
    batch = []
    for obj in qs:
        batch.append(obj)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def build_semantic_summaries(document_dict):
    text = dict_to_markdown(document_dict)
    summaries = [
        doc.page_content
        for doc in text_splitter.split_documents(token_splitter.split_text(text))
        if doc.page_content.strip()
    ]
    return summaries
