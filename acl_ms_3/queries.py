from typing import Any, Dict, List, Optional

queries = [
    # Query 1: Hotels by rating and optional location
    {
        "query": """MATCH (h:Hotel)-[:LOCATED_IN]->(c:City)-[:LOCATED_IN]->(co:Country) WHERE ($rating_num IS NULL OR h.average_reviews_score >= $rating_num) AND ($city IS NULL OR c.name IN $city) AND ($country IS NULL OR co.name IN $country) RETURN h ORDER BY h.average_reviews_score DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating"],
            "optional": ["location"],
        },
    },
    # Query 2: Hotels by city and/or country
    {
        "query": """MATCH (h:Hotel)-[:LOCATED_IN]->(c:City)-[:LOCATED_IN]->(co:Country) WHERE ($city IS NULL OR c.name IN $city) AND ($country IS NULL OR co.name IN $country) RETURN h LIMIT $limit_num""",
        "intents": {
            "required": ["location"],
            "optional": [],
        },
    },
    # Query 3: Visa information by country and type
    {
        "query": """MATCH (v:Visa) WHERE ($country IS NULL OR v.to_country IN $country) OR ($country IS NULL OR v.from_country IN $country) AND ($type IS NULL OR v.visa_type = $type) RETURN v LIMIT $limit_num""",
        "intents": {
            "required": ["visa", "location"],
            "optional": ["type"],
        },
    },
    # Query 4: Hotels by traveler demographics
    {
        "query": """MATCH (t:Traveller)-[:STAYED_AT]->(h:Hotel) WHERE ($age_group IS NULL OR t.age_group = $age_group) AND ($gender IS NULL OR t.gender = $gender) RETURN DISTINCT h LIMIT $limit_num""",
        "intents": {
            "required": ["demographics"],
            "optional": [],
        },
    },
    # Query 5: Hotels by cleanliness rating
    {
        "query": """MATCH (h:Hotel) WHERE h.cleanliness_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["cleanliness"],
            "optional": [],
        },
    },
    # Query 6: Hotels by value for money rating
    {
        "query": """MATCH (h:Hotel) WHERE h.value_for_money_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["value_for_money"],
            "optional": [],
        },
    },
    # Query 7: Hotels by location rating
    {
        "query": """MATCH (h:Hotel) WHERE h.location_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["location_rating"],
            "optional": [],
        },
    },
    # Query 8: Hotels by comfort rating
    {
        "query": """MATCH (h:Hotel) WHERE h.comfort_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["comfort"],
            "optional": [],
        },
    },
    # Query 9: Hotels by facilities rating
    {
        "query": """MATCH (h:Hotel) WHERE h.facilities_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["facilities"],
            "optional": [],
        },
    },
    # Query 10: Hotels by staff rating
    {
        "query": """MATCH (h:Hotel) WHERE h.staff_base >= $num RETURN h.name ORDER BY h DESC LIMIT $limit_num""",
        "intents": {
            "required": ["staff"],
            "optional": [],
        },
    },
]


def find_best_matching_query(
    detected_intents: List[str], parameters: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    if parameters is None:
        parameters = {}

    for query_element in queries:
        required_intents = set(query_element["intents"]["required"])
        optional_intents = set(query_element["intents"]["optional"])
        required_and_optional = required_intents.union(optional_intents)
        detected_intents_set = set(detected_intents)

        # Check if all required intents are present
        if not required_intents.issubset(detected_intents_set):
            continue

        # Check if detected_intents contains only intents from required and optional
        if not detected_intents_set.issubset(required_and_optional):
            continue

        # Found a matching query, now populate it with parameters
        query = query_element["query"]
        populated_query = _populate_query_parameters(query, parameters)
        return populated_query

    return None


def _populate_query_parameters(query: str, parameters: Dict[str, Any]) -> str:
    populated_query = query

    param_defaults = {
        "limit_num": 100,
        "rating_num": None,
        "num": None,
        "city": None,
        "country": None,
        "age_group": None,
        "gender": None,
        "type": None,
    }

    # Merge parameters with defaults
    final_params = {**param_defaults, **parameters}

    # Replace each parameter in the query
    for param_name, param_value in final_params.items():
        placeholder = f"${param_name}"
        if placeholder in populated_query:
            if param_value is None:
                # Keep as NULL for Cypher query
                populated_query = populated_query.replace(placeholder, "NULL")
            elif isinstance(param_value, list):
                # Convert list to Cypher list format: ['item1', 'item2']
                if param_value:
                    quoted_items = [f"'{item}'" for item in param_value]
                    list_str = f"[{', '.join(quoted_items)}]"
                    populated_query = populated_query.replace(placeholder, list_str)
                else:
                    # Empty list treated as NULL
                    populated_query = populated_query.replace(placeholder, "NULL")
            elif isinstance(param_value, str):
                # Quote string values
                populated_query = populated_query.replace(
                    placeholder, f"'{param_value}'"
                )
            else:
                # Numeric values don't need quotes
                populated_query = populated_query.replace(placeholder, str(param_value))

    return populated_query


__all__ = ["queries", "find_best_matching_query"]
