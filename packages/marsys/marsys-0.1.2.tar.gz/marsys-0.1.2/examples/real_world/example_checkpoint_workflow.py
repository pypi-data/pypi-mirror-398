#!/usr/bin/env python3
"""
Checkpoint/Restore Example - Complex Workflow with Recovery Points
===============================================================

This example demonstrates advanced checkpoint functionality in multi-agent workflows.
It shows how to create checkpoints at key stages, restore to previous states,
and explore different execution paths from the same checkpoint.

Features demonstrated:
- Creating named checkpoints at strategic points
- Restoring workflow to previous checkpoints  
- Comparing different execution paths
- Checkpoint management and cleanup
- Recovery from failures using checkpoints

Workflow:
- Multi-stage decision-making process
- Checkpoints after each major decision
- Ability to explore alternative paths
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.coordination.state.state_manager import StateManager, FileStorageBackend
from marsys.models import ModelConfig

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_model_configs() -> Dict[str, ModelConfig]:
    """Create model configurations for agents."""
    return {
        "gpt4": ModelConfig(
            type="api",
            name="gpt-4",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={"temperature": 0.7, "max_tokens": 2000}
        ),
        "claude": ModelConfig(
            type="api",
            name="claude-3-sonnet-20240229",
            provider="anthropic",  
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            parameters={"temperature": 0.7, "max_tokens": 2000}
        ),
        "gemini": ModelConfig(
            type="api",
            name="gemini-1.5-pro",
            provider="google",
            api_key=os.getenv("GOOGLE_API_KEY"),
            parameters={"temperature": 0.7, "max_tokens": 2000}
        )
    }


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create agents for the checkpoint workflow."""
    agents = {}
    
    # Strategic Planner
    agents["StrategicPlanner"] = Agent(
        model_config=configs["gpt4"],
        name="StrategicPlanner",
        goal="Lead business expansion decisions by synthesizing market and risk analysis",
        instruction="""You are the Strategic Planner for a business expansion decision.

Your tasks:
        1. Analyze the business expansion opportunity
        2. Create multiple strategic options
        3. Delegate market analysis to MarketAnalyst
        4. Delegate risk assessment to RiskAssessor
        5. Make final recommendation based on inputs

Consider multiple strategic paths and their implications.""",
        system_prompt="You are a strategic business planner who creates comprehensive expansion strategies."
    )
    
    # Market Analyst
    agents["MarketAnalyst"] = Agent(
        model_config=configs["claude"],
        name="MarketAnalyst",
        goal="Evaluate market opportunities with data-driven analysis and scoring",
        instruction="""You are the Market Analyst evaluating market opportunities.

Your tasks:
        1. Analyze market size and growth potential
        2. Evaluate competitive landscape
        3. Identify target customer segments
        4. Assess market entry barriers
        5. Provide market opportunity score (1-10)

Be thorough and data-driven in your analysis.""",
        system_prompt="You are a market analysis expert who provides detailed market insights."
    )
    
    # Risk Assessor
    agents["RiskAssessor"] = Agent(
        model_config=configs["gemini"],
        name="RiskAssessor",
        goal="Identify and assess comprehensive business risks with scoring",
        instruction="""You are the Risk Assessor evaluating business risks.

Your tasks:
        1. Identify operational risks
        2. Assess financial risks
        3. Evaluate regulatory compliance risks
        4. Consider reputational risks
        5. Provide overall risk score (1-10, where 10 is highest risk)

Be comprehensive in identifying potential risks.""",
        system_prompt="You are a risk assessment expert who identifies and evaluates business risks."
    )
    
    # Register agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


