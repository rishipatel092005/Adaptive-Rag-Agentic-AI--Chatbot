"""
HyDE (Hypothetical Document Embeddings) query transformation.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from src.llms.openai import llm


class HyDEResponse(BaseModel):
    hypothetical_document: str = Field(
        description=(
            "A hypothetical document that would contain "
            "the answer to the user's question."
        )
    )


def generate_hyde_query(query: str) -> str:
    """
    Generate a hypothetical document for HyDE retrieval.

    The generated document is not shown directly to the user.
    It is used only to improve retrieval.
    """

    prompt = PromptTemplate(
        template="""
You are helping a retrieval system.

Given the user's question, write a hypothetical answer/document
that would likely contain the information needed to answer it.

Requirements:
- Focus on factual content relevant to the question.
- Include useful technical terms and concepts.
- Do not mention that you are generating a hypothetical document.
- Do not add unrelated information.
- Write one concise but information-rich paragraph.

User question:
{query}
""",
        input_variables=["query"],
    )

    structured_llm = llm.with_structured_output(
        HyDEResponse
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "query": query
        }
    )

    return result.hypothetical_document