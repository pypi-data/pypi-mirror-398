# Critical Multi-Agent Patterns & Implementation

## 🎉 FRAMEWORK CORE COMPLETE!

## Migration Context (Updated Session 10 - 2025-07-13)
MARS framework coordination system core is now complete! All major components implemented and tested:
- ✅ **Orchestra**: High-level API with `Orchestra.run(task, topology)`
- ✅ **Router**: Complete routing logic for all action types
- ✅ **ValidationProcessor**: Centralized response parsing
- ✅ **DynamicBranchSpawner**: Runtime branch creation
- ✅ **All Patterns**: 5/5 multi-agent patterns fully supported
- ✅ **All Tests**: Passing (11/11 coordination tests + 5 integration tests)
- ✅ **StateManager**: Full persistence with checkpoints
- ✅ **RulesEngine**: Complete with 6+ rule types
- ✅ **Real Examples**: OpenAI, Anthropic, and mixed provider examples

### Completed in Session 10:
1. ✅ Integration tests for all 5 patterns
2. ✅ StateManager with FileStorageBackend
3. ✅ RulesEngine with comprehensive rules
4. ✅ 3 real-world examples with different LLMs

## Five Critical Multi-Agent Patterns with Detailed Analysis

### Pattern 1: Hub-and-Spoke (Planner + Sequential Executors) ✅
```
                    PlannerAgent
                   /     |      \
                  ↓      ↓       ↓
           ExecutorAgent1 ExecutorAgent2 ExecutorAgent3
                  ↓      ↓       ↓
                    PlannerAgent
```

**System Architecture Flow**:
```
1. User → PlannerAgent: "Analyze sales data"
2. PlannerAgent creates plan:
   - Step 1: ExecutorAgent1 extracts data
   - Step 2: ExecutorAgent2 cleans data  
   - Step 3: ExecutorAgent3 generates report
3. PlannerAgent → ExecutorAgent1: "Extract Q4 sales"
4. ExecutorAgent1 → PlannerAgent: Returns data
5. PlannerAgent → ExecutorAgent2: "Clean this data"
6. ExecutorAgent2 → PlannerAgent: Returns cleaned data
7. PlannerAgent → ExecutorAgent3: "Generate report"
8. ExecutorAgent3 → PlannerAgent: Returns report
9. PlannerAgent → User: Final consolidated report
```

**Data Flow Analysis**:
- **Memory**: Single CONVERSATION branch with shared memory
- **Control**: PlannerAgent maintains full control
- **State**: All state tracked in branch memory
- **Efficiency**: Sequential execution, no parallelism

**Implementation**:
```python
topology = TopologyDefinition(
    nodes=["User", "PlannerAgent", "ExecutorAgent1", "ExecutorAgent2", "ExecutorAgent3"],
    edges=[
        "User -> PlannerAgent",
        "PlannerAgent <-> ExecutorAgent1",
        "PlannerAgent <-> ExecutorAgent2", 
        "PlannerAgent <-> ExecutorAgent3"
    ]
)
# Creates single CONVERSATION branch
```

### Pattern 2: Dynamic Parallel Execution (Runtime Decision) ✅
```
                    PlannerAgent
                   (decides at runtime)
                   /            \
                  ↓              ↓
        [Parallel Branch 1]  [Parallel Branch 2]
         ExecutorAgent1       ExecutorAgent2
                  ↓              ↓
                   \            /
                    PlannerAgent
                   (aggregates results)
```

**System Architecture Flow**:
```
1. User → PlannerAgent: "Gather competitive intelligence"
2. PlannerAgent analyzes request
3. PlannerAgent returns: {
       "next_action": "parallel_invoke",
       "agents": ["WebSearchAgent", "DatabaseAgent", "APIAgent"],
       "action_input": {
           "WebSearchAgent": "Search competitor pricing",
           "DatabaseAgent": "Query historical data",
           "APIAgent": "Fetch market trends"
       }
   }
4. System spawns 3 child branches in parallel:
   - Branch 1: WebSearchAgent executes
   - Branch 2: DatabaseAgent executes  
   - Branch 3: APIAgent executes
5. Parent branch enters WAITING state
6. All child branches complete
7. System aggregates results for PlannerAgent
8. PlannerAgent resumes with all data
9. PlannerAgent → User: Consolidated intelligence report
```

