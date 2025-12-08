import time
from typing import Any, Dict, List, Tuple

from classes.database import neo4j_conn
from classes.embeddor import Embeddor


def get_all_node_labels() -> List[str]:
    query = "CALL db.labels()"
    result = neo4j_conn.execute_query(query)
    labels = [record["label"] for record in result]
    print(f"Found {len(labels)} node labels: {labels}")
    return labels


def get_nodes_by_label(label: str) -> List[Dict[str, Any]]:
    query = f"MATCH (n:{label}) RETURN id(n) as node_id, labels(n) as labels, properties(n) as properties"

    try:
        result = neo4j_conn.execute_query(query)
        print(f"Fetched {len(result)} nodes with label '{label}'")
        return result
    except Exception as e:
        print(f"Error fetching nodes with label '{label}': {e}")
        return []


def store_embeddings_batch(node_embeddings: List[Tuple[int, List[float]]]) -> int:
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

        with neo4j_conn.driver.session() as session:
            session.run(query, batch=batch_data)

        print(f"Successfully stored {len(node_embeddings)} embeddings")
        return len(node_embeddings)
    except Exception as e:
        print(f"Error in batch storing embeddings: {e}")
        return 0


# create a vector index on the embedding property for similarity search.
# dimension: Dimension of the embedding vectors (default 384 for all-MiniLM-L6-v2)
def create_vector_index(index_name: str = "node_embeddings", dimension: int = 768):
    # Get all labels that we've just embedded
    labels_query = "CALL db.labels()"
    labels_result = neo4j_conn.execute_query(labels_query)
    labels = [record["label"] for record in labels_result]

    print(f"\nCreating vector indices for {len(labels)} node types...")

    created_indices = []

    for label in labels:
        current_index_name = f"{index_name}_{label}"

        # drop the index if it exists
        try:
            drop_query = f"DROP INDEX {current_index_name} IF EXISTS"
            neo4j_conn.execute_query(drop_query)
            print(f"  Dropped existing index '{current_index_name}' (if it existed)")
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
                    `vector.dimensions`: {dimension},
                    `vector.similarity_function`: 'cosine'
                }}
            }}
            """
            neo4j_conn.execute_query(create_query)
            print(f"  ✓ Created vector index '{current_index_name}'")
            created_indices.append(current_index_name)
        except Exception as e:
            print(f"  ✗ Error creating vector index for {label}: {e}")

    print(
        f"\n✓ Created {len(created_indices)} vector indices with dimension {dimension}"
    )


def embed_all_nodes(batch_size: int = 100):
    print("=" * 80)
    print("Starting Neo4j Node Embedding Process")
    print("=" * 80)

    embedder = Embeddor()
    embedding_dim = embedder.get_embedding_dimension()

    labels = get_all_node_labels()

    total_nodes = 0
    total_embedded = 0
    start_time = time.time()

    for label in labels:
        print(f"\n{'=' * 60}")
        print(f"Processing nodes with label: {label}")
        print(f"{'=' * 60}")

        nodes = get_nodes_by_label(label)

        if not nodes:
            print(f"No nodes found for label '{label}'")
            continue

        total_nodes += len(nodes)

        # process nodes in batches
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(nodes) + batch_size - 1) // batch_size

            print(f"\nBatch {batch_num}/{total_batches} ({len(batch)} nodes)")

            # generate descriptions for all nodes in batch
            descriptions = []
            node_ids = []

            for node in batch:
                node_id = node["node_id"]
                properties = node["properties"]

                description = embedder.generate_description(label, properties)
                descriptions.append(description)
                node_ids.append(node_id)

                if len(descriptions) <= 3:  # show first few examples
                    print(f"  Node {node_id}: {description[:100]}...")

            print(f"  Generating embeddings for {len(descriptions)} descriptions...")
            embeddings = embedder.generate_embeddings_batch(descriptions)

            # store embeddings back to Neo4j
            node_embeddings = list(zip(node_ids, embeddings))
            embedded_count = store_embeddings_batch(node_embeddings)
            total_embedded += embedded_count

            print(f"  ✓ Completed batch {batch_num}/{total_batches}")

    # create vector index
    print(f"\n{'=' * 60}")
    print("Creating vector index...")
    print(f"{'=' * 60}")
    create_vector_index(dimension=embedding_dim)

    # summary
    print(f"\n{'=' * 80}")
    print("EMBEDDING PROCESS COMPLETE")
    print(f"{'=' * 80}")
    print(f"Total nodes processed: {total_nodes}")
    print(f"Total embeddings stored: {total_embedded}")
    print(f"Embedding dimension: {embedding_dim}")
    print(f"{'=' * 80}")


def verify_embeddings():
    """
    Verify that embeddings have been stored correctly.
    """
    print("\n" + "=" * 60)
    print("Verifying Embeddings")
    print("=" * 60)

    # Count nodes with embeddings
    query = """
    MATCH (n)
    WHERE n.embedding IS NOT NULL
    RETURN labels(n)[0] as label, count(n) as count
    ORDER BY count DESC
    """

    result = neo4j_conn.execute_query(query)

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
    WHERE n.embedding IS NOT NULL
    RETURN labels(n)[0] as label, properties(n) as props, size(n.embedding) as embedding_size
    LIMIT 1
    """

    sample = neo4j_conn.execute_query(sample_query)
    if sample:
        record = sample[0]
        print(f"\nSample node:")
        print(f"  Label: {record['label']}")
        print(f"  Embedding size: {record['embedding_size']}")
        print(f"  ✓ Embeddings verified!")


if __name__ == "__main__":
    # Run the embedding process
    embed_all_nodes(50)

    # Verify the results
    verify_embeddings()

    print(
        "\n✨ All done! Your nodes are now embedded and ready for vector similarity search!"
    )
