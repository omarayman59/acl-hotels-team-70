# from acl_ms_3.shared.comparison_cycle import ComparisonCycle


# def main():
#     options = {
#         "selection": ["semantic", "baseline"],
#         "embeddingModel": "SBERT",
#         "LLMModel": "gpt-4.1",
#     }

#     comparison_cycle = ComparisonCycle("hotels with good cleanliness rating", options)
#     results = comparison_cycle.compare_results()
#     print(results)


# if __name__ == "__main__":
#     main()

from acl_ms_3.shared.database import Neo4jConnection


def generate_embeddings_for_nodes_and_relations():
    neo4j_mini_lm = Neo4jConnection(model_name="MiniLM")
    neo4j_mini_lm.embed_nodes()
    neo4j_mini_lm.embed_relationships()
    neo4j_mini_lm.verify_node_embeddings()
    neo4j_mini_lm.verify_relationship_embeddings()
    neo4j_mini_lm.close()

    neo4j_sbert = Neo4jConnection(model_name="SBERT")
    neo4j_sbert.embed_nodes()
    neo4j_sbert.embed_relationships()
    neo4j_sbert.verify_node_embeddings()
    neo4j_sbert.verify_relationship_embeddings()
    neo4j_sbert.close()


if __name__ == "__main__":
    generate_embeddings_for_nodes_and_relations()
