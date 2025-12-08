import os

import requests
from classes.database import neo4j_conn
from classes.embeddor import Embeddor
from classes.processor import Preprocessor
from flask import Flask, jsonify, request
from flask_cors import CORS
from queries import find_best_matching_query

app = Flask(__name__)
CORS(app)

# Initialize the embedder globally to avoid reloading the model on each request
embedder = Embeddor()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "ACL Hotels Query API"}), 200


@app.route("/api/baseline ", methods=["POST"])
def baseline_query():
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


@app.route("/api/embed", methods=["POST"])
def embed_query():
    """
    Vectorize user input and find top 30 most similar nodes.

    Request body:
    {
        "prompt": "luxury hotels with good facilities"
    }

    Response:
    {
        "success": true,
        "prompt": "...",
        "embedding_dimension": 768,
        "results": [
            {
                "node_id": ...,
                "labels": [...],
                "properties": {...},
                "similarity_score": 0.95
            },
            ...
        ],
        "result_count": 30
    }
    """
    try:
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

        # Step 1: generate embedding for the user's prompt
        prompt_embeddings = embedder.generate_embeddings_batch([prompt])
        prompt_embedding = prompt_embeddings[0]

        # Convert to list if it's a numpy array
        if hasattr(prompt_embedding, "tolist"):
            prompt_embedding = prompt_embedding.tolist()

        # Step 2: query Neo4j for the top 30 most similar nodes using vector similarity
        # get all available node labels to query all vector indices
        labels_query = "CALL db.labels()"
        labels_result = neo4j_conn.execute_query(labels_query)
        labels = [record["label"] for record in labels_result]

        all_results = []

        with neo4j_conn.driver.session() as session:
            for label in labels:
                index_name = f"node_embeddings_{label}"

                similarity_query = """
                CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
                YIELD node, score
                RETURN 
                    elementId(node) as node_id,
                    labels(node) as labels,
                    properties(node) as properties,
                    score as similarity_score
                """

                try:
                    result = session.run(
                        similarity_query,
                        index_name=index_name,
                        top_k=30,
                        embedding=prompt_embedding,
                    )

                    for record in result:
                        all_results.append(
                            {
                                "node_id": record["node_id"],
                                "labels": record["labels"],
                                "properties": record["properties"],
                                "similarity_score": record["similarity_score"],
                            }
                        )
                except Exception as e:
                    # index might not exist for this label, skip it
                    pass

        results = sorted(
            all_results, key=lambda x: x["similarity_score"], reverse=True
        )[:30]

        return (
            jsonify(
                {
                    "success": True,
                    "prompt": prompt,
                    "embedding_dimension": len(prompt_embedding),
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


@app.route("/api/query", methods=["POST"])
def combined_query():
    """
    Combined endpoint that runs both baseline and embed functionalities,
    then sends the combined results to OpenAI LLM API.

    Request body:
    {
        "prompt": "Find me luxury hotels in Cairo with good facilities"
    }

    Response:
    {
        "success": true,
        "prompt": "...",
        "baseline_results": {...},
        "embed_results": {...},
        "llm_response": "..."
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

        # ===== BASELINE FUNCTIONALITY =====
        baseline_results = {}
        try:
            # Step 1: Preprocess the prompt and detect intents
            preprocessor = Preprocessor(prompt)
            detected_intents = preprocessor.map_intents()
            extracted_parameters = preprocessor.get_query_parameters()

            # Step 2: Find the best matching query
            matched_query = find_best_matching_query(
                detected_intents, extracted_parameters
            )

            if matched_query:
                # Step 3: Execute the query against Neo4j
                results = neo4j_conn.execute_query(matched_query)

                baseline_results = {
                    "success": True,
                    "detected_intents": detected_intents,
                    "extracted_parameters": extracted_parameters,
                    "cypher_query": matched_query,
                    "results": results,
                    "result_count": len(results),
                }
            else:
                baseline_results = {
                    "success": True,
                    "message": "Question out of scope",
                    "detected_intents": detected_intents,
                    "extracted_parameters": extracted_parameters,
                    "cypher_query": None,
                    "results": [],
                    "result_count": 0,
                }
        except Exception as e:
            baseline_results = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        # ===== EMBED FUNCTIONALITY =====
        embed_results = {}
        try:
            # Step 1: Generate embedding for the user's prompt
            prompt_embeddings = embedder.generate_embeddings_batch([prompt])
            prompt_embedding = prompt_embeddings[0]

            # Convert to list if it's a numpy array
            if hasattr(prompt_embedding, "tolist"):
                prompt_embedding = prompt_embedding.tolist()

            # Step 2: Query Neo4j for the top 30 most similar nodes
            labels_query = "CALL db.labels()"
            labels_result = neo4j_conn.execute_query(labels_query)
            labels = [record["label"] for record in labels_result]

            all_results = []

            with neo4j_conn.driver.session() as session:
                for label in labels:
                    index_name = f"node_embeddings_{label}"

                    similarity_query = """
                    CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
                    YIELD node, score
                    RETURN 
                        elementId(node) as node_id,
                        labels(node) as labels,
                        properties(node) as properties,
                        score as similarity_score
                    """

                    try:
                        result = session.run(
                            similarity_query,
                            index_name=index_name,
                            top_k=30,
                            embedding=prompt_embedding,
                        )

                        for record in result:
                            all_results.append(
                                {
                                    "node_id": record["node_id"],
                                    "labels": record["labels"],
                                    "properties": {
                                        k: v
                                        for k, v in record["properties"].items()
                                        if k != "embedding"
                                    },
                                    "similarity_score": record["similarity_score"],
                                }
                            )
                    except Exception:
                        # Index might not exist for this label, skip it
                        pass

            results = sorted(
                all_results, key=lambda x: x["similarity_score"], reverse=True
            )[:30]

            embed_results = {
                "success": True,
                "embedding_dimension": len(prompt_embedding),
                "results": results,
                "result_count": len(results),
            }
        except Exception as e:
            embed_results = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }

        # ===== SEND TO OPENAI LLM =====
        llm_response = None
        llm_error = None

        try:
            # Prepare context from both results
            context_parts = []

            # Add baseline results to context
            if baseline_results.get("success") and baseline_results.get("results"):
                context_parts.append("=== Structured Query Results ===")
                context_parts.append(
                    f"Detected Intents: {baseline_results.get('detected_intents', [])}"
                )
                context_parts.append(
                    f"Extracted Parameters: {baseline_results.get('extracted_parameters', {})}"
                )

                # Filter and limit results to reduce token usage
                for idx, result in enumerate(baseline_results["results"][:30], 1):
                    filtered_result = {}
                    for key, value in result.items():
                        # Skip embedding vectors and other large/irrelevant fields
                        if key == "embedding":
                            continue
                        # Truncate long text fields
                        if isinstance(value, str) and len(value) > 300:
                            filtered_result[key] = value[:300] + "..."
                        else:
                            filtered_result[key] = value
                    context_parts.append(f"Result {idx}: {filtered_result}")

            # Add embed results to context
            if embed_results.get("success") and embed_results.get("results"):
                context_parts.append("\n=== Vector Similarity Results ===")
                for idx, result in enumerate(embed_results["results"][:30], 1):
                    context_parts.append(
                        f"{idx}. {result['labels']} - Similarity: {result['similarity_score']:.4f}"
                    )
                    # Filter properties to exclude embeddings and truncate long text
                    filtered_props = {}
                    for key, value in result["properties"].items():
                        # Skip embedding vectors
                        if key == "embedding":
                            continue
                        # Truncate long text fields
                        if isinstance(value, str) and len(value) > 300:
                            filtered_props[key] = value[:300] + "..."
                        else:
                            filtered_props[key] = value
                    context_parts.append(f"   Properties: {filtered_props}")

            context = "\n".join(context_parts)

            # Safety check: ensure context doesn't exceed token limit
            # Roughly 4 chars = 1 token, so 8000 chars ≈ 2000 tokens (leaving room for system prompt + response)
            max_context_chars = 8000
            if len(context) > max_context_chars:
                context = (
                    context[:max_context_chars]
                    + "\n\n[Context truncated due to length...]"
                )

            # Prepare OpenAI API request
            openai_api_key = os.getenv("OPENAI_API_KEY")

            if openai_api_key:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_api_key}",
                }

                payload = {
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful hotel recommendation assistant. Use only the information provided in the given baseline data and embedded data to answer the user's question accurately, concisely, and naturally. Do NOT use information from anywhere else except the provided baseline and embedded data. Do NOT change, paraphrase, or alter any names or proper nouns appearing in the given baseline or embedded data.",
                        },
                        {
                            "role": "user",
                            "content": f"Context from database:\n{context}\n\nUser question: {prompt}\n\nPlease provide a helpful response based on the above context.",
                        },
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000,
                }

                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30,
                )

                if response.status_code == 200:
                    llm_response = response.json()["choices"][0]["message"]["content"]
                else:
                    llm_error = (
                        f"OpenAI API error: {response.status_code} - {response.text}"
                    )
            else:
                llm_error = "OpenAI API key not configured"

        except Exception as e:
            llm_error = f"Error calling OpenAI API: {str(e)}"

        # Return combined response
        return (
            jsonify(
                {
                    "success": True,
                    "prompt": prompt,
                    "baseline_results": baseline_results,
                    "embed_results": embed_results,
                    "llm_response": llm_response,
                    "llm_error": llm_error,
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
