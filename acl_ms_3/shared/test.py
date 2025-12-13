import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List

from dotenv import load_dotenv

from acl_ms_3.baseline.processor import Preprocessor
from acl_ms_3.baseline.queries import find_best_matching_query
from acl_ms_3.shared.comparison_cycle import ComparisonCycle
from acl_ms_3.shared.database import Neo4jConnection

load_dotenv()


class SemanticSearchExtension(Neo4jConnection):
    """
    Extends Neo4jConnection with semantic search capabilities.
    """

    def execute_query_with_params(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Neo4j query with parameters.

        Args:
            query: The Cypher query string
            parameters: Dictionary of parameters for the query

        Returns:
            List of result records as dictionaries
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            records = []
            for record in result:
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    if hasattr(value, "__dict__"):
                        record_dict[key] = dict(value)
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            return records

    def semantic_search(
        self, query_text: str, top_k: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform semantic search across all embedded nodes and relationships.

        Args:
            query_text: The search query string
            top_k: Number of top results to return per category

        Returns:
            Dictionary with 'nodes' and 'relationships' keys containing search results
        """

        # Step 1: Embed the query string
        query_embedding = self.embedder.generate_embeddings_batch([query_text])[0]

        # Step 2: Search nodes
        node_results = self._search_nodes(query_embedding, top_k)

        # Step 3: Search relationships
        relationship_results = self._search_relationships(query_embedding, top_k)

        return {"nodes": node_results, "relationships": relationship_results}

    def _search_nodes(
        self, query_embedding: List[float], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search across all node types using vector similarity.

        Args:
            query_embedding: The embedded query vector
            top_k: Number of top results to return

        Returns:
            List of matching nodes with similarity scores (embeddings excluded)
        """
        all_results = []
        labels = self.get_all_node_labels()

        for label in labels:
            if label == "RelationshipType":  # Skip metadata nodes
                continue

            index_name = f"node_embeddings_{label}"

            query = """
            CALL db.index.vector.queryNodes($index_name, $top_k, $query_embedding)
            YIELD node, score
            RETURN 
                elementId(node) as node_id,
                labels(node) as labels,
                properties(node) as properties,
                score
            ORDER BY score DESC
            """

            try:
                results = self.execute_query_with_params(
                    query,
                    {
                        "index_name": index_name,
                        "top_k": top_k,
                        "query_embedding": query_embedding,
                    },
                )
                # Add label type for context and remove embedding from properties
                for result in results:
                    result["label"] = label
                    # Remove embedding field from properties
                    if "properties" in result and isinstance(
                        result["properties"], dict
                    ):
                        result["properties"].pop("embedding", None)
                all_results.extend(results)
            except Exception as e:
                print(f"  ✗ Error searching nodes with label '{label}': {e}")

        # Sort all results by score and return top_k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]

    def _search_relationships(
        self, query_embedding: List[float], top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Search across all relationship types using vector similarity.

        Args:
            query_embedding: The embedded query vector
            top_k: Number of top results to return

        Returns:
            List of matching relationships with similarity scores (embeddings excluded)
        """
        all_results = []
        rel_types = self.get_all_relationship_types()

        for rel_type in rel_types:
            index_name = f"rel_embeddings_{rel_type}"

            query = """
            CALL db.index.vector.queryRelationships($index_name, $top_k, $query_embedding)
            YIELD relationship, score
            WITH relationship, score
            MATCH (start)-[relationship]->(end)
            RETURN 
                elementId(relationship) as rel_id,
                type(relationship) as rel_type,
                properties(relationship) as rel_properties,
                labels(start) as start_labels,
                properties(start) as start_properties,
                labels(end) as end_labels,
                properties(end) as end_properties,
                score
            ORDER BY score DESC
            """

            try:
                results = self.execute_query_with_params(
                    query,
                    {
                        "index_name": index_name,
                        "top_k": top_k,
                        "query_embedding": query_embedding,
                    },
                )
                # Remove embedding fields from all properties
                for result in results:
                    if "rel_properties" in result and isinstance(
                        result["rel_properties"], dict
                    ):
                        result["rel_properties"].pop("embedding", None)
                    if "start_properties" in result and isinstance(
                        result["start_properties"], dict
                    ):
                        result["start_properties"].pop("embedding", None)
                    if "end_properties" in result and isinstance(
                        result["end_properties"], dict
                    ):
                        result["end_properties"].pop("embedding", None)

                all_results.extend(results)
            except Exception as e:
                print(f"  ✗ Error searching relationships of type '{rel_type}': {e}")

        # Sort all results by score and return top_k
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k]

    def get_hotel_names_from_results(
        self, results: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        """
        Extract hotel names and all properties from search results.

        Args:
            results: Dictionary containing 'nodes' and 'relationships' search results

        Returns:
            List of dictionaries with all hotel properties and similarity_score
        """
        hotels = []

        # Extract from node results
        for node in results.get("nodes", []):
            if node.get("label") == "Hotel":
                # Get all properties from the node
                hotel_info = dict(node["properties"])
                # Add similarity score
                hotel_info["similarity_score"] = node["score"]
                hotels.append(hotel_info)

        # Extract from relationship results (hotels connected to matched entities)
        for rel in results.get("relationships", []):
            # Check if start node is a Hotel
            if rel.get("start_labels") and "Hotel" in rel["start_labels"]:
                # Get all properties from the start node
                hotel_info = dict(rel["start_properties"])
                # Add similarity score and match type
                hotel_info["similarity_score"] = rel["score"]
                hotel_info["match_type"] = f"via {rel['rel_type']}"
                hotels.append(hotel_info)

            # Check if end node is a Hotel
            if rel.get("end_labels") and "Hotel" in rel["end_labels"]:
                # Get all properties from the end node
                hotel_info = dict(rel["end_properties"])
                # Add similarity score and match type
                hotel_info["similarity_score"] = rel["score"]
                hotel_info["match_type"] = f"via {rel['rel_type']}"
                hotels.append(hotel_info)

        # Remove duplicates based on hotel_id and keep highest score
        unique_hotels = {}
        for hotel in hotels:
            hotel_id = hotel.get("hotel_id")
            if hotel_id:
                if (
                    hotel_id not in unique_hotels
                    or hotel["similarity_score"]
                    > unique_hotels[hotel_id]["similarity_score"]
                ):
                    unique_hotels[hotel_id] = hotel

        # Sort by similarity score
        sorted_hotels = sorted(
            unique_hotels.values(), key=lambda x: x["similarity_score"], reverse=True
        )

        return sorted_hotels

    def baseline_search(self, query_text: str) -> Dict[str, Any]:
        """
        Perform baseline model search using rule-based intent detection and Cypher queries.

        Args:
            query_text: The search query string

        Returns:
            Dictionary with baseline search results including intents, parameters, query, and results
        """
        # Step 1: Preprocess the query to extract intents and parameters
        preprocessor = Preprocessor(query_text)
        detected_intents = preprocessor.map_intents()
        parameters = preprocessor.get_query_parameters()

        # Step 2: Find the best matching query
        cypher_query = find_best_matching_query(detected_intents, parameters)

        # Step 3: Execute the query if found
        results = []
        if cypher_query:
            try:
                results = self.execute_query_with_params(cypher_query, parameters)
            except Exception as e:
                print(f"  ✗ Error executing baseline query: {e}")

        return {
            "detected_intents": detected_intents,
            "parameters": parameters,
            "cypher_query": cypher_query,
            "results": results,
            "num_results": len(results),
        }

    def get_hotels_from_baseline_results(
        self, baseline_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract hotel information from baseline search results.

        Args:
            baseline_results: Dictionary containing baseline search results

        Returns:
            List of hotel dictionaries
        """
        hotels = []

        for result in baseline_results.get("results", []):
            # Check if result contains a hotel node
            if "h" in result and isinstance(result["h"], dict):
                hotel = result["h"]
                hotel_info = {
                    "hotel_name": hotel.get("hotel_name", "Unknown"),
                    "hotel_id": hotel.get("hotel_id"),
                    "star_rating": hotel.get("star_rating"),
                    "average_reviews_score": hotel.get("average_reviews_score"),
                    "cleanliness_base": hotel.get("cleanliness_base"),
                    "comfort_base": hotel.get("comfort_base"),
                    "facilities_base": hotel.get("facilities_base"),
                    "staff_base": hotel.get("staff_base"),
                    "value_for_money_base": hotel.get("value_for_money_base"),
                    "location_base": hotel.get("location_base"),
                }
                hotels.append(hotel_info)
            # Check if result contains a visa node
            elif "v" in result and isinstance(result["v"], dict):
                # For visa queries, we don't return hotels
                pass

        # Remove duplicates based on hotel_id
        unique_hotels = {}
        for hotel in hotels:
            hotel_id = hotel.get("hotel_id")
            if hotel_id and hotel_id not in unique_hotels:
                unique_hotels[hotel_id] = hotel

        return list(unique_hotels.values())

    def get_all_entities_from_baseline_results(
        self, baseline_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract all entity types from baseline search results.

        Args:
            baseline_results: Dictionary containing baseline search results

        Returns:
            List of entity dictionaries with type information
        """
        entities = []

        for result in baseline_results.get("results", []):
            # Check for Hotel nodes
            if "h" in result and isinstance(result["h"], dict):
                hotel = result["h"]
                entity = {
                    "type": "hotel",
                    "data": {
                        "hotel_name": hotel.get("hotel_name", "Unknown"),
                        "hotel_id": hotel.get("hotel_id"),
                        "star_rating": hotel.get("star_rating"),
                        "average_reviews_score": hotel.get("average_reviews_score"),
                        "cleanliness_base": hotel.get("cleanliness_base"),
                        "comfort_base": hotel.get("comfort_base"),
                        "facilities_base": hotel.get("facilities_base"),
                        "location_base": hotel.get("location_base"),
                        "staff_base": hotel.get("staff_base"),
                        "value_for_money_base": hotel.get("value_for_money_base"),
                        "hotel_link": hotel.get("hotel_link"),
                    },
                }
                entities.append(entity)

            # Check for Visa nodes
            elif "v" in result and isinstance(result["v"], dict):
                visa = result["v"]
                entity = {
                    "type": "visa",
                    "data": {
                        "from_country": visa.get("from_country"),
                        "to_country": visa.get("to_country"),
                        "visa_type": visa.get("visa_type"),
                        "visa_info": visa.get("visa_info"),
                    },
                }
                entities.append(entity)

            # Check for City nodes
            elif "c" in result and isinstance(result["c"], dict):
                city = result["c"]
                entity = {
                    "type": "city",
                    "data": {
                        "city_name": city.get("city_name"),
                        "city_id": city.get("city_id"),
                    },
                }
                entities.append(entity)

            # Check for Country nodes
            elif "co" in result and isinstance(result["co"], dict):
                country = result["co"]
                entity = {
                    "type": "country",
                    "data": {
                        "country_name": country.get("country_name"),
                        "country_id": country.get("country_id"),
                    },
                }
                entities.append(entity)

            # Check for Traveller nodes
            elif "t" in result and isinstance(result["t"], dict):
                traveller = result["t"]
                entity = {
                    "type": "traveller",
                    "data": {
                        "traveler_id": traveller.get("traveler_id"),
                        "age_group": traveller.get("age_group"),
                        "gender": traveller.get("gender"),
                    },
                }
                entities.append(entity)

        return entities

    def get_all_entities_from_semantic_results(
        self, semantic_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Extract all entities from semantic search results.

        Args:
            semantic_results: Dictionary containing node and relationship results

        Returns:
            List of entity dictionaries with type and score information
        """
        entities = []

        # Extract from nodes
        for node in semantic_results.get("nodes", []):
            label = node.get("label", "unknown")
            properties = node.get("properties", {})
            score = node.get("score", 0)

            # Remove embedding from properties if present
            if "embedding" in properties:
                properties = {k: v for k, v in properties.items() if k != "embedding"}

            entity = {
                "type": label.lower(),
                "data": properties,
                "score": score,
            }
            entities.append(entity)

        return entities

    def llm_filter_results(
        self,
        user_query: str,
        baseline_results: Dict[str, Any],
        semantic_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Use LLM to filter and rank the most relevant results from both models.
        Uses direct HTTP requests instead of OpenAI library.

        Args:
            user_query: The original user query
            baseline_results: Results from baseline model
            semantic_results: Results from semantic search model

        Returns:
            Dictionary with LLM response and filtered results
        """
        # Get API key from environment variable or config file
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return {
                "error": "OPENAI_API_KEY not found in environment variables",
                "raw_response": None,
                "filtered_results": [],
            }

        # Prepare the data for the LLM - extract all entity types
        baseline_entities = self.get_all_entities_from_baseline_results(
            baseline_results
        )
        semantic_entities = self.get_all_entities_from_semantic_results(
            semantic_results
        )

        # Group entities by type for better presentation
        baseline_by_type = {}
        for entity in baseline_entities:
            entity_type = entity["type"]
            if entity_type not in baseline_by_type:
                baseline_by_type[entity_type] = []
            baseline_by_type[entity_type].append(entity["data"])

        semantic_by_type = {}
        for entity in semantic_entities:
            entity_type = entity["type"]
            if entity_type not in semantic_by_type:
                semantic_by_type[entity_type] = []
            semantic_by_type[entity_type].append(
                {"data": entity["data"], "score": entity["score"]}
            )

        # Create a comprehensive context with all results
        context = {
            "baseline_model": {
                "detected_intents": baseline_results["detected_intents"],
                "parameters": baseline_results["parameters"],
                "entities": baseline_by_type,
                "num_results": len(baseline_entities),
            },
            # "baseline_model": {
            #     "detected_intents": [],
            #     "parameters": [],
            #     "entities": [],
            #     "num_results": 0,
            # },
            "semantic_search_model": {
                "entities": semantic_by_type,
                "num_results": len(semantic_entities),
            },
        }

        # System prompt - updated to handle any entity type
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
        user_prompt = f"""User Query: "{user_query}"

Available Results:

BASELINE MODEL RESULTS:
- Detected Intents: {', '.join(context['baseline_model']['detected_intents']) if context['baseline_model']['detected_intents'] else 'None'}
- Extracted Parameters: {json.dumps(context['baseline_model']['parameters'], indent=2)}
- Number of Results Found: {context['baseline_model']['num_results']}
- Results by Type: {json.dumps(context['baseline_model']['entities'], indent=2, default=str)}

SEMANTIC SEARCH MODEL RESULTS:
- Number of Results Found: {context['semantic_search_model']['num_results']}
- Results by Type (with similarity scores): {json.dumps(context['semantic_search_model']['entities'], indent=2, default=str)}

Based ONLY on the above data, provide the user with an appropriate response to their query."""

        # Prepare the API request
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            # "model": "gpt-5-mini-2025-08-07",
            "model": "gpt-4.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            # "temperature": 0.3,
            "max_completion_tokens": 5000,
        }

        print(
            "💓💓💓💓💓💓💓", json.dumps(context["semantic_search_model"]["entities"])
        )

        try:
            # Create the request
            request = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            # Make the API call
            with urllib.request.urlopen(request) as response:
                response_data = json.loads(response.read().decode("utf-8"))

            llm_response = response_data["choices"][0]["message"]["content"]

            return {
                "error": None,
                "raw_response": llm_response,
                "context_sent": context,
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
                "context_sent": context,
            }
        except urllib.error.URLError as e:
            return {
                "error": f"URL Error: {str(e.reason)}",
                "raw_response": None,
                "context_sent": context,
            }
        except Exception as e:
            return {
                "error": f"Error calling OpenAI API: {str(e)}",
                "raw_response": None,
                "context_sent": context,
            }


def print_search_results(results: Dict[str, List[Dict[str, Any]]]):
    """
    Pretty print semantic search results.

    Args:
        results: Dictionary containing 'nodes' and 'relationships' search results
    """
    # Print node results
    print(f"\n📍 TOP NODE MATCHES:")
    print("-" * 80)
    for i, node in enumerate(results["nodes"], 1):
        print(f"\n{i}. {node['label']} (Similarity Score: {node['score']:.4f})")
        print(f"   Node ID: {node['node_id']}")
        print(f"   Properties:")
        for key, value in node["properties"].items():
            # Truncate long text fields
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"     - {key}: {value}")

    # Print relationship results
    print(f"\n\n🔗 TOP RELATIONSHIP MATCHES:")
    print("-" * 80)
    for i, rel in enumerate(results["relationships"], 1):
        print(f"\n{i}. {rel['rel_type']} (Similarity Score: {rel['score']:.4f})")
        print(f"   Relationship ID: {rel['rel_id']}")
        print(
            f"   Connection: {rel['start_labels'][0] if rel['start_labels'] else 'Unknown'} -> {rel['end_labels'][0] if rel['end_labels'] else 'Unknown'}"
        )

        if rel["rel_properties"]:
            print(f"   Relationship Properties:")
            for key, value in rel["rel_properties"].items():
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
                print(f"     - {key}: {value}")

        print(f"   Start Node Properties (sample):")
        for key, value in list(rel["start_properties"].items()):
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"     - {key}: {value}")

        print(f"   End Node Properties (sample):")
        for key, value in list(rel["end_properties"].items()):
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print(f"     - {key}: {value}")

    print(f"\n{'=' * 80}\n")


def print_hotel_results(
    hotels: List[Dict[str, Any]], model_name: str = "Semantic Search"
):
    """
    Print hotel names and all available properties in a clean format.

    Args:
        hotels: List of hotel dictionaries with names and scores
        model_name: Name of the model (for display purposes)
    """
    print(f"\n🏨 TOP HOTELS ({model_name}):")
    print("=" * 80)

    if not hotels:
        print("No hotels found in search results.")
        return

    for i, hotel in enumerate(hotels, 1):
        print(f"\n{i}. {hotel.get('hotel_name', 'Unknown')}")

        # Print similarity score if available (semantic search)
        if hotel.get("similarity_score"):
            print(f"   Similarity Score: {hotel['similarity_score']:.4f}")

        # Print match type if available
        if hotel.get("match_type"):
            print(f"   Matched: {hotel['match_type']}")

        # Print basic hotel info
        if hotel.get("hotel_id"):
            print(f"   Hotel ID: {hotel['hotel_id']}")
        if hotel.get("star_rating"):
            print(f"   Star Rating: {hotel['star_rating']}")
        if hotel.get("average_reviews_score"):
            print(f"   Average Review Score: {hotel['average_reviews_score']:.2f}")

        # Print detailed ratings
        rating_fields = [
            ("cleanliness_base", "Cleanliness"),
            ("comfort_base", "Comfort"),
            ("facilities_base", "Facilities"),
            ("staff_base", "Staff"),
            ("value_for_money_base", "Value for Money"),
            ("location_base", "Location"),
        ]

        for field, label in rating_fields:
            if hotel.get(field) is not None:
                print(f"   {label}: {hotel[field]:.2f}")

        # Print location information
        if hotel.get("city"):
            print(f"   City: {hotel['city']}")
        if hotel.get("country"):
            print(f"   Country: {hotel['country']}")

        # Print other available properties (excluding already printed ones and embedding)
        printed_keys = {
            "hotel_name",
            "similarity_score",
            "match_type",
            "hotel_id",
            "star_rating",
            "average_reviews_score",
            "cleanliness_base",
            "comfort_base",
            "facilities_base",
            "staff_base",
            "value_for_money_base",
            "location_base",
            "city",
            "country",
            "embedding",  # Skip embedding vector
        }

        other_properties = {
            k: v for k, v in hotel.items() if k not in printed_keys and v is not None
        }
        if other_properties:
            print(f"   Other Properties:")
            for key, value in other_properties.items():
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"     - {key}: {value}")

    print(f"\n{'=' * 80}\n")


def print_baseline_results(baseline_results: Dict[str, Any]):
    """
    Print baseline model results including intents, parameters, and query.

    Args:
        baseline_results: Dictionary containing baseline search results
    """
    print(f"\n📊 BASELINE MODEL RESULTS:")
    print("=" * 80)
    print(
        f"\n🎯 Detected Intents: {', '.join(baseline_results['detected_intents']) if baseline_results['detected_intents'] else 'None'}"
    )
    print(f"\n📋 Extracted Parameters:")
    for key, value in baseline_results["parameters"].items():
        if value not in [None, [], ""]:
            print(f"   - {key}: {value}")

    print(f"\n💬 Generated Cypher Query:")
    if baseline_results["cypher_query"]:
        print(
            f"   {baseline_results['cypher_query'][:200]}..."
            if len(baseline_results["cypher_query"]) > 200
            else f"   {baseline_results['cypher_query']}"
        )
    else:
        print("   No matching query found for the detected intents.")

    print(f"\n📦 Number of Results: {baseline_results['num_results']}")
    print(f"\n{'=' * 80}\n")


def print_llm_results(llm_results: Dict[str, Any]):
    """
    Print LLM-filtered results in a clean format.

    Args:
        llm_results: Dictionary containing LLM response and metadata
    """
    print(f"\n🤖 LLM RECOMMENDATIONS:")
    print("=" * 80)

    if llm_results.get("error"):
        print(f"\n❌ Error: {llm_results['error']}")
        return

    if llm_results.get("raw_response"):
        print(f"\n{llm_results['raw_response']}")

    if llm_results.get("tokens_used"):
        print(f"\n📊 Token Usage:")
        print(f"   Prompt: {llm_results['tokens_used']['prompt_tokens']}")
        print(f"   Completion: {llm_results['tokens_used']['completion_tokens']}")
        print(f"   Total: {llm_results['tokens_used']['total_tokens']}")

    print(f"\n{'=' * 80}\n")


def main():
    """
    Run both baseline and semantic search models and compare results.
    """
    # Initialize connection with semantic search capabilities
    search_conn = SemanticSearchExtension()

    try:
        # Example queries
        queries = [
            "hotels with good cleanliness rating",
        ]

        # Run searches
        for query in queries:
            print(f"\n{'=' * 80}")
            print(f"🔍 QUERY: '{query}'")
            print(f"{'=' * 80}\n")

            # ===== BASELINE MODEL =====
            print("\n" + "🔷" * 40)
            print("BASELINE MODEL (Rule-Based)")
            print("🔷" * 40)

            baseline_results = search_conn.baseline_search(query)
            print_baseline_results(baseline_results)

            baseline_hotels = search_conn.get_hotels_from_baseline_results(
                baseline_results
            )
            print_hotel_results(baseline_hotels, model_name="Baseline Model")

            # ===== SEMANTIC SEARCH MODEL =====
            print("\n" + "🔶" * 40)
            print("SEMANTIC SEARCH MODEL (Embedding-Based)")
            print("🔶" * 40)

            semantic_results = search_conn.semantic_search(query, top_k=10)
            # Optionally print full results (commented out to reduce output)
            # print_search_results(semantic_results)

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

            # Add a separator between different queries
            print("\n" + "=" * 80)
            print("=" * 80 + "\n")

    finally:
        # Close connection
        search_conn.close()
        print("✓ Connection closed")


def testFn():
    comparison_cycle = ComparisonCycle("hotels with good cleanliness rating")
    results = comparison_cycle.compare_results()
    print(results)


if __name__ == "__main__":
    # main()
    testFn()
