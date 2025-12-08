"use client";

import { useKeyDown } from "@/hooks/use-key-down";
import { useChats } from "@/features/(shared)/chats";

import { SidebarGroup } from "@/components/ui/sidebar";
import { YourChatsSection } from "./YourChatsSection";

export const NavigationMain = () => {
  const { handleCreateNewChat } = useChats();

  useKeyDown({
    keyComboCheck: (e) => e.ctrlKey && e.shiftKey && e.key === "O",
    action: handleCreateNewChat,
  });

  return (
    <SidebarGroup>
      <YourChatsSection />
    </SidebarGroup>
  );
};
