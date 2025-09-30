"use client";

import React, { useState } from "react";
import { ChevronRight, ChevronLeft, Map } from "lucide-react";

interface RightPanelProps {
  children?: React.ReactNode;
}

export function RightPanel({ children }: RightPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div
      className={`
        relative h-full bg-background border-l
        transition-all duration-300 ease-in-out flex-shrink-0
        ${isOpen ? "w-full" : "w-12"}
      `}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute left-2 top-2 p-2 rounded-lg bg-background border shadow-sm hover:bg-accent transition-colors z-10"
        aria-label={isOpen ? "Close panel" : "Open panel"}
      >
        {isOpen ? (
          <ChevronRight className="w-4 h-4" />
        ) : (
          <ChevronLeft className="w-4 h-4" />
        )}
      </button>

      {/* Panel Content */}
      <div
        className={`
          h-full overflow-hidden
          ${isOpen ? "opacity-100" : "opacity-0"}
          transition-opacity duration-300
        `}
      >
        {isOpen && (
          <div className="h-full flex flex-col pt-12">
            {/* Header */}
            <div className="px-4 pb-3 border-b flex items-center gap-2">
              <Map className="w-5 h-5" />
              <h2 className="font-semibold">Map View</h2>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto">
              {children || (
                <div className="flex items-center justify-center h-full text-muted-foreground p-4">
                  <p>Map content will appear here</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Collapsed State Icon */}
      {!isOpen && (
        <div className="flex items-center justify-center h-full">
          <Map className="w-5 h-5 text-muted-foreground" />
        </div>
      )}
    </div>
  );
}