const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export interface QueryResponse {
  success: boolean;
  response: string;
}

async function processQuery({
  prompt,
  signal,
}: {
  prompt: string;
  signal: AbortSignal;
}): Promise<QueryResponse> {
  // const endpoint = `${API_BASE_URL}/api/embed`;
  // const endpoint = `${API_BASE_URL}/api/embed`;
  const endpoint = `${API_BASE_URL}/api/query`;
  const response = await fetch(endpoint, {
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

  console.log(data);

  return {
    success: data.success,
    response: data?.llm_response ?? "Problem with response",
  };
}

export { processQuery };
