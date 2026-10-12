"""
LangGraph node implementations for Adaptive RAG.
"""

from langchain_community.tools import TavilySearchResults
from langchain_core.messages import AIMessage
from langchain_core.prompts import PromptTemplate

from src.config.settings import Config
from src.llms.openai import llm
from src.models.grade import Grade
from src.models.route_identifier import RouteIdentifier
from src.models.state import State
from src.rag.hybrid.hybrid_retriever import hybrid_retriever


config = Config()


def _format_documents(
    documents,
) -> str:
    """
    Convert retrieved documents into readable context.
    """

    if not documents:
        return "No relevant documents were found."

    formatted_parts = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        metadata = document.metadata or {}

        source = metadata.get(
            "source",
            "unknown",
        )

        page = metadata.get(
            "page",
            None,
        )

        page_text = (
            f", page {page + 1}"
            if isinstance(page, int)
            else ""
        )

        formatted_parts.append(
            (
                f"[Document {index} | "
                f"source: {source}{page_text}]\n"
                f"{document.page_content}"
            )
        )

    return "\n\n".join(formatted_parts)


def query_classifier(
    state: State,
):
    """
    Classify the query using context retrieved by Hybrid Search.
    """

    question = state["messages"][-1].content

    documents = hybrid_retriever.invoke(
        question,
    )

    context = _format_documents(
        documents,
    )

    llm_with_structured_output = (
        llm.with_structured_output(
            RouteIdentifier
        )
    )

    classify_prompt = PromptTemplate(
        template=config.prompt(
            "classify_prompt"
        ),
        input_variables=[
            "question",
            "context",
        ],
    )

    chain = (
        classify_prompt
        | llm_with_structured_output
    )

    result = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    print(
        f"[query_classifier] Route: {result.route}"
    )

    return {
        "messages": state["messages"],
        "route": result.route,
        "latest_query": question,
    }


def general_llm(
    state: State,
):
    """
    Answer general knowledge questions.
    """

    result = llm.invoke(
        state["messages"]
    )

    return {
        "messages": [result]
    }


def retriever_node(
    state: State,
):
    """
    Retrieve documents using Hybrid Search.

    Dense:
        FAISS

    Sparse:
        BM25

    Fusion:
        RRF
    """

    query = state["latest_query"]

    documents = hybrid_retriever.invoke(
        query,
    )

    context = _format_documents(
        documents,
    )

    print(
        f"[retriever_node] Retrieved "
        f"{len(documents)} documents"
    )

    return {
        "messages": [
            AIMessage(
                content=context
            )
        ]
    }


def grade(
    state: State,
):
    """
    Grade retrieved context for relevance.
    """

    grading_prompt = PromptTemplate(
        template=config.prompt(
            "grading_prompt"
        ),
        input_variables=[
            "question",
            "context",
        ],
    )

    context = (
        state["messages"][-1].content
    )

    question = state["latest_query"]

    llm_with_grade = (
        llm.with_structured_output(
            Grade
        )
    )

    chain = (
        grading_prompt
        | llm_with_grade
    )

    result = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    print(
        f"[grade] Binary score: "
        f"{result.binary_score}"
    )

    return {
        "messages": state["messages"],
        "binary_score": result.binary_score,
    }


def rewrite_query(
    state: State,
):
    """
    Rewrite the query when retrieved context
    is not relevant.
    """

    query = state["latest_query"]

    rewrite_prompt = PromptTemplate(
        template=config.prompt(
            "rewrite_prompt"
        ),
        input_variables=[
            "query"
        ],
    )

    chain = rewrite_prompt | llm

    result = chain.invoke(
        {
            "query": query
        }
    )

    rewritten_query = result.content

    print(
        f"[rewrite_query] "
        f"{query} -> {rewritten_query}"
    )

    return {
        "latest_query": rewritten_query
    }


def generate(
    state: State,
):
    """
    Generate final answer from retrieved context.
    """

    context = (
        state["messages"][-1].content
    )

    generate_prompt = PromptTemplate(
        template=config.prompt(
            "generate_prompt"
        ),
        input_variables=[
            "context"
        ],
    )

    generate_chain = (
        generate_prompt
        | llm
    )

    result = generate_chain.invoke(
        {
            "context": context
        }
    )

    return {
        "messages": [result]
    }


def web_search(
    state: State,
):
    """
    Search the web using Tavily.
    """

    search_tool = TavilySearchResults()

    results = search_tool.invoke(
        state["latest_query"]
    )

    contents = []

    for item in results:

        if isinstance(item, dict):

            content = item.get(
                "content"
            )

            if content:
                contents.append(
                    content
                )

    context = "\n\n".join(
        contents
    )

    return {
        "messages": [
            AIMessage(
                content=context
            )
        ]
    }