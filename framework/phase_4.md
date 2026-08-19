# Phase 4: Continuous Learning & Feedback Loop

## Overview
A static SRE architecture will eventually become obsolete as infrastructure evolves. Phase 4 introduces a self-improving Reinforcement Learning (RL) loop to ensure the architecture continuously adapts to new types of incidents while aggressively minimizing API costs.

## Pipeline Architecture
Phase 4 resides in `src/evaluation/`. It is triggered *after* the Action Layer executes a remediation script.

### 1. Incident Evaluator (`evaluator.py`)
- **Purpose**: Acts as an "LLM-as-a-Judge" to determine if the executed script successfully resolved the incident (e.g., by checking if the 503 error rate dropped back to 0).
- **Implementation**: It calculates a numerical Reward Signal based on both operational success and financial efficiency. 
  - Perfect outcome (Local SLM succeeds for $0.00): **+10 Reward**
  - Acceptable outcome (Cloud LLM succeeds but costs API credits): **+4 Reward**
  - Bad outcome (Failure): **Negative Penalty**

### 2. Tabular Q-Learning Router (`q_learning.py`)
- **Purpose**: Mathematically optimizes the dynamic routing decision over time.
- **Implementation**: We use Tabular Q-Learning due to the discrete nature of our state space (Severity 1-10, Complexity 1-10) and action space (0 = SLM, 1 = Cloud LLM). The system maintains a `q_table.pkl` matrix. As it receives rewards from the Evaluator, it updates its Q-values using the Bellman equation.
- **Result**: Over thousands of incidents, the Q-Table mathematically converges on the absolute most cost-efficient routing strategy for any given severity and complexity.

## Pre-Training Simulation
To prevent the agent from making costly mistakes on "Day 1" of production, the architecture includes a pre-training simulation (`test_phase4.py`). This script generates thousands of synthetic incidents, simulating how an SLM struggles with high complexity and succeeds at low complexity. By running this script, the Q-Table is populated with baseline intelligence before it ever touches live infrastructure.
