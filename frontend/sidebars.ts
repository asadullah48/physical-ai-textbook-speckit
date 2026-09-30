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
      items: [
        'module-2-ros2/index',
        'module-2-ros2/ros2-architecture',
        'module-2-ros2/services-actions-parameters',
        'module-2-ros2/urdf-tf2-launch',
      ],
    },
    {
      type: 'category',
      label: 'Module 3: Simulation',
      items: [
        'module-3-simulation/index',
        'module-3-simulation/gazebo-fundamentals',
        'module-3-simulation/sensor-simulation',
        'module-3-simulation/sim-to-real',
      ],
    },
    {
      type: 'category',
      label: 'Module 4: NVIDIA Isaac',
      items: [
        'module-4-isaac/index',
        'module-4-isaac/isaac-sim-and-usd',
        'module-4-isaac/isaac-ros-perception',
        'module-4-isaac/navigation-and-locomotion',
      ],
    },
    {
      type: 'category',
      label: 'Module 5: VLA Systems',
      items: [
        'module-5-vla/index',
        'module-5-vla/vla-architecture',
        'module-5-vla/voice-to-action',
        'module-5-vla/llm-task-planning',
      ],
    },
    {
      type: 'category',
      label: 'Instructor Guide',
      items: ['instructor-guide/course-breakdown'],
    },
  ],
};

export default sidebars;
