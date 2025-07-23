"use client";

import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Brain, ChevronRight, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { MarkdownText } from "./markdown-text";

interface ThinkingDisplayProps {
  /** The full content containing thinking tokens */
  content: string;
  /** Whether the thinking is currently in progress */
  isThinking?: boolean;
  /** Custom className for styling */
  className?: string;
}

interface ThinkingContent {
  thinking: string;
  remaining: string;
  isComplete: boolean;
  hasThinking: boolean;
}

/**
 * Extracts thinking content from text with <think>...</think> tokens
 */
function parseThinkingContent(content: string): ThinkingContent {
  if (!content.includes('<think>')) {
    return {
      thinking: '',
      remaining: content.trim(),
      isComplete: false,
      hasThinking: false,
    };
  }

  // Extract complete thinking blocks
  const completeBlocks: string[] = [];
  const completeRegex = /<think>([\s\S]*?)<\/think>/g;
  let match;
  
  while ((match = completeRegex.exec(content)) !== null) {
    completeBlocks.push(match[1].trim());
  }

  // Remove complete blocks and check for incomplete ones
  let processedContent = content.replace(completeRegex, '');
  const incompleteMatch = processedContent.match(/<think>([\s\S]*?)$/);
  const incompleteContent = incompleteMatch?.[1]?.trim() || '';

  if (incompleteMatch) {
    processedContent = processedContent.replace(/<think>[\s\S]*$/, '');
  }

  // Combine all thinking content
  const allThinking = [...completeBlocks];
  if (incompleteContent) {
    allThinking.push(incompleteContent);
  }

  return {
    thinking: allThinking.join('\n\n'),
    remaining: processedContent.trim(),
    isComplete: completeBlocks.length > 0 && !incompleteContent,
    hasThinking: true,
  };
}

/**
 * Custom hook for managing thinking display state
 */
function useThinkingState(isThinking: boolean, isComplete: boolean) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [userManuallyToggled, setUserManuallyToggled] = useState(false);

  // Auto-expand when thinking starts (if user hasn't manually controlled it)
  useEffect(() => {
    if (isThinking && !userManuallyToggled) {
      setIsExpanded(true);
    }
  }, [isThinking, userManuallyToggled]);

  // Auto-collapse when thinking completes (if user hasn't manually controlled it)
  useEffect(() => {
    if (isComplete && !userManuallyToggled) {
      setIsExpanded(false);
    }
  }, [isComplete, userManuallyToggled]);

  // Reset manual toggle flag when new thinking session starts
  useEffect(() => {
    if (isThinking) {
      setUserManuallyToggled(false);
    }
  }, [isThinking]);

  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev);
    setUserManuallyToggled(true);
  }, []);

  return { isExpanded, toggleExpanded };
}

/**
 * Custom hook for auto-scrolling with native scroll
 */
function useAutoScroll(isThinking: boolean, isComplete: boolean, thinkingContent: string, isExpanded: boolean) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only auto-scroll if thinking is active and not complete, and content is visible
    if (!isThinking || isComplete || !isExpanded || !thinkingContent) return;

    const scrollToBottom = () => {
      const container = scrollContainerRef.current;
      if (!container) return;

      // Smooth scroll to bottom
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    };

    // Use multiple timeouts to handle different rendering scenarios
    const timeouts = [
      setTimeout(scrollToBottom, 0),
      setTimeout(scrollToBottom, 10),
      setTimeout(scrollToBottom, 50),
    ];

    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, [thinkingContent, isThinking, isComplete, isExpanded]);

  // Also scroll when content becomes visible (expansion)
  useEffect(() => {
    if (!isExpanded || !thinkingContent) return;

    const scrollToBottom = () => {
      const container = scrollContainerRef.current;
      if (!container) return;

      // Scroll to bottom after expansion animation
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    };

    // Wait for expansion animation to complete
    const timeoutId = setTimeout(scrollToBottom, 350);
    return () => clearTimeout(timeoutId);
  }, [isExpanded, thinkingContent]);

  return scrollContainerRef;
}

