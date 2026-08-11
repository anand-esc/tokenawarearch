# Self-Healing SRE Agent: Standard Flowchart

This flowchart uses standard flowchart symbols (decisions as diamonds, processes as rectangles, data as parallelograms/databases) to represent the entire pipeline from top to bottom.

```mermaid
flowchart TD
    %% Node Definitions with Standard Flowchart Shapes
    Start([Incoming Incident Alert])
    InputData[/Raw Logs, Webhooks, Spikes/]
    
    %% Phase 1
    P1A[Chat History Summarization]
    P1B[Query Rewriting]
    P1C[Semantic Chunking]
    P1D[Context Pruning]
    P1E[Prompt Compression]
    CompressedData[(Highly Compressed Payload)]
    
    %% Phase 2
    RouterProcess[Global Dynamic Router Ingress]
    Classifier[BERT Classifier: Severity & Complexity]
    Budget[Token Budgeting: Max Allowable Spend]
    RouteDecision{Complexity vs Budget}
    
    %% Phase 3
    LocalNode[Execute Local SLM Node<br/>Qwen 1.5B via Ollama]
    CloudNode[Execute Cloud LLM Node<br/>Frontier Model via API]
    RespCompress[Response Compression]
    
    %% Action Layer
    RiskAssessment{Risk & Confidence Check}
    AutoFix[Auto-Remediation<br/>Execute Script/Fix]
    HumanReview[SRE Dashboard<br/>Human Review]
    HumanDecision{Human Approves?}
    Resolved([Incident Resolved])
    EndAbort([Incident Escalated / Aborted])
    
    %% Phase 4
    Judge[LLM as Judge<br/>Evaluate Full Resolution]
    RL[Reinforcement Learning<br/>Calculate Reward/Penalty]
    UpdateWeights[(Update Routing Policy Weights)]

    %% Flow Connections
    Start --> InputData
    InputData --> P1A
    P1A --> P1B
    P1B --> P1C
    P1C --> P1D
    P1D --> P1E
    P1E --> CompressedData
    
    CompressedData --> RouterProcess
    RouterProcess --> Classifier
    RouterProcess --> Budget
    Classifier --> RouteDecision
    Budget --> RouteDecision
    
    RouteDecision -- "Low/Medium Complexity" --> LocalNode
    RouteDecision -- "High Complexity" --> CloudNode
    
    LocalNode --> RespCompress
    CloudNode --> RespCompress
    
    RespCompress --> RiskAssessment
    
    RiskAssessment -- "Safe & High Confidence" --> AutoFix
    RiskAssessment -- "Risky, Destructive, Low Confidence" --> HumanReview
    
    HumanReview --> HumanDecision
    HumanDecision -- "Yes" --> AutoFix
    HumanDecision -- "No / Abort" --> EndAbort
    
    AutoFix --> Resolved
    
    Resolved --> Judge
    Judge --> RL
    RL --> UpdateWeights
    UpdateWeights -.->|Feedback Loop| RouterProcess

    %% Styling
    classDef startend fill:#ffcdd2,stroke:#b71c1c,stroke-width:2px,color:#b71c1c
    classDef inputdata fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,color:#f57f17
    classDef process fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,color:#0d47a1
    classDef database fill:#e0f2f1,stroke:#00695c,stroke-width:2px,color:#004d40
    classDef decision fill:#ffe0b2,stroke:#e65100,stroke-width:2px,color:#e65100
    
    class Start,Resolved,EndAbort startend;
    class InputData inputdata;
    class P1A,P1B,P1C,P1D,P1E,RouterProcess,Classifier,Budget,LocalNode,CloudNode,RespCompress,AutoFix,HumanReview,Judge,RL process;
    class CompressedData,UpdateWeights database;
    class RouteDecision,RiskAssessment,HumanDecision decision;
```
