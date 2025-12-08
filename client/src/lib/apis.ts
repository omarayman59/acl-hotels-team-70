const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export interface QueryResponse {
  success: boolean;
  prompt: string;
  detected_intents: string[];
  extracted_parameters: Record<string, any>;
  cypher_query: string;
  results: any[];
  result_count: number;
  error?: string;
  error_type?: string;
}

async function processQuery({
  prompt,
  signal,
}: {
  prompt: string;
  signal: AbortSignal;
}): Promise<QueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt }),
    signal,
  });

  const data = await response.json();

  if (!response.ok && !data.success) {
    throw new Error(data.error || `Query failed: ${response.statusText}`);
  }

  return data;
}

/**
 * Format hotel results for display
 */
function formatHotelResults(results: any[]): string[] {
  return results.map((result) => {
    // Handle different result structures
    if (result["h.name"]) {
      return result["h.name"];
    }
    if (result.h && result.h.name) {
      return result.h.name;
    }
    return JSON.stringify(result);
  });
}

export { processQuery };
