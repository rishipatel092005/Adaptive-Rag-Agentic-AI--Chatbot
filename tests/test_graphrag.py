import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.rag.graphrag.graph_store import Neo4jGraphStore
from src.rag.graphrag.knowledge_graph import KnowledgeGraphBuilder
from src.rag.graphrag.graph_retriever import GraphRetriever


load_dotenv()


def main():
    # -----------------------------------------
    # 1. Connect to Neo4j
    # -----------------------------------------

    store = Neo4jGraphStore()

    print(
        "Neo4j connected:",
        store.verify_connection()
    )

    if not store.verify_connection():
        store.close()
        return

    # -----------------------------------------
    # 2. Build knowledge graph
    # -----------------------------------------

    builder = KnowledgeGraphBuilder(store)

    text = """
    LangGraph is used to orchestrate an Agentic RAG system.
    The RAG system uses Qdrant as its vector database.
    LangChain provides components for document processing
    and retrieval.
    """

    result = builder.process_chunk(text)

    print("\nExtracted entities:")

    for entity in result.entities:
        print(entity)

    print("\nExtracted relationships:")

    for relationship in result.relationships:
        print(relationship)

    # -----------------------------------------
    # 3. Query GraphRAG
    # -----------------------------------------

    retriever = GraphRetriever(store)

    context = retriever.retrieve(
        "How does LangGraph work with RAG?"
    )

    print("\nGraph context:")
    print(context)

    # -----------------------------------------
    # 4. Close connection
    # -----------------------------------------

    store.close()


if __name__ == "__main__":
    main()