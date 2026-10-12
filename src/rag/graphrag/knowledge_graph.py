"""
Knowledge graph construction pipeline.
"""

from src.rag.graphrag.entity_extractor import (
    extract_graph_data,
)

from src.rag.graphrag.graph_store import (
    Neo4jGraphStore,
)

from src.rag.graphrag.graph_utils import (
    normalize_entity_name,
)


class KnowledgeGraphBuilder:
    """
    Converts document chunks into a Neo4j knowledge graph.
    """

    def __init__(
        self,
        graph_store: Neo4jGraphStore,
    ):
        self.graph_store = graph_store

    def process_chunk(
        self,
        text: str,
    ):
        """
        Extract graph information from one chunk
        and store it in Neo4j.
        """

        extraction = extract_graph_data(
            text
        )

        # ------------------------------
        # Store entities
        # ------------------------------

        for entity in extraction.entities:

            name = normalize_entity_name(
                entity.name
            )

            if not name:
                continue

            self.graph_store.add_entity(
                name=name,
                entity_type=entity.type,
            )

        # ------------------------------
        # Store relationships
        # ------------------------------

        for relationship in extraction.relationships:

            source = normalize_entity_name(
                relationship.source
            )

            target = normalize_entity_name(
                relationship.target
            )

            if not source or not target:
                continue

            self.graph_store.add_relationship(
                source=source,
                source_type=relationship.source_type,
                relationship=relationship.relationship,
                target=target,
                target_type=relationship.target_type,
            )

        return extraction

    def build_from_chunks(
        self,
        chunks,
    ):
        """
        Build the graph from a list of LangChain Documents.
        """

        results = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            print(
                f"[GraphRAG] Processing chunk "
                f"{index}/{len(chunks)}"
            )

            extraction = self.process_chunk(
                chunk.page_content
            )

            results.append(
                extraction
            )

        return results