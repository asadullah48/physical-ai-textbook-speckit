import React, { useEffect, useState } from 'react';
import Layout from '@theme/Layout';
import Link from '@docusaurus/Link';
import styles from './index.module.css';
import { useProgress, ProgressSummary, ContentProgress } from '../hooks/useProgress';

interface ModuleProgressData {
  moduleId: string;
  title: string;
  totalChapters: number;
  completedChapters: number;
  totalExercises: number;
  completedExercises: number;
  overallProgress: number;
}

const MODULE_INFO: Record<string, { title: string; link: string }> = {
  'module-1': { title: 'Introduction to Physical AI', link: '/docs/module-1-intro/' },
  'module-2': { title: 'ROS 2 Fundamentals', link: '/docs/module-2-ros2/' },
  'module-3': { title: 'Simulation Environments', link: '/docs/module-3-simulation/' },
  'module-4': { title: 'NVIDIA Isaac Platform', link: '/docs/module-4-isaac/' },
  'module-5': { title: 'Vision-Language-Action Systems', link: '/docs/module-5-vla/' },
};

function ProgressBar({ percent }: { percent: number }): JSX.Element {
  return (
    <div className={styles.progressBar}>
      <div
        className={styles.progressFill}
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}

function ModuleProgressCard({ module }: { module: ModuleProgressData }): JSX.Element {
  const info = MODULE_INFO[module.moduleId] || { title: module.moduleId, link: '#' };

  return (
    <div className={styles.moduleCard}>
      <div className={styles.moduleHeader}>
        <h3 className={styles.moduleTitle}>{info.title}</h3>
        <span className={styles.progressPercent}>{module.overallProgress.toFixed(0)}%</span>
      </div>
      <ProgressBar percent={module.overallProgress} />
      <div className={styles.moduleStats}>
        <span>Chapters: {module.completedChapters}/{module.totalChapters}</span>
        <span>Exercises: {module.completedExercises}/{module.totalExercises}</span>
      </div>
      <Link className={styles.moduleLink} to={info.link}>
        {module.overallProgress > 0 ? 'Continue →' : 'Start →'}
      </Link>
    </div>
  );
}

function SummaryCards({ summary }: { summary: ProgressSummary }): JSX.Element {
  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  return (
    <div className={styles.summaryCards}>
      <div className={styles.summaryCard}>
        <div className={styles.summaryValue}>{summary.modulesCompleted}</div>
        <div className={styles.summaryLabel}>Modules Completed</div>
      </div>
      <div className={styles.summaryCard}>
        <div className={styles.summaryValue}>{summary.chaptersCompleted}</div>
        <div className={styles.summaryLabel}>Chapters Completed</div>
      </div>
      <div className={styles.summaryCard}>
        <div className={styles.summaryValue}>{summary.exercisesCompleted}</div>
        <div className={styles.summaryLabel}>Exercises Completed</div>
      </div>
      <div className={styles.summaryCard}>
        <div className={styles.summaryValue}>{formatTime(summary.totalReadingTimeSeconds)}</div>
        <div className={styles.summaryLabel}>Total Study Time</div>
      </div>
    </div>
  );
}

function ResumeSection({ lastContentId }: { lastContentId?: string }): JSX.Element | null {
  if (!lastContentId) return null;

  return (
    <div className={styles.resumeSection}>
      <h3>Continue Where You Left Off</h3>
      <Link className="button button--primary" to={`/docs/${lastContentId}`}>
        Resume: {lastContentId}
      </Link>
    </div>
  );
}

export default function Dashboard(): JSX.Element {
  const { summary, progress, isLoading, error, refreshProgress } = useProgress();
  const [moduleProgress, setModuleProgress] = useState<ModuleProgressData[]>([]);

  // Calculate module progress from individual progress items
  useEffect(() => {
    const modules: Map<string, ModuleProgressData> = new Map();

    // Initialize modules
    Object.keys(MODULE_INFO).forEach((moduleId) => {
      modules.set(moduleId, {
        moduleId,
        title: MODULE_INFO[moduleId].title,
        totalChapters: 4, // Default, would be fetched from API
        completedChapters: 0,
        totalExercises: 3,
        completedExercises: 0,
        overallProgress: 0,
      });
    });

    // Aggregate progress
    progress.forEach((item, contentId) => {
      const moduleMatch = contentId.match(/module-(\d)/);
      if (!moduleMatch) return;

      const moduleId = `module-${moduleMatch[1]}`;
      const module = modules.get(moduleId);
      if (!module) return;

      if (item.contentType === 'chapter' && item.status === 'completed') {
        module.completedChapters++;
      }
      if (item.contentType === 'exercise' && item.status === 'completed') {
        module.completedExercises++;
      }
    });

    // Calculate overall progress
    modules.forEach((module) => {
      const chapterProgress = module.totalChapters > 0
        ? (module.completedChapters / module.totalChapters) * 70
        : 0;
      const exerciseProgress = module.totalExercises > 0
        ? (module.completedExercises / module.totalExercises) * 30
        : 0;
      module.overallProgress = chapterProgress + exerciseProgress;
    });

    setModuleProgress(Array.from(modules.values()));
  }, [progress]);

  if (isLoading) {
    return (
      <Layout title="Dashboard" description="Your learning progress dashboard">
        <main className="container margin-vert--lg">
          <div className={styles.loading}>Loading your progress...</div>
        </main>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard" description="Your learning progress dashboard">
      <main className="container margin-vert--lg">
        <div className={styles.dashboardHeader}>
          <h1>Your Learning Dashboard</h1>
          <button
            className="button button--secondary button--sm"
            onClick={() => refreshProgress()}
          >
            Refresh
          </button>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        {summary && (
          <>
            <SummaryCards summary={summary} />
            <ResumeSection lastContentId={summary.lastContentId} />
          </>
        )}

        <section className={styles.modulesSection}>
          <h2>Module Progress</h2>
          <div className={styles.modulesGrid}>
            {moduleProgress.map((module) => (
              <ModuleProgressCard key={module.moduleId} module={module} />
            ))}
          </div>
        </section>

        <section className={styles.actionsSection}>
          <h2>Quick Actions</h2>
          <div className={styles.actionsGrid}>
            <Link className="button button--primary button--lg" to="/docs/">
              Browse All Content
            </Link>
            <Link
              className="button button--secondary button--lg"
              to="/docs/module-1-intro/01-what-is-physical-ai"
            >
              Start from Beginning
            </Link>
          </div>
        </section>
      </main>
    </Layout>
  );
}
