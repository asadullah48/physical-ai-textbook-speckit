import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Physical AI & Humanoid Robotics',
  tagline: 'A comprehensive textbook for the Panaversity Physical AI course',
  favicon: 'img/favicon.ico',

  // Production URL
  url: 'https://physical-ai-textbook.example.com',
  baseUrl: '/',

  // GitHub Pages deployment config
  organizationName: 'panaversity',
  projectName: 'physical-ai-textbook',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Internationalization
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/panaversity/physical-ai-textbook/tree/main/',
          showLastUpdateTime: true,
          showLastUpdateAuthor: true,
        },
        blog: false, // Disable blog
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    // Social card image
    image: 'img/social-card.jpg',

    // Announcement bar (optional)
    announcementBar: {
      id: 'course_announcement',
      content:
        'Welcome to the Panaversity Physical AI & Humanoid Robotics course textbook!',
      backgroundColor: '#4f46e5',
      textColor: '#ffffff',
      isCloseable: true,
    },

    navbar: {
      title: 'Physical AI',
      logo: {
        alt: 'Physical AI Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'tutorialSidebar',
          position: 'left',
          label: 'Textbook',
        },
        {
          to: '/dashboard',
          label: 'Dashboard',
          position: 'left',
        },
        {
          href: 'https://github.com/panaversity/physical-ai-textbook',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },

    footer: {
      style: 'dark',
      links: [
        {
          title: 'Learn',
          items: [
            {
              label: 'Module 1: Introduction',
              to: '/docs/module-1-intro/',
            },
            {
              label: 'Module 2: ROS 2',
              to: '/docs/module-2-ros2/',
            },
            {
              label: 'Module 3: Simulation',
              to: '/docs/module-3-simulation/',
            },
          ],
        },
        {
          title: 'Advanced',
          items: [
            {
              label: 'Module 4: Isaac Platform',
              to: '/docs/module-4-isaac/',
            },
            {
              label: 'Module 5: VLA Systems',
              to: '/docs/module-5-vla/',
            },
          ],
        },
        {
          title: 'Community',
          items: [
            {
              label: 'Panaversity',
              href: 'https://panaversity.com',
            },
            {
              label: 'Discord',
              href: 'https://discord.gg/panaversity',
            },
            {
              label: 'GitHub',
              href: 'https://github.com/panaversity',
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Panaversity. Built with Docusaurus.`,
    },

    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'bash', 'yaml', 'json', 'xml'],
    },

    // Table of contents depth
    tableOfContents: {
      minHeadingLevel: 2,
      maxHeadingLevel: 4,
    },

    // Color mode
    colorMode: {
      defaultMode: 'light',
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
  } satisfies Preset.ThemeConfig,

  // Custom fields for environment variables
  customFields: {
    apiUrl: process.env.DOCUSAURUS_API_URL || 'http://localhost:8000',
  },
};

export default config;
