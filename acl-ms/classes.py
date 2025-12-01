from typing import Any, Dict, List

import pandas as pd
from neo4j import GraphDatabase


class Neo4jManager:
    def __init__(self, uri: str, username: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        if self.driver:
            self.driver.close()

    def create_nodes_from_dataframe(
        self, df: pd.DataFrame, label: str, unique_key: str = None
    ):
        records = df.to_dict("records")

        with self.driver.session() as session:
            if unique_key:
                try:
                    session.run(
                        f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
                        f"REQUIRE n.{unique_key} IS UNIQUE"
                    )
                except Exception as e:
                    print(f"Note: Could not create constraint - {e}")

            count = 0
            for record in records:
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
