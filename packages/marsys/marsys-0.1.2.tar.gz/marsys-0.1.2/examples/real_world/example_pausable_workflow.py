#!/usr/bin/env python3
"""
Pausable Workflow Example - Long-Running Research with StateManager
================================================================

This example demonstrates how to use the StateManager for pause/resume functionality
in a long-running multi-agent workflow. The workflow can be paused at any time,
state is persisted to disk, and execution can be resumed later.

Features demonstrated:
- StateManager integration with Orchestra
- Pause workflow mid-execution
- Resume from saved state
- Progress tracking and recovery
- Handling interruptions gracefully

Workflow:
- Research task that could take significant time
- Multiple agents working sequentially and in parallel
- Ability to pause and resume at any point
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.coordination.state.state_manager import StateManager, FileStorageBackend
from marsys.models import ModelConfig
from marsys.environment.tools import tool_google_search_api

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for handling interruption
current_session_id: Optional[str] = None
orchestra_instance: Optional[Orchestra] = None
interrupted = False


def signal_handler(signum, frame):
    """Handle interrupt signal for graceful pause."""
    global interrupted
    logger.info("\n🛑 Interrupt received! Pausing workflow...")
    interrupted = True


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
            name="gemini-1.5-flash",
            provider="google",
            api_key=os.getenv("GOOGLE_API_KEY"),
            parameters={"temperature": 0.7, "max_tokens": 2000}
        )
    }


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create agents for the pausable workflow."""
    agents = {}
    
    # Lead Researcher
    agents["LeadResearcher"] = Agent(
        model_config=configs["gpt4"],
        name="LeadResearcher",
        description="""You are the Lead Researcher coordinating a comprehensive research project.
        
Your tasks:
        1. Break down the research topic into subtopics
        2. Delegate research tasks to specialist researchers
        3. Review and synthesize findings
        4. Ensure comprehensive coverage
        
First, analyze the topic and invoke DataGatherer for initial research.
Then invoke DeepAnalyst for in-depth analysis.
Finally, synthesize all findings.""",
        system_prompt="You are a senior researcher coordinating comprehensive research projects."
    )
    
    # Data Gatherer
    agents["DataGatherer"] = Agent(
        model_config=configs["gemini"],
        name="DataGatherer",
        description="""You are the Data Gatherer, responsible for collecting information.
        
Your tasks:
        1. Search for relevant information using Google Search
        2. Identify key sources and references
        3. Extract important data points
        4. Organize findings by topic
        
Use multiple searches to gather comprehensive data.""",
        system_prompt="You are an expert at finding and organizing information.",
        tools=[tool_google_search_api]
    )
    
    # Deep Analyst
    agents["DeepAnalyst"] = Agent(
        model_config=configs["claude"],
        name="DeepAnalyst",
        description="""You are the Deep Analyst, responsible for detailed analysis.
        
Your tasks:
        1. Analyze collected data for patterns
        2. Identify key insights and implications
        3. Evaluate different perspectives
        4. Draw meaningful conclusions
        
Provide thorough, evidence-based analysis.""",
        system_prompt="You are an expert analyst who excels at finding deep insights."
    )
    
    # Register agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


async def run_pausable_research(topic: str, resume_from: Optional[str] = None) -> Dict[str, Any]:
    """Run the pausable research workflow."""
    global current_session_id, orchestra_instance
    
    # Create state storage
    state_dir = Path("examples/real_world/output/state_storage")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    backend = FileStorageBackend(state_dir)
    state_manager = StateManager(backend)
    
    # Create Orchestra with StateManager
    orchestra_instance = Orchestra(
        agent_registry=AgentRegistry,
        state_manager=state_manager
    )
    
    # Define topology
    topology = {
        "agents": ["User", "LeadResearcher", "DataGatherer", "DeepAnalyst"],
        "flows": [
            "User -> LeadResearcher",
            "LeadResearcher -> DataGatherer",
            "DataGatherer -> LeadResearcher",
            "LeadResearcher -> DeepAnalyst",
            "DeepAnalyst -> LeadResearcher",
            "LeadResearcher -> User"
        ],
        "rules": [
            "timeout(1200)",  # 20 minute timeout
            "max_steps(100)"
        ]
    }
    
    try:
        if resume_from:
            # Resume from saved session
            logger.info(f"Resuming session: {resume_from}")
            result = await orchestra_instance.resume_session(resume_from)
            current_session_id = resume_from
        else:
            # Create new session
            session = await orchestra_instance.create_session(
                task=f"Conduct comprehensive research on: {topic}",
                context={
                    "topic": topic,
                    "research_depth": "comprehensive",
                    "output_format": "detailed_report"
                },
                enable_pause=True
            )
            current_session_id = session.id
            logger.info(f"Created new session: {current_session_id}")
            
            # Run with interrupt handling
            result = await session.run(topology)
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "duration": result.total_duration,
            "session_id": current_session_id,
            "was_paused": False
        }
        
    except asyncio.CancelledError:
        # Handle interruption
        logger.info("Workflow interrupted, saving state...")
        if current_session_id and orchestra_instance:
            success = await orchestra_instance.pause_session(current_session_id)
            if success:
                logger.info(f"✅ Session paused successfully: {current_session_id}")
                return {
                    "success": False,
                    "session_id": current_session_id,
                    "was_paused": True,
                    "message": "Workflow paused. Can be resumed later."
                }
        raise
    
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": current_session_id
        }


