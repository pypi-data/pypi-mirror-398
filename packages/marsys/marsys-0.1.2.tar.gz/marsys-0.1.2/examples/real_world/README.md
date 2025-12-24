# Real-World Multi-Agent Examples

This directory contains comprehensive examples demonstrating the MARS framework's capabilities with real LLM integrations. Each example showcases different multi-agent coordination patterns and features.

## 🚀 Quick Start

### Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```bash
# OpenAI
OPENAI_API_KEY=your_openai_key

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key

# Google (Gemini)
GOOGLE_API_KEY=your_google_key

# xAI (Grok)
XAI_API_KEY=your_xai_key

# Google Search (for research examples)
GOOGLE_SEARCH_API_KEY=your_search_key
GOOGLE_CSE_ID_GENERIC=your_cse_id
```

### Running Examples

Each example can be run independently:

```bash
# Hub-and-Spoke Pattern
python example_hub_spoke_research.py

# Dynamic Parallel Pattern
python example_parallel_market_analysis.py

# Multi-Level Mixed Pattern
python example_mixed_content_pipeline.py

# Hierarchical Team Pattern
python example_hierarchical_dev_team.py

# Swarm Intelligence Pattern
python example_swarm_optimization.py

# Pausable Workflow
python example_pausable_workflow.py

# Checkpoint/Restore Workflow
python example_checkpoint_workflow.py
```

## 📁 Examples Overview

### 1. Hub-and-Spoke Pattern (`example_hub_spoke_research.py`)
**Use Case**: AI-powered research assistant

**Pattern**: Central coordinator manages sequential specialist agents
```
ResearchCoordinator (GPT-4)
    ├── DataCollector (Gemini-flash)
    ├── Analyzer (Claude)
    └── ReportWriter (GPT-4)
```

**Key Features**:
- Sequential execution with shared memory
- Central control flow
- Result aggregation
- Google Search integration

### 2. Dynamic Parallel Pattern (`example_parallel_market_analysis.py`)
**Use Case**: Market intelligence gathering

**Pattern**: Coordinator decides at runtime which agents to run in parallel
```
MarketCoordinator (Claude)
    ├── [Parallel]
    ├── CompetitorAnalyst (Grok)
    ├── TrendAnalyst (Gemini-Pro)
    └── CustomerSentimentAnalyst (GPT-4-mini)
```

**Key Features**:
- Runtime-decided parallelism
- Independent branch execution
- Result aggregation from parallel sources
- Agent-initiated parallel execution

### 3. Multi-Level Mixed Pattern (`example_mixed_content_pipeline.py`)
**Use Case**: Content creation pipeline

**Pattern**: Combines parallel research, sequential processing, and conversation loops
```
ContentPlanner (GPT-4)
    ├── Researcher (Gemini-flash + Google Search) [Parallel]
    ├── Writer <-> Editor (Conversation Loop)
    └── SEOOptimizer (Grok)
```

**Key Features**:
- Mixed execution patterns
- Conversation loops for iterative improvement
- Tool integration (Google Search)
- Multiple convergence points

### 4. Hierarchical Team Pattern (`example_hierarchical_dev_team.py`)
**Use Case**: Software development team simulation

**Pattern**: Multi-level hierarchy with nested parallelism
```
ProjectManager (GPT-4)
    ├── FrontendLead (Claude) [Parallel]
    │   ├── UIDesigner (GPT-4-mini) [Parallel]
    │   └── UIImplementer (Gemini-flash)
    └── BackendLead (Gemini-Pro)
        ├── APIDeveloper (GPT-4-mini) [Parallel]
        └── DatabaseDeveloper (Gemini-flash)
```

**Key Features**:
- Multi-level delegation
- Nested parallel execution
- Task distribution and aggregation
- Realistic team dynamics

### 5. Swarm Intelligence Pattern (`example_swarm_optimization.py`)
**Use Case**: Collaborative problem solving

**Pattern**: Agents communicate with each other to find optimal solutions
```
SwarmCoordinator (Claude)
    └── [Mesh Network]
        ├── Explorer1 <-> Explorer2
        ├── Explorer2 <-> Explorer3
        └── Explorer3 <-> Explorer1
