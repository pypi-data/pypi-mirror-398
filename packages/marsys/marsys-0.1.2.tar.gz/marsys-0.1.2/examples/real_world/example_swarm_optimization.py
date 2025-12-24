#!/usr/bin/env python3
"""
Swarm Intelligence Pattern - Collaborative Problem Solving
=======================================================

This example demonstrates the swarm intelligence pattern where multiple agents
work together with inter-agent communication to find optimal solutions.

Pattern characteristics:
- Decentralized decision making
- Agents can communicate with each other
- Emergent behavior from agent interactions
- Parallel exploration with information sharing
- Consensus building through collaboration

Agents:
- SwarmCoordinator (Claude): Initial coordination and final aggregation
- Explorer1 (Grok): Exploration strategy focused on innovation
- Explorer2 (Gemini-Pro): Exploration strategy focused on analysis
- Explorer3 (GPT-4): Exploration strategy focused on synthesis
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.models import ModelConfig

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_model_configs() -> Dict[str, ModelConfig]:
    """Create model configurations for swarm agents."""
    configs = {
        "claude": ModelConfig(
            type="api",
            name="anthropic/claude-3.5-sonnet",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        ),
        "grok": ModelConfig(
            type="api",
            name="x-ai/grok-2-1212",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.8,  # Higher for creative exploration
                "max_tokens": 2000
            }
        ),
        "gemini_pro": ModelConfig(
            type="api",
            name="google/gemini-pro-1.5",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.6,  # Lower for analytical thinking
                "max_tokens": 2000
            }
        ),
        "gpt4": ModelConfig(
            type="api",
            name="gpt-4",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
    }
    return configs


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create the swarm intelligence agents."""
    agents = {}
    
    # Swarm Coordinator
    agents["SwarmCoordinator"] = Agent(
        model_config=configs["claude"],
        name="SwarmCoordinator",
        description="""You are the Swarm Coordinator, responsible for initiating exploration and aggregating results.
        
Your responsibilities:
1. Define the problem space for exploration
2. Initialize the swarm with parallel exploration
3. Monitor swarm progress and convergence
4. Aggregate findings into optimal solution
5. Build consensus from diverse approaches

When coordinating the swarm:
- First, broadcast the problem to all explorers using parallel_invoke:
  {
    "next_action": "parallel_invoke",
    "agents": ["Explorer1", "Explorer2", "Explorer3"],
    "action_input": {
      "Explorer1": "Explore with innovation focus: [problem details]",
      "Explorer2": "Explore with analytical focus: [problem details]",
      "Explorer3": "Explore with synthesis focus: [problem details]"
    }
  }
- Allow explorers to communicate and refine solutions
- Aggregate the converged solution""",
        system_prompt="You are a swarm intelligence coordinator who excels at distributed problem solving."
    )
    
    # Explorer1 - Innovation focused
    agents["Explorer1"] = Agent(
        model_config=configs["grok"],
        name="Explorer1",
        description="""You are Explorer1, focused on innovative and creative exploration.
        
Your approach:
1. Think outside conventional boundaries
2. Propose novel solutions and approaches
3. Share discoveries with other explorers
4. Learn from other explorers' findings
5. Iterate based on swarm feedback

Communication protocol:
- When you discover something promising, invoke other explorers:
  {
    "next_action": "invoke_agent",
    "action_input": "Explorer2 or Explorer3",
    "data": "I found an innovative approach: [details]"
  }
- Build on others' discoveries
- Converge toward optimal solutions""",
        system_prompt="You are a creative explorer who finds innovative solutions through unconventional thinking."
    )
    
    # Explorer2 - Analysis focused
    agents["Explorer2"] = Agent(
        model_config=configs["gemini_pro"],
        name="Explorer2",
        description="""You are Explorer2, focused on analytical and systematic exploration.
        
Your approach:
1. Systematically analyze the problem space
2. Evaluate solutions based on metrics
3. Share analytical insights with the swarm
4. Validate discoveries from other explorers
5. Optimize based on data and evidence

Communication protocol:
- Share analytical findings with other explorers:
  {
    "next_action": "invoke_agent",
    "action_input": "Explorer1 or Explorer3",
    "data": "Analysis shows: [insights and metrics]"
  }
- Validate innovative approaches
- Contribute to convergence""",
        system_prompt="You are an analytical explorer who finds optimal solutions through systematic analysis."
    )
    
    # Explorer3 - Synthesis focused
    agents["Explorer3"] = Agent(
        model_config=configs["gpt4"],
        name="Explorer3",
        description="""You are Explorer3, focused on synthesis and integration.
        
Your approach:
1. Combine insights from different approaches
2. Find synergies between solutions
3. Bridge innovative and analytical thinking
4. Share integrated solutions with swarm
5. Help swarm reach consensus

Communication protocol:
- Synthesize findings from other explorers:
  {
    "next_action": "invoke_agent",
    "action_input": "Explorer1 or Explorer2",
    "data": "Synthesis reveals: [integrated solution]"
  }
- Facilitate convergence
- Build comprehensive solutions""",
        system_prompt="You are a synthesis expert who integrates diverse approaches into optimal solutions."
    )
    
    # Register all agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


