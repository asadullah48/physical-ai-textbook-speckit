import React, { useState, useCallback } from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

interface CopyButtonProps {
  code: string;
  className?: string;
}

/**
 * Copy button for code blocks.
 *
 * Provides visual feedback on copy success/failure.
 */
export function CopyButton({ code, className }: CopyButtonProps): JSX.Element {
  const [isCopied, setIsCopied] = useState(false);
  const [isError, setIsError] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setIsCopied(true);
      setIsError(false);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
      setIsError(true);
      setTimeout(() => setIsError(false), 2000);
    }
  }, [code]);

  return (
    <button
      type="button"
      aria-label={isCopied ? 'Copied!' : 'Copy code to clipboard'}
      title={isCopied ? 'Copied!' : 'Copy'}
      className={clsx(
        styles.copyButton,
        isCopied && styles.copied,
        isError && styles.error,
        className
      )}
      onClick={handleCopy}
    >
      <span className={styles.copyIcon}>
        {isCopied ? (
          // Checkmark icon
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path
              fill="currentColor"
              d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"
            />
          </svg>
        ) : isError ? (
          // X icon
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path
              fill="currentColor"
              d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"
            />
          </svg>
        ) : (
          // Copy icon
          <svg viewBox="0 0 24 24" width="16" height="16">
            <path
              fill="currentColor"
              d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"
            />
          </svg>
        )}
      </span>
      <span className={styles.copyText}>
        {isCopied ? 'Copied!' : isError ? 'Failed' : 'Copy'}
      </span>
    </button>
  );
}

export default CopyButton;
