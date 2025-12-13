import { ScrollArea } from "@/components/ui/scroll-area";
import { type MessageMetadata } from "../types";

interface ExtraMessageDetailsProps {
  metadata: MessageMetadata | undefined;
}

export const ExtraMessageDetails = ({ metadata }: ExtraMessageDetailsProps) => {
  if (!metadata) return <EmptyMetaData />;

  const { elapsed_time, tokens_used, rag_response } = metadata;

  return (
    <div className="my-4 pb-4 px-4 w-full h-[50vh]">
      <ScrollArea className="h-full">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Performance Metrics */}
          <section className="space-y-3">
            <h3 className="text-sm font-light text-gray-500 tracking-wide">
              Performance
            </h3>
            <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
              <MetricRow
                label="Response time"
                value={`${elapsed_time.toFixed(2)}s`}
              />
              <MetricRow
                label="Total tokens"
                value={tokens_used.total_tokens.toLocaleString()}
              />
              <MetricRow
                label="Prompt tokens"
                value={tokens_used.prompt_tokens.toLocaleString()}
              />
              <MetricRow
                label="Completion tokens"
                value={tokens_used.completion_tokens.toLocaleString()}
              />
            </div>
          </section>

          {/* RAG Response */}
          <section className="space-y-3">
            <h3 className="text-sm font-light text-gray-500 tracking-wide">
              Response Data
            </h3>
            <div className="mb-2 rounded-xl border border-gray-200 overflow-hidden">
              <ResponseBlock
                title="Semantic Response"
                data={rag_response.semantic_response}
              />
              <div className="border-t border-gray-100" />
              <ResponseBlock
                title="Baseline Response"
                data={rag_response.baseline_response}
              />
            </div>
          </section>
        </div>
      </ScrollArea>
    </div>
  );
};

const MetricRow = ({ label, value }: { label: string; value: string }) => {
  return (
    <div className="px-5 py-3.5 flex items-center justify-between">
      <span className="text-sm font-light text-gray-600">{label}</span>
      <span className="text-sm font-normal text-gray-900">{value}</span>
    </div>
  );
};

const ResponseBlock = ({ title, data }: { title: string; data: any }) => {
  const isEmpty =
    !data || (typeof data === "object" && Object.keys(data).length === 0);

  return (
    <div className="p-5">
      <h4 className="text-xs font-light text-gray-500 mb-3 tracking-wide uppercase">
        {title}
      </h4>
      {isEmpty ? (
        <p className="text-sm font-light text-gray-400 italic">
          No data available
        </p>
      ) : (
        <pre className="text-xs font-light text-gray-700 bg-gray-50 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap break-words">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
};

const EmptyMetaData = () => {
  return (
    <div className="mt-6 pb-4 w-full">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <p className="text-sm font-light text-gray-400">
            No metadata available
          </p>
        </div>
      </div>
    </div>
  );
};

// Demo component
export default function Demo() {
  const sampleMetadata: MessageMetadata = {
    rag_response: {
      semantic_response: {
        results: ["Result 1", "Result 2", "Result 3"],
        score: 0.95,
      },
      baseline_response: {
        matches: 42,
        confidence: 0.87,
      },
    },
    elapsed_time: 1.234,
    tokens_used: {
      prompt_tokens: 150,
      completion_tokens: 350,
      total_tokens: 500,
    },
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-2xl font-light text-gray-900 mb-8">
          Message Details
        </h1>

        <div className="space-y-8">
          <div>
            <h2 className="text-sm font-light text-gray-500 mb-4">
              With Metadata
            </h2>
            <ExtraMessageDetails metadata={sampleMetadata} />
          </div>

          <div>
            <h2 className="text-sm font-light text-gray-500 mb-4">
              Empty State
            </h2>
            <ExtraMessageDetails metadata={undefined} />
          </div>
        </div>
      </div>
    </div>
  );
}
