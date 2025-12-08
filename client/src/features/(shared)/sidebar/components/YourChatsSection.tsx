"use client";

import { useState } from "react";
import { useChats } from "@/features/(shared)/chats";

import {
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { ChevronDown, ChevronRight, Ellipsis, Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";

export const YourChatsSection = () => {
  const { state } = useSidebar();
  const isExpanded = state === "expanded";

  const { chats, currentChat, handleSelectChat } = useChats();
  const [open, setOpen] = useState<boolean>(true);

  if (!isExpanded) return null;

  return (
    <>
      <SidebarGroupLabel
        className="group gap-1"
        onClick={() => setOpen((prev) => !prev)}
      >
        <span>Your Chats</span>
        {open ? (
          <ChevronDown className="size-3! hidden group-hover:block" />
        ) : (
          <ChevronRight className="size-3! hidden group-hover:block" />
        )}
      </SidebarGroupLabel>
      <SidebarMenu>
        {open &&
          chats.map((chat) => (
            <SidebarMenuItem key={chat.id} className="group/item">
              <div className="relative w-full">
                <SidebarMenuButton
                  tooltip={chat.title}
                  onClick={() => handleSelectChat(chat.id)}
                  className="w-full"
                  isActive={chat.id === currentChat.id}
                >
                  <span>{chat.title}</span>
                </SidebarMenuButton>
                <div className="absolute right-2 top-1/2 -translate-y-1/2">
                  <ChatActions chatId={chat.id} />
                </div>
              </div>
            </SidebarMenuItem>
          ))}
      </SidebarMenu>
    </>
  );
};

const ChatActions = ({ chatId }: { chatId: string }) => {
  const { handleDeleteChat } = useChats();
  const [open, setOpen] = useState<boolean>(false);

  const destructiveColor = "text-red-600";

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button
          className={cn(
            "transition-opacity cursor-pointer p-1 rounded ring-0! group-data-[active=true]:bg-sidebar-accent group-data-[active=true]:text-sidebar-accent-foreground",
            open ? "opacity-100" : "opacity-0 group-hover/item:opacity-100"
          )}
          onClick={(e) => e.stopPropagation()}
        >
          <Ellipsis className="size-4" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-40 rounded-xl" align="start">
        <DropdownMenuItem
          className="hover:bg-red-600/10 rounded-lg"
          onSelect={() => handleDeleteChat(chatId)}
        >
          <div
            className={cn(
              "flex items-center gap-2 w-full cursor-pointer",
              destructiveColor
            )}
          >
            <Trash2 className={cn("size-4", destructiveColor)} />
            Delete
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
