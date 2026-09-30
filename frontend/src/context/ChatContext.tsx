import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { sendChatMessage, checkBackendReady } from '@site/src/hooks/useChat';
import { answerFromBook, loadIndex } from '@site/src/lib/bookAssistant';

/** Which engine produced an answer: the Gemini RAG backend or in-browser retrieval over the book. */
export type AnswerMode = 'gemini' | 'book';

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
  mode?: AnswerMode;
}

/**
 * Source citation for RAG responses.
 */
export interface ChatSource {
  moduleId: string;
  chapterId: string;
  section: string;
  score: number;
  /** Path relative to the site baseUrl, e.g. "docs/module-2-ros2/ros2-architecture#topics". */
  url?: string;
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
  // Match /docs/module-N-xxx/chapter-slug (works under any baseUrl)
  const match = path.match(/\/docs\/(module-\d+-[^/]+\/[^/#?]+)/);
  return match ? match[1] : undefined;
}

/**
 * Provider component for chat state.
 */
export function ChatProvider({ children }: { children: React.ReactNode }) {
  const { siteConfig } = useDocusaurusContext();
  const baseUrl = siteConfig.baseUrl;
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

    const currentChapterId = getCurrentChapterId();
    const selectedText = currentSelection?.text;

    const answerLocally = async (): Promise<ChatMessage> => {
      const index = await loadIndex(baseUrl);
      const local = answerFromBook(index, content.trim(), { route: currentChapterId, selectedText });
      return {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: local.answer,
        timestamp: new Date(),
        sources: local.sources,
        mode: 'book',
      };
    };

    try {
      let assistantMessage: ChatMessage | null = null;
      // Prefer the Gemini RAG backend when it reports healthy; otherwise (or
      // if it fails mid-request) answer from the book in the browser.
      if (await checkBackendReady()) {
        try {
          const result = await sendChatMessage({
            query: content.trim(),
            selectedText,
            chapterId: currentSelection?.chapterId || currentChapterId,
            sessionId: sessionId || undefined,
          });
          if (result.sessionId) setSessionId(result.sessionId);
          assistantMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: result.answer,
            timestamp: new Date(),
            sources: result.sources.map((src) => ({ ...src, url: `docs/${src.chapterId}` })),
            mode: 'gemini',
          };
        } catch {
          assistantMessage = null;
        }
      }
      if (!assistantMessage) assistantMessage = await answerLocally();
      setMessages((prev) => [...prev, assistantMessage as ChatMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      const errorAssistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'Sorry, I could not load the textbook index. Check your connection and try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorAssistantMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [selectionContext, sessionId, baseUrl]);

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
