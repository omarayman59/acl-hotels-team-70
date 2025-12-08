"use client";

import { useCallback, useEffect, useState } from "react";
import { useChats } from "../utils/provider";
import { useSend } from "../hooks/useSend";

import {
  InputGroup,
  InputGroupButton,
  InputGroupInput,
} from "@/components/ui/input-group";

import { SendIcon } from "lucide-react";
import { useKeyDown } from "@/hooks/use-key-down";

export const MessageInput = () => {
  const { currentChat, handleSendMessage: handleSendMessageAction } =
    useChats();

  const [message, setMessage] = useState<string>("");

  const { mutate: sendMessage, isPending } = useSend();

  const disableSend = !message.trim() || isPending;

  const handleSendMessage = useCallback(() => {
    if (disableSend) return;

    handleSendMessageAction(message);
    sendMessage({ chatId: currentChat.id, message });

    setMessage("");
  }, [message, currentChat.id, handleSendMessageAction, sendMessage]);

  useKeyDown({
    keyComboCheck: (e) => e.key === "Enter" && !e.shiftKey,
    action: handleSendMessage,
  });

  return (
    <InputGroup className="h-12 bg-sidebar rounded-3xl ring-0! shadow-md px-2">
      <InputGroupInput
        placeholder="Ask anything hotels"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <InputGroupButton
        className="size-9 bg-primary hover:bg-primary/90 rounded-full active:scale-103 transition-all duration-100"
        onClick={handleSendMessage}
        disabled={disableSend}
      >
        <SendIcon className="size-5 text-white" />
      </InputGroupButton>
    </InputGroup>
  );
};
