"use client";

import {
  SidebarProvider as ShadcnSidebarProvider,
  SidebarInset,
} from "@/components/ui/sidebar";

import { NavigationBar } from "../components/NavigationBar";
import { AppSidebar } from "../components/AppSidebar";

export const SidebarProvider = ({
  children,
}: {
  children: React.ReactNode;
}) => {
  return (
    <ShadcnSidebarProvider>
      <AppSidebar />
      <SidebarInset className="flex flex-col">
        <NavigationBar />
        <main className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 flex flex-col items-center w-full">
            <div className="flex-1 w-full max-w-3xl px-4">{children}</div>
          </div>
        </main>
      </SidebarInset>
    </ShadcnSidebarProvider>
  );
};
