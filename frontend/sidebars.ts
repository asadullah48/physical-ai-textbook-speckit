import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Module 1: Introduction to Physical AI',
      items: [
        'module-1-intro/what-is-physical-ai',
        'module-1-intro/sensor-systems',
        'module-1-intro/embodied-intelligence',
        'module-1-intro/humanoid-advantages',
      ],
    },
    {
      type: 'category',
      label: 'Module 2: ROS 2 Fundamentals',
      items: ['module-2-ros2/index'],
    },
    {
      type: 'category',
      label: 'Module 3: Simulation',
      items: ['module-3-simulation/index'],
    },
    {
      type: 'category',
      label: 'Module 4: NVIDIA Isaac',
      items: ['module-4-isaac/index'],
    },
    {
      type: 'category',
      label: 'Module 5: VLA Systems',
      items: ['module-5-vla/index'],
    },
    {
      type: 'category',
      label: 'Instructor Guide',
      items: ['instructor-guide/course-breakdown'],
    },
  ],
};

export default sidebars;
