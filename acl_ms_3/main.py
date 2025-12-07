from input_processing import Preprocessor
from queries import find_best_matching_query


def main():
    # Example prompts to test the system
    example_prompts = ["Find me the good hotels in Cairo Egypt"]

    print("=" * 80)
    print("INTENT DETECTION AND QUERY MATCHING EXAMPLES")
    print("=" * 80)

    for prompt in example_prompts:
        print(f"\n📝 User Prompt: '{prompt}'")
        print("-" * 80)

        # Step 1: Preprocess the prompt and detect intents
        preprocessor = Preprocessor(prompt)
        detected_intents = preprocessor.map_intents()
        extracted_parameters = preprocessor.get_query_parameters()

        print(f"🔍 Detected Intents: {detected_intents}")
        print(f"📊 Extracted Parameters: {extracted_parameters}")

        # Step 2: Find the best matching query with parameters inserted
        matched_query = find_best_matching_query(detected_intents, extracted_parameters)

        if matched_query:
            print(f"✅ Matched Query:\n{matched_query}")
        else:
            print("❌ No matching query found for these intents")

        print("-" * 80)


if __name__ == "__main__":
    main()
