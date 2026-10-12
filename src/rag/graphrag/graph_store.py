"""
Neo4j graph storage layer.
"""

import os

from neo4j import GraphDatabase


class Neo4jGraphStore:
    """
    Handles communication with Neo4j.
    """

    def __init__(
        self,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ):
        self.uri = uri or os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )

        self.username = username or os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )

        self.password = password or os.getenv(
            "NEO4J_PASSWORD",
            "",
        )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

    def close(self):
        self.driver.close()

    def verify_connection(self) -> bool:
        """
        Check whether Neo4j is reachable.
        """

        try:
            self.driver.verify_connectivity()
            return True

        except Exception as exc:
            print(
                f"[Neo4j] Connection failed: {exc}"
            )
            return False

    def add_entity(
        self,
        name: str,
        entity_type: str,
    ):
        """
        Add or update an entity.
        """

        query = """
        MERGE (e:Entity {name: $name})
        SET e.type = $entity_type
        """

        with self.driver.session() as session:
            session.run(
                query,
                name=name,
                entity_type=entity_type,
            )

    def add_relationship(
        self,
        source: str,
        source_type: str,
        relationship: str,
        target: str,
        target_type: str,
    ):
        """
        Add a relationship between two entities.
        """

        query = """
        MERGE (source:Entity {name: $source})
        SET source.type = $source_type

        MERGE (target:Entity {name: $target})
        SET target.type = $target_type

        MERGE (source)-[r:RELATED_TO {type: $relationship}]->(target)
        """

        with self.driver.session() as session:
            session.run(
                query,
                source=source,
                source_type=source_type,
                relationship=relationship,
                target=target,
                target_type=target_type,
            )

    def get_entity_relationships(
        self,
        entity_name: str,
        limit: int = 20,
    ):
        """
        Retrieve relationships around an entity.
        """

        query = """
        MATCH (source:Entity)-[r]->(target:Entity)
        WHERE toLower(source.name) = toLower($entity_name)
           OR toLower(target.name) = toLower($entity_name)

        RETURN
            source.name AS source,
            source.type AS source_type,
            r.type AS relationship,
            target.name AS target,
            target.type AS target_type

        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                entity_name=entity_name,
                limit=limit,
            )

            return [
                record.data()
                for record in result
            ]

    def search_entities(
        self,
        entity_name: str,
        limit: int = 10,
    ):
        """
        Find entities whose names contain the query.
        """

        query = """
        MATCH (e:Entity)
        WHERE toLower(e.name) CONTAINS toLower($name)

        RETURN
            e.name AS name,
            e.type AS type

        LIMIT $limit
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                name=entity_name,
                limit=limit,
            )

            return [
                record.data()
                for record in result
            ]

    def clear_graph(self):
        """
        Delete all graph data.

        Use carefully.
        """

        query = """
        MATCH (n)
        DETACH DELETE n
        """

        with self.driver.session() as session:
            session.run(query)