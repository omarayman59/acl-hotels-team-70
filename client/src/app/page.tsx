"use client";

import { useSidebar } from "@/components/ui/sidebar";
import { useChats } from "@/features/(shared)/chats";

import { MessageDisplay } from "@/features/(shared)/chats/components/MessageDisplay";
import { MessageInput } from "@/features/(shared)/chats/components/MessageInput";

import { cn } from "@/lib/utils";

const HomePage = () => {
  const { isMobile } = useSidebar();
  const { currentChat } = useChats();
  const isEmptyChat = !currentChat.messages.length;

  const shouldCenterHigher = isEmptyChat && !isMobile;
  const shouldPlaceAtBottom = !isEmptyChat;

  return (
    <div
      className={cn("flex flex-col h-full items-center", {
        "justify-center -mt-16 space-y-6": shouldCenterHigher,
        "justify-end pb-6": shouldPlaceAtBottom,
        "justify-center space-y-6": isEmptyChat && isMobile,
      })}
    >
      {isEmptyChat ? (
        <div
          className={cn("w-full max-w-lg text-center", {
            "flex-1 flex items-center justify-center": shouldPlaceAtBottom,
          })}
        >
          <span className="flex items-center justify-center text-3xl">
            What would you like to know?
          </span>
        </div>
      ) : (
        <MessageDisplay />
      )}
      <MessageInput />
    </div>
  );
};

export default HomePage;
