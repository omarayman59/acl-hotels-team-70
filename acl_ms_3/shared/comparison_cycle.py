import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List

from dotenv import load_dotenv

from acl_ms_3.baseline.processor import Preprocessor
from acl_ms_3.baseline.queries import find_best_matching_query
from acl_ms_3.shared.database import Neo4jConnection

load_dotenv()


class ComparisonCycle(Neo4jConnection):
    def __init__(self, prompt: str):
        super().__init__()
        self.baseline_processor = Preprocessor(prompt)
        self.prompt = prompt

    # baseline cycle
    def baseline_cycle(self) -> List[Any]:
        # Step 1: extract feature values and intents using Preprocessor
        detected_intents = self.baseline_processor.map_intents()
        parameters = self.baseline_processor.get_query_parameters()

        # Step 2: find the best matching query from queries.py
        cypher_query = find_best_matching_query(detected_intents, parameters)

        # Step 3: execute the query if found
        results = []
        if cypher_query:
            try:
                # execute the query (it's already populated with parameters)
                results = self.execute_query_with_params(cypher_query)
            except Exception as e:
                print(f"Error executing baseline query: {e}")
                results = []
        else:
            print("No matching query found for the detected intents and parameters")

        return results
        # return {
        #     # "detected_intents": detected_intents,
        #     # "parameters": parameters,
        #     # "cypher_query": cypher_query,
        #     "results": results,
        #     # "num_results": len(results),
        # }

    # semantic cycle
    def _semantic_embed_prompt(self) -> List[float]:
        embeddings = self.embedder.generate_embeddings_batch([self.prompt])
        return embeddings[0] if embeddings else []

    def semantic_cycle(self) -> Dict[str, Any]:
        embedding = self._semantic_embed_prompt()
        closest_nodes = self.get_closest_nodes(embedding)
        closest_relationships = self.get_closest_relationships(embedding)

        sorted_return = closest_nodes + closest_relationships
        sorted_return.sort(key=lambda x: x["score"], reverse=True)
        return sorted_return

    # LLM filtering
    def compare_results(self) -> Dict[str, Any]:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return {
                "error": "OPENAI_API_KEY not found in environment variables",
            }

        results = {
            "baseline": self.baseline_cycle(),
            "semantic": self.semantic_cycle(),
        }

        system_prompt = """You are an intelligent search assistant. Your task is to analyze the results from two different search models (baseline rule-based and semantic search) and provide the most relevant recommendations based ONLY on the given data.

The results may include various entity types such as:
- Hotels (with ratings, scores, location, facilities, etc.)
- Visa information (country requirements, visa types, etc.)
- Cities and Countries (location information)
- Traveler demographics
- And other related entities

CRITICAL RULES:
1. DO NOT use any external knowledge or data
2. DO NOT make assumptions beyond what is provided in the results
3. ONLY recommend entities that appear in the provided results and are asked by the in the query
4. Base your recommendations ONLY on the data fields present in the results
5. Explain your reasoning based on the available data
6. If both models return similar entities, give them higher priority
7. Consider both the semantic similarity scores and the baseline model's query matching
8. Sort and prioritize results based on the user's query intent
9. ONLY RETURN RESULTS YOU ARE SURE OF
10. If a query states that it wants something in a SPECIFIC country make sure that your results are in that country.
11. If results from semantic and baseline are present but they dont respond to what the query states exactly DISREGARD THEM.
12.WHEN A SPECIFIC NUMBER OF RESULTS IS REQUESTED, PRIORITIZE ACCURACY OVER MEETING THE EXACT COUNT. ONLY RETURN RESULTS THAT GENUINELY MATCH THE QUERY CRITERIA. IF FEWER QUALIFYING RESULTS EXIST THAN REQUESTED, RETURN ONLY THOSE THAT QUALIFY RATHER THAN INCLUDING IRRELEVANT RESULTS TO MEET THE NUMBER.
13. IF A RESULT STANDS OUT AND LOOKS LIKE IT IS GOOD BUT IT DOES NOT MEET THE QUERY REQUIREMENTS, DISREGARD IT. DO NOT EXPLAIN WHY YOU DISREGARD IT.
14. IF NO RESULT FITS THE CRITERIAL RETURN NO RESULTS.
Your response should include:
1. Answer the user's query directly and comprehensively
2. Dont put reasons on why you removed anything just answer the query.
3. DO NOT EXPLAIN YOUR REASONING.
4. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
5. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
6. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
7. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
8. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
9. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.
10. DO NOT PUT ANYTHING ELSE IN YOUR RESPONSE.

Format your response as a structured, helpful analysis that directly addresses the user's query."""

        # User prompt with context
        user_prompt = f"""User Prompt: "{self.prompt}"

Available Results:

BASELINE MODEL RESULTS:
- Results: {results['baseline']}

SEMANTIC SEARCH MODEL RESULTS:
- Results: {results['semantic']}

Based ONLY on the above data, provide the user with an appropriate response to their query."""

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": "gpt-5-mini-2025-08-07",
            # "model": "gpt-4.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_completion_tokens": 5000,
        }

        try:
            start_time = time.time()  # start timer

            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            end_time = time.time()  # end timer
            elapsed_time = end_time - start_time

            llm_response = response_data["choices"][0]["message"]["content"]

            return {
                "error": None,
                "raw_response": llm_response,
                # "context_sent": user_prompt,
                "elapsed_time": elapsed_time,
                "tokens_used": {
                    "prompt_tokens": response_data["usage"]["prompt_tokens"],
                    "completion_tokens": response_data["usage"]["completion_tokens"],
                    "total_tokens": response_data["usage"]["total_tokens"],
                },
            }

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            return {
                "error": f"HTTP Error {e.code}: {error_body}",
                "raw_response": None,
                # "context_sent": user_prompt,
            }
        except urllib.error.URLError as e:
            return {
                "error": f"URL Error: {str(e.reason)}",
                "raw_response": None,
                # "context_sent": user_prompt,
            }
        except Exception as e:
            return {
                "error": f"Error calling OpenAI API: {str(e)}",
                "raw_response": None,
                # "context_sent": user_prompt,
            }
