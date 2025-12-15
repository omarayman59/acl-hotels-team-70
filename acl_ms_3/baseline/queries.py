from typing import Any, Dict, List, Optional

queries = [
    # Query 1: Hotels by rating and optional location
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) 
        WHERE ($rating_num IS NULL OR hotel.average_reviews_score >= $rating_num) AND ($city IS NULL OR city.city_name IN $city)
         AND ($country IS NULL OR country.country_name IN $country) 
        RETURN hotel, city, country ORDER BY hotel.average_reviews_score DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating"],
            "optional": ["location"],
        },
    },
    # Query 2: Hotels by city and/or country
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN hotel, city, country ORDER BY hotel.average_reviews_score DESC LIMIT $limit_num""",
        "intents": {
            "required": ["location"],
            "optional": [],
        },
    },
    # Query 3: Visa information by country and type
    {
        "query": """MATCH (visa:Visa) 
        WHERE (($country IS NULL OR visa.to_country IN $country) OR ($country IS NULL OR visa.from_country IN $country)) 
         AND ($type IS NULL OR visa.visa_type = $type) 
        RETURN visa LIMIT $limit_num""",
        "intents": {
            "required": ["visa", "location"],
            "optional": [],
        },
    },
    # Query 4: Hotels by traveler demographics
    {
        "query": """MATCH (traveller:Traveller)-[:STAYED_AT]->(hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($age IS NULL OR traveller.age = $age) AND ($gender IS NULL OR traveller.gender = $gender) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN DISTINCT hotel, city, country ORDER BY hotel.average_reviews_score DESC LIMIT $limit_num""",
        "intents": {
            "required": ["demographics"],
            "optional": ["location"],
        },
    },
    # Query 5: Hotels by cleanliness rating
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) 
        WHERE ($num IS NULL OR hotel.cleanliness_base >= $num) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) 
        RETURN hotel, city, country ORDER BY hotel.cleanliness_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "cleanliness"],
            "optional": [
                "location",
            ],
        },
    },
    # Query 6: Hotels by value for money rating
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($num IS NULL OR hotel.value_for_money_base >= $num) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN hotel, city, country ORDER BY hotel.value_for_money_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "value_for_money"],
            "optional": ["location"],
        },
    },
    # Query 7: Hotels by location rating
    {
        "query": """MATCH (hotel:Hotel) WHERE $num IS NULL OR hotel.location_base >= $num RETURN hotel ORDER BY hotel.location_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "location_rating"],
            "optional": [],
        },
    },
    # Query 8: Hotels by comfort rating
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($num IS NULL OR hotel.comfort_base >= $num) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN hotel, city, country ORDER BY hotel.comfort_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "comfort"],
            "optional": ["location"],
        },
    },
    # Query 9: Hotels by facilities rating
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($num IS NULL OR hotel.facilities_base >= $num) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN hotel, city, country ORDER BY hotel.facilities_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "facilities"],
            "optional": ["location"],
        },
    },
    # Query 10: Hotels by staff rating
    {
        "query": """MATCH (hotel:Hotel)-[:LOCATED_IN]->(city:City)-[:LOCATED_IN]->(country:Country) WHERE ($num IS NULL OR hotel.staff_base >= $num) AND ($city IS NULL OR city.city_name IN $city) AND ($country IS NULL OR country.country_name IN $country) RETURN hotel, city, country ORDER BY hotel.staff_base DESC LIMIT $limit_num""",
        "intents": {
            "required": ["rating", "staff"],
            "optional": [
                "location",
            ],
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

        # check if all required intents are present
        if not required_intents.issubset(detected_intents_set):
            continue

        # check if detected_intents contains only intents from required and optional
        if not detected_intents_set.issubset(required_and_optional):
            continue

        # found a matching query, now populate it with parameters
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
        "age": None,
        "gender": None,
        "type": None,
    }

    # merge parameters with defaults
    final_params = {**param_defaults, **parameters}

    # replace each parameter in the query
    for param_name, param_value in final_params.items():
        placeholder = f"${param_name}"
        if placeholder in populated_query:
            if param_value is None:
                # keep as NULL for Cypher query
                populated_query = populated_query.replace(placeholder, "NULL")
            elif isinstance(param_value, list):
                # convert list to Cypher list format: ['item1', 'item2']
                if param_value:
                    quoted_items = [f"'{item}'" for item in param_value]
                    list_str = f"[{', '.join(quoted_items)}]"
                    populated_query = populated_query.replace(placeholder, list_str)
                else:
                    # empty list treated as NULL
                    populated_query = populated_query.replace(placeholder, "NULL")
            elif isinstance(param_value, str):
                # quote string values
                populated_query = populated_query.replace(
                    placeholder, f"'{param_value}'"
                )
            else:
                # numeric values don't need quotes
                populated_query = populated_query.replace(placeholder, str(param_value))

    return populated_query


__all__ = ["queries", "find_best_matching_query"]
