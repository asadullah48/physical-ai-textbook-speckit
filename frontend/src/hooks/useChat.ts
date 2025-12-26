/**
 * Hook for Server-Sent Events (SSE) streaming chat.
 */

import { useState, useCallback, useRef } from 'react';
import type { ChatSource } from '@site/src/context/ChatContext';

// Get API URL
const getApiUrl = (): string => {
  return 'https://asadullahshafique-physical-ai-backend.hf.space';
};

export interface StreamingChatOptions {
  query: string;
  selectedText?: string;
  moduleId?: string;
  chapterId?: string;
  sessionId?: string;
}

export interface StreamingChatResult {
  sources: ChatSource[];
  answer: string;
  sessionId: string | null;
}

export interface UseStreamingChatReturn {
  isStreaming: boolean;
  error: string | null;
  streamChat: (options: StreamingChatOptions) => Promise<StreamingChatResult>;
  abortStream: () => void;
}

/**
 * Hook for streaming chat responses via SSE.
 */
export function useStreamingChat(): UseStreamingChatReturn {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const abortStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const streamChat = useCallback(
    async (options: StreamingChatOptions): Promise<StreamingChatResult> => {
      // Abort any existing stream
      abortStream();

      setIsStreaming(true);
      setError(null);

      const result: StreamingChatResult = {
        sources: [],
        answer: '',
        sessionId: null,
      };

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      try {
        const url = `${getApiUrl()}/api/chat/query/stream`;

        // Get auth token if available
        const token = typeof window !== 'undefined'
          ? localStorage.getItem('accessToken')
          : null;

        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(url, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            query: options.query,
            selected_text: options.selectedText,
            module_id: options.moduleId,
            chapter_id: options.chapterId,
            session_id: options.sessionId,
          }),
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');

          // Keep the last incomplete line in the buffer
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === 'sources') {
                  result.sources = (data.data || []).map((s: {
                    module_id: string;
                    chapter_id: string;
                    section: string;
                    score: number;
                  }) => ({
                    moduleId: s.module_id,
                    chapterId: s.chapter_id,
                    section: s.section,
                    score: s.score,
                  }));
                } else if (data.type === 'chunk') {
                  result.answer += data.data || '';
                } else if (data.type === 'done') {
                  result.sessionId = data.data?.session_id || null;
                } else if (data.type === 'error') {
                  throw new Error(data.data);
                }
              } catch (parseError) {
                // Skip invalid JSON lines
                console.warn('Failed to parse SSE data:', line);
              }
            }
          }
        }

        return result;
      } catch (err) {
        if ((err as Error).name === 'AbortError') {
          // Stream was intentionally aborted
          return result;
        }
        const message = err instanceof Error ? err.message : 'Failed to stream response';
        setError(message);
        throw err;
      } finally {
        setIsStreaming(false);
        abortControllerRef.current = null;
      }
    },
    [abortStream]
  );

  return {
    isStreaming,
    error,
    streamChat,
    abortStream,
  };
}

/**
 * Non-streaming chat API call (fallback).
 */
export async function sendChatMessage(options: StreamingChatOptions): Promise<StreamingChatResult> {
  const url = `${getApiUrl()}/api/chat/query`;

  const token = typeof window !== 'undefined'
    ? localStorage.getItem('accessToken')
    : null;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      query: options.query,
      selected_text: options.selectedText,
      module_id: options.moduleId,
      chapter_id: options.chapterId,
      session_id: options.sessionId,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  const data = await response.json();

  return {
    sources: (data.sources || []).map((s: {
      module_id: string;
      chapter_id: string;
      section: string;
      score: number;
    }) => ({
      moduleId: s.module_id,
      chapterId: s.chapter_id,
      section: s.section,
      score: s.score,
    })),
    answer: data.answer,
    sessionId: data.session_id,
  };
}
