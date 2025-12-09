import csv
import os
from typing import Set


def _load_location_data() -> tuple[Set[str], Set[str]]:
    cities = set()
    countries = set()

    csv_path = os.path.join(os.path.dirname(__file__), "../hotels.csv")

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "city" in row:
                    cities.add(row["city"].lower())
                if "country" in row:
                    countries.add(row["country"].lower())
    except FileNotFoundError:
        print(f"Warning: {csv_path} not found. Location detection may be limited.")

    return cities, countries


CITIES, COUNTRIES = _load_location_data()

__all__ = ["CITIES", "COUNTRIES"]
