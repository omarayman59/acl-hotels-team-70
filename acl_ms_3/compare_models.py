from acl_ms_3.shared.test import (
    SemanticSearchExtension,
    print_baseline_results,
    print_hotel_results,
    print_llm_results,
)


def compare_models_for_query(query: str):
    """
    Compare baseline and semantic search models for a single query.

    Args:
        query: The search query string
    """
    # Initialize connection
    search_conn = SemanticSearchExtension()

    try:
        print(f"\n{'=' * 80}")
        print(f"🔍 QUERY: '{query}'")
        print(f"{'=' * 80}\n")

        # ===== BASELINE MODEL =====
        print("\n" + "🔷" * 40)
        print("BASELINE MODEL (Rule-Based)")
        print("🔷" * 40)

        baseline_results = search_conn.baseline_search(query)
        print_baseline_results(baseline_results)

        baseline_hotels = search_conn.get_hotels_from_baseline_results(baseline_results)
        print_hotel_results(baseline_hotels, model_name="Baseline Model")

        # ===== SEMANTIC SEARCH MODEL =====
        print("\n" + "🔶" * 40)
        print("SEMANTIC SEARCH MODEL (Embedding-Based)")
        print("🔶" * 40)

        semantic_results = search_conn.semantic_search(query, top_k=20)
        semantic_hotels = search_conn.get_hotel_names_from_results(semantic_results)
        print_hotel_results(semantic_hotels, model_name="Semantic Search")

        # ===== COMPARISON =====
        print("\n" + "📊" * 40)
        print("COMPARISON SUMMARY")
        print("📊" * 40)
        print(f"\n✓ Baseline Model: {len(baseline_hotels)} hotels found")
        print(f"✓ Semantic Search: {len(semantic_hotels)} hotels found")

        # Find common hotels
        baseline_names = set(
            h.get("hotel_name") for h in baseline_hotels if h.get("hotel_name")
        )
        semantic_names = set(
            h.get("hotel_name") for h in semantic_hotels if h.get("hotel_name")
        )
        common_hotels = baseline_names.intersection(semantic_names)

        if common_hotels:
            print(f"✓ Common Hotels: {len(common_hotels)}")
            print(
                f"   {', '.join(list(common_hotels)[:5])}"
                + (" ..." if len(common_hotels) > 5 else "")
            )
        else:
            print("✗ No common hotels found")

        # ===== LLM FILTERING =====
        print("\n" + "🤖" * 40)
        print("LLM-POWERED RECOMMENDATION")
        print("🤖" * 40)

        llm_results = search_conn.llm_filter_results(
            query, baseline_results, semantic_results
        )
        print_llm_results(llm_results)

        print("\n" + "=" * 80 + "\n")

        # Return results for programmatic use
        return {
            "query": query,
            "baseline": {
                "intents": baseline_results["detected_intents"],
                "parameters": baseline_results["parameters"],
                "hotels": baseline_hotels,
                "num_results": len(baseline_hotels),
            },
            "semantic": {
                "hotels": semantic_hotels,
                "num_results": len(semantic_hotels),
            },
            "common_hotels": list(common_hotels),
            "llm_filtered": llm_results,
        }

    finally:
        search_conn.close()


def run_multiple_queries():
    """
    Run comparison on multiple example queries.
    """
    queries = [
        "hotels with good cleanliness rating",
    ]

    results = []
    for query in queries:
        result = compare_models_for_query(query)
        results.append(result)

    return results


if __name__ == "__main__":
    # Example 1: Single query
    print("=" * 80)
    print("EXAMPLE 1: Single Query Comparison")
    print("=" * 80)
    compare_models_for_query("hotels with good cleanliness rating in Paris")

    # Example 2: Multiple queries
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Multiple Query Comparison")
    print("=" * 80)
    all_results = run_multiple_queries()

    # Summary statistics
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    for result in all_results:
        print(f"\nQuery: '{result['query']}'")
        print(f"  Baseline: {result['baseline']['num_results']} hotels")
        print(f"  Semantic: {result['semantic']['num_results']} hotels")
        print(f"  Common: {len(result['common_hotels'])} hotels")
