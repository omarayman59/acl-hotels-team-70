from acl_ms_3.shared.comparison_cycle import ComparisonCycle


def main():
    options = {
        "selection": ["semantic", "baseline"],
        "embeddingModel": "MiniLM",
        "LLMModel": "gpt-4.1",
    }

    comparison_cycle = ComparisonCycle("hotels with good cleanliness rating", options)
    results = comparison_cycle.compare_results()
    print(results)


if __name__ == "__main__":
    main()
