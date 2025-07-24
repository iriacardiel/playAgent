import { ThemeProvider } from "@/providers/theme-provider";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import React from "react";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  preload: true,
  display: "swap",
});

export const metadata: Metadata = {
  title: "DORI - AI Agent Sandbox",
  description: "AI-powered assistant",
  icons: {
    icon: "/DORI_logo.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light" // Set default to light / dark / system
          enableSystem
          disableTransitionOnChange
        >
          <NuqsAdapter>{children}</NuqsAdapter> {/* page.tsx content is rendered here */}
        </ThemeProvider>
      </body>
    </html>
  );
}

// The RootLayout wraps all pages (React components with type React.ReactNode), including page.tsx, providing global structure, styling, and context providers.

