import { type MessageType } from "../types";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";

interface MessageItemProps {
  message: MessageType;
}

export const MessageItem = ({ message }: MessageItemProps) => {
  const isUser = message.role === "user";

  const { content } = message;

  return (
    <div
      className={cn(
        "flex w-full gap-3 px-4 py-6",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <div className="flex-1 max-w-[80%] space-y-1">
        <div
          className={cn(
            "prose prose-sm max-w-none w-fit py-2 px-3 rounded-3xl text-sm leading-relaxed",
            isUser ? "bg-accent text-accent-foreground ml-auto" : "mr-auto",
            content === "Thinking..." ? "animate-pulse" : ""
          )}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              code: ({ className, children, ...props }) => {
                const isInline = !className;
                return isInline ? (
                  <code
                    className="bg-muted px-1 py-0.5 rounded text-xs font-mono"
                    {...props}
                  >
                    {children}
                  </code>
                ) : (
                  <code
                    className="block bg-muted p-2 rounded text-xs font-mono overflow-x-auto"
                    {...props}
                  >
                    {children}
                  </code>
                );
              },
              ul: ({ children }) => (
                <ul className="list-disc list-inside mb-2 last:mb-0">
                  {children}
                </ul>
              ),
              ol: ({ children }) => (
                <ol className="list-decimal list-inside mb-2 last:mb-0">
                  {children}
                </ol>
              ),
              li: ({ children }) => <li className="mb-1">{children}</li>,
              a: ({ children, href }) => (
                <a
                  href={href}
                  className="text-blue-500 hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {children}
                </a>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold">{children}</strong>
              ),
              em: ({ children }) => <em className="italic">{children}</em>,
              h1: ({ children }) => (
                <h1 className="text-xl font-bold mb-2 mt-4 first:mt-0">
                  {children}
                </h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">
                  {children}
                </h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-base font-bold mb-2 mt-2 first:mt-0">
                  {children}
                </h3>
              ),
              blockquote: ({ children }) => (
                <blockquote className="border-l-4 border-gray-300 pl-4 italic my-2">
                  {children}
                </blockquote>
              ),
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};
