"use client";

import { useState } from "react";
import { useChats } from "@/features/(shared)/chats";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetBody,
} from "@/components/ui/sheet";
import { RAGOptions } from "@/features/(shared)/chats/components/RAGOptions";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

import { Settings } from "lucide-react";

export const OptionsSheet = () => {
  const [open, setOpen] = useState<boolean>(false);
  const { showLastMessageDetail, setShowLastMessageDetail } = useChats();

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="cursor-pointer">
          <Settings className="size-4" />
        </Button>
      </SheetTrigger>

      <SheetContent>
        <SheetHeader>
          <SheetTitle>Options</SheetTitle>
          <SheetDescription>
            Configure your options for the chat
          </SheetDescription>
        </SheetHeader>

        <SheetBody>
          <div className="space-y-6">
            <RAGOptions />

            <Separator />

            <div className="space-y-4">
              <div className="space-y-2">
                <h3 className="text-sm font-medium">Display Settings</h3>
                <p className="text-xs text-muted-foreground">
                  Customize how messages are displayed
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <Checkbox
                  id="show-detail"
                  checked={showLastMessageDetail}
                  onCheckedChange={(checked) =>
                    setShowLastMessageDetail(checked === true)
                  }
                  className="border-primary hover:border-primary/90 cursor-pointer"
                />
                <Label
                  htmlFor="show-detail"
                  className="text-sm font-normal cursor-pointer leading-tight"
                >
                  Show last message in detail view
                </Label>
              </div>
            </div>
          </div>
        </SheetBody>
      </SheetContent>
    </Sheet>
  );
};
