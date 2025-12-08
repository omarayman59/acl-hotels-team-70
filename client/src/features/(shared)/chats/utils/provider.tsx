"use client";

import { createContext, useContext, useState } from "react";

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

  function handleCreateNewChat() {
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
      setCurrentChat(selectedChat);
    }
  }

  function handleDeleteChat(chatId: string) {
    setChats((prev) => {
      const filteredChats = prev.filter((chat) => chat.id !== chatId);

      // If we deleted all chats or the current chat, create a new one
      if (filteredChats.length === 0 || chatId === currentChat.id) {
        const newChat = createNewChat();
        setCurrentChat(newChat);
        return [newChat];
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

  return (
    <ChatsContext.Provider
      value={{
        currentChat,
        chats,
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
