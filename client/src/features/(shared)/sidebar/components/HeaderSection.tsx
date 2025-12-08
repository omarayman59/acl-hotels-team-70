"use client";

import {
  SidebarHeader,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";

export const HeaderSection = () => {
  const { state } = useSidebar();
  const isExpanded = state === "expanded";

  return (
    <SidebarHeader>
      {isExpanded ? (
        <div className="flex items-center justify-between w-full px-2">
          <div className="flex items-center justify-center size-8 rounded-full bg-sidebar-accent">
            <span className="text-sm font-semibold">H</span>
          </div>
          <SidebarTrigger />
        </div>
      ) : (
        <div className="group relative flex items-center justify-center w-full">
          <div className="flex items-center justify-center size-8 rounded-full bg-sidebar-accent group-hover:opacity-0 transition-opacity">
            <span className="text-sm font-semibold">H</span>
          </div>
          <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <SidebarTrigger />
          </div>
        </div>
      )}
    </SidebarHeader>
  );
};
