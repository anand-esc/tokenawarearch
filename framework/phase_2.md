# Phase 2: Intelligent Routing Gatekeeper (The Brain)

## Overview
Phase 2 serves as the central intelligence node of the Self-Healing Token Aware Multi-Agent Architecture. After Phase 1 highly compresses the raw incident logs, Phase 2 evaluates the payload to determine the severity, complexity, and maximum allowable API spend (Token Budgeting). It then routes the incident to the most cost-effective and capable language model.

## Pipeline Architecture
Phase 2 consists of three distinct modules located in `src/router/`:

### 1. Incident Classifier (`classifier.py`)
- **Purpose**: Evaluates the compressed payload to gauge Severity (1-10) and Complexity (1-10).
- **Implementation**: Uses a local, fast zero-shot classification model (`cross-encoder/nli-distilroberta-base`) via HuggingFace `transformers`. By running locally, we determine the severity and complexity *without* spending any external API budget.

### 2. Token Budgeting (`budgeting.py`)
- **Purpose**: Translates the severity score into a strict financial token limit.
- **Implementation**: Calculates the maximum allowed spend in USD and the corresponding token limit. Low severity incidents are strictly assigned a $0.00 budget, forcing the system to resolve them via free local SLMs. High severity incidents are granted a higher budget to utilize frontier cloud LLMs if needed.

### 3. Global Dynamic Router (`dynamic_router.py`)
- **Purpose**: The final ingress point that makes the routing decision.
- **Implementation**: It takes the outputs from the Classifier and the Budgeter.
  - If the budget is restricted to $0.00, it forces routing to the `LOCAL_SLM`.
  - If the complexity is high (>= 7) AND there is available budget, it routes to the `CLOUD_LLM`.
  - Otherwise, it defaults to the `LOCAL_SLM` to preserve API budget.

This logic ensures that expensive cloud models are only ever invoked when absolutely necessary to resolve critical, highly complex outages.
