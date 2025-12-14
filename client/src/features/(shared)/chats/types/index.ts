import { z } from "zod";

import { type SuccessResponseType } from "@/lib/apis";

export type MessageMetadata = Omit<
  SuccessResponseType,
  "error" | "success" | "raw_response"
>;

export type MessageType = {
  id: string;
  content: string;
  createdAt: Date;
  role: "user" | "system";
  metadata?: MessageMetadata;
};

export type ChatType = {
  id: string;
  title: string;
  createdAt: Date;
  messages: MessageType[];
};

export interface ChatsContextType {
  currentChat: ChatType;
  chats: ChatType[];
  ragOptions: RAGOptionsType;
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  showLastMessageDetail: boolean;
  setCurrentChat: React.Dispatch<React.SetStateAction<ChatType>>;
  setChats: React.Dispatch<React.SetStateAction<ChatType[]>>;
  setRAGOptions: React.Dispatch<React.SetStateAction<RAGOptionsType>>;
  setShowLastMessageDetail: React.Dispatch<React.SetStateAction<boolean>>;
  handleCreateNewChat: () => void;
  handleSelectChat: (chatId: string) => void;
  handleDeleteChat: (chatId: string) => void;
  handleSendMessage: (message: string) => void;
}

export const RAGOptionsSchema = z
  .object({
    selection: z
      .array(z.enum(["semantic", "baseline"]))
      .refine((arr) => arr.length > 0, {
        message:
          "At least one method must be selected (semantic or baseline or both)",
      }),
    embeddingModel: z.enum(["SBERT", "MiniLM"]).optional(),
    LLMModel: z.enum(["gpt-5-mini-2025-08-07", "gpt-4.1", "gpt-4o"]),
  })
  .superRefine((data, ctx) => {
    if (data.selection.includes("semantic")) {
      if (!data.embeddingModel) {
        ctx.addIssue({
          path: ["embeddingModel"],
          code: z.ZodIssueCode.custom,
          message: "Embedding model must be selected when embedding is chosen.",
        });
      }
    }
    if (!data.LLMModel) {
      ctx.addIssue({
        path: ["LLMModel"],
        code: z.ZodIssueCode.custom,
        message: "LLM Model must be selected.",
      });
    }
  });

export type RAGOptionsType = z.infer<typeof RAGOptionsSchema>;
