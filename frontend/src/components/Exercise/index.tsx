import React, { useState } from 'react';
import { DifficultyBadge, type DifficultyLevel } from './DifficultyBadge';

export interface ExerciseProps {
  /** Exercise title */
  title: string;
  /** Difficulty level */
  difficulty: DifficultyLevel;
  /** Estimated time in minutes */
  estimatedTime?: number;
  /** Exercise description/instructions */
  children: React.ReactNode;
  /** Optional hint text */
  hint?: string;
  /** Exercise type */
  type?: 'coding' | 'conceptual' | 'hands-on';
}

/**
 * Exercise component for displaying structured exercises in chapters.
 */
export function Exercise({
  title,
  difficulty,
  estimatedTime,
  children,
  hint,
  type = 'conceptual',
}: ExerciseProps) {
  const [showHint, setShowHint] = useState(false);

  const typeLabel = {
    coding: 'Coding Exercise',
    conceptual: 'Conceptual Exercise',
    'hands-on': 'Hands-on Lab',
  };

  return (
    <div
      style={{
        margin: '24px 0',
        padding: '20px',
        border: '1px solid var(--ifm-color-emphasis-300)',
        borderRadius: '8px',
        backgroundColor: 'var(--ifm-background-surface-color)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
          paddingBottom: '12px',
          borderBottom: '1px solid var(--ifm-color-emphasis-200)',
        }}
      >
        <span
          style={{
            fontSize: '11px',
            color: 'var(--ifm-color-emphasis-600)',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            fontWeight: 600,
          }}
        >
          {typeLabel[type]}
        </span>
        <DifficultyBadge level={difficulty} />
        {estimatedTime && (
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '12px',
              color: 'var(--ifm-color-emphasis-600)',
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            ~{estimatedTime} min
          </span>
        )}
      </div>

      {/* Title */}
      <h4
        style={{
          margin: '0 0 12px',
          fontSize: '18px',
          fontWeight: 600,
          color: 'var(--ifm-heading-color)',
        }}
      >
        {title}
      </h4>

      {/* Content */}
      <div
        style={{
          fontSize: '15px',
          lineHeight: '1.6',
          color: 'var(--ifm-font-color-base)',
        }}
      >
        {children}
      </div>

      {/* Hint */}
      {hint && (
        <div style={{ marginTop: '16px' }}>
          <button
            onClick={() => setShowHint(!showHint)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              background: 'transparent',
              border: '1px solid var(--ifm-color-emphasis-300)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              color: 'var(--ifm-color-primary)',
              fontFamily: 'inherit',
            }}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            {showHint ? 'Hide Hint' : 'Show Hint'}
          </button>

          {showHint && (
            <div
              style={{
                marginTop: '12px',
                padding: '12px 16px',
                background: 'var(--ifm-color-primary-lightest)',
                borderRadius: '6px',
                borderLeft: '3px solid var(--ifm-color-primary)',
                fontSize: '14px',
                color: 'var(--ifm-color-emphasis-800)',
              }}
            >
              <strong style={{ display: 'block', marginBottom: '4px' }}>Hint:</strong>
              {hint}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Re-export for convenience
export { DifficultyBadge, type DifficultyLevel };
