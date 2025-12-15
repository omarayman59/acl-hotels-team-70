const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

export type SuccessResponseType = {
  error: null;
  success: true;
  raw_response: string;
  rag_response: {
    semantic_response: any;
    baseline_response: any;
  };
  elapsed_time: number;
  tokens_used: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
};

type ErrorResponseType = {
  error: string;
  success: false;
  raw_response: null;
  rag_response: {
    semantic_response: any;
    baseline_response: any;
  };
};

type ResponseType = SuccessResponseType | ErrorResponseType;

export interface QueryResponse {
  success: boolean;
  response: ResponseType;
}

export interface RAGOptionsType {
  selection: ("semantic" | "baseline")[];
  embeddingModel?: "SBERT" | "MiniLM";
  LLMModel: "gpt-5-mini-2025-08-07" | "gpt-4.1" | "gpt-4o";
}

async function processQuery({
  prompt,
  signal,
  options,
}: {
  prompt: string;
  signal: AbortSignal;
  options?: RAGOptionsType;
}): Promise<QueryResponse> {
  const endpoint = `${API_BASE_URL}/api/query`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: prompt,
      options: {
        selection: options?.selection || ["semantic", "baseline"],
        embeddingModel: options?.embeddingModel || "SBERT",
        LLMModel: options?.LLMModel || "gpt-5-mini-2025-08-07",
      },
    }),
    signal,
  });

  const data: ResponseType = await response.json();

  if (!response.ok && !data.success) {
    throw new Error(data.error || `Query failed: ${response.statusText}`);
  }

  return {
    success: data.success,
    response: data,
  };
}

export { processQuery };
