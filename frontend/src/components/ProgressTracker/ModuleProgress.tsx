import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

interface ModuleProgressProps {
  moduleId: string;
  title: string;
  totalChapters: number;
  completedChapters: number;
  className?: string;
}

/**
 * Module progress component showing completion status.
 */
export function ModuleProgress({
  moduleId,
  title,
  totalChapters,
  completedChapters,
  className,
}: ModuleProgressProps): JSX.Element {
  const progressPercent = totalChapters > 0
    ? Math.round((completedChapters / totalChapters) * 100)
    : 0;

  const isComplete = completedChapters >= totalChapters;

  return (
    <div className={clsx(styles.moduleProgress, className)}>
      <div className={styles.moduleHeader}>
        <span className={styles.moduleTitle}>{title}</span>
        <span className={styles.moduleStatus}>
          {completedChapters}/{totalChapters} chapters
        </span>
      </div>
      <div className={styles.progressBarContainer}>
        <div
          className={clsx(
            styles.progressBar,
            isComplete && styles.progressComplete
          )}
          style={{ width: `${progressPercent}%` }}
          role="progressbar"
          aria-valuenow={progressPercent}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${title} progress: ${progressPercent}%`}
        />
      </div>
      {isComplete && (
        <span className={styles.completeIndicator} aria-label="Module complete">
          ✓
        </span>
      )}
    </div>
  );
}

export default ModuleProgress;
