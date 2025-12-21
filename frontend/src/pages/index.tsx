import React from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import styles from './index.module.css';

interface Module {
  id: string;
  title: string;
  description: string;
  weeks: string;
  link: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
}

const MODULES: Module[] = [
  {
    id: 'module-1',
    title: 'Introduction to Physical AI',
    description:
      'Foundations of embodied intelligence, sensor systems (LiDAR, cameras, IMUs), and humanoid advantages.',
    weeks: 'Weeks 1-2',
    link: '/docs/module-1-intro/',
    difficulty: 'beginner',
  },
  {
    id: 'module-2',
    title: 'ROS 2 Fundamentals',
    description:
      'Robot Operating System 2 concepts: nodes, topics, services, actions, and URDF for humanoid robots.',
    weeks: 'Weeks 3-5',
    link: '/docs/module-2-ros2/',
    difficulty: 'intermediate',
  },
  {
    id: 'module-3',
    title: 'Simulation Environments',
    description:
      'Gazebo physics simulation, Unity rendering, and sensor simulation for safe robot development.',
    weeks: 'Weeks 6-7',
    link: '/docs/module-3-simulation/',
    difficulty: 'intermediate',
  },
  {
    id: 'module-4',
    title: 'NVIDIA Isaac Platform',
    description:
      'Isaac Sim, Isaac ROS with VSLAM, and Nav2 path planning for bipedal locomotion.',
    weeks: 'Weeks 8-10',
    link: '/docs/module-4-isaac/',
    difficulty: 'advanced',
  },
  {
    id: 'module-5',
    title: 'Vision-Language-Action Systems',
    description:
      'Voice-to-action pipelines, LLM cognitive planning, and capstone project.',
    weeks: 'Weeks 11-13',
    link: '/docs/module-5-vla/',
    difficulty: 'advanced',
  },
];

function ModuleCard({ module }: { module: Module }): JSX.Element {
  return (
    <div className={styles.moduleCard}>
      <div className={styles.moduleHeader}>
        <span className={clsx(styles.difficulty, styles[module.difficulty])}>
          {module.difficulty}
        </span>
        <span className={styles.weeks}>{module.weeks}</span>
      </div>
      <h3 className={styles.moduleTitle}>{module.title}</h3>
      <p className={styles.moduleDescription}>{module.description}</p>
      <Link className={styles.moduleLink} to={module.link}>
        Start Learning →
      </Link>
    </div>
  );
}

function HomepageHeader(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();

  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <div className="container">
        <h1 className={styles.heroTitle}>{siteConfig.title}</h1>
        <p className={styles.heroSubtitle}>{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className={clsx('button button--primary button--lg', styles.heroButton)}
            to="/docs/"
          >
            Start Learning
          </Link>
          <Link
            className={clsx(
              'button button--secondary button--lg',
              styles.heroButton
            )}
            to="/docs/module-1-intro/what-is-physical-ai"
          >
            Module 1: Introduction
          </Link>
        </div>
      </div>
    </header>
  );
}

function CourseOverview(): JSX.Element {
  return (
    <section className={styles.courseOverview}>
      <div className="container">
        <h2 className={styles.sectionTitle}>Course Modules</h2>
        <p className={styles.sectionDescription}>
          A 13-week comprehensive curriculum covering the foundations of Physical AI
          and humanoid robotics.
        </p>
        <div className={styles.modulesGrid}>
          {MODULES.map((module) => (
            <ModuleCard key={module.id} module={module} />
          ))}
        </div>
      </div>
    </section>
  );
}

function Features(): JSX.Element {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className={styles.featuresGrid}>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>📚</div>
            <h3>Comprehensive Content</h3>
            <p>
              5 modules with 20+ chapters covering everything from sensor systems
              to LLM-based cognitive planning.
            </p>
          </div>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>💻</div>
            <h3>Hands-on Code</h3>
            <p>
              Every concept includes working Python code examples you can run,
              modify, and learn from.
            </p>
          </div>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>🤖</div>
            <h3>AI Assistant</h3>
            <p>
              Get help anytime with our AI chatbot trained on the textbook content.
              Select any text to ask questions.
            </p>
          </div>
          <div className={styles.feature}>
            <div className={styles.featureIcon}>📈</div>
            <h3>Track Progress</h3>
            <p>
              Monitor your learning journey with progress tracking across all
              modules and exercises.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): JSX.Element {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout
      title={siteConfig.title}
      description="Physical AI & Humanoid Robotics - A comprehensive textbook for Panaversity"
    >
      <HomepageHeader />
      <main>
        <CourseOverview />
        <Features />
      </main>
    </Layout>
  );
}
