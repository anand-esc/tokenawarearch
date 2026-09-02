# Token-Aware Multi-Agent Architecture: Interactive Frontend

This directory contains the React-based interactive frontend for the Self-Healing Token-Aware Multi-Agent Architecture. It serves as a visual control plane to interface with the core Python backend, demonstrating the pipeline's capabilities in real-time.

## Features

- **Real-Time Log Ingestion & Routing Analysis**: Submit raw infrastructure logs and monitor the pipeline's routing decisions (Phase 1 and Phase 2) in real-time.
- **Dynamic Model Configuration**: Configure the Local Small Language Model (SLM) endpoint and Cloud Large Language Model (LLM) API keys directly from the UI. The system supports direct integration with local instances of Ollama.
- **Transparency Traces**: Inspect exactly why the routing agent made a decision. View detailed breakdowns of context reduction percentages, risk scores, calculated severity, and estimated cost savings per query.
- **Interactive Q-Learning Heatmap**: A live visualization of the Tabular Q-Learning state matrix mapping Severity vs. Complexity. The heatmap updates as the system issues rewards and updates its routing policy.
- **Human-in-the-Loop Simulation**: Configurable agent autonomy controls. Set the system to Ask Everytime to pause execution at the routing phase, allowing human operators to manually approve or override the agent's model selection.
- **Session Persistence**: Chat history and metrics are saved locally in the browser, allowing operators to maintain multiple simulated incident investigations seamlessly.

## Quick Start Guide

### Prerequisites

Ensure you have Node.js (v18+) and npm installed on your system.
The frontend is designed to run in tandem with the primary Python backend.

### 1. Start the Backend Server

Before running the frontend, ensure the FastAPI backend is active. From the root of the repository:

\\ash
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 8000
`
### 2. Install Frontend Dependencies

Navigate to the frontend directory and install the required Node modules:

\\ash
cd frontend
npm install
`
### 3. Start the Development Server

Launch the Vite development server:

\\ash
npm run dev
`
The application will be accessible at http://localhost:5173.

### 4. Configure Models

Upon loading the application, use the top-right configuration panels to initialize your models:
- **Local SLM**: Defaults to http://localhost:11434 for standard Ollama deployments. Click Test to verify the connection.
- **Cloud LLM**: Input your cloud provider API key and click Test to authenticate.

Once both models register as Online, the system is ready to process incident logs.

## Technology Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: TailwindCSS (v4)
- **Icons**: Lucide React
- **Network**: Fetch API against local FastAPI Uvicorn server
