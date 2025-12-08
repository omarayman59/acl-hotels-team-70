"use client";

import { useEffect, useRef } from "react";
import { useChats } from "../utils/provider";

import { MessageItem } from "./MessageItem";
import { ScrollArea } from "@/components/ui/scroll-area";

export const MessageDisplay = () => {
  const { currentChat } = useChats();
  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentChat.messages]);

  return (
    <ScrollArea className="flex-1 w-full pb-4">
      <div ref={scrollRef} className="w-full h-0">
        {currentChat.messages.map((message) => (
          <MessageItem key={message.id} message={message} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
};
