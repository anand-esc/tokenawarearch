# Self-Healing Token-Aware Multi-Agent Architecture

## Objective

The objective of this project is to provide an advanced Site Reliability Engineering (SRE) automation framework. It aims to ingest high-volume, noisy incident alerts and autonomously remediate them using a multi-agent system. 

The core differentiator of this architecture is its token-awareness. Large Language Models (LLMs) incur significant API costs, and feeding them unoptimized raw logs is inefficient. This architecture introduces a highly optimized pipeline that shrinks, summarizes, and prunes incident data locally before securely routing it to either a local Small Language Model (SLM) or a cloud-based Frontier LLM, depending on calculated incident complexity and severity.

## Goals

1. Cost Efficiency: Reduce API costs by executing pre-processing, summarization, and trivial remediations on local hardware using SLMs, reserving cloud LLMs for complex, high-severity issues.
2. Token Optimization: Prevent context window exhaustion and save budget by aggressively compressing logs and chat histories while preserving semantic meaning.
3. Self-Healing and Auto-Remediation: Safely execute scripts and fix infrastructure issues autonomously, utilizing a risk assessor gatekeeper.
4. Dynamic Architecture: Utilize a thread-safe FastAPI backend that dynamically integrates model factories and agent schedulers to adapt to varying LLM providers without hardcoded constraints.

## Project Phases

### Phase 1: Input Processing and Optimization

This phase acts as the ingestion point. It heavily compresses chaotic data into a token-efficient payload.
- Query Rewriting: Normalizes raw logs or JSON webhooks into readable text.
- Semantic Chunking: Breaks large stack traces into safe, overlapping chunks.
- Context Pruning: Drops redundant log lines to preserve budget.
- Prompt Compression: Shrinks the payload further by removing non-essential tokens.

### Phase 2: Intelligent Routing Gatekeeper

This phase decides where the compressed payload should be routed.
- Global Dynamic Routing: The ingress point that distributes the payload based on internal policy weights.
- Severity and Complexity Analysis: Evaluates the incident to determine the risk level.
- Token Budgeting: Calculates maximum allowable API spend and token heuristic limits for the incident.
- Dynamic Model Routing: Decides whether to route the incident to a local SLM for low-complexity issues or a cloud LLM for high-complexity issues based on the calculated budget.

### Phase 3: Multi-Agent Model Execution

This phase handles the actual troubleshooting and remediation.
- Model Factory: Dynamically instantiates the correct model interfaces based on runtime configurations and routing decisions.
- Agent Scheduler: Coordinates tasks among specialized personas (e.g., Database Administrator, Network Engineer).
- Thread-Safe Execution: Executes heavy synchronous operations and model inferences within isolated threadpools to prevent ASGI event loop blocking.

### Phase 4: Action Layer and Risk Assessment

This phase evaluates and executes the generated solution.
- Action Assessment: Evaluates the generated solution for risk and confidence.
- Auto-Remediation: Safely executes fixes automatically for trusted scenarios.
- SRE Dashboard: Routes risky or destructive fixes to human operators for manual review, trace inspection, and execution approval.

## Architecture

```mermaid
graph TD
    classDef trigger fill:#ffebee,stroke:#c62828,stroke-width:2px,color:#b71c1c,rx:5px,ry:5px
    classDef phase1 fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1,rx:5px,ry:5px
    classDef phase2 fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:#e65100,rx:5px,ry:5px
    classDef phase3 fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20,rx:5px,ry:5px
    classDef action fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px,color:#4a148c,rx:5px,ry:5px
    classDef global fill:#fff8e1,stroke:#fbc02d,stroke-width:2px,color:#f57f17,rx:5px,ry:5px

    A([Incident Trigger / Alert]):::trigger --> B
    
    subgraph Phase1 ["Phase 1: Input Processing & Optimization"]
        B[Query Rewriting & Summarization]:::phase1 --> C[Semantic Chunking]:::phase1
        C --> D[Context Pruning & Prompt Compression]:::phase1
    end

    D --> |Compressed Payload| E
    
    subgraph Phase2 ["Phase 2: Intelligent Routing Gatekeeper"]
        E{Dynamic Router}:::global
        E --> F[Severity & Complexity Analysis]:::phase2
        E --> G[Token Budgeting & Cost Calculation]:::phase2
        F --> H{Dynamic Model Routing}:::phase2
        G --> H
    end
    
    H --> |Low/Medium Complexity| L_SLM
    H --> |High Complexity| C_LLM

    subgraph Phase3 ["Phase 3: Multi-Agent Model Execution"]
        L_SLM[Local SLM Node]:::phase3 --> Scheduler[Agent Scheduler]:::phase3
        C_LLM[Cloud LLM Node]:::phase3 --> Scheduler
        Scheduler --> Factory[Dynamic Model Factory]:::phase3
    end

    Factory --> I
    
    subgraph Phase4 ["Phase 4: Action Layer & Risk Assessment"]
        I{Risk Assessment Gatekeeper}:::action
        I --> |Safe & High Confidence| J[Auto-Remediation Execution]:::action
        I --> |Risky / Low Confidence| K[SRE Dashboard Human Review]:::action
    end
    
    J --> L([Incident Resolved]):::action
    K --> |Approved by Operator| J
```

## Continuous Learning and Feedback

The Reinforcement Learning mechanism connects the resolution layer back to the routing layer. After an incident is resolved, the system reviews the actions taken. The system computes a reward (if the issue was solved efficiently by an SLM) or a penalty (if the SLM failed and it had to be escalated). 

These rewards and penalties dynamically adjust the Q-Table weights inside the dynamic router. Over time, the router learns to trust the local SLM for specific classes of errors that previously required a cloud LLM, creating a continuously self-optimizing and increasingly cost-effective SRE architecture.
