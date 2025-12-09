from acl_ms_3.shared.database import Neo4jConnection

if __name__ == "__main__":
    neo4j = Neo4jConnection()

    neo4j.embed_relationships()
    neo4j.embed_nodes()

    neo4j.verify_relationship_embeddings()
    neo4j.verify_node_embeddings()

    print(
        "\n✨ All done! Your nodes and relationships are now embedded and ready for vector similarity search!"
    )

    # Close the connection
    neo4j.close()
