# Phase 3: Multi-Agent Model Execution & Action Layer

## Overview
Phase 3 bridges the gap between AI theory and infrastructure reality. Once the Phase 2 router has selected a model based on complexity and budget, Phase 3 assigns an optimal persona (e.g., DBA or Networking Expert) to the LLM/SLM, queries it for a fix, and strictly evaluates the generated code for safety before execution.

## Pipeline Architecture
Phase 3 is split into two directories: `src/execution/` and `src/action_layer/`.

### 1. Model Factory (`model_factory.py`)
- **Purpose**: Connects to the appropriate Language Model.
- **Implementation**: Uses `LangChain` to securely interface with models. `LOCAL_SLM` connects to Ollama instances (e.g., Qwen), while `CLOUD_LLM` connects to frontier models via their APIs (e.g., Google Gemini).

### 2. Agent Scheduler (`agent_scheduler.py`)
- **Purpose**: Dynamically assigns a persona based on the incident context.
- **Implementation**: Instead of a generic query, the scheduler scans the payload for keywords. If it detects "SQL", it spins up the Database Administrator persona. It then runs inference on the selected model to output raw, actionable bash commands.

### 3. Risk Assessor (`risk_assessor.py`)
- **Purpose**: The primary safety net preventing destructive AI actions.
- **Implementation**: Before any AI-generated code is executed, this module scans the script for highly destructive regular expression patterns (`rm -rf`, `drop table`, `reboot`, `sudo`). It calculates a rigid risk score. Scripts exceeding the risk threshold are aborted immediately.

### 4. Mock Executor (`executor.py`)
- **Purpose**: Safely simulates the execution of the bash script on the host machine.
- **Implementation**: 
  - **Auto-Remediation**: If the risk score is low, it proceeds with execution (simulated).
  - **Human-in-the-Loop**: If the risk score is high, it triggers the "SRE Dashboard" workflow, printing out a structured ticket requiring human review before proceeding.
