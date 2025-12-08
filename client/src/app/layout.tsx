import { type Metadata } from "next";

import { Geist, Geist_Mono } from "next/font/google";

import "./globals.css";

import { TanstackQueryProvider } from "@/providers/TanstackQueryProvider";
import { SidebarProvider } from "@/features/(shared)/sidebar";
import { ChatsProvider } from "@/features/(shared)/chats";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Hotel Recommender",
  description: "AI Powered Hotel Recommendations",
};

const RootLayout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <TanstackQueryProvider>
          <ChatsProvider>
            <SidebarProvider>{children}</SidebarProvider>
          </ChatsProvider>
        </TanstackQueryProvider>
      </body>
    </html>
  );
};

export default RootLayout;