class CheckpointWorkflow:
    """Manages the checkpoint workflow with state tracking."""
    
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.backend = FileStorageBackend(state_dir)
        self.state_manager = StateManager(self.backend)
        self.orchestra = Orchestra(
            agent_registry=AgentRegistry,
            state_manager=self.state_manager
        )
        self.checkpoints: Dict[str, str] = {}  # name -> checkpoint_id mapping
        self.session_id: Optional[str] = None
        
    async def run_with_checkpoints(self, scenario: str) -> Dict[str, Any]:
        """Run workflow with checkpoint creation at key stages."""
        
        # Define topology
        topology = {
            "agents": ["User", "StrategicPlanner", "MarketAnalyst", "RiskAssessor"],
            "flows": [
                "User -> StrategicPlanner",
                "StrategicPlanner -> MarketAnalyst",
                "MarketAnalyst -> StrategicPlanner",
                "StrategicPlanner -> RiskAssessor",
                "RiskAssessor -> StrategicPlanner",
                "StrategicPlanner -> User"
            ],
            "rules": [
                "timeout(600)",  # 10 minute timeout
                "max_steps(40)"
            ]
        }
        
        # Create session
        session = await self.orchestra.create_session(
            task=f"Evaluate business expansion opportunity: {scenario}",
            context={
                "scenario": scenario,
                "decision_type": "strategic_expansion",
                "checkpoint_enabled": True
            },
            enable_pause=True
        )
        self.session_id = session.id
        
        logger.info(f"Created session: {self.session_id}")
        
        # Run workflow
        result = await session.run(topology)
        
        # Create final checkpoint
        if result.success:
            await self.create_checkpoint("final_decision")
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "session_id": self.session_id,
            "checkpoints": list(self.checkpoints.keys())
        }
    
    async def create_checkpoint(self, name: str) -> str:
        """Create a named checkpoint."""
        if not self.session_id:
            raise ValueError("No active session")
            
        checkpoint_id = await self.orchestra.create_checkpoint(
            self.session_id,
            name
        )
        self.checkpoints[name] = checkpoint_id
        logger.info(f"Created checkpoint '{name}': {checkpoint_id}")
        return checkpoint_id
    
    async def restore_checkpoint(self, name: str) -> Dict[str, Any]:
        """Restore workflow state from a named checkpoint."""
        if name not in self.checkpoints:
            raise ValueError(f"Checkpoint '{name}' not found")
            
        checkpoint_id = self.checkpoints[name]
        state = await self.orchestra.restore_checkpoint(checkpoint_id)
        
        logger.info(f"Restored checkpoint '{name}': {checkpoint_id}")
        return state
    
    async def explore_alternative_path(self, checkpoint_name: str, modification: str) -> Dict[str, Any]:
        """Explore an alternative execution path from a checkpoint."""
        # Restore to checkpoint
        state = await self.restore_checkpoint(checkpoint_name)
        
        # Create new session from restored state
        session = await self.orchestra.create_session(
            task=f"Continue with modification: {modification}",
            context=state.get("context", {}),
            session_id=f"{self.session_id}_alt_{len(self.checkpoints)}"
        )
        
        # Continue execution with modification
        topology = {
            "agents": ["User", "StrategicPlanner", "MarketAnalyst", "RiskAssessor"],
            "flows": [
                "User -> StrategicPlanner",
                "StrategicPlanner -> MarketAnalyst",
                "MarketAnalyst -> StrategicPlanner",
                "StrategicPlanner -> RiskAssessor", 
                "RiskAssessor -> StrategicPlanner",
                "StrategicPlanner -> User"
            ],
            "rules": ["timeout(300)", "max_steps(20)"]
        }
        
        result = await session.run(topology)
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "modification": modification,
            "checkpoint_used": checkpoint_name
        }
    
    def list_checkpoints(self) -> List[Dict[str, str]]:
        """List all available checkpoints."""
        return [
            {"name": name, "id": checkpoint_id}
            for name, checkpoint_id in self.checkpoints.items()
        ]


