"""
GraphRAG query-time retrieval.
"""

from src.rag.graphrag.graph_store import (
    Neo4jGraphStore,
)

from src.rag.graphrag.graph_utils import (
    deduplicate_relationships,
    format_graph_results,
)


class GraphRetriever:
    """
    Retrieves relevant information from the knowledge graph.
    """

    def __init__(
        self,
        graph_store: Neo4jGraphStore,
    ):
        self.graph_store = graph_store

    def retrieve(
        self,
        query: str,
        limit: int = 20,
    ) -> str:
        """
        Retrieve graph context for a query.

        First finds entities related to words in the query,
        then retrieves relationships around those entities.
        """

        words = query.split()

        all_relationships = []

        for word in words:

            if len(word) < 3:
                continue

            entities = (
                self.graph_store.search_entities(
                    word,
                    limit=5,
                )
            )

            for entity in entities:

                relationships = (
                    self.graph_store
                    .get_entity_relationships(
                        entity["name"],
                        limit=limit,
                    )
                )

                all_relationships.extend(
                    relationships
                )

        all_relationships = (
            deduplicate_relationships(
                all_relationships
            )
        )

        return format_graph_results(
            all_relationships[:limit]
        )