**Data Flow Analysis**:
- **Memory**: Parent branch + isolated child branches
- **Control**: Agent-initiated parallelism
- **State**: Parent waits, children independent
- **Efficiency**: True parallel execution

**Implementation**:
```python
# Agent decides parallelism at runtime
return {
    "next_action": "parallel_invoke",
    "agents": ["Agent1", "Agent2", "Agent3"],
    "wait_for_all": True,
    "action_input": {...}
}
```

### Pattern 3: Multi-Level Mixed Topology ✅
```
User ─┬─→ ResearchAgent (12 steps, 6 tools) ────────┐
      │                                              ↓
      └─→ CoordinatorAgent ←→ AnalystAgent ←→ ReviewerAgent ─→ SummaryAgent
                          (conversation loop)
```

**System Architecture Flow**:
```
1. User request triggers 2 parallel branches:
   - Branch A: ResearchAgent (independent, tool-heavy)
   - Branch B: Conversation branch (Coordinator ↔ Analyst ↔ Reviewer)

2. Branch A execution:
   - ResearchAgent uses 6 different tools
   - Performs 12 sequential steps
   - Builds comprehensive dataset

3. Branch B execution (single conversation branch):
   - CoordinatorAgent: "Analyst, examine this aspect"
   - AnalystAgent: "Here's my analysis, Reviewer please verify"
   - ReviewerAgent: "Found issues, Analyst please revise"
   - AnalystAgent: "Revised analysis ready"
   - CoordinatorAgent: "Approved, moving forward"

4. Synchronization at SummaryAgent:
   - Waits for both branches to complete
   - Receives: ResearchAgent data + Conversation conclusions
   - Generates final summary

5. SummaryAgent → User: Integrated final report
```

**Data Flow Analysis**:
- **Memory**: 2 parallel branches + convergence
- **Control**: Topology-driven parallelism
- **State**: Independent branch states
- **Efficiency**: Parallel research + collaborative review

### Pattern 4: Hierarchical Team Structure ✅
```
                 SupervisorAgent
                /       |        \
               ↓        ↓         ↓
        TeamLead1   TeamLead2   TeamLead3
           / \         / \         / \
          ↓   ↓       ↓   ↓       ↓   ↓
       Worker1 W2   Worker3 W4  Worker5 W6
```

**System Architecture Flow**:
```
1. User → SupervisorAgent: "Complete project X"

2. SupervisorAgent analyzes and delegates:
   return {
       "next_action": "parallel_invoke",
       "agents": ["TeamLead1", "TeamLead2", "TeamLead3"],
       "action_input": {
           "TeamLead1": "Handle frontend tasks",
           "TeamLead2": "Handle backend tasks",
           "TeamLead3": "Handle infrastructure"
       }
   }

3. Each TeamLead (in parallel branches) further delegates:
   TeamLead1 returns: {
       "next_action": "parallel_invoke",
       "agents": ["UIWorker", "UXWorker"],
       "action_input": {...}
   }

4. Nested parallel execution:
   - 3 TeamLead branches running
   - Each spawns 2 worker sub-branches
   - Total: 9 agents executing in parallel

5. Results bubble up:
   - Workers → TeamLeads (aggregate)
   - TeamLeads → Supervisor (aggregate)
   - Supervisor → User (final report)
```

**Data Flow Analysis**:
- **Memory**: Hierarchical branch isolation
- **Control**: Multi-level agent decisions
- **State**: Parent-child branch relationships
- **Efficiency**: Massive parallelism possible

