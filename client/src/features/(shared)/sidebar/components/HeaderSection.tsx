"use client";

import {
  SidebarHeader,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";

import { getNavigationItems } from "../utils/helpers";

export const HeaderSection = () => {
  const navigationItems = getNavigationItems();

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

      {navigationItems.map((item) => (
        <SidebarMenuItem key={item.id} className="mt-4">
          <SidebarMenuButton tooltip={item.title} onClick={item.action}>
            <div className="w-full flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 w-[60%]">
                <span className="flex items-center justify-center w-6">
                  {item.icon && <item.icon className="size-4 mx-auto" />}
                </span>
                <span>{item.title}</span>
              </div>
              {isExpanded && item.hoverText && (
                <span className="text-xs text-muted-foreground opacity-0 group-hover/menu-item:opacity-100 transition-opacity">
                  {item.hoverText}
                </span>
              )}
            </div>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarHeader>
  );
};
