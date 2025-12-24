# MARSYS: Open-source multi-agent AI reasoning Framework

**Submitted to:** AMLD 2026 (Applied Machine Learning Days)
**Submission Date:** December 2025

---

Multi-agent AI systems promise to solve complex tasks through agent collaboration, but moving from demos to production reveals consistent problems.

Existing frameworks force rigid workflow patterns, often fragmented across libraries. Shared memory makes context hand-off a constant fight. Validation logic scatters across every agent. Error handling crashes everything or requires extensive boilerplate. And agent code becomes polluted with orchestration concerns.

MARSYS is an open-source Python framework addressing these challenges. For workflow flexibility, MARSYS uses a graph-based topology where agents are nodes and relationships are edges, letting you create any multi-agent pattern rather than being forced into pre-determined structures.
For validation, all response parsing happens in one centralized component, providing consistent behavior whether handling JSON, structured data, plain text, or tool calls. For error recovery, the steering system automatically retries failed responses with contextual guidance.
Agents self-correct without crashing the workflow. For context and memory, each agent maintains isolated memory with configurable retention, and context passing between agents is handled cleanly by the framework rather than through problematic shared memory.
For separation of concerns, agents implement their task without side effects while the framework handles orchestration, memory, and state externally. For parallel execution, agents dynamically spawn concurrent branches at runtime with automatic result aggregation at convergence, enabling faster execution without manual coordination code.
For long-running workflows, the state management system provides pause/resume, checkpointing, and session recovery.

MARSYS also includes specialized agents: BrowserAgent for vision-based web automation, and FileOperationAgent for intelligent document handling with token-aware strategies. The framework supports human-in-the-loop workflows and multiple LLM providers including OpenAI, Anthropic, Google, xAI, OpenRouter, and local models (such as Apertus, Switzerland's first large-scale open, multilingual language model) .

Our internal benchmarks show that these architectural decisions combined with smart context management enable agents to succeed more reliably on longer, complex tasks. Released under Apache 2.0: https://github.com/rezaho/MARSYS
