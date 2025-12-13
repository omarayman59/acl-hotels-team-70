from acl_ms_3.shared.comparison_cycle import ComparisonCycle


def main():
    comparison_cycle = ComparisonCycle("hotels with good cleanliness rating")
    results = comparison_cycle.compare_results()
    print(results)


if __name__ == "__main__":
    main()
