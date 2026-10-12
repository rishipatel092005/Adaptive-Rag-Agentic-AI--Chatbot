"""
GraphRAG utility functions.
"""


def normalize_entity_name(
    name: str,
) -> str:
    """
    Normalize entity names for consistent storage.
    """

    return " ".join(
        name.strip().split()
    )


def format_relationship(
    relationship: dict,
) -> str:
    """
    Convert a graph relationship into readable text.
    """

    return (
        f"{relationship['source']} "
        f"--{relationship['relationship']}--> "
        f"{relationship['target']}"
    )


def format_graph_results(
    relationships: list[dict],
) -> str:
    """
    Convert graph relationships into LLM-readable context.
    """

    if not relationships:
        return "No graph relationships were found."

    lines = []

    for relationship in relationships:

        lines.append(
            format_relationship(
                relationship
            )
        )

    return "\n".join(lines)


def deduplicate_relationships(
    relationships: list[dict],
) -> list[dict]:
    """
    Remove duplicate graph relationships.
    """

    unique = []
    seen = set()

    for relationship in relationships:

        key = (
            relationship.get("source", "").lower(),
            relationship.get(
                "relationship",
                "",
            ).lower(),
            relationship.get(
                "target",
                "",
            ).lower(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(
                relationship
            )

    return unique