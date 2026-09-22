# Phase 2: Intelligent Routing

## Overview
Phase 2 determines the most cost-efficient execution model for resolving the incident. It operates entirely locally to prevent baseline API costs.

## Architecture and Workflow

1.  **Classification:** The compressed context is evaluated by a fine-tuned DistilRoBERTa model. This zero-API regression model outputs explicit scores for both the Severity (1-10) and Complexity (1-10) of the incident.
2.  **Budget Allocation:** The Severity score is mapped to a strict financial limit. Minor anomalies (Severity 1-3) receive a $0.00 budget, strictly confining resolution to local resources. Critical outages unlock higher API limits.
3.  **Reinforcement Learning Router:** The Q-Learning matrix evaluates the (Severity, Complexity) state array against historical policies. The Tabular RL agent selects between three routing paths: Local SLM, Cloud LLM, or Hybrid Orchestration, optimizing for maximum token efficiency without sacrificing resolution accuracy.
