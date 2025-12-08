"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarRail,
} from "@/components/ui/sidebar";
import { HeaderSection } from "./HeaderSection";
import { NavigationUser } from "./NavigationUser";
import { NavigationMain } from "./NavigationMain";

export const AppSidebar = ({
  ...props
}: React.ComponentProps<typeof Sidebar>) => {
  return (
    <Sidebar collapsible="icon" {...props}>
      <HeaderSection />
      <SidebarContent>
        <NavigationMain />
      </SidebarContent>
      <SidebarFooter>
        <NavigationUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
};
