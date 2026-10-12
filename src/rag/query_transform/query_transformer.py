"""
Main query transformation controller.
"""

from langchain_core.prompts import PromptTemplate

from src.llms.openai import llm
from src.config.settings import Config

from .hyde import generate_hyde_query
from .multi_query import generate_multi_queries
from .decomposition import decompose_query


config = Config()


def rewrite_query(query: str) -> str:
    """
    Basic query rewriting.

    This upgrades the rewriting logic that already existed
    in the original Adaptive RAG project.
    """

    prompt = PromptTemplate(
        template=config.prompt(
            "rewrite_prompt"
        ),
        input_variables=["query"],
    )

    chain = prompt | llm

    result = chain.invoke(
        {
            "query": query
        }
    )

    return result.content.strip()


def transform_query(
    query: str,
    strategy: str = "rewrite",
) -> list[str]:
    """
    Transform a query using the selected strategy.

    Supported strategies:
        none
        rewrite
        hyde
        multi_query
        decomposition
    """

    query = query.strip()

    if not query:
        return []

    # --------------------------------------------------
    # No transformation
    # --------------------------------------------------

    if strategy == "none":
        return [query]

    # --------------------------------------------------
    # Basic Rewrite
    # --------------------------------------------------

    if strategy == "rewrite":

        rewritten = rewrite_query(query)

        return [
            rewritten
        ]

    # --------------------------------------------------
    # HyDE
    # --------------------------------------------------

    if strategy == "hyde":

        hypothetical_document = (
            generate_hyde_query(query)
        )

        return [
            hypothetical_document
        ]

    # --------------------------------------------------
    # Multi Query
    # --------------------------------------------------

    if strategy == "multi_query":

        return generate_multi_queries(
            query
        )

    # --------------------------------------------------
    # Query Decomposition
    # --------------------------------------------------

    if strategy == "decomposition":

        return decompose_query(
            query
        )

    raise ValueError(
        f"Unknown query transformation strategy: "
        f"{strategy}"
    )