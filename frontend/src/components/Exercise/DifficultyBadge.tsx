import React from 'react';

export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

interface DifficultyBadgeProps {
  level: DifficultyLevel;
}

const DIFFICULTY_CONFIG: Record<DifficultyLevel, { label: string; color: string; bgColor: string }> = {
  beginner: {
    label: 'Beginner',
    color: 'var(--ifm-color-success-darkest)',
    bgColor: 'var(--ifm-color-success-lightest)',
  },
  intermediate: {
    label: 'Intermediate',
    color: 'var(--ifm-color-warning-darkest)',
    bgColor: 'var(--ifm-color-warning-lightest)',
  },
  advanced: {
    label: 'Advanced',
    color: 'var(--ifm-color-danger-darkest)',
    bgColor: 'var(--ifm-color-danger-lightest)',
  },
};

/**
 * Badge component to display exercise difficulty level.
 */
export function DifficultyBadge({ level }: DifficultyBadgeProps) {
  const config = DIFFICULTY_CONFIG[level] || DIFFICULTY_CONFIG.beginner;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '4px 10px',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: 600,
        color: config.color,
        backgroundColor: config.bgColor,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}
    >
      {config.label}
    </span>
  );
}
