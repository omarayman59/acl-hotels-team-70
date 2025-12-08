"use client";

import { useEffect } from "react";

interface UseKeyDownProps {
  keyComboCheck: (e: KeyboardEvent) => boolean;
  action: () => void;
}

export const useKeyDown = ({ keyComboCheck, action }: UseKeyDownProps) => {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (keyComboCheck(e)) {
        e.preventDefault();
        action();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [keyComboCheck, action]);
};
