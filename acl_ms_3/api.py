from classes.database import neo4j_conn
from classes.processor import Preprocessor
from flask import Flask, jsonify, request
from flask_cors import CORS
from queries import find_best_matching_query

app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ACL Hotels Query API"}), 200


@app.route("/api/query", methods=["POST"])
def process_query():
    """
    Process a natural language query and return Neo4j results.

    Request body:
    {
        "prompt": "Find me the good hotels in Cairo Egypt"
    }

    Response:
    {
        "success": true,
        "prompt": "...",
        "detected_intents": [...],
        "extracted_parameters": {...},
        "cypher_query": "...",
        "results": [...],
        "result_count": ...
    }
    """
    try:
        # Get prompt from request
        data = request.get_json()

        if not data or "prompt" not in data:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing 'prompt' field in request body",
                    }
                ),
                400,
            )

        prompt = data["prompt"]

        if not prompt or not isinstance(prompt, str):
            return (
                jsonify(
                    {"success": False, "error": "Prompt must be a non-empty string"}
                ),
                400,
            )

        # Step 1: Preprocess the prompt and detect intents
        preprocessor = Preprocessor(prompt)
        detected_intents = preprocessor.map_intents()
        extracted_parameters = preprocessor.get_query_parameters()

        # Step 2: Find the best matching query
        matched_query = find_best_matching_query(detected_intents, extracted_parameters)

        if not matched_query:
            return (
                jsonify(
                    {
                        "success": True,
                        "message": "Question out of scope",
                        "prompt": prompt,
                        "detected_intents": detected_intents,
                        "extracted_parameters": extracted_parameters,
                        "cypher_query": None,
                        "results": [],
                        "result_count": 0,
                    }
                ),
                404,
            )

        # Step 3: Execute the query against Neo4j
        results = neo4j_conn.execute_query(matched_query)

        # Step 4: Return the results
        return (
            jsonify(
                {
                    "success": True,
                    "prompt": prompt,
                    "detected_intents": detected_intents,
                    "extracted_parameters": extracted_parameters,
                    "cypher_query": matched_query,
                    "results": results,
                    "result_count": len(results),
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "error": str(e), "error_type": type(e).__name__}
            ),
            500,
        )


@app.teardown_appcontext
def close_db_connection(exception=None):
    """Close Neo4j connection when app context ends."""
    pass  # Connection is managed globally


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        neo4j_conn.close()
