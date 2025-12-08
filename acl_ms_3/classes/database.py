import os
from typing import Any, Dict, List

from neo4j import GraphDatabase


class Neo4jConnection:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self.driver:
            self.driver.close()

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(query)
            records = []
            for record in result:
                # Convert Neo4j record to dictionary
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    # Handle Neo4j node objects
                    if hasattr(value, "__dict__"):
                        record_dict[key] = dict(value)
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            return records


def load_config() -> Dict[str, str]:
    config = {}
    config_path = os.path.join(os.path.dirname(__file__), "../../config.txt")

    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                config[key] = value

    return config


config = load_config()
neo4j_conn = Neo4jConnection(
    uri=config.get("URI"),
    user=config.get("USERNAME"),
    password=config.get("PASSWORD"),
)

__all__ = ["neo4j_conn"]
