"""
Extract entities and relationships from document chunks.
"""

from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

from src.llms.openai import llm


class EntityModel(BaseModel):
    name: str = Field(
        description="Name of the entity."
    )

    type: str = Field(
        description=(
            "Entity type such as Person, Organization, "
            "Technology, Project, Concept, Product or Document."
        )
    )


class RelationshipModel(BaseModel):
    source: str = Field(
        description="Source entity name."
    )

    source_type: str = Field(
        description="Type of the source entity."
    )

    relationship: str = Field(
        description=(
            "Relationship between source and target. "
            "Use concise uppercase labels such as "
            "USES, WORKS_ON, PART_OF, DEPENDS_ON, "
            "IMPLEMENTS, ORCHESTRATES, RELATED_TO."
        )
    )

    target: str = Field(
        description="Target entity name."
    )

    target_type: str = Field(
        description="Type of the target entity."
    )


class GraphExtractionModel(BaseModel):
    entities: list[EntityModel] = Field(
        default_factory=list
    )

    relationships: list[RelationshipModel] = Field(
        default_factory=list
    )


def extract_graph_data(
    text: str,
) -> GraphExtractionModel:
    """
    Extract entities and relationships from one
    document chunk.
    """

    prompt = PromptTemplate(
        template="""
You are an information extraction system for a GraphRAG pipeline.

Extract important entities and relationships from the text.

Rules:

1. Extract only entities explicitly supported by the text.
2. Do not invent facts.
3. Normalize repeated entity names when possible.
4. Extract meaningful relationships between entities.
5. Keep relationship names concise and uppercase.
6. Ignore generic words that are not useful entities.

Examples of entity types:
- Person
- Organization
- Technology
- Project
- Product
- Concept
- Document

Examples of relationships:
- USES
- WORKS_ON
- PART_OF
- DEPENDS_ON
- IMPLEMENTS
- ORCHESTRATES
- RELATED_TO

Text:
{text}
""",
        input_variables=["text"],
    )

    structured_llm = llm.with_structured_output(
        GraphExtractionModel
    )

    chain = prompt | structured_llm

    return chain.invoke(
        {
            "text": text
        }
    )