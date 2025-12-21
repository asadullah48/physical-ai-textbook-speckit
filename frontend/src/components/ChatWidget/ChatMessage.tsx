import React from 'react';
import type { ChatMessage as ChatMessageType, ChatSource } from '@site/src/context/ChatContext';
import styles from './styles.module.css';

interface ChatMessageProps {
  message: ChatMessageType;
}

/**
 * Individual chat message component.
 */
export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`${styles.message} ${isUser ? styles.messageUser : styles.messageAssistant}`}
    >
      <div className={styles.messageAvatar}>
        {isUser ? '👤' : '🤖'}
      </div>
      <div className={styles.messageBubble}>
        <div>{message.content}</div>
        {message.sources && message.sources.length > 0 && (
          <Sources sources={message.sources} />
        )}
      </div>
    </div>
  );
}

interface SourcesProps {
  sources: ChatSource[];
}

/**
 * Source citations display.
 */
function Sources({ sources }: SourcesProps) {
  return (
    <div className={styles.sources}>
      <div className={styles.sourcesLabel}>Sources</div>
      <div className={styles.sourcesList}>
        {sources.slice(0, 3).map((source, index) => (
          <a
            key={index}
            href={`/docs/${source.chapterId}`}
            className={styles.sourceChip}
            title={`${source.moduleId} - ${source.section}`}
          >
            {source.section}
          </a>
        ))}
      </div>
    </div>
  );
}

/**
 * Typing indicator for loading state.
 */
export function TypingIndicator() {
  return (
    <div className={`${styles.message} ${styles.messageAssistant}`}>
      <div className={styles.messageAvatar}>🤖</div>
      <div className={`${styles.messageBubble} ${styles.typingIndicator}`}>
        <div className={styles.typingDot} />
        <div className={styles.typingDot} />
        <div className={styles.typingDot} />
      </div>
    </div>
  );
}
