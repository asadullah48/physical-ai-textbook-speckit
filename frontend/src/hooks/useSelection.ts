/**
 * Hook for detecting and handling text selection.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export interface TextSelection {
  text: string;
  position: {
    top: number;
    left: number;
    width: number;
    height: number;
  } | null;
  range: Range | null;
}

export interface UseTextSelectionReturn {
  selection: TextSelection;
  clearSelection: () => void;
}

/**
 * Hook to track text selection in the document.
 *
 * @param containerSelector - Optional CSS selector to limit selection to a container
 * @returns Current selection state and clear function
 */
export function useTextSelection(containerSelector?: string): UseTextSelectionReturn {
  const [selection, setSelection] = useState<TextSelection>({
    text: '',
    position: null,
    range: null,
  });

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearSelection = useCallback(() => {
    setSelection({
      text: '',
      position: null,
      range: null,
    });
  }, []);

  useEffect(() => {
    // Only run on client side
    if (typeof window === 'undefined') return;

    const handleSelectionChange = () => {
      // Debounce selection changes
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        const windowSelection = window.getSelection();

        if (!windowSelection || windowSelection.isCollapsed) {
          // No selection or collapsed selection
          return;
        }

        const text = windowSelection.toString().trim();

        // Only process selections with meaningful text (at least 10 chars)
        if (text.length < 10) {
          return;
        }

        // Check if selection is within container (if specified)
        if (containerSelector) {
          const container = document.querySelector(containerSelector);
          if (container) {
            const anchorNode = windowSelection.anchorNode;
            if (anchorNode && !container.contains(anchorNode)) {
              return;
            }
          }
        }

        // Exclude selections from input elements, code blocks, etc.
        const anchorNode = windowSelection.anchorNode;
        if (anchorNode) {
          const parentElement = anchorNode.parentElement;
          if (parentElement) {
            const tagName = parentElement.tagName?.toLowerCase();
            if (['input', 'textarea', 'code', 'pre'].includes(tagName)) {
              return;
            }
            // Also check for elements with specific classes
            if (
              parentElement.closest('.chatWidgetContainer') ||
              parentElement.closest('pre') ||
              parentElement.closest('.prism-code')
            ) {
              return;
            }
          }
        }

        try {
          const range = windowSelection.getRangeAt(0);
          const rect = range.getBoundingClientRect();

          // Only update if there's a valid position
          if (rect.width > 0 && rect.height > 0) {
            setSelection({
              text,
              position: {
                top: rect.top + window.scrollY,
                left: rect.left + window.scrollX,
                width: rect.width,
                height: rect.height,
              },
              range: range.cloneRange(),
            });
          }
        } catch {
          // Handle potential errors from getRangeAt
        }
      }, 200); // 200ms debounce
    };

    const handleMouseUp = () => {
      // Trigger selection check after mouse up
      handleSelectionChange();
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      // Handle keyboard selection (Shift + Arrow keys)
      if (e.shiftKey) {
        handleSelectionChange();
      }
    };

    const handleScroll = () => {
      // Clear selection on scroll to avoid stale positions
      if (selection.text) {
        clearSelection();
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keyup', handleKeyUp);
    document.addEventListener('selectionchange', handleSelectionChange);
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keyup', handleKeyUp);
      document.removeEventListener('selectionchange', handleSelectionChange);
      window.removeEventListener('scroll', handleScroll);

      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [containerSelector, selection.text, clearSelection]);

  return { selection, clearSelection };
}

/**
 * Get the chapter ID from the current page's main content.
 */
export function getChapterIdFromPage(): string | undefined {
  if (typeof window === 'undefined') return undefined;

  const path = window.location.pathname;
  // Match /docs/module-N-xxx/chapter-slug pattern
  const match = path.match(/\/docs\/(module-\d+-[^/]+\/[^/]+)/);
  return match ? match[1] : undefined;
}
