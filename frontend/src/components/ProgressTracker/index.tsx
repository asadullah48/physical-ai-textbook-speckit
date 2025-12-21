import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

interface ProgressTrackerProps {
  className?: string;
}

/**
 * Progress tracker component for displaying user progress.
 *
 * Shows overall course progress and links to resume reading.
 * Full functionality implemented in User Story 6.
 */
export function ProgressTracker({ className }: ProgressTrackerProps): JSX.Element {
  // TODO: Integrate with useProgress hook and API in US6

  return (
    <div className={clsx(styles.progressTracker, className)}>
      <div className={styles.header}>
        <h3 className={styles.title}>Your Progress</h3>
      </div>
      <div className={styles.content}>
        <p className={styles.placeholder}>
          Sign in to track your progress through the course.
        </p>
      </div>
    </div>
  );
}

export default ProgressTracker;