### Pattern 5: Swarm Intelligence (Emergent Behavior) ✅
```
         ┌─→ SwarmAgent1 ←─┐
         │                 │
    Coordinator ←────────→ SwarmAgent2
         │                 │
         └─→ SwarmAgent3 ←─┘
         
(Agents can communicate with each other)
```

**System Architecture Flow**:
```
1. User → Coordinator: "Find optimal solution"

2. Coordinator broadcasts to swarm:
   return {
       "next_action": "parallel_invoke",
       "agents": ["SwarmAgent1", "SwarmAgent2", "SwarmAgent3"],
       "action_input": "Explore solution space"
   }

3. Swarm agents execute with inter-communication:
   - SwarmAgent1 explores path A
   - SwarmAgent1 → SwarmAgent2: "Found promising direction"
   - SwarmAgent2 adjusts search based on Agent1's finding
   - SwarmAgent2 → SwarmAgent3: "Avoid this area"
   - SwarmAgent3 → SwarmAgent1: "Better solution here"

4. Dynamic convergence:
   - Agents share discoveries in real-time
   - Emergent consensus forms
   - Best solution propagates through swarm

5. Coordinator aggregates final consensus
6. Coordinator → User: Optimal solution found by swarm
```

**Data Flow Analysis**:
- **Memory**: Shared swarm memory space
- **Control**: Decentralized decision making
- **State**: Emergent from agent interactions
- **Efficiency**: Explores solution space in parallel

**Implementation Considerations**:
```python
topology = TopologyDefinition(
    nodes=["Coordinator", "SwarmAgent1", "SwarmAgent2", "SwarmAgent3"],
    edges=[
        "Coordinator <-> SwarmAgent1",
        "Coordinator <-> SwarmAgent2",
        "Coordinator <-> SwarmAgent3",
        "SwarmAgent1 <-> SwarmAgent2",
        "SwarmAgent2 <-> SwarmAgent3",
        "SwarmAgent3 <-> SwarmAgent1"
    ],
    rules=["parallel(SwarmAgent1, SwarmAgent2, SwarmAgent3)"]
)
```

## Current Implementation Status

### ✅ All Patterns Fully Supported
1. **Pattern 1**: Hub-and-Spoke (single CONVERSATION branch)
2. **Pattern 2**: Dynamic Parallel (agent-initiated parallelism)
3. **Pattern 3**: Multi-Level Mixed (topology-driven parallelism)
4. **Pattern 4**: Hierarchical Teams (nested parallel_invoke)
5. **Pattern 5**: Swarm Intelligence (inter-agent communication via invoke_agent)

### ✅ All Core Components Implemented
1. **Router**: Full routing logic with all action types ✅
2. **Orchestra**: Complete high-level coordination API ✅
3. **ValidationProcessor**: Centralized response parsing ✅
4. **DynamicBranchSpawner**: Runtime branch creation ✅
5. **All Tests**: Passing (11/11 coordination tests) ✅

## Component Architecture & Data Flow

### 1. Topology Definition → Execution Plan
```python
topology = TopologyDefinition(
    nodes=["User", "Agent1", "Agent2", "Agent3"],
    edges=["User -> Agent1", "Agent1 <-> Agent2", "Agent2 -> Agent3"],
    rules=["parallel(Agent1, Agent2)", "max_turns(Agent1 <-> Agent2, 5)"]
)
↓
TopologyAnalyzer.analyze() → TopologyGraph
↓
DynamicBranchSpawner monitors execution
```

### 2. Branch Execution Flow
```
User Request → Orchestra.run(task, topology)
    ↓
Initial Branch Creation (entry points)
    ↓
BranchExecutor.execute_branch()
    ├─→ StepExecutor.execute_step()
    │      ├─→ Prepare memory (inject)
    │      ├─→ Agent.run_step() → _run() [PURE]
    │      └─→ ValidationProcessor.process_response()
    │
    └─→ Check completion/routing
         ├─→ If divergence: spawn child branches
         ├─→ If parallel_invoke: create children + wait
         └─→ If convergence: wait + aggregate
```

