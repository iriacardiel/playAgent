"use client";

import React, { useState } from "react";
import { ChevronRight, ChevronLeft, Map } from "lucide-react";
import { cn } from "@/lib/utils";

interface MapPanelProps {
  children?: React.ReactNode;
  defaultOpen?: boolean;
  title?: string;
}

export function MapPanel({ 
  children, 
  defaultOpen = true,
  title = "Map View" 
}: MapPanelProps) {
const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div
      className={cn(
        "relative h-full bg-background border-l flex-shrink-0 transition-all duration-300 ease-in-out",
        isOpen ? "w-full" : "w-12"
      )}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute left-2 top-2 z-10 rounded-lg border bg-background p-2 shadow-sm transition-colors hover:bg-accent"
        aria-label={isOpen ? "Close panel" : "Open panel"}
      >
        {isOpen ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
      </button>

      {/* Collapsed State */}
      {!isOpen && (
        <div className="flex h-full items-center justify-center">
          <Map className="h-5 w-5 text-muted-foreground" />
        </div>
      )}

      {/* Expanded Content */}
      {isOpen && (
        <div className="flex h-full flex-col pt-12">
          {/* Header */}
          <div className="flex items-center gap-2 border-b px-4 pb-3">
            <Map className="h-5 w-5" />
            <h2 className="font-semibold">{title}</h2>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-auto">
            {children || (
              <div className="flex h-full items-center justify-center p-4 text-muted-foreground">
                <p>Map content will appear here</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}