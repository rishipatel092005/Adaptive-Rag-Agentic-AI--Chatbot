"""
ReAct agent setup for document retrieval and question answering.
"""

import os
from langchain_core.prompts import ChatPromptTemplate

from src.config.settings import Config
from src.llms.openai import llm

config = Config()

# Create ReAct agent prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", config.prompt("system_prompt")),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])

# Lazy import to avoid version conflicts
def _get_agent(user_id: str | None):
    """Lazy import to handle version conflicts with LangChain"""
    from langchain.agents import create_react_agent, AgentExecutor
    from src.rag.retriever_setup import get_retriever

    tools = [get_retriever(user_id=user_id)]
    react_agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=react_agent,
        tools=tools,
        handle_parsing_errors=True,
        max_iterations=2,
        verbose=True,
        return_intermediate_steps=True
    )

_agent_executors = {}

def get_agent_executor(user_id: str | None = None):
    if user_id not in _agent_executors:
        _agent_executors[user_id] = _get_agent(user_id)
    return _agent_executors[user_id]