### 3. Agent Response Processing
```
Agent._run() returns response
    ↓
ValidationProcessor (centralized parsing)
    ├─→ StructuredJSONProcessor (priority 100)
    ├─→ ToolCallProcessor (priority 90)  
    └─→ NaturalLanguageProcessor (priority 10)
    ↓
Extract action_type + validate permissions
    ↓
Router.route() → RoutingDecision
    ├─→ next_agent: Continue in branch
    ├─→ parallel_invoke: Spawn children
    ├─→ tool_call: Execute tools
    └─→ final_response: Complete branch
```

## How to Define and Run Each Pattern (Complete Code Examples)

### Pattern 1: Hub-and-Spoke Implementation

```python
from marsys.coordination import Orchestra, TopologyDefinition
from marsys.agents import Agent

# Define agents
planner = Agent(name="PlannerAgent", model_config={"model": "gpt-4"})
executor1 = Agent(name="ExecutorAgent1", model_config={"model": "gpt-3.5-turbo"})
executor2 = Agent(name="ExecutorAgent2", model_config={"model": "gpt-3.5-turbo"})
executor3 = Agent(name="ExecutorAgent3", model_config={"model": "gpt-3.5-turbo"})

# Define topology
topology = TopologyDefinition(
    nodes=["User", planner, executor1, executor2, executor3],
    edges=[
        "User -> PlannerAgent",
        "PlannerAgent <-> ExecutorAgent1",
        "PlannerAgent <-> ExecutorAgent2", 
        "PlannerAgent <-> ExecutorAgent3"
    ]
)

# Run with Orchestra (simple one-line API)
result = await Orchestra.run(
    task="Analyze Q4 sales data and generate report",
    topology=topology,
    context={"department": "sales"},
    max_steps=50
)

# Access results
print(f"Final report: {result.final_response}")
print(f"Execution took {result.total_steps} steps in {result.total_duration:.2f}s")
```

**Behind the Scenes - Request Flow:**
```
1. Orchestra.run() called
   └─> TopologyAnalyzer.analyze(topology)
       └─> Creates TopologyGraph with nodes and edges
       └─> Detects bidirectional edges (conversation patterns)
       └─> Returns analyzed graph

2. Orchestra creates initial branch
   └─> ExecutionBranch(type=CONVERSATION, agents=[Planner, Executor1, Executor2, Executor3])
   └─> Branch contains shared memory for all agents

3. BranchExecutor.execute_branch() starts
   └─> StepExecutor.execute_step(PlannerAgent, "Analyze Q4 sales...")
       └─> Injects empty memory (first step)
       └─> Calls PlannerAgent.run_step()
           └─> PlannerAgent._run() [PURE - no side effects]
           └─> Returns: {"next_action": "invoke_agent", "action_input": "ExecutorAgent1", "content": "Extract data"}

4. ValidationProcessor.process_response()
   └─> StructuredJSONProcessor detects JSON format
   └─> Extracts action_type = INVOKE_AGENT
   └─> Validates ExecutorAgent1 is in allowed transitions
   └─> Returns ValidationResult(is_valid=True, next_agents=["ExecutorAgent1"])

5. Router.route() determines next step
   └─> Creates ExecutionStep for ExecutorAgent1
   └─> Updates branch memory with PlannerAgent's response

6. Process repeats for each executor sequentially
```

**Data Flow:**
- Single shared memory array grows: [User request, Planner response, Executor1 response, Planner response, ...]
- Each agent sees full conversation history
- No parallel execution, strict sequential flow

### Pattern 2: Dynamic Parallel Execution Implementation

