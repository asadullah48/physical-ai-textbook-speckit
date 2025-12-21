import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import { sendChatMessage } from '@site/src/hooks/useChat';

/**
 * Message in a chat conversation.
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  sources?: ChatSource[];
  selectionContext?: SelectionContext;
}

/**
 * Source citation for RAG responses.
 */
export interface ChatSource {
  moduleId: string;
  chapterId: string;
  section: string;
  score: number;
}

/**
 * Context from text selection.
 */
export interface SelectionContext {
  text: string;
  chapterId?: string;
  position?: { start: number; end: number };
}

/**
 * Chat state and actions.
 */
interface ChatContextValue {
  // State
  isOpen: boolean;
  messages: ChatMessage[];
  sessionId: string | null;
  isLoading: boolean;
  error: string | null;
  selectionContext: SelectionContext | null;

  // Actions
  openChat: () => void;
  closeChat: () => void;
  toggleChat: () => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setSelectionContext: (context: SelectionContext | null) => void;
}

const ChatContext = createContext<ChatContextValue | null>(null);

/**
 * Hook to access chat context.
 *
 * @throws Error if used outside ChatProvider
 */
export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

/**
 * Get the current chapter ID from the URL.
 */
function getCurrentChapterId(): string | undefined {
  if (typeof window === 'undefined') return undefined;

  const path = window.location.pathname;
  // Match /docs/module-N-xxx/chapter-slug pattern
  const match = path.match(/\/docs\/(module-\d+-[^/]+\/[^/]+)/);
  return match ? match[1] : undefined;
}

/**
 * Provider component for chat state.
 */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectionContext, setSelectionContext] = useState<SelectionContext | null>(null);

  // Ref to track abort controller for streaming
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load session from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedSessionId = localStorage.getItem('chatSessionId');
      if (savedSessionId) {
        setSessionId(savedSessionId);
      }
    }
  }, []);

  // Save session to localStorage when it changes
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId) {
      localStorage.setItem('chatSessionId', sessionId);
    }
  }, [sessionId]);

  const openChat = useCallback(() => {
    setIsOpen(true);
    setError(null);
  }, []);

  const closeChat = useCallback(() => {
    setIsOpen(false);
    // Abort any ongoing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const toggleChat = useCallback(() => {
    setIsOpen((prev) => !prev);
    setError(null);
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
      selectionContext: selectionContext || undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    // Capture selection context before clearing
    const currentSelection = selectionContext;
    setSelectionContext(null);

    try {
      const currentChapterId = getCurrentChapterId();

      // Use the non-streaming API for now (streaming can be enabled later)
      const result = await sendChatMessage({
        query: content.trim(),
        selectedText: currentSelection?.text,
        chapterId: currentSelection?.chapterId || currentChapterId,
        sessionId: sessionId || undefined,
      });

      // Update session ID
      if (result.sessionId) {
        setSessionId(result.sessionId);
      }

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: result.answer,
        timestamp: new Date(),
        sources: result.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);

      // Add error message to chat
      const errorAssistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorAssistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [selectionContext, sessionId]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('chatSessionId');
    }
  }, []);

  const value: ChatContextValue = {
    isOpen,
    messages,
    sessionId,
    isLoading,
    error,
    selectionContext,
    openChat,
    closeChat,
    toggleChat,
    sendMessage,
    clearMessages,
    setSelectionContext,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}
