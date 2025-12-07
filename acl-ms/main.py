import pandas as pd
from classes import Neo4jManager


def read_config(config_file):
    """Read configuration from config.txt file"""
    config = {}
    with open(config_file, "r") as file:
        for line in file:
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                config[key] = value
    return config


def data_cleaning():
    df_reviews = pd.read_csv("../reviews.csv")
    df_users = pd.read_csv("../users.csv")
    df_hotels = pd.read_csv("../hotels.csv")
    df_visa = pd.read_csv("../visa.csv")

    traveller_df = df_users[
        ["user_id", "age_group", "traveller_type", "user_gender"]
    ].copy()
    traveller_df = traveller_df.rename(
        columns={"age_group": "age", "traveller_type": "type", "user_gender": "gender"}
    )

    avg_reviews = df_reviews.groupby("hotel_id")["score_overall"].mean().reset_index()
    avg_reviews = avg_reviews.rename(columns={"score_overall": "average_reviews_score"})

    hotel_and_reviews = df_hotels.merge(avg_reviews, on="hotel_id", how="left")

    hotel_df = hotel_and_reviews[
        [
            "hotel_id",
            "hotel_name",
            "star_rating",
            "cleanliness_base",
            "comfort_base",
            "facilities_base",
            "average_reviews_score",
        ]
    ].copy()
    hotel_df = hotel_df.rename(columns={"hotel_name": "name"})

    city_df = df_hotels[["city"]].copy()
    city_df = city_df.rename(columns={"city": "name"})

    hotels_countries = df_hotels[["country"]].drop_duplicates()
    users_countries = df_users[["country"]].drop_duplicates()

    country_df = pd.concat([hotels_countries, users_countries], ignore_index=True)
    country_df = country_df.drop_duplicates().reset_index(drop=True)
    country_df = country_df.rename(columns={"country": "name"})

    review_df = df_reviews[
        [
            "review_id",
            "review_text",
            "review_date",
            "score_overall",
            "score_cleanliness",
            "score_comfort",
            "score_facilities",
            "score_location",
            "score_staff",
            "score_value_for_money",
        ]
    ].copy()

    return (
        traveller_df,
        hotel_df,
        city_df,
        country_df,
        review_df,
    )


def create_wrote_relationship(manager: Neo4jManager):
    df_reviews = pd.read_csv("reviews.csv")

    manager.create_relationships_from_dataframe(
        df=df_reviews,
        from_label="Traveller",
        from_key="user_id",
        from_column="user_id",
        to_label="Review",
        to_key="review_id",
        to_column="review_id",
        relationship_type="WROTE",
    )

    manager.close()


def create_from_country_relationship(manager: Neo4jManager):
    df_users = pd.read_csv("users.csv")
    manager.create_relationships_from_dataframe(
        df=df_users,
        from_label="Traveller",
        from_key="user_id",
        from_column="user_id",
        to_label="Country",
        to_key="name",
        to_column="country",
        relationship_type="FROM_COUNTRY",
    )
    manager.close()


def create_stayed_at_relationship(manager: Neo4jManager):
    df_users = pd.read_csv("users.csv")
    df_hotels = pd.read_csv("hotels.csv")
    df_reviews = pd.read_csv("reviews.csv")
    df_reviews_and_hotels = df_reviews.merge(df_hotels, on="hotel_id", how="left")
    df_users_and_reviews_and_hotels = df_users.merge(
        df_reviews_and_hotels, on="user_id", how="left"
    )

    manager.create_relationships_from_dataframe(
        df=df_users_and_reviews_and_hotels,
        from_label="Traveller",
        from_key="user_id",
        from_column="user_id",
        to_label="Hotel",
        to_key="hotel_id",
        to_column="hotel_id",
        relationship_type="STAYED_AT",
    )
    manager.close()


def create_reviewed_relationship(manager: Neo4jManager):
    df_reviews = pd.read_csv("reviews.csv")

    manager.create_relationships_from_dataframe(
        df=df_reviews,
        from_label="Review",
        from_key="review_id",
        from_column="review_id",
        to_label="Hotel",
        to_key="hotel_id",
        to_column="hotel_id",
        relationship_type="REVIEWED",
    )
    manager.close()


def create_located_in_relationship(manager: Neo4jManager):
    df_hotels = pd.read_csv("hotels.csv")

    manager.create_relationships_from_dataframe(
        df=df_hotels,
        from_label="Hotel",
        from_key="hotel_id",
        from_column="hotel_id",
        to_label="City",
        to_key="name",
        to_column="city",
        relationship_type="LOCATED_IN",
    )
    manager.close()


def create_located_in_city_country_relationship(manager: Neo4jManager):
    df_hotels = pd.read_csv("hotels.csv")

    manager.create_relationships_from_dataframe(
        df=df_hotels,
        from_label="City",
        from_key="name",
        from_column="city",
        to_label="Country",
        to_key="name",
        to_column="country",
        relationship_type="LOCATED_IN",
    )
    manager.close()


def create_needs_visa_relationship(manager: Neo4jManager):
    df_visa = pd.read_csv("visa.csv")

    df_visa_required = df_visa[df_visa["requires_visa"] == "Yes"].copy()

    manager.create_relationships_from_dataframe(
        df=df_visa_required,
        from_label="Country",
        from_key="name",
        from_column="from",
        to_label="Country",
        to_key="name",
        to_column="to",
        relationship_type="NEEDS_VISA",
        property_columns=["visa_type"],
    )
    manager.close()


def main():
    config = read_config("config.txt")

    URI = config.get("URI")
    USERNAME = config.get("USERNAME")
    PASSWORD = config.get("PASSWORD")

    manager = Neo4jManager(URI, USERNAME, PASSWORD)

    try:
        traveller_df, hotel_df, city_df, country_df, review_df = data_cleaning()

        # Create nodes:
        # manager.create_nodes_from_dataframe(traveller_df, "Traveller", "user_id")
        # manager.create_nodes_from_dataframe(hotel_df, "Hotel", "hotel_id")
        # manager.create_nodes_from_dataframe(city_df, "City", "city_id")
        # manager.create_nodes_from_dataframe(country_df, "Country", "country_id")
        # manager.create_nodes_from_dataframe(review_df, "Review", "review_id")

        # Create relationships:
        # create_wrote_relationship(manager)
        # create_from_country_relationship(manager)
        # create_stayed_at_relationship(manager)
        # create_reviewed_relationship(manager)
        # create_located_in_relationship(manager)
        # create_located_in_city_country_relationship(manager)
        # create_needs_visa_relationship(manager)

    finally:
        print("Closed")


if __name__ == "__main__":
    main()
