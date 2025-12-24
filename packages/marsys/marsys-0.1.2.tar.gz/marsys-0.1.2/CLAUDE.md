# MARSYS Framework - Multi-Agent Coordination System

## Table of Contents
1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Design Principles](#design-principles)
4. [Core Components](#core-components)
5. [Models Architecture](#models-architecture)
6. [Agent System](#agent-system)
7. [Specialized Agents](#specialized-agents)
8. [Topology System](#topology-system)
9. [Built-in Tools](#built-in-tools)
10. [Configuration](#configuration)
11. [Usage Patterns](#usage-patterns)
12. [Best Practices](#best-practices)

---

## Overview

**MARSYS** (Multi-Agent Reasoning Systems) is a framework for building and coordinating multi-agent AI systems. It provides a flexible, scalable architecture for orchestrating complex agent interactions with support for parallel execution, dynamic branching, state persistence, and user interaction.

### Status
- **Version**: 0.1-beta
- **Code Location**: `./src/marsys/`
- **Examples**: `./examples/`
- **Documentation**: `./docs/`

### Key Features
- **Flexible Topology Definition**: 3 ways to define agent workflows (string, object, pattern)
- **Dynamic Branching**: Runtime parallel agent spawning
- **State Persistence**: Pause/resume with checkpointing
- **Agent Pools**: True parallel execution isolation
- **User Interaction**: Built-in human-in-the-loop support
- **Multi-Provider Models**: OpenAI, Anthropic, Google, OpenRouter, xAI
- **Local Model Support**: HuggingFace and vLLM backends for LLMs and VLMs
- **Specialized Agents**: BrowserAgent, FileOperationAgent, WebSearchAgent
- **7 Pre-defined Patterns**: Hub-and-spoke, pipeline, mesh, hierarchical, star, ring, broadcast

---

## Core Architecture

```
                        ┌─────────────────────────────────────────────────────────────┐
                        │                      ORCHESTRA                              │
                        │            High-level Coordination API                      │
                        │        Orchestra.run(task, topology, config)                │
                        └────────────────────┬────────────────────────────────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                        ▼                    ▼                    ▼
                  ┌───────────┐       ┌────────────┐       ┌────────────┐
                  │ TOPOLOGY  │       │ VALIDATION │       │   BRANCH   │
                  │   GRAPH   │◄──────┤ PROCESSOR  │──────►│  EXECUTOR  │
                  └─────┬─────┘       └──────┬─────┘       └──────┬─────┘
                        │                    │                    │
          ┌─────────────┼────────────────────┼────────────────────┼─────────────┐
          │             │                    │                    │             │
          ▼             ▼                    ▼                    ▼             ▼
    ┌──────────┐  ┌──────────┐        ┌──────────┐        ┌──────────┐   ┌──────────┐
    │  RULES   │  │  ROUTER  │        │   STEP   │        │  BRANCH  │   │  STATE   │
    │  ENGINE  │  │          │        │ EXECUTOR │        │ SPAWNER  │   │ MANAGER  │
    └──────────┘  └──────────┘        └──────────┘        └──────────┘   └──────────┘
```

### Execution Flow
1. **Define Topology**: Specify agents, edges, and rules
2. **Orchestra Analyzes**: Validates and creates execution graph
3. **Branch Creation**: Initial branches spawned at entry points
4. **Step Execution**: Each step validated -> routed -> executed
5. **Dynamic Branching**: Agents can spawn parallel child branches
6. **Result Aggregation**: Parent branches resume with child results
7. **Completion**: Final response extracted and returned

---

## Design Principles

### 1. Pure Agent Logic
Agents implement pure `_run()` methods with NO side effects:
```python
# CORRECT - Pure logic
async def _run(self, prompt, context, **kwargs):
    messages = self._prepare_messages(prompt)
    response = await self.model.arun(messages)
    return Message(role="assistant", content=response.content)

# WRONG - Side effects
async def _run(self, prompt, context, **kwargs):
    self.memory.add_message(...)  # NO! Memory handled externally
    await self._log_progress(...)  # NO! Logging handled by coordinator
    return response
```

**Why?** Enables branch isolation, parallel execution, and state persistence.

### 2. Centralized Validation
ALL response processing happens in `ValidationProcessor`:
- Parses agent responses (JSON, structured, text)
- Validates action types
- Extracts tool calls, agent invocations, final responses
- No parsing logic scattered across agents

### 3. Dynamic Branching
Branches created on-the-fly at divergence points:
- Parallel invocations spawn child branches
- Parent branches wait for children
- Results automatically aggregated
- Topology controls allowed transitions

### 4. Branch Isolation
Each branch maintains its own:
- Memory state (per-agent conversation history)
- Execution trace (step-by-step actions)
- Metadata (branch-specific context)
- Status (pending, running, waiting, completed, failed)

### 5. Topology-Driven Routing
Router uses topology graph for all decisions:
- Permission validation (can Agent A invoke Agent B?)
- Conversation detection (bidirectional edges)
- Entry point identification
- Convergence point detection

### 6. Adapter Pattern for Models
All providers abstracted via adapters:
- Standardized request/response format
- Provider-specific handling encapsulated
- Easy to add new providers
- Unified error handling with automatic retry

---

## Core Components

### Orchestra
**Location**: [src/marsys/coordination/orchestra.py](src/marsys/coordination/orchestra.py)

High-level coordination API. Single entry point for all multi-agent workflows.

**Design Principle**: Orchestra is the **facade** - it hides all complexity behind a simple `run()` method. It owns the execution lifecycle but delegates actual work to specialized components.

```python
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig

result = await Orchestra.run(
    task="Research quantum computing applications",
    topology=topology,
    agent_registry=AgentRegistry,
    context={"session_id": "abc123"},
    execution_config=ExecutionConfig(
        user_interaction="terminal",
        convergence_timeout=300.0,
        status=StatusConfig.from_verbosity(1)
    ),
    max_steps=100,
    state_manager=StateManager(storage),
    allow_follow_ups=True
)

# Access results
print(result.success)
print(result.final_response)
print(result.total_steps)
print(result.total_duration)
print(result.branch_results)
```

**Key Methods**:
- `Orchestra.run()`: One-line execution (classmethod)
- `execute()`: Instance method for more control
- `pause_session()`: Pause execution
- `resume_session()`: Resume from pause
- `create_checkpoint()`: Save execution state
- `restore_checkpoint()`: Restore from checkpoint

**OrchestraResult**:
```python
@dataclass
class OrchestraResult:
    success: bool
    final_response: Any
    branch_results: List[BranchResult]
    total_steps: int
    total_duration: float
    metadata: Dict[str, Any]
    error: Optional[str]
```

---

### BranchExecutor
**Location**: [src/marsys/coordination/execution/branch_executor.py](src/marsys/coordination/execution/branch_executor.py)

**Design Principle**: BranchExecutor handles **branch lifecycle** - it knows how to execute different branch types (simple, conversation, nested, user interaction) but delegates individual step execution to StepExecutor.

```python
class BranchType(Enum):
    SIMPLE = "simple"                # Sequential execution
    CONVERSATION = "conversation"    # Bidirectional dialogue
    NESTED = "nested"                # Hierarchical sub-branches
    AGGREGATION = "aggregation"      # Waits for multiple branches
    USER_INTERACTION = "user_interaction"  # Human-in-the-loop

async def execute_branch(
    branch: ExecutionBranch,
    initial_request: Any,
    context: Dict[str, Any],
    resume_with_results: Optional[Dict] = None
) -> BranchResult
```

**Branch States**:
- `PENDING`: Not yet started
- `RUNNING`: Currently executing
- `PAUSED`: Paused for user input
- `WAITING`: Paused for child branches
- `COMPLETED`: Successfully finished
- `FAILED`: Terminated with error
- `CANCELLED`: Cancelled by user/system

---

### StepExecutor
**Location**: [src/marsys/coordination/execution/step_executor.py](src/marsys/coordination/execution/step_executor.py)

**Design Principle**: StepExecutor is **single-responsibility** - it executes exactly one step (agent invocation or tool call). It handles memory injection, retry logic, and error classification but knows nothing about branches or workflows.

```python
async def execute_step(
    agent_name: str,
    request: Any,
    context: Dict[str, Any],
    branch: ExecutionBranch,
    memory: List[Dict[str, Any]],
    tools_enabled: bool = True
) -> StepResult

async def execute_tools(
    tool_calls: List[Dict[str, Any]],
    agent_name: str,
    context: Dict[str, Any]
) -> ToolExecutionResult
```

**Features**:
- Retry logic with exponential backoff
- Memory injection before agent invocation
- Tool execution integration
- User node handling
- Error classification and recovery

---

### DynamicBranchSpawner
**Location**: [src/marsys/coordination/execution/branch_spawner.py](src/marsys/coordination/execution/branch_spawner.py)

**Design Principle**: BranchSpawner handles **parallelism** - it creates child branches when agents request parallel execution, tracks convergence points, and aggregates results. It's the only component that knows about branch relationships.

```python
async def handle_agent_completion(
    agent_name: str,
    response: Dict[str, Any],
    context: Dict[str, Any],
    parent_branch_id: str
) -> List[asyncio.Task]

async def create_child_branches(
    invocations: List[AgentInvocation],
    parent_branch: ExecutionBranch,
    context: Dict[str, Any]
) -> List[ExecutionBranch]

async def wait_for_convergence(
    parent_branch_id: str,
    child_branch_ids: List[str],
    convergence_point: str,
    timeout: float
) -> AggregatedContext
```

**Capabilities**:
- Agent-initiated parallel invocations
- Child branch creation
- Result aggregation at convergence points
- Parent branch resumption
- Timeout handling for convergence
- Orphan branch termination

---

### ValidationProcessor
**Location**: [src/marsys/coordination/validation/response_validator.py](src/marsys/coordination/validation/response_validator.py)

**Design Principle**: ValidationProcessor is the **single source of truth** for response parsing. All response formats (JSON, text, tool calls) are handled here. No parsing logic exists in agents or other components.

```python
class ActionType(Enum):
    INVOKE_AGENT = "invoke_agent"
    PARALLEL_INVOKE = "parallel_invoke"
    CALL_TOOL = "call_tool"
    FINAL_RESPONSE = "final_response"
    END_CONVERSATION = "end_conversation"
    WAIT_AND_AGGREGATE = "wait_and_aggregate"
    ERROR_RECOVERY = "error_recovery"
    TERMINAL_ERROR = "terminal_error"
    AUTO_RETRY = "auto_retry"

async def validate_response(
    response: Any,
    agent_name: str,
    allowed_agents: List[str],
    branch: ExecutionBranch,
    topology_graph: Optional[TopologyGraph] = None,
    error_context: Optional[Dict] = None
) -> ValidationResult
```

**Response Formats Supported**:
```python
# Sequential invocation
{"next_action": "invoke_agent", "action_input": "Agent2"}

# Parallel invocation
{"next_action": "parallel_invoke", "agents": ["A", "B"], "agent_requests": {"A": "task1", "B": "task2"}}

# Tool call
{"next_action": "call_tool", "tool_calls": [...]}

# Final response
{"next_action": "final_response", "content": "Result..."}

# Error recovery
{"next_action": "error_recovery", "error_details": {...}, "suggested_action": "retry"}
```

---

### Router
**Location**: [src/marsys/coordination/routing/router.py](src/marsys/coordination/routing/router.py)

**Design Principle**: Router **translates decisions into actions** - it converts ValidationResults into ExecutionSteps. It uses the topology graph for permission checks but doesn't execute anything itself.

```python
async def route(
    validation_result: ValidationResult,
    current_branch: ExecutionBranch,
    routing_context: RoutingContext
) -> RoutingDecision

@dataclass
class RoutingDecision:
    next_steps: List[ExecutionStep]
    should_continue: bool
    should_wait: bool
    child_branch_specs: List[BranchSpec]
    completion_reason: Optional[str]
    metadata: Dict[str, Any]
```

**Routing Patterns**:
- Sequential agent invocation
- Parallel branch spawning
- Tool execution
- Conversation continuation
- Error recovery routing to User
- Final response extraction

---

## Models Architecture

### ModelConfig
**Location**: [src/marsys/models/models.py](src/marsys/models/models.py)

**Design Principle**: Configuration is **declarative** - users describe what they want, not how to get it. The system figures out the right adapter, endpoint, and parameters.

```python
from marsys.models import ModelConfig

# API Model Configuration
config = ModelConfig(
    type="api",                    # "api" or "local"
    name="anthropic/claude-sonnet-4.5",  # Model identifier
    provider="openrouter",         # openai, anthropic, google, openrouter, xai
    api_key=None,                  # Reads from env if None
    max_tokens=12000,
    temperature=0.7,

    # Reasoning/thinking parameters (provider-specific)
    thinking_budget=1024,          # For Gemini, Anthropic, Alibaba
    reasoning_effort="low",        # For OpenAI o1/o3: minimal, low, medium, high
)

# Local Model Configuration
local_config = ModelConfig(
    type="local",
    name="Qwen/Qwen3-4B-Instruct-2507",
    model_class="llm",             # "llm" or "vlm"
    backend="huggingface",         # "huggingface" or "vllm"
    torch_dtype="bfloat16",
    device_map="auto",
    max_tokens=4096,
)

# Local VLM with vLLM (production)
vlm_config = ModelConfig(
    type="local",
    name="Qwen/Qwen3-VL-8B-Instruct",
    model_class="vlm",
    backend="vllm",
    tensor_parallel_size=2,        # Multi-GPU
    gpu_memory_utilization=0.9,
    quantization="fp8",            # awq, gptq, fp8
    max_tokens=4096,
)
```

**Environment Variable Mapping**:
- `openai` -> `OPENAI_API_KEY`
- `anthropic` -> `ANTHROPIC_API_KEY`
- `google` -> `GOOGLE_API_KEY`
- `openrouter` -> `OPENROUTER_API_KEY`
- `xai` -> `XAI_API_KEY`

### BaseAPIModel
**Location**: [src/marsys/models/models.py](src/marsys/models/models.py)

**Design Principle**: Models use the **adapter pattern** - each provider has its own adapter that handles request formatting, response parsing, and error handling with automatic retry. The base class provides a unified interface.

```python
from marsys.models import BaseAPIModel

model = BaseAPIModel(
    provider="openrouter",
    model_name="anthropic/claude-haiku-4.5",
    temperature=0.7,
    max_tokens=12000,
)

# Synchronous call
response = model.run(messages, tools=tools)

# Asynchronous call
response = await model.arun(messages, tools=tools)
```

**Automatic Retry Behavior**:
- **Max Retries**: 3 (total 4 attempts)
- **Backoff**: 1s → 2s → 4s (exponential)
- **Retryable Status Codes**: 500, 502, 503, 504, 529 (Anthropic), 408, 429 (rate limit)

### BaseLocalModel
**Location**: [src/marsys/models/models.py](src/marsys/models/models.py)

Unified interface for local models with adapter pattern supporting two backends:

```python
from marsys.models import BaseLocalModel

# HuggingFace backend (development)
model = BaseLocalModel(
    model_name="Qwen/Qwen3-4B-Instruct-2507",
    model_class="llm",
    backend="huggingface",
    torch_dtype="bfloat16",
    device_map="auto",
    max_tokens=4096
)

# vLLM backend (production)
vlm_model = BaseLocalModel(
    model_name="Qwen/Qwen3-VL-8B-Instruct",
    model_class="vlm",
    backend="vllm",
    tensor_parallel_size=2,
    gpu_memory_utilization=0.9,
    max_tokens=4096
)

response = model.run(messages=[{"role": "user", "content": "Hello!"}])
```

**Backend Comparison**:
| Feature | HuggingFace | vLLM |
|---------|-------------|------|
| Use Case | Development | Production |
| Training | Supported | Not supported |
| Throughput | Lower | Higher |
| Multi-GPU | device_map="auto" | tensor_parallel_size |

### HarmonizedResponse
**Location**: [src/marsys/models/response_models.py](src/marsys/models/response_models.py)

All providers return a standardized response format:

```python
@dataclass
class HarmonizedResponse:
    content: str                           # Main response content
    tool_calls: Optional[List[ToolCall]]   # Tool calls (if any)
    usage: Optional[UsageInfo]             # Token usage info
    metadata: ResponseMetadata             # Model, provider, timing
    raw_response: Optional[Dict]           # Original response
```

---

## Agent System

### BaseAgent
**Location**: [src/marsys/agents/agents.py](src/marsys/agents/agents.py)

**Design Principle**: Agents are **stateless executors** - they receive a prompt and context, return a response. Memory and coordination are handled externally. This enables branch isolation and parallel execution.

```python
from marsys.agents import BaseAgent

class BaseAgent(ABC):
    def __init__(
        self,
        model: Union[BaseLocalModel, BaseAPIModel],
        name: str,                              # Unique agent identifier
        goal: str,                              # 1-2 sentence summary
        instruction: str,                       # Detailed behavior instructions
        tools: Optional[Dict[str, Callable]] = None,
        max_tokens: Optional[int] = 10000,
        allowed_peers: Optional[List[str]] = None,
        bidirectional_peers: bool = False,
        is_convergence_point: Optional[bool] = None,
        memory_retention: str = "session",      # single_run, session, persistent
        input_schema: Optional[Any] = None,
        output_schema: Optional[Any] = None,
    ):
        ...

    @abstractmethod
    async def _run(
        self,
        prompt: Any,
        context: Dict[str, Any],
        **kwargs
    ) -> Message:
        """Pure execution logic - NO side effects"""
        pass

    async def run(self, prompt, context=None, **kwargs) -> Message:
        """Public interface with retry and monitoring"""

    async def auto_run(
        self,
        initial_prompt: str,
        max_steps: int = 10,
        **kwargs
    ) -> Union[Message, str]:
        """Run agent autonomously with automatic tool/agent invocation"""

    async def cleanup(self) -> None:
        """Clean up agent resources (model sessions, browser handles, etc.)"""
```

### Creating an Agent

```python
from marsys.agents import Agent
from marsys.models import ModelConfig

agent = Agent(
    model_config=ModelConfig(
        type="api",
        name="anthropic/claude-haiku-4.5",
        provider="openrouter",
        max_tokens=12000
    ),
    name="Researcher",
    goal="Research topics and provide comprehensive summaries",
    instruction="""You are a thorough researcher. When given a topic:
    1. Search for relevant information
    2. Analyze multiple sources
    3. Provide a comprehensive summary""",
    tools={"search": search_tool, "scrape": scrape_tool},
    memory_retention="session"
)

# Single run
result = await agent.run("Research AI trends")

# Autonomous execution with tool calling
result = await agent.auto_run(
    "Research and summarize recent AI breakthroughs",
    max_steps=5
)

# Cleanup when done
await agent.cleanup()
```

### Memory System
**Location**: [src/marsys/agents/memory.py](src/marsys/agents/memory.py)

```python
@dataclass
class Message:
    role: str                              # user, assistant, system, tool
    content: Optional[Union[str, Dict]]
    message_id: str
    name: Optional[str]                    # Tool name or agent name
    tool_calls: Optional[List[ToolCallMsg]]
    agent_calls: Optional[List[AgentCallMsg]]
    structured_data: Optional[Dict]
    images: Optional[List[str]]            # For vision models

class ConversationMemory:
    def add_message(msg: Message) -> None
    def get_messages() -> List[Message]
    def get_recent(n: int) -> List[Message]
    def clear() -> None
    def save_to_file(path: Path) -> None
    def load_from_file(path: Path) -> None
```

**Memory Retention Policies**:
- `single_run`: Cleared after each run
- `session`: Persists within session
- `persistent`: Persists across sessions (to file)

### AgentRegistry
**Location**: [src/marsys/agents/registry.py](src/marsys/agents/registry.py)

**Design Principle**: Registry is a **singleton** - all agents register themselves on creation. This enables topology validation and runtime agent lookup.

```python
from marsys.agents import AgentRegistry

# Agents auto-register on creation
agent = Agent(name="MyAgent", ...)

# Manual operations
AgentRegistry.register(agent, name="CustomName")
AgentRegistry.unregister("MyAgent")
AgentRegistry.unregister_if_same("MyAgent", agent)  # Identity-safe
agent = AgentRegistry.get("MyAgent")
names = AgentRegistry.list()
```

### AgentPool
**Location**: [src/marsys/agents/agent_pool.py](src/marsys/agents/agent_pool.py)

**Design Principle**: Pools enable **true parallelism** - each branch gets its own agent instance with separate state. The pool manages instance lifecycle and fair allocation.

```python
from marsys.agents import AgentPool

pool = AgentPool(
    agent_class=BrowserAgent,
    num_instances=3,
    model_config=config,
    agent_name="BrowserPool"
)

# Acquire instance for branch
async with pool.acquire(branch_id="branch_123") as agent:
    result = await agent.run(task)

# Pool handles:
# - Instance creation with unique names
# - Allocation tracking
# - Automatic release
# - Statistics (total allocations, wait time, etc.)

await pool.cleanup()

# Check statistics
stats = pool.get_statistics()
print(f"Total allocations: {stats['total_allocations']}")
```

---

## Specialized Agents

MARSYS provides specialized agents that extend the base Agent class with domain-specific tools and capabilities.

### BrowserAgent
**Location**: [src/marsys/agents/browser_agent.py](src/marsys/agents/browser_agent.py)

Autonomous browser automation with vision-based interaction and screenshot analysis.

**Best for**: Web scraping, UI testing, form filling, web research, dynamic content extraction

```python
from marsys.agents import BrowserAgent

# BrowserAgent requires async creation via create_safe()
agent = await BrowserAgent.create_safe(
    model_config=config,
    name="WebAutomation",
    mode="advanced",        # "primitive" or "advanced"
    headless=True,
    viewport_width=1920,
    viewport_height=1080
)

try:
    result = await agent.auto_run(
        "Go to example.com and extract all product names and prices",
        max_steps=3
    )
finally:
    await agent.browser_tool.close_browser()
```

**Key Features**:
- Vision-based element interaction (no selectors needed)
- Multi-mode operation (basic, cdp, stealth, vision)
- Screenshot analysis with multimodal models
- JavaScript execution and console monitoring

### FileOperationAgent
**Location**: [src/marsys/agents/file_operation_agent.py](src/marsys/agents/file_operation_agent.py)

Intelligent file and directory operations with optional bash command execution.

**Best for**: Code analysis, configuration management, log processing, documentation generation

```python
from marsys.agents import FileOperationAgent

agent = FileOperationAgent(
    model_config=config,
    name="FileHelper",
    enable_bash=True,                              # Enable bash commands
    allowed_bash_commands=["grep", "find", "wc"]   # Whitelist
)

result = await agent.auto_run(
    "Read the README.md and summarize its contents",
    max_steps=5
)
```

**Key Features**:
- Type-aware file handling (Python, JSON, PDF, Markdown, images)
- Intelligent reading strategies (AUTO, FULL, PARTIAL, OVERVIEW, PROGRESSIVE)
- Unified diff editing with high success rate
- Content and structure search (ripgrep-based)
- Security: Command validation, blocked dangerous patterns, timeouts

### WebSearchAgent
**Location**: [src/marsys/agents/web_search_agent.py](src/marsys/agents/web_search_agent.py)

Multi-source information gathering across web and scholarly databases.

**Best for**: Research, fact-checking, literature reviews, current events

```python
from marsys.agents import WebSearchAgent

agent = WebSearchAgent(
    model_config=config,
    name="Researcher",
    search_mode="all",                            # "web", "scholarly", or "all"
    bing_api_key=os.getenv("BING_SEARCH_API_KEY")
)

result = await agent.auto_run(
    "Research recent advances in quantum computing",
    max_steps=5
)
```

**Key Features**:
- Multi-source search (Bing, Google, arXiv, Semantic Scholar, PubMed)
- Configurable search modes
- API key validation at initialization
- Query formulation strategies

---

## Topology System

### Three Ways to Define Topologies

**Location**: [src/marsys/coordination/topology/](src/marsys/coordination/topology/)

**1. String Notation (Simplest)**
```python
topology = {
    "agents": ["User", "Coordinator", "Worker1", "Worker2"],
    "flows": [
        "User -> Coordinator",
        "Coordinator -> Worker1",
        "Coordinator -> Worker2",
        "Worker1 -> Coordinator",
        "Worker2 -> Coordinator"
    ],
    "rules": ["timeout(300)", "max_agents(10)"]
}
```

**2. Object-Based (Type-Safe)**
```python
from marsys.coordination.topology import Topology, Node, Edge, EdgeType, NodeType

topology = Topology(
    nodes=[
        Node("Coordinator", node_type=NodeType.AGENT),
        Node("Worker1", node_type=NodeType.AGENT),
        Node("Worker2", node_type=NodeType.AGENT)
    ],
    edges=[
        Edge("Coordinator", "Worker1", edge_type=EdgeType.INVOKE),
        Edge("Coordinator", "Worker2", edge_type=EdgeType.INVOKE),
        Edge("Worker1", "Coordinator"),
        Edge("Worker2", "Coordinator")
    ]
)
```

**3. Pattern Configuration (Pre-defined)**
```python
from marsys.coordination.topology.patterns import PatternConfig

# Hub-and-spoke
topology = PatternConfig.hub_and_spoke(
    hub="Coordinator",
    spokes=["Worker1", "Worker2", "Worker3"],
    parallel_spokes=True
)

# Pipeline
topology = PatternConfig.pipeline(
    stages=[
        {"name": "stage1", "agents": ["Preprocessor"]},
        {"name": "stage2", "agents": ["Analyzer", "Checker"]},
        {"name": "stage3", "agents": ["Reporter"]}
    ],
    parallel_within_stage=True
)

# Hierarchical
topology = PatternConfig.hierarchical(
    tree={
        "Manager": ["Lead1", "Lead2"],
        "Lead1": ["Worker1", "Worker2"],
        "Lead2": ["Worker3", "Worker4"]
    }
)

# Mesh
topology = PatternConfig.mesh(
    agents=["Agent1", "Agent2", "Agent3"],
    fully_connected=True
)
```

### Topology Core Types
**Location**: [src/marsys/coordination/topology/core.py](src/marsys/coordination/topology/core.py)

```python
class NodeType(Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"

class EdgeType(Enum):
    INVOKE = "invoke"
    NOTIFY = "notify"
    QUERY = "query"
    STREAM = "stream"

class EdgePattern(Enum):
    ALTERNATING = "alternating"  # A <~> B (ping-pong)
    SYMMETRIC = "symmetric"      # A <|> B (peer)
```

### TopologyGraph
**Location**: [src/marsys/coordination/topology/graph.py](src/marsys/coordination/topology/graph.py)

Runtime graph representation for routing decisions:

```python
class TopologyGraph:
    def can_transition(source: str, target: str) -> bool
    def get_allowed_targets(source: str) -> List[str]
    def identify_divergence_points() -> List[str]
    def identify_convergence_points() -> List[str]
    def get_parallel_groups(source: str) -> List[ParallelGroup]
```

### Available Patterns
**Location**: [src/marsys/coordination/topology/patterns.py](src/marsys/coordination/topology/patterns.py)

| Pattern | Description |
|---------|-------------|
| `HUB_AND_SPOKE` | Central coordinator with spoke agents |
| `HIERARCHICAL` | Tree-based delegation |
| `PIPELINE` | Sequential stages with optional parallelism |
| `MESH` | Fully connected peer network |
| `STAR` | Similar to hub-and-spoke with bidirectional edges |
| `RING` | Circular agent chain |
| `BROADCAST` | One-to-many notification |

---

## Built-in Tools

### Web Search Tools
**Location**: [src/marsys/environment/search_tools.py](src/marsys/environment/search_tools.py)

```python
from marsys.environment.tools import web_search, tool_google_search_api

# Unified web search (auto-fallback)
results = await web_search(
    query="AI trends 2025",
    max_results=5
)

# Google Custom Search API (production recommended)
results = tool_google_search_api(
    query="Python machine learning",
    num_results=5,
    lang="en"
)
```

**Environment Variables for Search**:
- `GOOGLE_SEARCH_API_KEY`: Google Custom Search API key
- `GOOGLE_CSE_ID_GENERIC`: Google Custom Search Engine ID
- `BING_SEARCH_API_KEY`: Bing Search API key

### File Operations Toolkit
**Location**: [src/marsys/environment/file_operations/](src/marsys/environment/file_operations/)

```python
from marsys.environment import create_file_operation_tools, FileOperationConfig

# Create with default config
file_tools = create_file_operation_tools()

# Create with custom config
config = FileOperationConfig(
    base_directory=Path("/workspace"),
    force_base_directory=True,
    max_file_size_bytes=100 * 1024 * 1024,
    max_characters_absolute=120000,
    blocked_patterns=["*.key", "*.pem", ".env*"],
    auto_approve_patterns=["*.md", "*.txt", "*.py"],
    enable_editing=True,
    enable_audit_log=True,
)
file_tools = create_file_operation_tools(config)
```

**Available File Operation Tools**:
| Tool | Description |
|------|-------------|
| `read_file` | Read file with intelligent strategy selection |
| `write_file` | Write content to file |
| `edit_file` | Edit using unified diff or search/replace |
| `search_files` | Search content, filenames, or structure |
| `get_file_structure` | Extract hierarchical structure |
| `list_files` | List directory contents |

**Reading Strategies**:
- `AUTO`: Automatically selects based on file size
- `FULL`: Complete file content
- `PARTIAL`: Structure overview + selected sections
- `OVERVIEW`: Structure and summary only
- `PROGRESSIVE`: Load sections incrementally

### URL Fetch Tool
```python
from marsys.environment.tools import fetch_url_content

content = await fetch_url_content(
    url="https://example.com/article",
    timeout=30,
    include_metadata=True
)
```

---

## Configuration

### ExecutionConfig
**Location**: [src/marsys/coordination/config.py](src/marsys/coordination/config.py)

```python
from marsys.coordination.config import ExecutionConfig, StatusConfig, VerbosityLevel

config = ExecutionConfig(
    # Timeouts (seconds)
    convergence_timeout=300.0,
    branch_timeout=600.0,
    agent_acquisition_timeout=240.0,
    step_timeout=300.0,
    tool_execution_timeout=120.0,
    user_interaction_timeout=300.0,

    # Convergence behavior
    dynamic_convergence_enabled=True,
    convergence_policy=1.0,  # or "strict", "majority", "any"

    # Steering (retry logic)
    steering_mode="auto",  # auto, always, error, never

    # Agent lifecycle
    auto_cleanup_agents=True,

    # Status updates
    status=StatusConfig.from_verbosity(VerbosityLevel.NORMAL),

    # User interaction
    user_interaction="terminal",  # terminal, none, async
    user_first=False,
    initial_user_msg=None,
)
```

### StatusConfig

```python
from marsys.coordination.config import StatusConfig, VerbosityLevel

status = StatusConfig(
    enabled=True,
    verbosity=VerbosityLevel.NORMAL,  # QUIET=0, NORMAL=1, VERBOSE=2
    cli_output=True,
    cli_colors=True,
    show_thoughts=False,
    show_tool_calls=True,
    show_timings=True,
    show_agent_prefixes=True,
    aggregation_window_ms=500,
    aggregate_parallel=True,
)

# Quick setup
status = StatusConfig.from_verbosity(VerbosityLevel.VERBOSE)
```

### ConvergencePolicyConfig

Controls behavior when parallel branches timeout:

```python
from marsys.coordination.config import ConvergencePolicyConfig

# Float: minimum convergence ratio
config = ExecutionConfig(convergence_policy=0.8)  # 80% must converge

# String: named policy
config = ExecutionConfig(convergence_policy="strict")  # All must converge
# Options: "strict" (100%), "majority" (51%), "fail" (100%), "any" (0%)

# Full config
policy = ConvergencePolicyConfig(
    min_ratio=0.75,
    on_insufficient="fail",  # fail, proceed, user
    terminate_orphans=True,
)
```

---

## Usage Patterns

### Pattern 1: Simple Sequential Flow

```python
from marsys.coordination import Orchestra

topology = {
    "agents": ["Coordinator", "Worker"],
    "flows": ["Coordinator -> Worker"]
}

result = await Orchestra.run(
    task="Analyze the quarterly report",
    topology=topology
)
```

### Pattern 2: Hub-and-Spoke

```python
from marsys.coordination.topology.patterns import PatternConfig

topology = PatternConfig.hub_and_spoke(
    hub="Coordinator",
    spokes=["DataCollector", "Analyzer", "Reporter"],
    parallel_spokes=False
)

result = await Orchestra.run(
    task="Research AI trends",
    topology=topology
)
```

### Pattern 3: Parallel Execution

```python
topology = PatternConfig.hub_and_spoke(
    hub="Coordinator",
    spokes=["Worker1", "Worker2", "Worker3"],
    parallel_spokes=True
)

# Coordinator decides which workers to invoke in parallel:
# {"next_action": "parallel_invoke", "agents": ["Worker1", "Worker2"], ...}
```

### Pattern 4: User Interaction

```python
topology = {
    "agents": ["User", "Agent1", "Agent2"],
    "flows": [
        "User -> Agent1",
        "Agent1 -> User",
        "Agent1 -> Agent2",
        "Agent2 -> User"
    ]
}

result = await Orchestra.run(
    task="Help me plan my vacation",
    topology=topology,
    execution_config=ExecutionConfig(
        user_interaction="terminal",
        user_first=True,
        initial_user_msg="Hello! How can I help?"
    )
)
```

### Pattern 5: With Agent Pool

```python
from marsys.agents import AgentPool, AgentRegistry

pool = AgentPool(
    agent_class=BrowserAgent,
    num_instances=3,
    model_config=config,
    agent_name="BrowserPool"
)

AgentRegistry.register_pool(pool, "BrowserPool")

topology = {
    "agents": ["Coordinator", "BrowserPool"],
    "flows": ["Coordinator -> BrowserPool"]
}

result = await Orchestra.run(
    task="Scrape these 10 websites",
    topology=topology
)

await pool.cleanup()
```

### Pattern 6: With State Persistence

```python
from marsys.coordination.state import StateManager, FileStorageBackend
from pathlib import Path

storage = FileStorageBackend(Path("./state"))
state_manager = StateManager(storage)

result = await Orchestra.run(
    task="Multi-day research project",
    topology=topology,
    state_manager=state_manager,
)

# Pause/resume
await state_manager.pause_execution(session_id, state)
state = await state_manager.resume_execution(session_id)
```

### Pattern 7: Multi-Agent Specialized Workflow

```python
from marsys.agents import BrowserAgent, FileOperationAgent, WebSearchAgent

# Create specialized agents
browser_agent = await BrowserAgent.create_safe(
    model_config=config, name="BrowserAgent", headless=True
)
file_agent = FileOperationAgent(
    model_config=config, name="FileHelper", enable_bash=True
)
search_agent = WebSearchAgent(
    model_config=config, name="Researcher", search_mode="all"
)

topology = PatternConfig.hub_and_spoke(
    hub="Coordinator",
    spokes=["BrowserAgent", "FileHelper", "Researcher"]
)

result = await Orchestra.run(
    task="Research topic, scrape related websites, and save findings",
    topology=topology
)
```

---

## Best Practices

### Topology Design

**DO**:
- Start with simple patterns (sequential, hub-and-spoke)
- Use pre-defined PatternConfig when possible
- Keep convergence points clear
- Limit parallel branches (< 10 concurrent)
- Add timeout rules for all workflows

**DON'T**:
- Create cyclic dependencies without max_turns
- Mix too many patterns in one topology
- Skip timeout configuration

### Agent Implementation

**DO**:
- Keep `_run()` pure (no side effects)
- Return structured responses when appropriate
- Use type hints for tool functions
- Test agents individually first
- Call `cleanup()` when done with agents

**DON'T**:
- Manipulate memory directly in `_run()`
- Use global state
- Mix coordination logic with agent logic
- Use deprecated `invoke_agent()` (use Orchestra instead)

### Memory Management

**DO**:
- Set appropriate memory retention policy
- Use `session` for most workflows
- Clear memory when appropriate

**DON'T**:
- Keep unlimited history (impacts token usage)
- Share memory across unrelated workflows

### Error Handling

**DO**:
- Include User node in topology for recovery
- Configure provider-specific retry logic
- Set reasonable timeouts
- Use `auto_cleanup_agents=True` for automatic resource cleanup

**DON'T**:
- Assume APIs always work
- Use infinite retries

### Model Selection

**DO**:
- Use OpenRouter for access to multiple providers
- Use HuggingFace backend for development/training
- Use vLLM backend for production inference
- Set appropriate max_tokens for your use case

**DON'T**:
- Hardcode API keys in code
- Ignore rate limits

---

## Additional Components

### Rules Engine
**Location**: [src/marsys/coordination/rules/](src/marsys/coordination/rules/)

```python
from marsys.coordination.rules import TimeoutRule, MaxAgentsRule, MaxStepsRule

# Built-in rules
TimeoutRule(max_duration_seconds=300)
MaxAgentsRule(max_agents=10)
MaxStepsRule(max_steps=100)
```

### State Manager
**Location**: [src/marsys/coordination/state/](src/marsys/coordination/state/)

Handles persistence, pause/resume, and checkpointing.

### Communication System
**Location**: [src/marsys/coordination/communication/](src/marsys/coordination/communication/)

Channels for user interaction: Terminal, EnhancedTerminal, Web.

### Steering Manager
**Location**: [src/marsys/coordination/steering/](src/marsys/coordination/steering/)

Handles retry guidance and error recovery strategies.

---

## File Structure Reference

```
src/marsys/
├── __init__.py
├── agents/
│   ├── agents.py              # BaseAgent, Agent classes
│   ├── agent_pool.py          # AgentPool for parallel execution
│   ├── browser_agent.py       # Browser automation agent
│   ├── file_operation_agent.py # File operations agent
│   ├── web_search_agent.py    # Web search agent
│   ├── learnable_agents.py    # PEFT fine-tunable agents
│   ├── memory.py              # Message, ConversationMemory
│   ├── memory_strategies.py   # Memory retention strategies
│   ├── registry.py            # AgentRegistry singleton
│   ├── pool_factory.py        # Agent pool factory
│   ├── exceptions.py          # Agent exceptions
│   └── utils.py
├── coordination/
│   ├── orchestra.py           # Main Orchestra class
│   ├── config.py              # ExecutionConfig, StatusConfig
│   ├── context_manager.py     # Execution context
│   ├── event_bus.py           # Event system
│   ├── branches/
│   │   └── types.py           # ExecutionBranch, BranchType
│   ├── communication/
│   │   ├── manager.py         # CommunicationManager
│   │   ├── core.py            # Communication core
│   │   ├── user_node_handler.py
│   │   └── channels/          # Terminal, EnhancedTerminal, Web
│   ├── configs/
│   │   └── auto_run.py        # Auto-run configuration
│   ├── execution/
│   │   ├── branch_executor.py # Branch execution
│   │   ├── step_executor.py   # Step execution
│   │   ├── branch_spawner.py  # Dynamic branching
│   │   └── tool_executor.py   # Tool execution
│   ├── routing/
│   │   ├── router.py          # Routing logic
│   │   └── types.py           # RoutingDecision, ExecutionStep
│   ├── rules/
│   │   ├── rules_engine.py    # RulesEngine
│   │   ├── basic_rules.py     # Built-in rules
│   │   └── rule_factory.py    # Rule factory
│   ├── state/
│   │   ├── state_manager.py   # Persistence
│   │   └── checkpoint.py      # Checkpointing
│   ├── status/
│   │   ├── manager.py         # Status updates
│   │   ├── events.py          # Status events
│   │   └── channels.py        # Status channels
│   ├── steering/
│   │   └── manager.py         # Steering/retry management
│   ├── topology/
│   │   ├── core.py            # Node, Edge, Topology (in __init__.py)
│   │   ├── graph.py           # TopologyGraph (in __init__.py)
│   │   ├── patterns.py        # PatternConfig
│   │   ├── analyzer.py        # TopologyAnalyzer
│   │   └── converters/        # String/Pattern converters
│   └── validation/
│       ├── response_validator.py  # ValidationProcessor
│       └── types.py           # ActionType, ValidationResult
├── environment/
│   ├── tools.py               # Tool utilities
│   ├── utils.py               # Schema generation
│   ├── web_browser.py         # Browser automation (Playwright)
│   ├── browser_utils.py       # Browser utilities
│   ├── web_tools.py           # Web content tools
│   ├── search_tools.py        # Search tools
│   ├── bash_tools.py          # Bash command tools
│   ├── operator.py            # Environment operator
│   ├── tool_response.py       # Tool response models
│   └── file_operations/       # File handling toolkit
│       ├── core.py            # Core file operations
│       ├── config.py          # FileOperationConfig
│       ├── readers.py         # File readers
│       ├── editors.py         # File editors
│       ├── search.py          # File search
│       ├── security.py        # Security features
│       ├── token_estimation.py # Token estimation
│       ├── data_models.py     # Data models
│       ├── handlers/          # Type-specific handlers
│       │   ├── base.py
│       │   ├── text.py
│       │   ├── pdf_handler.py
│       │   └── image_handler.py
│       └── parsers/           # File parsers
│           └── pdf_extractor.py
├── models/
│   ├── models.py              # BaseAPIModel, BaseLocalModel, ModelConfig
│   ├── response_models.py     # HarmonizedResponse
│   ├── processors.py          # Response processors
│   └── utils.py               # Model utilities
├── learning/
│   └── rl.py                  # Reinforcement learning utilities
├── inference/
│   └── __init__.py            # Inference utilities
└── utils/
    ├── parsing.py             # Parsing utilities
    ├── tokens.py              # Token utilities
    ├── monitoring.py          # Monitoring utilities
    ├── display.py             # Display utilities
    └── schema_utils.py        # Schema utilities

docs/
├── api/                       # API reference
├── concepts/                  # Conceptual guides
├── getting-started/           # Quick start guides
├── guides/                    # How-to guides
├── use-cases/                 # Use case examples
├── project/                   # Project overview
└── contributing/              # Contribution guidelines

examples/
├── real_world/               # Production-ready examples
├── 00_documentation_examples/ # Tutorial examples
├── 01_IP_Valuation/          # IP valuation example
├── 02_financial_analyst/     # Financial analysis example
└── notebooks/                # Jupyter notebooks
```

---

## License

MARSYS is released under the **Apache License 2.0**. See [LICENSE](LICENSE) for full terms.

Copyright 2025 Marsys Project
Original Author: [rezaho](https://github.com/rezaho)

---

**Last Updated**: 2025-12-11
**Framework Version**: 0.1-beta
