# Self-Healing Token-Aware Multi-Agent Architecture

This repository contains the full enterprise-grade implementation of the Token-Aware Multi-Agent routing architecture for autonomous Site Reliability Engineering (SRE).

## Interactive UI Control Plane

The repository includes a highly polished React/Vite interactive frontend for real-time demonstration of the multi-agent routing pipeline. 

**[See the Frontend README](frontend/README.md)** for features, setup instructions, and deployment details.

## Architecture Phases

### Phase 1: Context Optimization (`src/optimization/`)
Reduces the payload size of incoming Datadog/Slack incident logs before they are fed to any LLM, saving significant API token costs.
* **`pruner.py`**: Uses local `all-MiniLM-L6-v2` embeddings and Cosine Similarity to strip out semantically redundant stack trace frames.
* **`compressor.py`**: Uses `LLMLingua` (or TinyLlama) to semantically compress prompts by stripping stopwords.

### Phase 2: Dynamic Routing (`src/router/`)
Evaluates the optimized payload to determine whether to route the remediation task to a free Local SLM or a highly capable Cloud LLM.
* **`classifier.py`**: A Zero-Shot classifier (`cross-encoder/nli-distilroberta-base`) that scores incident Severity and Complexity instantly without API calls.
* **`budgeting.py`**: Allocates a strict maximum financial API budget based on the Severity score.
* **`dynamic_router.py`**: The central brain that weighs the complexity against the financial budget to make the final routing decision.

### Phase 3: Model Execution (`src/execution/`)
* **`model_factory.py`**: A LangChain-powered factory that seamlessly hot-swaps between executing the Local SLM (`ChatOllama/qwen`) or the Cloud LLM (`ChatGoogleGenerativeAI/gemini-1.5-pro`).

### Phase 4: Continuous Learning (`src/evaluation/`)
* **`q_learning.py`**: A mathematically rigorous Tabular Q-Learning reinforcement loop. It tracks the `(Severity, Complexity)` state space and updates routing policies based on the Bellman equation, continually shifting trust towards the Local SLM to drive down costs.

### Action Layer: Failsafe (`src/action_layer/`)
* **`risk_assessor.py`**: A strict regex-based safety net that intercepts generated Bash scripts, scoring them for destructive commands (e.g., `rm -rf`, `DROP TABLE`). If a script exceeds the `SAFE_RISK_THRESHOLD`, execution is halted and routed to the SRE Dashboard.

---

## 🛠️ Configuration & Testing

### Centralized Config (`src/config.py`)
All critical hyper-parameters (Q-Learning Alpha/Gamma, API limits, similarity thresholds, and safety bounds) are centrally managed and strongly type-hinted here.

### End-to-End Integration Test
To run a full real-time simulation simulating a database timeout across the entire 5-stage pipeline:
```bash
python tests/integration_test.py
```

### SRE Human-in-the-Loop Dashboard
A beautiful, interactive React application that provides LangSmith-style transparency tracing of the agent's thought process, and an SRE Action Center to approve or reject blocked bash scripts.
```bash
cd frontend
npm install
npm run dev
```
