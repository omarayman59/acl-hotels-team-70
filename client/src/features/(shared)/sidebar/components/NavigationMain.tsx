"use client";

import {
  SidebarGroup,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { YourChatsSection } from "./YourChatsSection";

import { getNavigationItems } from "../utils/helpers";

export const NavigationMain = () => {
  const navigationItems = getNavigationItems();

  return (
    <SidebarGroup>
      <SidebarMenu>
        {navigationItems.map((item) => (
          <SidebarMenuItem key={item.id}>
            <SidebarMenuButton tooltip={item.title} onClick={item.action}>
              {item.icon && <item.icon />}
              <span>{item.title}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        ))}
      </SidebarMenu>
      <YourChatsSection />
    </SidebarGroup>
  );
};
