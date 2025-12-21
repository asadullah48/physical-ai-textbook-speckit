import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

/**
 * Sidebar configuration for the Physical AI Textbook.
 *
 * Organized by module with collapsible sections for each chapter.
 * Each module corresponds to ~2-3 weeks of the 13-week course.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    {
      type: 'doc',
      id: 'intro',
      label: 'Introduction',
    },
    {
      type: 'category',
      label: 'Module 1: Introduction to Physical AI',
      link: {
        type: 'generated-index',
        title: 'Module 1: Introduction to Physical AI',
        description:
          'Foundations of embodied intelligence, sensor systems, and humanoid robotics advantages.',
        keywords: ['physical-ai', 'sensors', 'embodied-intelligence', 'humanoid'],
      },
      items: [
        'module-1-intro/01-what-is-physical-ai',
        'module-1-intro/02-sensor-systems',
        'module-1-intro/03-embodied-intelligence',
        'module-1-intro/04-humanoid-advantages',
      ],
    },
    {
      type: 'category',
      label: 'Module 2: ROS 2 Fundamentals',
      link: {
        type: 'generated-index',
        title: 'Module 2: ROS 2 Fundamentals',
        description:
          'Learn ROS 2 nodes, topics, services, actions, and URDF for humanoid robots.',
        keywords: ['ros2', 'nodes', 'topics', 'urdf', 'robotics'],
      },
      items: [
        'module-2-ros2/index',
      ],
    },
    {
      type: 'category',
      label: 'Module 3: Simulation Environments',
      link: {
        type: 'generated-index',
        title: 'Module 3: Simulation Environments',
        description:
          'Gazebo physics simulation, Unity rendering, and sensor simulation.',
        keywords: ['gazebo', 'unity', 'simulation', 'physics'],
      },
      items: [
        'module-3-simulation/index',
      ],
    },
    {
      type: 'category',
      label: 'Module 4: NVIDIA Isaac Platform',
      link: {
        type: 'generated-index',
        title: 'Module 4: NVIDIA Isaac Platform',
        description:
          'Isaac Sim, Isaac ROS with VSLAM, and Nav2 path planning for bipedal locomotion.',
        keywords: ['nvidia', 'isaac', 'vslam', 'nav2', 'locomotion'],
      },
      items: [
        'module-4-isaac/index',
      ],
    },
    {
      type: 'category',
      label: 'Module 5: Vision-Language-Action Systems',
      link: {
        type: 'generated-index',
        title: 'Module 5: Vision-Language-Action Systems',
        description:
          'Voice-to-action pipelines, LLM cognitive planning, and capstone project.',
        keywords: ['vla', 'llm', 'voice', 'cognitive', 'capstone'],
      },
      items: [
        'module-5-vla/index',
      ],
    },
  ],
};

export default sidebars;
