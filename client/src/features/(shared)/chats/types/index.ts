export type MessageType = {
  id: string;
  content: string;
  createdAt: Date;
  role: "user" | "system";
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
  abortControllerRef: React.MutableRefObject<AbortController | null>;
  setCurrentChat: React.Dispatch<React.SetStateAction<ChatType>>;
  setChats: React.Dispatch<React.SetStateAction<ChatType[]>>;
  handleCreateNewChat: () => void;
  handleSelectChat: (chatId: string) => void;
  handleDeleteChat: (chatId: string) => void;
  handleSendMessage: (message: string) => void;
}
