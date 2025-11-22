from typing import Any, Dict, List

import pandas as pd
from neo4j import GraphDatabase


class Neo4jManager:
    """
    A class to manage Neo4j database operations including node and relationship creation.
    """

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize connection to Neo4j database.

        Args:
            uri: Neo4j database URI (e.g., 'bolt://localhost:7687')
            username: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()

    def create_nodes_from_dataframe(
        self, df: pd.DataFrame, label: str, unique_key: str = None
    ):
        """
        Create nodes in Neo4j from a pandas DataFrame.

        Args:
            df: DataFrame containing the data
            label: Node label (e.g., 'Traveller', 'Hotel')
            unique_key: Column name to use as unique constraint (optional)

        Returns:
            Number of nodes created
        """
        records = df.to_dict("records")

        with self.driver.session() as session:
            # Create unique constraint if specified
            if unique_key:
                try:
                    session.run(
                        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
                        f"REQUIRE n.{unique_key} IS UNIQUE"
                    )
                except Exception as e:
                    print(f"Note: Could not create constraint - {e}")

            # Create nodes
            count = 0
            for record in records:
                # Remove None values
                props = {k: v for k, v in record.items() if pd.notna(v)}

                query = f"CREATE (n:{label} $props)"
                if unique_key and unique_key in props:
                    query = f"MERGE (n:{label} {{{unique_key}: $props.{unique_key}}}) SET n = $props"

                session.run(query, props=props)
                count += 1

            return count

    def create_relationship(
        self,
        from_label: str,
        from_key: str,
        from_value: Any,
        to_label: str,
        to_key: str,
        to_value: Any,
        relationship_type: str,
        properties: Dict[str, Any] = None,
    ):
        """
        Create a relationship between two nodes.

        Args:
            from_label: Label of the source node
            from_key: Property key to match source node
            from_value: Property value to match source node
            to_label: Label of the target node
            to_key: Property key to match target node
            to_value: Property value to match target node
            relationship_type: Type of relationship (e.g., 'REVIEWED', 'LOCATED_IN')
            properties: Optional dictionary of relationship properties

        Returns:
            True if relationship created, False otherwise
        """
        with self.driver.session() as session:
            props_clause = ""
            params = {"from_value": from_value, "to_value": to_value}

            if properties:
                props_clause = " SET r += $props"
                params["props"] = properties

            query = f"""
            MATCH (a:{from_label} {{{from_key}: $from_value}})
            MATCH (b:{to_label} {{{to_key}: $to_value}})
            MERGE (a)-[r:{relationship_type}]->(b)
            {props_clause}
            RETURN r
            """

            result = session.run(query, params)
            return result.single() is not None

    def create_relationships_from_dataframe(
        self,
        df: pd.DataFrame,
        from_label: str,
        from_key: str,
        from_column: str,
        to_label: str,
        to_key: str,
        to_column: str,
        relationship_type: str,
        property_columns: List[str] = None,
    ):
        """
        Create multiple relationships from a DataFrame.

        Args:
            df: DataFrame containing relationship data
            from_label: Label of source nodes
            from_key: Property key for source nodes
            from_column: DataFrame column for source node values
            to_label: Label of target nodes
            to_key: Property key for target nodes
            to_column: DataFrame column for target node values
            relationship_type: Type of relationship
            property_columns: List of columns to add as relationship properties

        Returns:
            Number of relationships created
        """
        count = 0

        for _, row in df.iterrows():
            props = {}
            if property_columns:
                props = {
                    col: row[col] for col in property_columns if pd.notna(row[col])
                }

            if self.create_relationship(
                from_label,
                from_key,
                row[from_column],
                to_label,
                to_key,
                row[to_column],
                relationship_type,
                props,
            ):
                count += 1

        return count
