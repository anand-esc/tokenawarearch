# Self-Healing Token Aware Multi-Agent Architecture

## Objective

The objective of this project is to create an advanced Site Reliability Engineering (SRE) automation framework. It aims to ingest massive, noisy incident alerts (like Datadog webhooks or Kubernetes stack traces) and autonomously remediate them using a multi-agent system. 

The core differentiator of this architecture is its Token Awareness. Large Language Models (LLMs) are expensive, and feeding them endless megabytes of raw logs is cost-prohibitive and inefficient. This architecture introduces a highly optimized funnel that shrinks, summarizes, and prunes incident data locally before securely routing it to either a local Small Language Model (SLM) or a cloud-based Frontier LLM, depending on complexity and budget.

## Goals

1.  Cost Efficiency: Drastically reduce API costs by executing pre-processing, summarization, and simple remediations on local hardware using SLMs, reserving cloud LLMs for complex, high-severity issues.
2.  Token Optimization: Prevent context window exhaustion and save budget by aggressively compressing logs and chat histories while preserving semantic meaning.
3.  Self-Healing and Auto-Remediation: Safely execute scripts and fix infrastructure issues autonomously when confidence is high.
4.  Continuous Learning: Implement a feedback loop that evaluates past resolutions and updates routing policy weights, allowing the system to learn when to trust local models versus cloud models.

## Project Phases

### Phase 1: Input Processing & Optimization (The Funnel)

This phase acts as the ingestion point. It heavily compresses chaotic data into a token-efficient payload.
-   Query Rewriting: Normalizes raw logs or JSON webhooks into readable text.
-   Chat History Summarization: Uses local models (like BART) to condense past troubleshooting context.
-   Semantic Chunking: Breaks large stack traces into safe, overlapping chunks.
-   Context Pruning: Uses Sentence Transformers to calculate cosine similarity, dropping redundant log lines.
-   Prompt Compression: Shrinks the payload further by dropping stopwords and filler tokens using LLMLingua.

### Phase 2: Intelligent Routing Gatekeeper (The Brain)

This phase decides where the compressed payload should go.
-   Global Dynamic Routing: The ingress point that distributes the payload based on internal policy weights.
-   BERT Classifier: Evaluates the severity and complexity of the incident.
-   Token Budgeting: Calculates maximum allowable API spend for the incident.
-   Dynamic Model Routing: Decides whether to route the incident to a local SLM (e.g., Qwen 1.5B) for low-complexity issues or a cloud LLM (e.g., GPT-4) for high-complexity issues.

### Phase 3: Multi-Agent Model Execution & Action Layer

This phase handles the actual troubleshooting and remediation.
-   Multi-Agent Scheduling: Coordinates tasks among specialized agents.
-   Action Assessment: Evaluates the generated solution for risk and confidence.
-   Auto-Remediation: Safely executes fixes automatically.
-   SRE Dashboard: Routes risky or destructive fixes to human operators for review and approval.

### Phase 4: Continuous Learning (The Feedback Loop)

This phase handles the Reinforcement Learning aspect.
-   LLM as a Judge: A highly capable LLM reviews the full incident resolution flow and scores the performance.
-   Reinforcement Learning: Generates a reward or penalty based on resolution time, accuracy, and cost.
-   Policy Weight Updates: The RL system feeds these updates back into the Global Dynamic Routing node in Phase 2. This continuous feedback loop teaches the Global Router which incidents can be safely handled by cheaper local SLMs in the future, optimizing long-term costs.

## Architecture and Flow

### Architecture Diagram

![Architecture Diagram](/d:/Self-Healing%20Token%20Aware%20Multi%20Agent%20Architercture/architecture_diagram/architecture_diagram.png)

### Flow Diagram

![Flow Diagram](/d:/Self-Healing%20Token%20Aware%20Multi%20Agent%20Architercture/flow_diagram/flow_diagram.png)

## Reinforcement Learning in Global Routing

The Reinforcement Learning (RL) mechanism connects Phase 4 back to Phase 2. After an incident is resolved (either successfully or unsuccessfully), an "LLM as a Judge" reviews the actions taken. The RL system computes a reward (if the issue was solved quickly and cheaply by an SLM) or a penalty (if the SLM failed and it had to be escalated). 

These rewards and penalties dynamically adjust the weights inside the Global Dynamic Router. Over time, the router learns to trust the local SLM for specific classes of errors that previously required a cloud LLM, creating a continuously self-optimizing and increasingly cost-effective SRE architecture.