```python
# Define agents
planner = Agent(name="PlannerAgent", model_config={"model": "gpt-4"})
web_agent = Agent(name="WebSearchAgent", model_config={"model": "gpt-3.5-turbo"})
db_agent = Agent(name="DatabaseAgent", model_config={"model": "gpt-3.5-turbo"})
api_agent = Agent(name="APIAgent", model_config={"model": "gpt-3.5-turbo"})

# Define topology (note: no parallel rule, agent decides)
topology = TopologyDefinition(
    nodes=["User", planner, web_agent, db_agent, api_agent],
    edges=[
        "User -> PlannerAgent",
        "PlannerAgent -> WebSearchAgent",
        "PlannerAgent -> DatabaseAgent",
        "PlannerAgent -> APIAgent"
    ]
)

# PlannerAgent's _run() implementation decides parallelism
async def planner_run(self, prompt, context, **kwargs):
    # Analyze the request
    response = await self.model.run(prompt)
    
    # Agent decides to parallelize
    return {
        "thinking": "Need to gather data from multiple sources simultaneously",
        "next_action": "parallel_invoke",
        "agents": ["WebSearchAgent", "DatabaseAgent", "APIAgent"],
        "action_input": {
            "WebSearchAgent": "Search competitor pricing for Q4",
            "DatabaseAgent": "Query sales_db for historical trends", 
            "APIAgent": "Fetch market data from Bloomberg"
        }
    }

# Run with Orchestra API
result = await Orchestra.run(
    task="Gather competitive intelligence for Q4 planning",
    topology=topology,
    max_steps=100  # Allow for parallel execution + aggregation
)
```

**Behind the Scenes - Request Flow:**
```
1. Initial branch created for PlannerAgent
   └─> Branch ID: "main_planner_001"
   └─> Type: SIMPLE (single agent)

2. PlannerAgent executes and returns parallel_invoke
   └─> ValidationProcessor detects "parallel_invoke" action
   └─> Validates all target agents are reachable
   └─> Returns ValidationResult with multiple next_agents

3. DynamicBranchSpawner.handle_agent_initiated_parallelism()
   └─> Creates 3 child branches:
       ├─> Branch "child_web_001" (parent: main_planner_001)
       ├─> Branch "child_db_002" (parent: main_planner_001)
       └─> Branch "child_api_003" (parent: main_planner_001)
   └─> Sets parent branch state to WAITING
   └─> Returns 3 asyncio.Task objects

4. Parallel execution begins
   └─> 3 branches execute simultaneously
   └─> Each branch has isolated memory: [parent_context, agent_specific_input]
   └─> No cross-branch communication

5. As each child completes:
   └─> DynamicBranchSpawner.handle_child_completion()
   └─> Adds result to aggregation buffer
   └─> Checks if all children done

6. When all children complete:
   └─> Parent branch state changes from WAITING to RUNNING
   └─> Aggregated results injected: {
       "WebSearchAgent": {result},
       "DatabaseAgent": {result},
       "APIAgent": {result}
   }
   └─> PlannerAgent resumes with all data
```

**Data Flow:**
- Parent memory: [User request, Planner parallel decision]
- Child memories (isolated):
  - Web branch: [Context, "Search competitor pricing...", Web results]
  - DB branch: [Context, "Query sales_db...", DB results]
  - API branch: [Context, "Fetch market data...", API results]
- Parent resumes with aggregated child results

### Pattern 3: Multi-Level Mixed Topology Implementation