export function ThinkingDisplay({ content, isThinking = false, className }: ThinkingDisplayProps) {
  const parsedContent = parseThinkingContent(content);
  const { isExpanded, toggleExpanded } = useThinkingState(isThinking, parsedContent.isComplete);
  const scrollContainerRef = useAutoScroll(isThinking, parsedContent.isComplete, parsedContent.thinking, isExpanded);

  // If no thinking content and not currently thinking, just show the content
  if (!parsedContent.hasThinking && !isThinking) {
    return (
      <div className={cn("w-full max-w-full min-w-0", className)}>
        <MarkdownText>{content}</MarkdownText>
      </div>
    );
  }

  // Don't show thinking section if there's no thinking content (even if isThinking is true)
  // This prevents empty bubbles for models without thinking capabilities
  if (!parsedContent.thinking && !isThinking) {
    return (
      <div className={cn("w-full max-w-full min-w-0", className)}>
        <MarkdownText>{parsedContent.remaining || content}</MarkdownText>
      </div>
    );
  }

  const shouldShowThinkingContent = (isThinking && !parsedContent.isComplete) || isExpanded;
  const hasThinkingBorder = parsedContent.thinking && shouldShowThinkingContent;
  const shouldShowThinkingSection = parsedContent.thinking || (isThinking && parsedContent.hasThinking);

  return (
    <div className={cn("flex flex-col gap-3 w-full max-w-full min-w-0", className)}>
      {/*
        NOTE: If you still see overflow, ensure the parent message area container also has min-w-0 and does not allow children to exceed its width.
      */}
      {shouldShowThinkingSection && (
        <div className="border border-blue-200 rounded-lg bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20 w-full max-w-full min-w-0">
        {/* Thinking Header */}
        <div className={cn(
          "flex items-center gap-2 p-3",
          hasThinkingBorder && "border-b border-blue-200 dark:border-blue-800"
        )}>
          <motion.button
            onClick={toggleExpanded}
            initial={false}
            animate={{ rotate: isExpanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
            className="flex h-5 w-5 items-center justify-center rounded-md text-blue-600 transition-colors hover:bg-blue-100 dark:text-blue-400 dark:hover:bg-blue-900/50"
            aria-label={isExpanded ? "Collapse thinking" : "Expand thinking"}
          >
            <ChevronRight className="h-4 w-4" />
          </motion.button>
          
          <Brain className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          
          <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
            {isThinking && !parsedContent.isComplete ? "Thinking..." : "Thought Process"}
          </span>
          
          {isThinking && !parsedContent.isComplete && (
            <Loader2 className="h-4 w-4 text-blue-600 animate-spin dark:text-blue-400" />
          )}
        </div>

        {/* Thinking Content */}
        {parsedContent.thinking && (
          <motion.div
            initial={false}
            animate={{
              height: shouldShowThinkingContent ? "auto" : 0,
              opacity: shouldShowThinkingContent ? 1 : 0,
            }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="p-3 w-full max-w-full min-w-0">
              {/* Native Scrollable Container */}
              <div
                ref={scrollContainerRef}
                className={cn(
                  "max-h-96 overflow-y-auto rounded-md w-full max-w-full min-w-0",
                  "scrollbar-thin scrollbar-thumb-blue-300 scrollbar-track-blue-100",
                  "dark:scrollbar-thumb-blue-600 dark:scrollbar-track-blue-900",
                  // Fallback for browsers that don't support scrollbar-thin
                  "[&::-webkit-scrollbar]:w-2",
                  "[&::-webkit-scrollbar-track]:bg-blue-100 dark:[&::-webkit-scrollbar-track]:bg-blue-900",
                  "[&::-webkit-scrollbar-thumb]:bg-blue-300 dark:[&::-webkit-scrollbar-thumb]:bg-blue-600",
                  "[&::-webkit-scrollbar-thumb]:rounded-full",
                  "[&::-webkit-scrollbar-thumb]:hover:bg-blue-400 dark:[&::-webkit-scrollbar-thumb]:hover:bg-blue-500"
                )}
              >
                <div className="text-xs leading-relaxed text-blue-800 dark:text-blue-200 pr-2 whitespace-pre-wrap break-words w-full max-w-full min-w-0">
                  {parsedContent.thinking}
                </div>
              </div>
            </div>
          </motion.div>
        )}
        </div>
      )}

      {/* Main Content */}
      {parsedContent.remaining && (
        <div className="w-full max-w-full min-w-0">
          <MarkdownText>{parsedContent.remaining}</MarkdownText>
        </div>
      )}
    </div>
  );
}

/**
 * Hook to check if content contains thinking and extract parts
 */
export function useThinkingContent(content: string) {
  return parseThinkingContent(content);
}