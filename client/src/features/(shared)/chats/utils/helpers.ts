import { type ChatType } from "../types";

export function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function createNewChat(): ChatType {
  return {
    id: generateId(),
    title: "Untitled Chat",
    createdAt: new Date(),
    messages: [],
  };
}
