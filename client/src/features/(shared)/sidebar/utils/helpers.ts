"use client";

import { useChats } from "@/features/(shared)/chats";

import { SquarePen } from "lucide-react";

import { type NavigationItemType } from "../types";

export function getNavigationItems(): NavigationItemType[] {
  const { handleCreateNewChat } = useChats();

  return [
    {
      id: "new_chat",
      title: "New chat",
      icon: SquarePen,
      action: () => {
        handleCreateNewChat();
      },
    },
  ];
}
