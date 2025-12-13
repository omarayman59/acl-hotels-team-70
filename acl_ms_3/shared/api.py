import logging
import os
from typing import Any, Dict

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from acl_ms_3.shared.comparison_cycle import ComparisonCycle

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ACL Hotels Query API"}), 200


@app.route("/api/query", methods=["POST"])
def compare_models():
    """
    Expected JSON payload:
    {
        "query": "string",
        "options": {}
    }
    """
    try:

        # Check content type
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400

        data = request.json

        # Validate required fields
        if not data:
            return jsonify({"error": "Request body cannot be empty"}), 400

        if "query" not in data:
            return jsonify({"error": "Missing 'query' field in request"}), 400

        if "options" not in data:
            return jsonify({"error": "Missing 'options' field in request"}), 400

        # Validate field types
        if not isinstance(data["query"], str):
            return jsonify({"error": "'query' must be a string"}), 400

        if not isinstance(data["options"], dict):
            return jsonify({"error": "'options' must be a dictionary"}), 400

        # Validate non-empty query
        if not data["query"].strip():
            return jsonify({"error": "'query' cannot be empty"}), 400

        print(
            "Received data😄😄😄😄:",
            data,
        )

        # Process request
        comparison_cycle = ComparisonCycle(data["query"], data["options"])
        results = comparison_cycle.compare_results()
        return jsonify(results), 200

    except (TypeError, ValueError) as e:
        logger.error(f"Invalid input: {str(e)}")
        return jsonify({"error": "Invalid input", "message": str(e)}), 400

    except Exception as e:
        logger.error(f"Unexpected error in compare_models: {str(e)}", exc_info=True)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "An unexpected error occurred during the comparison process",
                }
            ),
            500,
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting Flask server on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
