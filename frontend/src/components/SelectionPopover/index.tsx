import React, { useEffect, useState, useCallback } from 'react';
import { useChat } from '@site/src/context/ChatContext';
import { useTextSelection, getChapterIdFromPage } from '@site/src/hooks/useSelection';
import styles from './styles.module.css';

/**
 * Ask AI icon.
 */
function AskIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
      <circle cx="12" cy="10" r="1.5" />
      <circle cx="8" cy="10" r="1.5" />
      <circle cx="16" cy="10" r="1.5" />
    </svg>
  );
}

/**
 * Close icon.
 */
function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

interface PopoverPosition {
  top: number;
  left: number;
  placement: 'above' | 'below';
}

/**
 * Selection popover component.
 *
 * Shows a floating button when text is selected, allowing users to
 * ask questions about the selected text.
 */
export default function SelectionPopover() {
  const { selection, clearSelection } = useTextSelection('.markdown');
  const { openChat, setSelectionContext } = useChat();
  const [position, setPosition] = useState<PopoverPosition | null>(null);
  const [visible, setVisible] = useState(false);

  // Calculate popover position
  useEffect(() => {
    if (!selection.position || !selection.text) {
      setVisible(false);
      setPosition(null);
      return;
    }

    const { top, left, width, height } = selection.position;

    // Calculate center position of selection
    const centerX = left + width / 2;

    // Determine if popover should appear above or below
    // Place above if there's enough room, otherwise below
    const viewportTop = window.scrollY;
    const spaceAbove = top - viewportTop;
    const placement = spaceAbove > 80 ? 'above' : 'below';

    // Position horizontally centered on selection
    const popoverWidth = 160; // Approximate width
    const popoverLeft = Math.max(10, Math.min(centerX - popoverWidth / 2, window.innerWidth - popoverWidth - 10));

    // Position vertically
    const popoverTop = placement === 'above' ? top : top + height;

    setPosition({
      top: popoverTop,
      left: popoverLeft,
      placement,
    });

    // Small delay before showing to avoid flashing
    const timer = setTimeout(() => setVisible(true), 100);
    return () => clearTimeout(timer);
  }, [selection.position, selection.text]);

  // Handle "Ask AI" click
  const handleAskAI = useCallback(() => {
    const chapterId = getChapterIdFromPage();

    setSelectionContext({
      text: selection.text,
      chapterId,
    });

    openChat();
    clearSelection();
    setVisible(false);

    // Clear the browser selection
    window.getSelection()?.removeAllRanges();
  }, [selection.text, setSelectionContext, openChat, clearSelection]);

  // Handle close
  const handleClose = useCallback(() => {
    clearSelection();
    setVisible(false);
    window.getSelection()?.removeAllRanges();
  }, [clearSelection]);

  if (!visible || !position || !selection.text) {
    return null;
  }

  return (
    <div
      className={`${styles.popover} ${
        position.placement === 'above' ? styles.popoverAbove : styles.popoverBelow
      }`}
      style={{
        top: position.top,
        left: position.left,
      }}
    >
      <button className={styles.button} onClick={handleAskAI}>
        <AskIcon />
        Ask AI
      </button>
      <button
        className={styles.closeButton}
        onClick={handleClose}
        aria-label="Close"
      >
        <CloseIcon />
      </button>
    </div>
  );
}