async def check_for_interrupt():
    """Periodically check for interrupt signal."""
    global interrupted
    while not interrupted:
        await asyncio.sleep(0.1)
    raise asyncio.CancelledError("User interrupted")


def save_session_info(session_id: str, topic: str, status: str):
    """Save session information for easy resumption."""
    session_file = Path("examples/real_world/output/pausable_sessions.json")
    
    # Load existing sessions
    sessions = {}
    if session_file.exists():
        with open(session_file, 'r') as f:
            sessions = json.load(f)
    
    # Update with current session
    sessions[session_id] = {
        "topic": topic,
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save back
    with open(session_file, 'w') as f:
        json.dump(sessions, f, indent=2)


def list_pausable_sessions():
    """List all pausable sessions."""
    session_file = Path("examples/real_world/output/pausable_sessions.json")
    
    if not session_file.exists():
        return {}
    
    with open(session_file, 'r') as f:
        return json.load(f)


async def main():
    """Main function demonstrating pausable workflow."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check for existing paused sessions
    sessions = list_pausable_sessions()
    resume_session_id = None
    topic = "The Impact of Quantum Computing on Cybersecurity and Encryption"
    
    if sessions:
        print("\n📋 Found existing sessions:")
        for sid, info in sessions.items():
            if info['status'] == 'paused':
                print(f"  - {sid}: {info['topic']} (paused at {info['timestamp']})")
        
        resume = input("\nResume a session? (enter session ID or 'n' for new): ").strip()
        if resume != 'n' and resume in sessions:
            resume_session_id = resume
            topic = sessions[resume]['topic']
    
    # Create model configs and agents
    configs = create_model_configs()
    agents = create_agents(configs)
    
    print("\n" + "=" * 80)
    print("PAUSABLE WORKFLOW EXAMPLE")
    print("=" * 80)
    print(f"Topic: {topic}")
    print(f"Mode: {'RESUMING' if resume_session_id else 'NEW SESSION'}")
    print("\n⚡ Press Ctrl+C at any time to pause the workflow")
    print("=" * 80 + "\n")
    
    # Run the pausable research workflow
    try:
        # Run main task and interrupt checker concurrently
        research_task = asyncio.create_task(
            run_pausable_research(topic, resume_session_id)
        )
        interrupt_task = asyncio.create_task(check_for_interrupt())
        
        # Wait for either to complete
        done, pending = await asyncio.wait(
            [research_task, interrupt_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        
        # Cancel the other task
        for task in pending:
            task.cancel()
        
        # Get result from completed task
        for task in done:
            if task == research_task:
                results = task.result()
            else:
                # Interrupted
                results = {
                    "success": False,
                    "was_paused": True,
                    "session_id": current_session_id,
                    "message": "Workflow paused by user"
                }
                
                # Try to pause the session
                if current_session_id and orchestra_instance:
                    success = await orchestra_instance.pause_session(current_session_id)
                    if success:
                        save_session_info(current_session_id, topic, "paused")
    
    except asyncio.CancelledError:
        results = {
            "success": False,
            "was_paused": True,
            "session_id": current_session_id,
            "message": "Workflow paused by user"
        }
    
    # Save results and print summary
    if results.get("success"):
        # Save successful results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"examples/real_world/output/pausable_research_{timestamp}.md")
        
        content = f"""# Research Report: {topic}

**Session ID**: {results.get('session_id', 'unknown')}  
**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Steps**: {results.get('total_steps', 0)}  
**Duration**: {results.get('duration', 0):.2f} seconds

---

{results.get('final_response', 'No response generated')}
"""
        output_path.write_text(content)
        print(f"\n✅ Research completed! Report saved to: {output_path}")
        
        # Update session status
        if results.get('session_id'):
            save_session_info(results['session_id'], topic, "completed")
    
    elif results.get("was_paused"):
        print(f"\n⏸️  Workflow paused!")
        print(f"Session ID: {results.get('session_id', 'unknown')}")
        print(f"To resume, run the script again and select this session.")
    
    else:
        print(f"\n❌ Workflow failed: {results.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())