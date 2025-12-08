"use client";

import { processQuery, type QueryResponse } from "@/lib/apis";

import { useMutation } from "@tanstack/react-query";
import { useChats } from "../utils/provider";

import { generateId } from "../utils/helpers";

interface UseSendProps {
  chatId: string;
  message: string;
}

export const useSend = () => {
  const { abortControllerRef, setCurrentChat, setChats } = useChats();

  return useMutation({
    mutationFn: ({ chatId: _, message }: UseSendProps) => {
      const controller = new AbortController();
      abortControllerRef.current = controller;
      return processQuery({ prompt: message, signal: controller.signal });
    },

    onMutate: ({ chatId }: UseSendProps) => {
      const tempId = generateId();

      // Add a temporary "thinking" message
      setCurrentChat((prev) => {
        if (prev.id !== chatId) return prev;

        const newChat = {
          ...prev,
          messages: [
            ...prev.messages,
            {
              id: tempId,
              content: "Thinking...",
              createdAt: new Date(),
              role: "system" as const,
            },
          ],
        };

        setChats((prevChats) =>
          prevChats.map((chat) => (chat.id === chatId ? newChat : chat))
        );

        return newChat;
      });

      return { tempId, chatId };
    },

    onSuccess: (data: QueryResponse, _variables, context) => {
      if (!context) return;

      const { tempId, chatId } = context;
      abortControllerRef.current = null;

      // Replace the temporary "thinking" message with the actual response
      setCurrentChat((prev) => {
        if (prev.id !== chatId) return prev;

        const newChat = {
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === tempId
              ? { ...msg, content: data.response, createdAt: new Date() }
              : msg
          ),
        };

        setChats((prevChats) =>
          prevChats.map((chat) => (chat.id === chatId ? newChat : chat))
        );

        return newChat;
      });
    },

    onError: (error: Error, _variables, context) => {
      if (!context) return;

      const { tempId, chatId } = context;
      abortControllerRef.current = null;

      // If the request was aborted, don't show an error message
      if (error.name === "AbortError") {
        return;
      }

      setCurrentChat((prev) => {
        if (prev.id !== chatId) return prev;

        const newChat = {
          ...prev,
          messages: prev.messages.map((msg) =>
            msg.id === tempId
              ? {
                  ...msg,
                  content: `Problem: ${error.message}`,
                  createdAt: new Date(),
                }
              : msg
          ),
        };

        setChats((prevChats) =>
          prevChats.map((chat) => (chat.id === chatId ? newChat : chat))
        );

        return newChat;
      });
    },
  });
};
