import os
import time
from typing import Any, Dict, List, Tuple

from neo4j import GraphDatabase

from acl_ms_3.embedding.embeddor import Embeddor


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


DIMENSION_CONSTANT: int = 768
BATCH_SIZE_CONSTANT: int = 100


class Neo4jConnection:
    def __init__(self):
        config = load_config()
        self.driver = GraphDatabase.driver(
            uri=config.get("URI"),
            auth=(config.get("USERNAME"), config.get("PASSWORD")),
        )
        self.embedder = Embeddor()

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

    def get_all_node_labels(self) -> List[str]:
        query = "CALL db.labels()"
        result = self.execute_query(query)
        labels = [record["label"] for record in result]
        print(f"Found {len(labels)} node labels: {labels}")
        return labels

    def get_all_relationship_types(self) -> List[str]:
        query = "CALL db.relationshipTypes()"
        result = self.execute_query(query)
        rel_types = [record["relationshipType"] for record in result]
        print(f"Found {len(rel_types)} relationship types: {rel_types}")
        return rel_types

    def get_relationships_by_type(self, rel_type: str) -> List[Dict[str, Any]]:
        query = f"""
        MATCH (start)-[r:{rel_type}]->(end)
        RETURN id(r) as rel_id, 
               type(r) as rel_type,
               properties(r) as rel_properties,
               labels(start) as start_labels,
               properties(start) as start_properties,
               labels(end) as end_labels,
               properties(end) as end_properties
        """

        try:
            result = self.execute_query(query)
            print(f"Fetched {len(result)} relationship instances of type '{rel_type}'")
            return result
        except Exception as e:
            print(f"Error fetching relationships of type '{rel_type}': {e}")
            return []

    def get_nodes_by_label(self, label: str) -> List[Dict[str, Any]]:
        query = f"MATCH (n:{label}) RETURN id(n) as node_id, labels(n) as labels, properties(n) as properties"

        try:
            result = self.execute_query(query)
            print(f"Fetched {len(result)} nodes with label '{label}'")
            return result
        except Exception as e:
            print(f"Error fetching nodes with label '{label}': {e}")
            return []

    def store_node_embeddings_batch(
        self, node_embeddings: List[Tuple[int, List[float]]]
    ) -> int:
        query = """
        UNWIND $batch as item
        MATCH (n)
        WHERE id(n) = item.node_id
        SET n.embedding = item.embedding
        """

        try:
            batch_data = [
                {"node_id": node_id, "embedding": embedding}
                for node_id, embedding in node_embeddings
            ]

            with self.driver.session() as session:
                session.run(query, batch=batch_data)

            print(f"Successfully stored {len(node_embeddings)} embeddings")
            return len(node_embeddings)
        except Exception as e:
            print(f"Error in batch storing embeddings: {e}")
            return 0

    def store_relationship_embeddings_batch(
        self, relationship_embeddings: List[Tuple[int, List[float]]]
    ) -> int:
        query = """
        UNWIND $batch as item
        MATCH ()-[r]->()
        WHERE id(r) = item.rel_id
        SET r.embedding = item.embedding
        """

        try:
            batch_data = [
                {"rel_id": rel_id, "embedding": embedding}
                for rel_id, embedding in relationship_embeddings
            ]

            with self.driver.session() as session:
                session.run(query, batch=batch_data)

            print(
                f"Successfully stored {len(relationship_embeddings)} relationship embeddings"
            )
            return len(relationship_embeddings)
        except Exception as e:
            print(f"Error in batch storing relationship embeddings: {e}")
            return 0

    def create_node_vector_index(self):
        # get all labels that we've just embedded
        labels_query = "CALL db.labels()"
        labels_result = self.execute_query(labels_query)
        labels = [
            record["label"]
            for record in labels_result
            if record["label"] != "RelationshipType"  # exclude metadata nodes
        ]

        print(f"\nCreating vector indices for {len(labels)} node types...")

        created_indices = []

        for label in labels:
            current_index_name = f"node_embeddings_{label}"

            # drop the index if it exists
            try:
                drop_query = f"DROP INDEX {current_index_name} IF EXISTS"
                self.execute_query(drop_query)
                print(
                    f"  Dropped existing index '{current_index_name}' (if it existed)"
                )
            except Exception as e:
                pass  # Index may not exist

            # create the vector index
            try:
                create_query = f"""
                CREATE VECTOR INDEX {current_index_name} IF NOT EXISTS
                FOR (n:{label})
                ON (n.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {DIMENSION_CONSTANT},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                self.execute_query(create_query)
                print(f"  ✓ Created vector index '{current_index_name}'")
                created_indices.append(current_index_name)
            except Exception as e:
                print(f"  ✗ Error creating vector index for {label}: {e}")

        print(
            f"\n✓ Created {len(created_indices)} vector indices with dimension {DIMENSION_CONSTANT}"
        )

    def create_relationship_vector_index(self):

        # Get all relationship types
        rel_types = self.get_all_relationship_types()

        print(f"\nCreating vector indices for {len(rel_types)} relationship types...")

        created_indices = []

        for rel_type in rel_types:
            index_name = f"rel_embeddings_{rel_type}"

            # Drop the index if it exists
            try:
                drop_query = f"DROP INDEX {index_name} IF EXISTS"
                self.execute_query(drop_query)
                print(f"  Dropped existing index '{index_name}' (if it existed)")
            except Exception as e:
                pass  # Index may not exist

            # Create the vector index for relationships
            try:
                create_query = f"""
                CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR ()-[r:{rel_type}]-()
                ON (r.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: {DIMENSION_CONSTANT},
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                self.execute_query(create_query)
                print(
                    f"  ✓ Created vector index '{index_name}' for {rel_type} relationships"
                )
                created_indices.append(index_name)
            except Exception as e:
                print(f"  ✗ Error creating vector index for {rel_type}: {e}")

        print(
            f"\n✓ Created {len(created_indices)} relationship vector indices with dimension {DIMENSION_CONSTANT}"
        )

    def embed_nodes(self):
        print("=" * 80)
        print("Starting Neo4j Node Embedding Process")
        print("=" * 80)

        embedding_dim = self.embedder.get_embedding_dimension()

        labels = self.get_all_node_labels()

        total_nodes = 0
        total_embedded = 0
        start_time = time.time()

        for label in labels:
            print(f"\n{'=' * 60}")
            print(f"Processing nodes with label: {label}")
            print(f"{'=' * 60}")

            nodes = self.get_nodes_by_label(label)

            if not nodes:
                print(f"No nodes found for label '{label}'")
                continue

            total_nodes += len(nodes)

            # process nodes in batches
            for i in range(0, len(nodes), BATCH_SIZE_CONSTANT):
                batch = nodes[i : i + BATCH_SIZE_CONSTANT]
                batch_num = i // BATCH_SIZE_CONSTANT + 1
                total_batches = (
                    len(nodes) + BATCH_SIZE_CONSTANT - 1
                ) // BATCH_SIZE_CONSTANT

                print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} nodes)")

                # generate descriptions for all nodes in batch
                descriptions = []
                node_ids = []

                for node in batch:
                    node_id = node["node_id"]
                    properties = node["properties"]

                    description = self.embedder.generate_node_description(
                        label, properties
                    )
                    descriptions.append(description)
                    node_ids.append(node_id)

                    if len(descriptions) <= 3:  # show first few examples
                        print(f"  Node {node_id}: {description[:100]}...")

                print(
                    f"  Generating embeddings for {len(descriptions)} descriptions..."
                )
                embeddings = self.embedder.generate_embeddings_batch(descriptions)

                # store embeddings back to Neo4j
                node_embeddings = list(zip(node_ids, embeddings))
                embedded_count = self.store_node_embeddings_batch(node_embeddings)
                total_embedded += embedded_count

                print(f"  ✓ Completed batch {batch_num}/{total_batches}")

        # create vector index
        print(f"\n{'=' * 60}")
        print("Creating vector index...")
        print(f"{'=' * 60}")
        self.create_node_vector_index()

        # summary
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 80}")
        print("EMBEDDING PROCESS COMPLETE")
        print(f"{'=' * 80}")
        print(f"Total nodes processed: {total_nodes}")
        print(f"Total embeddings stored: {total_embedded}")
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"{'=' * 80}")

    def embed_relationships(self):
        print("=" * 80)
        print("Starting Neo4j Relationship Instance Embedding Process")
        print("=" * 80)
        print("Note: Storing ONE embedding per relationship INSTANCE")

        embedding_dim = self.embedder.get_embedding_dimension()

        rel_types = self.get_all_relationship_types()

        total_relationships = 0
        total_embedded = 0
        start_time = time.time()

        for rel_type in rel_types:
            print(f"\n{'=' * 60}")
            print(f"Processing relationships of type: {rel_type}")
            print(f"{'=' * 60}")

            relationships = self.get_relationships_by_type(rel_type)

            if not relationships:
                print(f"No relationships found for type '{rel_type}'")
                continue

            total_relationships += len(relationships)

            # Process relationships in batches
            for i in range(0, len(relationships), BATCH_SIZE_CONSTANT):
                batch = relationships[i : i + BATCH_SIZE_CONSTANT]
                batch_num = i // BATCH_SIZE_CONSTANT + 1
                total_batches = (
                    len(relationships) + BATCH_SIZE_CONSTANT - 1
                ) // BATCH_SIZE_CONSTANT

                print(
                    f"\nBatch {batch_num}/{total_batches} ({len(batch)} relationships)"
                )

                # Generate descriptions for all relationships in batch
                descriptions = []
                rel_ids = []

                for rel in batch:
                    rel_id = rel["rel_id"]
                    rel_properties = rel["rel_properties"]
                    start_properties = rel["start_properties"]
                    end_properties = rel["end_properties"]

                    description = self.embedder.generate_relationship_description(
                        rel_type, rel_properties, start_properties, end_properties
                    )
                    descriptions.append(description)
                    rel_ids.append(rel_id)

                    if len(descriptions) <= 3:  # Show first few examples
                        print(f"  Relationship {rel_id}: {description[:100]}...")

                print(
                    f"  Generating embeddings for {len(descriptions)} descriptions..."
                )
                embeddings = self.embedder.generate_embeddings_batch(descriptions)

                # Store embeddings back to Neo4j
                rel_embeddings = list(zip(rel_ids, embeddings))
                embedded_count = self.store_relationship_embeddings_batch(
                    rel_embeddings
                )
                total_embedded += embedded_count

                print(f"  ✓ Completed batch {batch_num}/{total_batches}")

        # Create vector indices
        print(f"\n{'=' * 60}")
        print("Creating relationship vector indices...")
        print(f"{'=' * 60}")
        self.create_relationship_vector_index()

        # Summary
        elapsed_time = time.time() - start_time
        print(f"\n{'=' * 80}")
        print("RELATIONSHIP INSTANCE EMBEDDING PROCESS COMPLETE")
        print(f"{'=' * 80}")
        print(f"Total relationships processed: {total_relationships}")
        print(f"Total embeddings stored: {total_embedded}")
        print(f"Embedding dimension: {embedding_dim}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"{'=' * 80}")

    def verify_node_embeddings(self):
        print("\n" + "=" * 60)
        print("Verifying Node Embeddings")
        print("=" * 60)

        # Count nodes with embeddings (excluding RelationshipType metadata nodes)
        query = """
        MATCH (n)
        WHERE n.embedding IS NOT NULL AND NOT 'RelationshipType' IN labels(n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """

        result = self.execute_query(query)

        total = 0
        for record in result:
            label = record["label"]
            count = record["count"]
            total += count
            print(f"  {label}: {count} nodes with embeddings")

        print(f"\nTotal nodes with embeddings: {total}")

        # Show a sample embedding
        sample_query = """
        MATCH (n)
        WHERE n.embedding IS NOT NULL AND NOT 'RelationshipType' IN labels(n)
        RETURN labels(n)[0] as label, properties(n) as props, size(n.embedding) as embedding_size
        LIMIT 1
        """

        sample = self.execute_query(sample_query)
        if sample:
            record = sample[0]
            print(f"\nSample node:")
            print(f"  Label: {record['label']}")
            print(f"  Embedding size: {record['embedding_size']}")
            print(f"  ✓ Node embeddings verified!")

    def verify_relationship_embeddings(self):
        print("\n" + "=" * 60)
        print("Verifying Relationship Instance Embeddings")
        print("=" * 60)

        # Count relationships with embeddings by type
        query = """
        MATCH ()-[r]->()
        WHERE r.embedding IS NOT NULL
        RETURN type(r) as rel_type, count(r) as count
        ORDER BY count DESC
        """

        result = self.execute_query(query)

        if not result:
            print("  ✗ No relationship embeddings found!")
            return

        total = 0
        print(f"\nFound relationship instances with embeddings:")
        for record in result:
            rel_type = record["rel_type"]
            count = record["count"]
            total += count
            print(f"  {rel_type}: {count} relationships with embeddings")

        print(f"\nTotal relationships with embeddings: {total}")

        # Show a sample embedding
        sample_query = """
        MATCH (start)-[r]->(end)
        WHERE r.embedding IS NOT NULL
        RETURN type(r) as rel_type, 
               size(r.embedding) as embedding_size,
               labels(start)[0] as start_label,
               labels(end)[0] as end_label
        LIMIT 1
        """

        sample = self.execute_query(sample_query)
        if sample:
            record = sample[0]
            print(f"\nSample relationship:")
            print(f"  Type: {record['rel_type']}")
            print(f"  From: {record['start_label']} -> To: {record['end_label']}")
            print(f"  Embedding size: {record['embedding_size']}")
            print(f"  ✓ Relationship instance embeddings verified!")


__all__ = ["Neo4jConnection"]
