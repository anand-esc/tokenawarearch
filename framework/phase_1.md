# Phase 1: Input Processing & Optimization (The Funnel)

## Overview
Phase 1 acts as the "Funnel" for the Self-Healing Token Aware Multi-Agent SRE Architecture. Its primary goal is to ingest messy, massive incident data and heavily compress it into a token-efficient payload while preserving maximum semantic meaning. This is critical for saving costs and API budget before data is sent to Phase 2 (the Routing logic) and Phase 3 (the LLMs).

## Pipeline Architecture
The pipeline executes the following 5 distinct steps sequentially, managed by `pipeline.py`.

### 1. Query Rewriting (`rewriter.py`)
- **Purpose**: Normalizes chaotic incoming logs (Datadog webhooks, raw text, standard JSON) into a predictable machine-readable text format.
- **Implementation**: Uses a hybrid approach. It first uses a fast heuristic to detect strict schemas like Datadog and parses them at near-zero compute cost. If the schema is unknown, it falls back to a generic JSON flattening logic or raw text handler.

### 2. Chat History Summarization (`summarizer.py`)
- **Purpose**: Condenses previous human/SRE troubleshooting context so the LLM doesn't waste tokens reading long conversational threads.
- **Implementation**: Uses `facebook/bart-large-cnn` via HuggingFace `transformers`. This runs completely locally to avoid external API costs, utilizing GPU hardware acceleration if available.

### 3. Semantic Chunking (`chunker.py`)
- **Purpose**: Prevents massive 10,000-line stack traces from breaking the token window or being lost.
- **Implementation**: Uses `langchain_text_splitters.RecursiveCharacterTextSplitter`. It breaks logs intelligently by double-newlines, single-newlines, and spaces to maintain stack trace integrity with a configurable overlap to prevent losing context midway through an error.

### 4. Context Pruning (`pruner.py`)
- **Purpose**: Identifies and drops redundant log lines (e.g., a repeating Java `NullPointerException` that flooded the logs 500 times).
- **Implementation**: Utilizes `sentence-transformers` (specifically `all-MiniLM-L6-v2`) to convert chunks into vector embeddings. It calculates the Cosine Similarity between incoming chunks and drops any chunk that is > 85% similar to a chunk already added to the payload.

### 5. Prompt Compression (`compressor.py`)
- **Purpose**: Shrinks the final payload by dropping stop-words and filler tokens without losing the actual root-cause meaning.
- **Implementation**: Powered by `LLMLingua`. It uses a tiny local language model (`TinyLlama-1.1B`) to analyze the text and compress it aggressively, targeting a 2x-3x token reduction before routing to the expensive cloud LLMs.
