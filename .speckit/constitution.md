# Physical AI Textbook - Project Constitution

## Project Vision
Create a comprehensive, interactive textbook for teaching Physical AI & Humanoid Robotics using Docusaurus, with an embedded RAG chatbot for intelligent Q&A.

## Core Requirements (from Hackathon)
1. **Textbook Platform**: Docusaurus-based, deployed to GitHub Pages
2. **RAG Chatbot**: FastAPI backend with OpenAI Agents SDK
3. **Database**: Neon Serverless Postgres + Qdrant Cloud (free tier)
4. **Content**: Based on PDF course outline (ROS 2, Gazebo, NVIDIA Isaac, VLA)
5. **Selection-based QA**: Chatbot can answer questions about selected text

## Technology Stack
- **Frontend**: Docusaurus (React-based)
- **Backend**: FastAPI (Python)
- **AI**: OpenAI SDK for RAG
- **Vector DB**: Qdrant Cloud
- **SQL DB**: Neon Postgres
- **Deployment**: GitHub Pages (frontend), separate backend deployment

## Development Methodology
- Spec-Kit Plus with slash commands
- Specification-first development
- Modular architecture
- Test before deploy

## Course Modules (5 total)
1. Introduction to Physical AI & Embodied Intelligence
2. ROS 2 Fundamentals - The Robotic Nervous System
3. Simulation Environments - Gazebo & Unity
4. NVIDIA Isaac Platform - AI-Robot Brain
5. Vision-Language-Action (VLA) Systems

## Success Criteria
- ✅ All 5 modules with comprehensive content
- ✅ Working RAG chatbot embedded in site
- ✅ Text selection Q&A functionality
- ✅ Deployed and accessible via URL
- ✅ < 90 second demo video
