"""
LangGraph workflow construction for Adaptive RAG.
"""

from langgraph.constants import START, END
from langgraph.graph.state import StateGraph

from src.models.state import State
from src.rag.nodes import (
    query_classifier,
    retriever_node,
    grade,
    rewrite_query,
    generate,
    web_search,
    general_llm,
)
from src.tools.graph_tools import (
    routing_tool,
    doc_tool,
)


# -----------------------------------------
# Create graph
# -----------------------------------------

graph = StateGraph(State)


# -----------------------------------------
# Add nodes
# -----------------------------------------

graph.add_node(
    "query_analysis",
    query_classifier,
)

graph.add_node(
    "retriever",
    retriever_node,
)

graph.add_node(
    "grade",
    grade,
)

graph.add_node(
    "rewrite",
    rewrite_query,
)

graph.add_node(
    "generate",
    generate,
)

graph.add_node(
    "web_search",
    web_search,
)

graph.add_node(
    "general_llm",
    general_llm,
)


# -----------------------------------------
# Start
# -----------------------------------------

graph.add_edge(
    START,
    "query_analysis",
)


# -----------------------------------------
# Query routing
# -----------------------------------------

graph.add_conditional_edges(
    "query_analysis",
    routing_tool,
)


# -----------------------------------------
# Retrieval → grading
# -----------------------------------------

graph.add_edge(
    "retriever",
    "grade",
)


# -----------------------------------------
# Grade → generate/rewrite
# -----------------------------------------

graph.add_conditional_edges(
    "grade",
    doc_tool,
)


# -----------------------------------------
# Rewrite → retrieve again
# -----------------------------------------

graph.add_edge(
    "rewrite",
    "retriever",
)


# -----------------------------------------
# Web search → generate
# -----------------------------------------

graph.add_edge(
    "web_search",
    "generate",
)


# -----------------------------------------
# Final nodes
# -----------------------------------------

graph.add_edge(
    "generate",
    END,
)

graph.add_edge(
    "general_llm",
    END,
)


# -----------------------------------------
# Compile
# -----------------------------------------

builder = graph.compile()