```python
# Define agents
research = Agent(name="ResearchAgent", model_config={"model": "gpt-4"}, tools=[...])
coordinator = Agent(name="CoordinatorAgent", model_config={"model": "gpt-4"})
analyst = Agent(name="AnalystAgent", model_config={"model": "gpt-4"})
reviewer = Agent(name="ReviewerAgent", model_config={"model": "gpt-3.5-turbo"})
summary = Agent(name="SummaryAgent", model_config={"model": "gpt-4"})

# Complex topology with parallel and conversation patterns
topology = TopologyDefinition(
    nodes=["User", research, coordinator, analyst, reviewer, summary],
    edges=[
        "User -> ResearchAgent",
        "User -> CoordinatorAgent",
        "CoordinatorAgent <-> AnalystAgent",  # Conversation loop
        "AnalystAgent <-> ReviewerAgent",      # Conversation loop
        "ResearchAgent -> SummaryAgent",
        "ReviewerAgent -> SummaryAgent"
    ],
    rules=[
        "parallel(ResearchAgent, CoordinatorAgent)",  # Explicit parallelism
        "wait_all(ResearchAgent, ReviewerAgent) -> SummaryAgent"
    ]
)

# Run complex analysis
result = await orchestra.run(
    task="Comprehensive market analysis with peer review",
    topology=topology
)
```

**Behind the Scenes - Request Flow:**
```
1. TopologyAnalyzer detects:
   └─> Divergence point: User (2 outgoing edges)
   └─> Conversation loop: Coordinator ↔ Analyst ↔ Reviewer
   └─> Convergence point: SummaryAgent (2 incoming edges)
   └─> Parallel rule reinforces divergence

2. Orchestra creates 2 initial branches:
   ├─> Branch "research_001" (SIMPLE type)
   │   └─> Single agent: ResearchAgent
   └─> Branch "conversation_002" (CONVERSATION type)
       └─> Multiple agents: [Coordinator, Analyst, Reviewer]

3. Parallel execution begins:

   Branch A (Research):
   └─> ResearchAgent.run_step()
       └─> Uses 6 tools sequentially
       └─> 12 internal steps with tool results
       └─> Memory grows: [task, tool1_result, tool2_result, ...]

   Branch B (Conversation):
   └─> CoordinatorAgent: "Analyst, please examine market trends"
   └─> AnalystAgent: "Initial analysis shows... Reviewer, please verify"
   └─> ReviewerAgent: "Found issues with methodology, please revise"
   └─> AnalystAgent: "Revised analysis... now shows..."
   └─> ReviewerAgent: "Approved. Key findings are..."
   └─> Conversation completes when reviewer satisfied

4. Synchronization at SummaryAgent:
   └─> DynamicBranchSpawner detects both branches done
   └─> Creates convergence context: {
       "ResearchAgent": {complete dataset},
       "ConversationBranch": {reviewed analysis}
   }
   └─> New branch created for SummaryAgent
   └─> SummaryAgent sees both inputs

5. SummaryAgent generates final report
```

**Data Flow:**
- Branch A memory: [task, step1, tool_call1, tool_result1, step2, ...]
- Branch B memory: [task, coordinator_msg, analyst_msg, reviewer_msg, ...]
- Convergence memory: [aggregated_inputs, summary_generation]
- No memory sharing between parallel branches until convergence

### Pattern 4: Hierarchical Team Implementation

