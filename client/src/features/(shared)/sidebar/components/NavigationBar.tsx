"use client";

import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";

export const NavigationBar = () => {
  const { isMobile } = useSidebar();

  return (
    <header className="sticky top-0 z-10 flex h-12 shrink-0 items-center gap-2 px-4">
      {isMobile && <SidebarTrigger className="-ml-1" />}
      <div className="flex items-center gap-1 text-xl font-medium">
        <span>HotelGPT</span>
        <span className="text-muted-foreground">0.1</span>
      </div>
    </header>
  );
};
