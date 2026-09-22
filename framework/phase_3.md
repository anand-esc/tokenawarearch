# Phase 3: Multi-Agent Model Execution

## Overview
Phase 3 is responsible for generating the actionable remediation script. The task is delegated dynamically based on the routing decision from Phase 2.

## Execution Modalities

1.  **Local SLM Agent:** Deployed via Ollama (e.g., Qwen 1.5B). This model handles low-complexity, routine tasks (e.g., restarting standard pods or clearing caches). It operates securely within the local infrastructure at zero variable cost.
2.  **Cloud LLM Agent:** Utilizes frontier cloud APIs (e.g., GPT-4 or Nemotron). This agent is reserved for maximum-complexity incidents requiring deep, cross-service diagnostic reasoning and multi-step remediation logic.
3.  **Hybrid Orchestrator:** Designed for medium-complexity incidents. The Local SLM acts as an orchestrator, parsing routine boilerplate data (such as extracting IP addresses or Pod names) locally. Only the abstracted, highly specific diagnostic query is forwarded to the Cloud LLM. The Local SLM subsequently stitches the API response into a final executable script, drastically reducing token consumption.
