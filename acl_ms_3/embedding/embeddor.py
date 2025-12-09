from typing import Any, Dict, List

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

node_descriptions = {
    "Traveller": "Traveller is a {age}-year-old {gender} {type} traveller.",
    "Hotel": "Hotel {hotel_name} is a {star_rating}-star hotel with an average review score of {average_reviews_score}. Ratings: cleanliness {cleanliness_base}, comfort {comfort_base}, facilities {facilities_base}, staff {staff_base}, location {location_base}, and value for money {value_for_money_base}.",
    "City": "The city of {city_name} is a travel destination.",
    "Country": "The country of {country_name} is a travel destination.",
    "Review": "Review posted on {review_date} with an overall score of {score_overall}. Scores: cleanliness {score_cleanliness}, comfort {score_comfort}, facilities {score_facilities}, location {score_location}, staff {score_staff}, and value for money {score_value_for_money}. Review text: {review_text}",
    "Visa": "Travellers from {from_country} travelling to {to_country} {requires_visa} a visa. Visa type: {visa_type}.",
}

relationship_descriptions = {
    "FROM_COUNTRY": "Traveller of type {type}, age {age} and gender {gender} is from country {country_name}",
    "STAYED_AT": "Traveller of type {type}, age {age} and gender {gender} stayed at hotel {hotel_name}",
    "WROTE": "Traveller of type {type}, age {age} and gender {gender} reviewed hotel with an overall score of {score_overall}. Scores: cleanliness {score_cleanliness}, comfort {score_comfort}, facilities {score_facilities}, location {score_location}, staff {score_staff}, and value for money {score_value_for_money}. Review text: {review_text}",
    "REVIEWED": "Hotel {hotel_name} ({star_rating}-stars, average rating {average_reviews_score}) was reviewed with an overall score of {score_overall}. Scores: cleanliness {score_cleanliness}, comfort {score_comfort}, facilities {score_facilities}, location {score_location}, staff {score_staff}, and value for money {score_value_for_money}. Review text: {review_text}",
    "LOCATED_IN": "Hotel {hotel_name} ({star_rating}-stars, average rating {average_reviews_score}) is located in city {city_name}",
    "NEEDS_VISA": "Country {from_country} requires visa for country {to_country}. Visa type: {visa_type}.",
}


class Embeddor:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("Muennighoff/SBERT-base-nli-v2")
        self.model = AutoModel.from_pretrained("Muennighoff/SBERT-base-nli-v2")
        self.model.eval()

        # Move to GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print("model loaded successfully✅")

    def generate_node_description(
        self, node_label: str, node_properties: Dict[str, Any]
    ) -> str:
        template = node_descriptions.get(node_label)

        # will never happen, just for clean code
        if template is None:
            props_str = ", ".join([f"{k}: {v}" for k, v in node_properties.items()])
            return f"{node_label} node with properties: {props_str}"

        # format the template with node properties
        return template.format(**node_properties)

    def generate_relationship_description(
        self,
        relationship_type: str,
        relationship_properties: Dict[str, Any] = None,
        start_node_properties: Dict[str, Any] = None,
        end_node_properties: Dict[str, Any] = None,
    ) -> str:
        template = relationship_descriptions.get(relationship_type)

        # will never happen, just for clean code
        if template is None:
            return f"{relationship_type} relationship"

        # Combine all properties for template formatting
        format_data = {}
        if relationship_properties:
            format_data.update(relationship_properties)
        if start_node_properties:
            format_data.update(start_node_properties)
        if end_node_properties:
            format_data.update(end_node_properties)

        # Format the template with available properties
        try:
            return template.format(**format_data)
        except KeyError as e:
            # If some keys are missing, return a partial description
            return f"{relationship_type} relationship with available data"

    # perform mean pooling on token embeddings to get sentence embedding.
    def mean_pooling(self, model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # tokenize all texts
        encoded_input = self.tokenizer(
            texts, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(self.device)

        # generate embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        # perform mean pooling
        sentence_embeddings = self.mean_pooling(
            model_output, encoded_input["attention_mask"]
        )

        # normalize embeddings
        sentence_embeddings = torch.nn.functional.normalize(
            sentence_embeddings, p=2, dim=1
        )

        # convert to list for JSON serialization
        return sentence_embeddings.cpu().tolist()

    def get_embedding_dimension(self) -> int:
        return self.model.config.hidden_size


__all__ = ["Embeddor", "node_descriptions", "relationship_descriptions"]
