"""
GraphRAG schema definitions.
"""

from typing import TypedDict


class Entity(TypedDict):
    name: str
    type: str


class Relationship(TypedDict):
    source: str
    source_type: str
    relationship: str
    target: str
    target_type: str


class GraphExtraction(TypedDict):
    entities: list[Entity]
    relationships: list[Relationship]