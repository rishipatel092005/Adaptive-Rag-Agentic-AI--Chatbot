"""
Multi-Query generation for RAG retrieval.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from src.llms.openai import llm


class MultiQueryResponse(BaseModel):
    queries: list[str] = Field(
        description=(
            "Three alternative search queries that preserve "
            "the meaning of the original question."
        )
    )


def generate_multi_queries(
    query: str,
    num_queries: int = 3,
) -> list[str]:
    """
    Generate multiple semantically different versions
    of the user's query.
    """

    prompt = PromptTemplate(
        template="""
You are a retrieval query expansion system.

Generate {num_queries} alternative search queries for the
user's question.

Requirements:
- Preserve the original intent.
- Use different wording and terminology.
- Include useful technical terms where appropriate.
- Make each query independently useful for document retrieval.
- Do not answer the question.
- Return only search queries.

Original question:
{query}
""",
        input_variables=[
            "query",
            "num_queries",
        ],
    )

    structured_llm = llm.with_structured_output(
        MultiQueryResponse
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "query": query,
            "num_queries": num_queries,
        }
    )

    queries = []

    for generated_query in result.queries:

        cleaned = generated_query.strip()

        if cleaned and cleaned not in queries:
            queries.append(cleaned)

    # Keep the original query as well.
    final_queries = [query]

    for generated_query in queries:
        if generated_query.lower() != query.lower():
            final_queries.append(generated_query)

    return final_queries[: num_queries + 1]