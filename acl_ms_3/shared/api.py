import os

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from acl_ms_3.shared.test import SemanticSearchExtension

app = Flask(__name__)
CORS(app)


def extract_all_entities(baseline_results):
    """
    Extract all entities from baseline search results.

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
                "identifier": hotel.get("hotel_name", "Unknown"),
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
                "identifier": f"{visa.get('from_country')}-{visa.get('to_country')}-{visa.get('visa_type')}",
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
                "identifier": city.get("city_name", "Unknown"),
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
                "identifier": country.get("country_name", "Unknown"),
            }
            entities.append(entity)

    return entities


def extract_semantic_entities(semantic_results):
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

        entity = {
            "type": label.lower(),
            "data": properties,
            "score": score,
            "identifier": get_node_identifier(label, properties),
        }
        entities.append(entity)

    # Extract from relationships (optional, can include if needed)
    for rel in semantic_results.get("relationships", []):
        rel_properties = rel.get("rel_properties", {})
        score = rel.get("score", 0)
        rel_type = rel.get("rel_type", "unknown")
        rel_id = rel.get("rel_id", "unknown")

        # Include start and end node information for context
        start_properties = rel.get("start_properties", {})
        end_properties = rel.get("end_properties", {})
        start_labels = rel.get("start_labels", [])
        end_labels = rel.get("end_labels", [])

        # Combine relationship properties with connected node info
        combined_data = {
            **rel_properties,  # Include any relationship properties
            "from": {
                "label": start_labels[0] if start_labels else "unknown",
                "properties": start_properties,
            },
            "to": {
                "label": end_labels[0] if end_labels else "unknown",
                "properties": end_properties,
            },
        }

        entity = {
            "type": f"relationship_{rel_type.lower()}",
            "data": combined_data,
            "score": score,
            "identifier": f"{rel_type}_{rel_id}",
        }
        entities.append(entity)

    return entities


def get_node_identifier(label, properties):
    """Get a unique identifier for a node based on its label and properties."""
    if label == "Hotel":
        return properties.get("hotel_name", "Unknown")
    elif label == "Visa":
        return f"{properties.get('from_country')}-{properties.get('to_country')}-{properties.get('visa_type')}"
    elif label == "City":
        return properties.get("city_name", "Unknown")
    elif label == "Country":
        return properties.get("country_name", "Unknown")
    elif label == "Traveller":
        return properties.get("traveler_id", "Unknown")
    else:
        return properties.get("name", properties.get("id", "Unknown"))


def get_entity_identifier(entity):
    """Get identifier from an entity dictionary."""
    return entity.get("identifier", "Unknown")


def sort_entities_by_relevance(entities):
    """
    Sort entities by relevance based on their type and properties.

    For hotels: sort by average_reviews_score descending
    For other entities: maintain order or sort alphabetically
    """
    # Separate entities by type
    hotels = [e for e in entities if e.get("type") == "hotel"]
    visas = [e for e in entities if e.get("type") == "visa"]
    other = [e for e in entities if e.get("type") not in ["hotel", "visa"]]

    # Sort hotels by average_reviews_score
    hotels.sort(
        key=lambda x: x.get("data", {}).get("average_reviews_score") or 0, reverse=True
    )

    # Combine: hotels first, then visas, then others
    return hotels + visas + other


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ACL Hotels Query API"}), 200


@app.route("/api/query", methods=["POST"])
def compare_models():
    """
    Compare baseline and semantic search models for a given query.

    Request Body:
        {
            "query": "hotels with good cleanliness rating in Paris"
        }

    Returns:
        JSON object containing:
        - query: the original query
        - baseline: baseline model results (intents, parameters, all entities sorted by relevance)
        - semantic: semantic search results (all entities sorted by similarity score)
        - common_entities: entities found by both models
        - llm_filtered: LLM-powered recommendations
    """
    try:
        # Get query from request body
        data = request.get_json()

        if not data or "query" not in data:
            return jsonify({"error": "Missing 'query' parameter in request body"}), 400

        query = data["query"]

        if not query or not query.strip():
            return jsonify({"error": "Query cannot be empty"}), 400

        # Initialize connection
        search_conn = SemanticSearchExtension()

        try:
            # ===== BASELINE MODEL =====
            baseline_results = search_conn.baseline_search(query)

            # Extract all entities from baseline results
            baseline_entities = extract_all_entities(baseline_results)

            # Sort baseline entities by relevance/score
            sorted_baseline = sort_entities_by_relevance(baseline_entities)

            # ===== SEMANTIC SEARCH MODEL =====
            semantic_results = search_conn.semantic_search(query, top_k=20)

            # Extract all entities from semantic results
            semantic_entities = extract_semantic_entities(semantic_results)

            # Already sorted by score, but let's ensure consistency
            sorted_semantic = sorted(
                semantic_entities, key=lambda x: x.get("score", 0), reverse=True
            )

            # ===== FIND COMMON ENTITIES =====
            baseline_identifiers = set(
                get_entity_identifier(e)
                for e in baseline_entities
                if get_entity_identifier(e)
            )
            semantic_identifiers = set(
                get_entity_identifier(e)
                for e in semantic_entities
                if get_entity_identifier(e)
            )
            common_entities = baseline_identifiers.intersection(semantic_identifiers)

            # ===== LLM FILTERING =====
            llm_results = search_conn.llm_filter_results(
                query, baseline_results, semantic_results
            )

            # Prepare response

            response = {
                "query": query,
                "baseline": {
                    "intents": baseline_results["detected_intents"],
                    "parameters": baseline_results["parameters"],
                    "results": sorted_baseline,
                    "num_results": len(sorted_baseline),
                    "cypher_query": baseline_results["cypher_query"],
                },
                "semantic": {
                    "results": sorted_semantic,
                    "num_results": len(sorted_semantic),
                },
                "common_entities": list(common_entities),
                "llm_filtered": llm_results,
            }
            print("response😂😂😂😂😂😂: ", response)

            return jsonify(response), 200

        finally:
            search_conn.close()

    except Exception as e:
        return (
            jsonify(
                {
                    "error": str(e),
                    "message": "An error occurred while processing your query",
                }
            ),
            500,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
