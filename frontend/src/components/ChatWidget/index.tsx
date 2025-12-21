import React, { useEffect, useRef } from 'react';
import { useChat } from '@site/src/context/ChatContext';
import { ChatMessage, TypingIndicator } from './ChatMessage';
import { ChatInput } from './ChatInput';
import styles from './styles.module.css';

/**
 * Chat widget FAB button icon.
 */
function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z" />
    </svg>
  );
}

/**
 * Close icon for header.
 */
function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
    </svg>
  );
}

/**
 * Clear icon for clearing chat.
 */
function ClearIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
    </svg>
  );
}

/**
 * Quote icon for selection context.
 */
function QuoteIcon() {
  return (
    <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path d="M6 17h3l2-4V7H5v6h3zm8 0h3l2-4V7h-6v6h3z" />
    </svg>
  );
}

/**
 * Selection context banner component.
 */
function SelectionBanner() {
  const { selectionContext, setSelectionContext } = useChat();

  if (!selectionContext) return null;

  return (
    <div className={styles.selectionBanner}>
      <QuoteIcon />
      <div className={styles.selectionText}>
        "{selectionContext.text.slice(0, 150)}
        {selectionContext.text.length > 150 ? '...' : ''}"
      </div>
      <button
        className={styles.clearSelection}
        onClick={() => setSelectionContext(null)}
        aria-label="Clear selection"
      >
        <CloseIcon />
      </button>
    </div>
  );
}

/**
 * Empty state when no messages.
 */
function EmptyState() {
  return (
    <div className={styles.emptyState}>
      <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
        <path
          fill="currentColor"
          d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"
        />
      </svg>
      <p>Ask me anything about the textbook!</p>
      <small>
        I can help explain concepts, answer questions, and guide you through the material.
      </small>
    </div>
  );
}

/**
 * Main ChatWidget component.
 *
 * Displays a floating action button that opens a chat interface
 * for interacting with the RAG-powered chatbot.
 */
export default function ChatWidget() {
  const {
    isOpen,
    messages,
    isLoading,
    error,
    toggleChat,
    closeChat,
    sendMessage,
    clearMessages,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  return (
    <div className={styles.chatWidgetContainer}>
      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          {/* Header */}
          <div className={styles.header}>
            <h3 className={styles.headerTitle}>AI Teaching Assistant</h3>
            <div className={styles.headerActions}>
              <button
                className={styles.headerButton}
                onClick={clearMessages}
                aria-label="Clear chat"
                title="Clear chat"
              >
                <ClearIcon />
              </button>
              <button
                className={styles.headerButton}
                onClick={closeChat}
                aria-label="Close chat"
              >
                <CloseIcon />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className={styles.messagesContainer}>
            <SelectionBanner />

            {messages.length === 0 && !isLoading && <EmptyState />}

            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {isLoading && <TypingIndicator />}

            {error && (
              <div className={styles.errorMessage}>
                <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                </svg>
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <ChatInput onSend={sendMessage} disabled={isLoading} />
        </div>
      )}

      {/* Toggle Button */}
      <button
        className={styles.toggleButton}
        onClick={toggleChat}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? <CloseIcon /> : <ChatIcon />}
      </button>
    </div>
  );
}
