"""
Query Decomposition for complex RAG questions.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from src.llms.openai import llm


class DecompositionResponse(BaseModel):
    sub_questions: list[str] = Field(
        description=(
            "Independent sub-questions required to answer "
            "the original complex question."
        )
    )


def decompose_query(
    query: str,
    max_sub_questions: int = 4,
) -> list[str]:
    """
    Break a complex question into smaller searchable
    sub-questions.
    """

    prompt = PromptTemplate(
        template="""
You are a query decomposition system for a RAG application.

Break the user's question into smaller, independently searchable
sub-questions.

Requirements:
- Only decompose when the question contains multiple concepts
  or requires multiple pieces of evidence.
- Each sub-question should be clear and self-contained.
- Preserve important entities, technical terms and constraints.
- Avoid duplicate sub-questions.
- Generate at most {max_sub_questions} sub-questions.

Original question:
{query}
""",
        input_variables=[
            "query",
            "max_sub_questions",
        ],
    )

    structured_llm = llm.with_structured_output(
        DecompositionResponse
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "query": query,
            "max_sub_questions": max_sub_questions,
        }
    )

    sub_questions = []

    for sub_question in result.sub_questions:

        cleaned = sub_question.strip()

        if cleaned and cleaned not in sub_questions:
            sub_questions.append(cleaned)

    return sub_questions[:max_sub_questions]