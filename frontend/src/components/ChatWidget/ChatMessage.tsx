import Link from '@docusaurus/Link';
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
        <div className={styles.messageText}>{message.content}</div>
        {message.sources && message.sources.length > 0 && (
          <Sources sources={message.sources} />
        )}
        {message.mode && (
          <div className={styles.modeLabel}>
            {message.mode === 'gemini'
              ? 'Answered by Gemini from retrieved textbook passages'
              : 'Answered in your browser from the textbook — quoted sentences, no AI model'}
          </div>
        )}
      </div>
    </div>
  );
}

interface SourcesProps {
  sources: ChatSource[];
}

/** Several citations can point at one section; show it once with all its numbers. */
function dedupe(sources: ChatSource[]): { source: ChatSource; labels: string }[] {
  const byUrl = new Map<string, { source: ChatSource; nums: number[] }>();
  sources.forEach((source, i) => {
    const key = source.url ?? source.chapterId;
    const entry = byUrl.get(key) ?? { source, nums: [] };
    entry.nums.push(i + 1);
    byUrl.set(key, entry);
  });
  return [...byUrl.values()].map(({ source, nums }) => ({ source, labels: nums.map((n) => `[${n}]`).join('') }));
}

/**
 * Source citations display.
 */
function Sources({ sources }: SourcesProps) {
  return (
    <div className={styles.sources}>
      <div className={styles.sourcesLabel}>Sources</div>
      <div className={styles.sourcesList}>
        {dedupe(sources.slice(0, 3)).map(({ source, labels }, index) => (
          // Client-side navigation keeps the conversation open while the reader jumps to a source.
          <Link
            key={index}
            to={`/${source.url ?? `docs/${source.chapterId}`}`}
            className={styles.sourceChip}
            title={`${source.moduleId} - ${source.section}`}
          >
            {labels} {source.section}
          </Link>
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
