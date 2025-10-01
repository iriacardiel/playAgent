"use client";

import React, { useState } from "react";
import { Map, Maximize2, Minimize2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface MapPanelProps {
  children?: React.ReactNode;
  defaultOpen?: boolean;
  defaultFullSize?: boolean;
  normalWidth?: number;
  title?: string;
}

export function MapPanel({ 
  children, 
  defaultOpen = true,
  defaultFullSize = false,
  normalWidth = 600,
}: MapPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isFullSize, setIsFullSize] = useState(defaultFullSize);

  return (
    <div
      className={cn(
        "relative h-full bg-background flex-shrink-0 transition-all duration-300 ease-in-out",
        !isOpen && "w-12",
        isOpen && !isFullSize && `w-[${normalWidth}px]`,
        isOpen && isFullSize && "fixed inset-0 w-screen h-screen z-50"
      )}
      style={
        isOpen && !isFullSize 
          ? { width: `${normalWidth}px` } 
          : undefined
      }
    >
      {/* Toggle Open/Close Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute left-2 top-2 z-10 rounded-lg bg-background p-2 transition-colors hover:bg-accent shadow-sm"
        aria-label={isOpen ? "Close panel" : "Open panel"}
      >
        <Map className="h-5 w-5 text-muted-foreground" />
      </button>

      {/* Full Size Toggle Button - only visible when open */}
      {isOpen && (
        <button
          onClick={() => setIsFullSize(!isFullSize)}
          className="absolute right-2 top-14 z-10 rounded-lg bg-background p-2 transition-colors hover:bg-accent shadow-sm border"
          aria-label={isFullSize ? "Normal size" : "Full size"}
        >
          {isFullSize ? (
            <Minimize2 className="h-5 w-5 text-muted-foreground" />
          ) : (
            <Maximize2 className="h-5 w-5 text-muted-foreground" />
          )}
        </button>
      )}

      {/* Expanded Content */}
      {isOpen && (
        <div className="flex h-full flex-col pt-12">
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