async def demonstrate_checkpoint_workflow():
    """Demonstrate the checkpoint/restore functionality."""
    # Create state directory
    state_dir = Path("examples/real_world/output/checkpoint_storage")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Create workflow manager
    workflow = CheckpointWorkflow(state_dir)
    
    # Business expansion scenario
    scenario = "Opening a new tech startup branch in Southeast Asia"
    
    print("\n" + "=" * 80)
    print("CHECKPOINT/RESTORE WORKFLOW EXAMPLE")
    print("=" * 80)
    print(f"Scenario: {scenario}")
    print("=" * 80)
    
    # Step 1: Run initial workflow with checkpoints
    print("\n📍 Step 1: Running initial workflow with checkpoints...")
    
    initial_result = await workflow.run_with_checkpoints(scenario)
    
    if initial_result["success"]:
        print(f"✅ Initial workflow completed")
        print(f"   - Total steps: {initial_result['total_steps']}")
        print(f"   - Checkpoints created: {', '.join(initial_result['checkpoints'])}")
        
        # Save initial result
        save_result(initial_result, "initial_analysis", scenario)
        
        # Step 2: Create checkpoint after market analysis
        print("\n📍 Step 2: Creating strategic checkpoint...")
        await workflow.create_checkpoint("post_market_analysis")
        
        # Step 3: Explore alternative paths
        print("\n📍 Step 3: Exploring alternative scenarios from checkpoint...")
        
        alternatives = [
            "Focus on B2B enterprise market instead of B2C",
            "Consider partnership model instead of direct investment",
            "Evaluate neighboring markets for better opportunities"
        ]
        
        alternative_results = []
        
        for alt in alternatives:
            print(f"\n   🔄 Exploring: {alt}")
            try:
                alt_result = await workflow.explore_alternative_path(
                    "post_market_analysis",
                    alt
                )
                alternative_results.append(alt_result)
                print(f"   ✅ Alternative path completed")
                
                # Save alternative result
                save_result(alt_result, f"alternative_{len(alternative_results)}", scenario)
                
            except Exception as e:
                logger.error(f"   ❌ Alternative path failed: {e}")
        
        # Step 4: Compare results
        print("\n📍 Step 4: Comparing different paths...")
        comparison = compare_results(initial_result, alternative_results)
        
        # Save comparison
        save_comparison(comparison, scenario)
        
        print("\n📊 COMPARISON SUMMARY")
        print("=" * 80)
        print(f"Original path: {comparison['original']['summary']}")
        print("\nAlternative paths:")
        for i, alt in enumerate(comparison['alternatives']):
            print(f"{i+1}. {alt['modification']}: {alt['summary']}")
        
    else:
        print(f"❌ Initial workflow failed: {initial_result.get('error', 'Unknown error')}")
    
    # List all checkpoints
    print("\n📋 Available checkpoints:")
    for cp in workflow.list_checkpoints():
        print(f"   - {cp['name']}: {cp['id']}")
    
    print("\n" + "=" * 80)


def save_result(result: Dict[str, Any], result_type: str, scenario: str):
    """Save workflow result to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"checkpoint_{result_type}_{timestamp}.json"
    filepath = Path(f"examples/real_world/output/{filename}")
    
    data = {
        "type": result_type,
        "scenario": scenario,
        "timestamp": timestamp,
        "success": result.get("success", False),
        "final_response": result.get("final_response", ""),
        "modification": result.get("modification", ""),
        "checkpoint_used": result.get("checkpoint_used", "")
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved {result_type} to: {filepath}")


def compare_results(original: Dict[str, Any], alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare original and alternative execution paths."""
    comparison = {
        "original": {
            "summary": extract_summary(original.get("final_response", "")),
            "total_steps": original.get("total_steps", 0)
        },
        "alternatives": []
    }
    
    for alt in alternatives:
        comparison["alternatives"].append({
            "modification": alt.get("modification", ""),
            "summary": extract_summary(alt.get("final_response", "")),
            "checkpoint_used": alt.get("checkpoint_used", "")
        })
    
    return comparison


def extract_summary(response: str) -> str:
    """Extract a brief summary from the response."""
    # Simple extraction - take first 200 characters
    if not response:
        return "No response"
    return response[:200] + "..." if len(response) > 200 else response


def save_comparison(comparison: Dict[str, Any], scenario: str):
    """Save comparison results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = Path(f"examples/real_world/output/checkpoint_comparison_{timestamp}.json")
    
    data = {
        "scenario": scenario,
        "timestamp": timestamp,
        "comparison": comparison
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved comparison to: {filepath}")


async def main():
    """Main function to run the checkpoint example."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Create model configs and agents
    configs = create_model_configs()
    agents = create_agents(configs)
    
    # Run the checkpoint demonstration
    await demonstrate_checkpoint_workflow()


if __name__ == "__main__":
    asyncio.run(main())