```python
# Define hierarchy
supervisor = Agent(name="SupervisorAgent", model_config={"model": "gpt-4"})
frontend_lead = Agent(name="FrontendLead", model_config={"model": "gpt-4"})
backend_lead = Agent(name="BackendLead", model_config={"model": "gpt-4"})
infra_lead = Agent(name="InfraLead", model_config={"model": "gpt-4"})

# Workers
ui_worker = Agent(name="UIWorker", model_config={"model": "gpt-3.5-turbo"})
ux_worker = Agent(name="UXWorker", model_config={"model": "gpt-3.5-turbo"})
api_worker = Agent(name="APIWorker", model_config={"model": "gpt-3.5-turbo"})
db_worker = Agent(name="DBWorker", model_config={"model": "gpt-3.5-turbo"})
k8s_worker = Agent(name="K8sWorker", model_config={"model": "gpt-3.5-turbo"})
ci_worker = Agent(name="CIWorker", model_config={"model": "gpt-3.5-turbo"})

# Hierarchical topology
topology = TopologyDefinition(
    nodes=[
        "User", supervisor,
        frontend_lead, backend_lead, infra_lead,
        ui_worker, ux_worker, api_worker, db_worker, k8s_worker, ci_worker
    ],
    edges=[
        "User -> SupervisorAgent",
        "SupervisorAgent -> FrontendLead",
        "SupervisorAgent -> BackendLead", 
        "SupervisorAgent -> InfraLead",
        "FrontendLead -> UIWorker",
        "FrontendLead -> UXWorker",
        "BackendLead -> APIWorker",
        "BackendLead -> DBWorker",
        "InfraLead -> K8sWorker",
        "InfraLead -> CIWorker"
    ]
)

# Supervisor decides to parallelize
async def supervisor_run(self, prompt, context, **kwargs):
    return {
        "next_action": "parallel_invoke",
        "agents": ["FrontendLead", "BackendLead", "InfraLead"],
        "action_input": {
            "FrontendLead": "Design and implement user dashboard",
            "BackendLead": "Create REST API with database",
            "InfraLead": "Setup Kubernetes and CI/CD"
        }
    }

# Each lead also parallelizes
async def frontend_lead_run(self, prompt, context, **kwargs):
    return {
        "next_action": "parallel_invoke",
        "agents": ["UIWorker", "UXWorker"],
        "action_input": {
            "UIWorker": "Implement React components",
            "UXWorker": "Create wireframes and designs"
        }
    }
```

**Behind the Scenes - Request Flow:**
```
1. Initial execution:
   └─> Branch "main_001" created for SupervisorAgent
   └─> Supervisor returns parallel_invoke for 3 leads

2. First level parallelization:
   └─> DynamicBranchSpawner creates 3 child branches:
       ├─> Branch "lead_frontend_002" (parent: main_001)
       ├─> Branch "lead_backend_003" (parent: main_001)
       └─> Branch "lead_infra_004" (parent: main_001)
   └─> Main branch enters WAITING state

3. Second level parallelization (each lead executes):
   
   FrontendLead (branch 002):
   └─> Returns parallel_invoke for UI/UX workers
   └─> Spawner creates 2 grandchild branches:
       ├─> Branch "worker_ui_005" (parent: lead_frontend_002)
       └─> Branch "worker_ux_006" (parent: lead_frontend_002)
   └─> Frontend branch enters WAITING

   BackendLead (branch 003):
   └─> Returns parallel_invoke for API/DB workers
   └─> Creates branches 007, 008

   InfraLead (branch 004):
   └─> Returns parallel_invoke for K8s/CI workers
   └─> Creates branches 009, 010

4. Execution tree (all running in parallel):
   main_001 (WAITING)
   ├── lead_frontend_002 (WAITING)
   │   ├── worker_ui_005 (RUNNING)
   │   └── worker_ux_006 (RUNNING)
   ├── lead_backend_003 (WAITING)
   │   ├── worker_api_007 (RUNNING)
   │   └── worker_db_008 (RUNNING)
   └── lead_infra_004 (WAITING)
       ├── worker_k8s_009 (RUNNING)
       └── worker_ci_010 (RUNNING)

5. Result aggregation (bottom-up):
   └─> Workers complete → Results to respective leads
   └─> Leads aggregate and complete → Results to supervisor
   └─> Supervisor aggregates all → Final report to user
```

**Data Flow:**
- 9 isolated memory branches during execution
- Hierarchical aggregation preserves structure
- Parent branches only see aggregated child results
- No direct worker-to-worker communication

### Pattern 5: Swarm Intelligence Implementation