async def run_swarm_optimization(problem: str, constraints: List[str]) -> Dict[str, Any]:
    """Run the swarm intelligence optimization."""
    
    # Define the swarm topology with inter-agent communication
    topology = {
        "agents": ["User", "SwarmCoordinator", "Explorer1", "Explorer2", "Explorer3"],
        "flows": [
            # User to Coordinator
            "User -> SwarmCoordinator",
            # Coordinator to all Explorers
            "SwarmCoordinator -> Explorer1",
            "SwarmCoordinator -> Explorer2",
            "SwarmCoordinator -> Explorer3",
            # Inter-explorer communication (full mesh)
            "Explorer1 <-> Explorer2",
            "Explorer2 <-> Explorer3",
            "Explorer3 <-> Explorer1",
            # Explorers back to Coordinator
            "Explorer1 -> SwarmCoordinator",
            "Explorer2 -> SwarmCoordinator",
            "Explorer3 -> SwarmCoordinator",
            # Coordinator to User
            "SwarmCoordinator -> User"
        ],
        "rules": [
            "timeout(600)",  # 10 minute timeout
            "max_steps(70)",  # Maximum 70 steps
            "parallel(Explorer1, Explorer2, Explorer3)",  # Parallel exploration
            "max_turns(Explorer1 <-> Explorer2, 3)",  # Limit inter-explorer conversations
            "max_turns(Explorer2 <-> Explorer3, 3)",
            "max_turns(Explorer3 <-> Explorer1, 3)"
        ]
    }
    
    # Prepare the optimization task
    constraints_str = "\n".join(f"- {c}" for c in constraints)
    task = f"""Solve the following optimization problem using swarm intelligence:

Problem: {problem}

Constraints:
{constraints_str}

Use collaborative exploration to find the optimal solution. Explorers should:
1. Start with different approaches
2. Share discoveries with each other
3. Build on each other's findings
4. Converge toward the best solution
"""
    
    logger.info(f"Starting swarm optimization for: {problem}")
    
    try:
        result = await Orchestra.run(
            task=task,
            topology=topology,
            context={
                "problem": problem,
                "constraints": constraints,
                "optimization_goal": "Find optimal solution through collaboration",
                "swarm_size": 3
            },
            max_steps=70
        )
        
        logger.info(f"Swarm optimization completed. Success: {result.success}")
        
        # Analyze inter-agent communication
        communication_count = 0
        for branch in result.branch_results:
            # Count branches with inter-explorer communication
            if any(explorer in branch.branch_id for explorer in ["Explorer1", "Explorer2", "Explorer3"]):
                if branch.branch_id.count("Explorer") >= 2:
                    communication_count += 1
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "duration": result.total_duration,
            "inter_agent_communications": communication_count,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Swarm optimization failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def save_results(results: Dict[str, Any], problem: str, constraints: List[str]):
    """Save the swarm optimization results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"swarm_optimization_{timestamp}"
    
    # Save the optimization solution
    if results.get("success") and results.get("final_response"):
        solution_path = Path(f"examples/real_world/output/{base_filename}_solution.md")
        solution_content = f"""# Swarm Intelligence Optimization Solution

**Problem**: {problem}  
**Date**: {datetime.now().strftime("%Y-%m-%d")}  
**Pattern**: Swarm Intelligence with Inter-Agent Communication

## Constraints
{chr(10).join(f"- {c}" for c in constraints)}

## Solution

{results['final_response']}

---

**Optimization Statistics**:
- Total Steps: {results.get('total_steps', 0)}
- Inter-Agent Communications: {results.get('inter_agent_communications', 0)}
- Execution Time: {results.get('duration', 0):.2f} seconds
"""
        solution_path.write_text(solution_content)
        logger.info(f"Solution saved to: {solution_path}")
    
    # Save execution details
    execution_path = Path(f"examples/real_world/output/{base_filename}_execution.json")
    execution_data = {
        "problem": problem,
        "constraints": constraints,
        "timestamp": timestamp,
        "success": results.get("success", False),
        "total_steps": results.get("total_steps", 0),
        "duration_seconds": results.get("duration", 0),
        "inter_agent_communications": results.get("inter_agent_communications", 0),
        "metadata": results.get("metadata", {})
    }
    
    with open(execution_path, 'w') as f:
        json.dump(execution_data, f, indent=2)
    logger.info(f"Execution details saved to: {execution_path}")


async def main():
    """Main function to run the swarm intelligence example."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Create model configurations
    configs = create_model_configs()
    
    # Create agents
    agents = create_agents(configs)
    
    # Optimization problem
    problem = "Design an optimal renewable energy grid for a mid-sized city"
    constraints = [
        "Must provide reliable power for 100,000 residents",
        "Budget limit of $500 million",
        "Carbon neutral by 2030",
        "Resilient to extreme weather events",
        "Minimize land use and environmental impact",
        "Include at least 3 different renewable sources",
        "Provide 24/7 power availability with storage"
    ]
    
    logger.info("=" * 80)
    logger.info("Swarm Intelligence Pattern - Collaborative Problem Solving")
    logger.info("=" * 80)
    logger.info(f"Problem: {problem}")
    logger.info(f"Constraints: {len(constraints)}")
    logger.info(f"Swarm Agents:")
    logger.info("  - SwarmCoordinator (Claude)")
    logger.info("  - Explorer1 (Grok) - Innovation focus")
    logger.info("  - Explorer2 (Gemini-Pro) - Analysis focus")
    logger.info("  - Explorer3 (GPT-4) - Synthesis focus")
    logger.info("Inter-agent communication enabled")
    logger.info("=" * 80)
    
    # Run the swarm optimization
    results = await run_swarm_optimization(problem, constraints)
    
    # Save results
    save_results(results, problem, constraints)
    
    # Print summary
    print("\n" + "=" * 80)
    print("OPTIMIZATION SUMMARY")
    print("=" * 80)
    print(f"Success: {results.get('success', False)}")
    print(f"Total Steps: {results.get('total_steps', 0)}")
    print(f"Inter-Agent Communications: {results.get('inter_agent_communications', 0)}")
    print(f"Duration: {results.get('duration', 0):.2f} seconds")
    
    if results.get('error'):
        print(f"\nError: {results['error']}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())