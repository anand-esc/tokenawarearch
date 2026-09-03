# Self-Healing Token-Aware Multi-Agent Architecture

This document contains the visual architecture diagram for the Self-Healing Token-Aware Multi-Agent SRE Architecture.

## Architecture Diagram

![Architecture Diagram](architecture_diagram.png)

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
