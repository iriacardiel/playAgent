
"use client";

import React, { useState, useRef, useEffect } from "react";
import { ChevronRight, ChevronLeft, Map, GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface MapPanelProps {
  children?: React.ReactNode;
  defaultOpen?: boolean;
  defaultWidth?: number;
  minWidth?: number;
  maxWidth?: number;
  title?: string;
}

export function MapPanel({ 
  children, 
  defaultOpen = true,
  defaultWidth = 600,
  minWidth = 0,
  maxWidth = 600,
  title = "Map View" 
}: MapPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [width, setWidth] = useState(defaultWidth);
  const [isResizing, setIsResizing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!panelRef.current) return;
      
      const panelRect = panelRef.current.getBoundingClientRect();
      const newWidth = panelRect.right - e.clientX;
      
      if (newWidth >= minWidth && newWidth <= maxWidth) {
        setWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing, minWidth, maxWidth]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  return (
    <div
      ref={panelRef}
      className={cn(
        "relative h-full bg-background flex-shrink-0 transition-all duration-600 ease-in-out",
        !isOpen && "w-12"
      )}
      style={isOpen ? { width: `${width}px` } : undefined}
    >
      {/* Resize Handle - only visible when open */}
      {isOpen && (
        <div
          onMouseDown={handleMouseDown}
          className={cn(
            "absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/20 transition-colors z-20",
            isResizing && "bg-primary/30"
          )}
        >
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full p-1">
            <GripVertical className="h-4 w-4 text-muted-foreground" />
          </div>
        </div>
      )}

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute left-2 top-2 z-10 rounded-lg bg-background p-2 transition-colors hover:bg-accent"
        aria-label={isOpen ? "Close panel" : "Open panel"}
      >
        <Map className="h-5 w-5 text-muted-foreground" />
      </button>


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
      
      {/* Prevent text selection during resize */}
      {isResizing && (
        <style jsx global>{`
          body {
            user-select: none;
            cursor: col-resize !important;
          }
        `}</style>
      )}
    </div>
  );
}