```

**Key Features**:
- Inter-agent communication
- Emergent behavior
- Decentralized decision making
- Consensus building

### 6. Pausable Workflow (`example_pausable_workflow.py`)
**Use Case**: Long-running research tasks

**Features**:
- Pause workflow with Ctrl+C
- State persistence to disk
- Resume from saved state
- Progress tracking
- Session management

**Usage**:
```bash
# Start new workflow
python example_pausable_workflow.py

# Press Ctrl+C to pause
# Run again and select session to resume
```

### 7. Checkpoint/Restore Workflow (`example_checkpoint_workflow.py`)
**Use Case**: Complex decision workflows with recovery points

**Features**:
- Create named checkpoints
- Restore to previous states
- Explore alternative paths
- Compare different executions
- Checkpoint management

**Workflow**:
1. Run initial analysis
2. Create checkpoints at key stages
3. Explore alternative scenarios from checkpoints
4. Compare results from different paths

## 📊 Output Structure

All examples save their outputs to the `output/` directory:

```
output/
├── hub_spoke_research_[timestamp]_report.md
├── hub_spoke_research_[timestamp]_execution.json
├── parallel_market_analysis_[timestamp]_report.md
├── parallel_market_analysis_[timestamp]_execution.json
├── state_storage/  # For pausable workflows
│   ├── sessions/
│   └── checkpoints/
└── ...
```

## 🔧 Configuration

### Model Selection

Each example uses different models optimized for specific tasks:

- **GPT-4**: High-level planning, complex reasoning
- **Claude-3-Sonnet**: Strategic analysis, creative tasks
- **Gemini-1.5-Pro**: Analytical tasks, systematic thinking
- **Gemini-1.5-Flash**: Fast data gathering, simple tasks
- **GPT-4-mini**: Cost-effective for simpler tasks
- **Grok-2**: Creative exploration, innovative thinking

### Topology Configuration

Topologies are defined using the three-way system:

```python
topology = {
    "agents": ["Agent1", "Agent2", "Agent3"],
    "flows": [
        "Agent1 -> Agent2",      # Directed edge
        "Agent2 <-> Agent3"      # Bidirectional (conversation)
    ],
    "rules": [
        "timeout(600)",          # 10 minute timeout
        "max_steps(50)",         # Max 50 steps
        "parallel(Agent2, Agent3)",  # Parallel execution
        "max_turns(Agent2 <-> Agent3, 3)"  # Limit conversations
    ]
}
```

## 🎯 Best Practices

1. **Model Selection**:
   - Use more powerful models for coordination and planning
   - Use faster/cheaper models for data gathering
   - Match model capabilities to task requirements

2. **Error Handling**:
   - All examples include comprehensive error handling
   - Failed workflows save partial results
   - Checkpoints enable recovery from failures

3. **Cost Optimization**:
   - Examples use appropriate models for each task
   - Parallel execution reduces total time
   - Token usage is logged in execution details

4. **Scalability**:
   - Patterns can be extended with more agents
   - Hierarchies can be deepened as needed
   - Swarms can include more participants

## 🐛 Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Ensure all required API keys are in `.env`
   - Check key format and validity
   - Verify API access permissions

2. **Rate Limiting**:
   - Examples include timeouts and retries
   - Adjust delays if hitting rate limits
   - Use different API keys for parallel agents

3. **Memory Issues**:
   - Long workflows may accumulate large states
   - Use checkpoints to manage memory
   - Clear old sessions periodically

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger("src.coordination").setLevel(logging.DEBUG)
```

## 📚 Learning Path

1. Start with **Hub-and-Spoke** to understand basic coordination
2. Try **Dynamic Parallel** to see runtime decisions
3. Explore **Mixed Pattern** for complex workflows
4. Study **Hierarchical** for team simulations
5. Experiment with **Swarm** for emergent behavior
6. Use **Pausable/Checkpoint** for production workflows

## 🤝 Contributing

To add new examples:

1. Follow the existing pattern structure
2. Use meaningful agent names and descriptions
3. Include comprehensive error handling
4. Add clear documentation
5. Save outputs in structured format

## 📄 License

These examples are part of the MARS framework and follow the same license terms.