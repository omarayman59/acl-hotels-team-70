"use client";

import { createContext, useContext, useRef, useState } from "react";

import { type ChatsContextType, type ChatType } from "../types";

import { generateId, createNewChat } from "./helpers";

const ChatsContext = createContext<ChatsContextType | undefined>(undefined);

const useChats = () => {
  const context = useContext(ChatsContext);

  if (!context) {
    throw new Error("useChats must be used within a ChatsProvider");
  }

  return context;
};

const ChatsProvider = ({ children }: { children: React.ReactNode }) => {
  const initialChat = createNewChat();
  const [currentChat, setCurrentChat] = useState<ChatType>(initialChat);
  const [chats, setChats] = useState<ChatType[]>([initialChat]);
  const abortControllerRef = useRef<AbortController | null>(null);

  function handleCreateNewChat() {
    abortCheck();

    // Clear thinking messages from the chat we're leaving
    handleClearThinkingMessages(currentChat.id);

    const newChat = createNewChat();
    setCurrentChat(newChat);

    setChats((prev) => {
      // Only keep chats that have at least one message (user has interacted)
      const existingChats = prev.filter((chat) => chat.messages.length > 0);
      return [newChat, ...existingChats];
    });
  }

  function handleSelectChat(chatId: string) {
    const selectedChat = chats.find((chat) => chat.id === chatId);
    if (selectedChat) {
      abortCheck();

      // Clear thinking messages from the chat we're leaving
      handleClearThinkingMessages(currentChat.id);
      setCurrentChat(selectedChat);
    }
  }

  function handleDeleteChat(chatId: string) {
    setChats((prev) => {
      const filteredChats = prev.filter((chat) => chat.id !== chatId);

      console.log("chats:", prev);
      console.log("filteredChats", filteredChats);

      // If there are no chats left after deletion, create a new one
      if (filteredChats.length === 0) {
        const newChat = createNewChat();
        setCurrentChat(newChat);
        return [newChat];
      }

      // If the chat being deleted is the current chat, switch to the first remaining chat
      if (chatId === currentChat.id) {
        setCurrentChat(filteredChats[0]);
      }

      return filteredChats;
    });
  }

  function handleSendMessage(message: string) {
    const userMessage = {
      id: generateId(),
      content: message,
      createdAt: new Date(),
      role: "user" as const,
    };

    setCurrentChat((prev) => {
      const newChat = {
        ...prev,
        title:
          prev.messages.length === 0
            ? message.slice(0, 30) + (message.length > 30 ? "..." : "")
            : prev.title,
        messages: [...prev.messages, userMessage],
      };

      // Update the chat in the chats list
      setChats((prevChats) =>
        prevChats.map((chat) => (chat.id === prev.id ? newChat : chat))
      );

      return newChat;
    });
  }

  // static method
  function handleClearThinkingMessages(chatId: string) {
    // Check if the chat has any thinking messages (system messages with "Thinking..." content)
    const chat = chats.find((c) => c.id === chatId);
    if (!chat) return;

    const hasThinkingMessages = chat.messages.some(
      (message) =>
        message.role === "system" && message.content === "Thinking..."
    );

    if (!hasThinkingMessages) return;

    // Update only thinking messages
    const updatedMessages = chat.messages.map((message) =>
      message.role === "system" && message.content === "Thinking..."
        ? { ...message, content: "Problem: Could not process request" }
        : message
    );

    setChats((prevChats) =>
      prevChats.map((c) =>
        c.id === chatId ? { ...c, messages: updatedMessages } : c
      )
    );

    // Update currentChat if this is the current chat
    if (currentChat.id === chatId) {
      setCurrentChat((prev) => ({ ...prev, messages: updatedMessages }));
    }
  }

  // static method
  function abortCheck() {
    // Abort any ongoing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }

  return (
    <ChatsContext.Provider
      value={{
        currentChat,
        chats,
        abortControllerRef,
        setCurrentChat,
        setChats,
        handleCreateNewChat,
        handleSelectChat,
        handleDeleteChat,
        handleSendMessage,
      }}
    >
      {children}
    </ChatsContext.Provider>
  );
};

export { useChats, ChatsProvider };
