import { type MessageType } from "../types";

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
            "prose prose-sm w-fit py-2 px-3 rounded-3xl",
            isUser ? "bg-accent text-accent-foreground ml-auto" : "mr-auto"
          )}
        >
          <p
            className={cn(
              "whitespace-pre-wrap text-sm leading-relaxed",
              content === "Thinking..." ? "animate-pulse" : ""
            )}
          >
            {content}
          </p>
        </div>
      </div>
    </div>
  );
};