```python
# Define swarm agents
coordinator = Agent(name="Coordinator", model_config={"model": "gpt-4"})
swarm1 = Agent(name="SwarmAgent1", model_config={"model": "gpt-3.5-turbo"})
swarm2 = Agent(name="SwarmAgent2", model_config={"model": "gpt-3.5-turbo"})
swarm3 = Agent(name="SwarmAgent3", model_config={"model": "gpt-3.5-turbo"})

# Full mesh topology for swarm
topology = TopologyDefinition(
    nodes=["User", coordinator, swarm1, swarm2, swarm3],
    edges=[
        "User -> Coordinator",
        "Coordinator <-> SwarmAgent1",
        "Coordinator <-> SwarmAgent2",
        "Coordinator <-> SwarmAgent3",
        # Inter-swarm communication
        "SwarmAgent1 <-> SwarmAgent2",
        "SwarmAgent2 <-> SwarmAgent3",
        "SwarmAgent3 <-> SwarmAgent1"
    ],
    rules=[
        "parallel(SwarmAgent1, SwarmAgent2, SwarmAgent3)",
        "max_iterations(SwarmAgent1 <-> SwarmAgent2, 10)",
        "shared_memory(SwarmAgent1, SwarmAgent2, SwarmAgent3)"  # Future feature
    ]
)

# Swarm agent behavior
async def swarm_agent_run(self, prompt, context, **kwargs):
    # Check messages from other swarm agents
    discoveries = self._extract_swarm_discoveries(context)
    
    # Explore based on collective knowledge
    my_exploration = await self._explore_solution_space(prompt, discoveries)
    
    # Decide next action based on findings
    if self._found_optimal_solution(my_exploration):
        return {"next_action": "final_response", "content": my_exploration}
    elif self._should_inform_peer(my_exploration):
        return {
            "next_action": "invoke_agent",
            "action_input": self._select_peer(),
            "content": f"Discovery: {my_exploration}"
        }
    else:
        return {"next_action": "continue_exploration", "content": my_exploration}
```

**Behind the Scenes - Request Flow:**
```
1. Coordinator initiates swarm:
   └─> Returns parallel_invoke for all swarm agents
   └─> Creates 3 parallel branches

2. Initial parallel exploration:
   ├─> SwarmAgent1 explores solution space sector A
   ├─> SwarmAgent2 explores solution space sector B
   └─> SwarmAgent3 explores solution space sector C

3. Dynamic inter-communication phase:
   
   Iteration 1:
   └─> Agent1 finds promising direction
   └─> Returns: invoke_agent(SwarmAgent2, "Found optimum near X")
   └─> Creates conversation sub-branch: Agent1 ↔ Agent2
   
   Iteration 2:
   └─> Agent2 adjusts search based on Agent1's info
   └─> Returns: invoke_agent(SwarmAgent3, "Confirming X, avoid Y")
   └─> Creates new sub-branch: Agent2 ↔ Agent3
   
   Iteration 3:
   └─> Agent3 validates and refines
   └─> Returns: invoke_agent(SwarmAgent1, "Better solution at X'")
   └─> Creates sub-branch: Agent3 ↔ Agent1

4. Convergence detection:
   └─> Agents reach consensus on optimal solution
   └─> All return similar final_response
   └─> Coordinator aggregates consensus

5. Branch structure evolves dynamically:
   coordinator_branch
   ├── swarm1_branch (shifts between exploring/communicating)
   ├── swarm2_branch (shifts between exploring/communicating)
   └── swarm3_branch (shifts between exploring/communicating)
   
   Plus temporary conversation branches:
   - conv_1_2 (when Agent1 talks to Agent2)
   - conv_2_3 (when Agent2 talks to Agent3)
   - conv_3_1 (when Agent3 talks to Agent1)
```

**Data Flow:**
- Initial: 3 parallel isolated memories
- During communication: Temporary shared conversation branches
- Information propagates through peer-to-peer messages
- Emergent behavior from local interactions
- Final: Aggregated consensus from all agents

## Key Design Decisions

1. **Agent Autonomy**: Agents can decide parallelism at runtime via `parallel_invoke`
2. **Branch Isolation**: Each branch has its own memory state
3. **Pure Logic**: Agent._run() has NO side effects
4. **Centralized Parsing**: ALL response parsing in ValidationProcessor
5. **Dynamic Creation**: Branches created on-the-fly, not pre-allocated