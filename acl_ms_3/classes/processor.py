import re
from typing import Any, Dict, List

import spacy
from data import CITIES, COUNTRIES
from intents import intents

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    import subprocess

    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")


def get_entity_types(text: str) -> Dict[str, str]:
    doc = nlp(text)

    entity_map = {}

    for ent in doc.ents:
        # Map spaCy entity labels to more intuitive names
        entity_type = _map_entity_label(ent.label_)
        entity_map[ent.text] = entity_type

    return entity_map


def _map_entity_label(label: str) -> str:
    label_mapping = {"GPE": "Location", "LOC": "Location"}

    return label_mapping.get(label, label)


class Preprocessor:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.entities = get_entity_types(prompt.lower())
        self.extracted_values = self._extract_values()

    def _extract_values(self) -> Dict[str, Any]:
        """Extract specific values from the prompt for query parameters."""
        values = {}
        prompt_lower = self.prompt.lower()

        values["city"] = []
        values["country"] = []

        # Extract locations (cities and countries)
        for entity_text, entity_type in self.entities.items():
            if entity_type == "Location":
                entity_lower = entity_text.lower()

                # Check if it's a known city or country
                if entity_lower in CITIES:
                    values["city"].append(entity_text.capitalize())
                elif entity_lower in COUNTRIES:
                    values["country"].append(entity_text.capitalize())

        # Extract numbers (for ratings, limits, etc.)
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", self.prompt)
        if numbers:
            values["num"] = float(numbers[0])
            values["rating_num"] = float(numbers[0])

        # Extract quality descriptors and map to ratings
        quality_mapping = {
            "excellent": 9.0,
            "great": 8.5,
            "very good": 8.0,
            "good": 7.0,
            "average": 6.0,
            "poor": 5.0,
        }

        for quality, rating in quality_mapping.items():
            if quality in prompt_lower:
                if "num" not in values:
                    values["num"] = rating
                if "rating_num" not in values:
                    values["rating_num"] = rating
                break

        values["limit_num"] = 100

        limit_match = re.search(r"(?:top|first|show|limit)\s+(\d+)", prompt_lower)
        if limit_match:
            values["limit_num"] = int(limit_match.group(1))

        return values

    def map_intents(self) -> List[str]:
        matched_intents = []
        prompt_lower = self.prompt.lower()

        for intent_name, intent_keywords in intents.items():
            for keyword in intent_keywords:
                if keyword in prompt_lower:
                    if intent_name not in matched_intents:
                        matched_intents.append(intent_name)
                    break  # Move to next intent once we find a match

            if intent_name == "location" and self.entities:
                for entity_type in self.entities.values():
                    if entity_type == "Location":
                        if intent_name not in matched_intents:
                            matched_intents.append(intent_name)
                        break
        return matched_intents

    def get_query_parameters(self) -> Dict[str, Any]:
        return self.extracted_values


__all__ = ["Preprocessor"]
