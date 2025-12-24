#!/usr/bin/env python3
"""
Hub-and-Spoke Pattern - AI Research Assistant
===========================================

This example demonstrates the hub-and-spoke coordination pattern where a central
coordinator (ResearchCoordinator) manages multiple specialist agents in sequence.

Pattern characteristics:
- Central coordinator maintains control flow
- Sequential execution with shared memory
- All communication goes through the hub
- Ideal for tasks requiring orchestrated steps

Agents:
- ResearchCoordinator (GPT-4.1): Plans and coordinates research
- DataCollector (Gemini-2.5-flash): Fast data gathering  
- Analyzer (Claude-Sonnet-4): Deep analysis
- ReportWriter (GPT-4.1): High-quality report writing
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.models import ModelConfig
from marsys.environment.tools import tool_google_search_api

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_model_configs() -> Dict[str, ModelConfig]:
    """Create model configurations for different agents."""
    configs = {
        "gpt4": ModelConfig(
            type="api",
            name="gpt-4",  # Using gpt-4 as gpt-4.1 might not be available yet
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        ),
        "gemini_flash": ModelConfig(
            type="api",
            name="gemini-1.5-flash",  # Using available Gemini model
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        ),
        "claude": ModelConfig(
            type="api",
            name="claude-3-sonnet-20240229",  # Using available Claude model
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
    }
    return configs


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create the hub-and-spoke agent team."""
    agents = {}
    
    # Research Coordinator - The Hub
    agents["ResearchCoordinator"] = Agent(
        model_config=configs["gpt4"],
        name="ResearchCoordinator",
        description="""You are the Research Coordinator, responsible for planning and orchestrating research tasks.
        
Your responsibilities:
1. Break down complex research queries into specific tasks
2. Delegate tasks to specialist agents in sequence
3. Review and integrate results from each agent
4. Ensure comprehensive coverage of the research topic
5. Maintain quality and coherence across all outputs

When you receive a research request:
- First, create a research plan
- Then invoke DataCollector to gather information
- Next, invoke Analyzer to analyze the data
- Finally, invoke ReportWriter to create the final report
- Review the final report before returning to the user""",
        system_prompt="You are a research coordination expert who excels at breaking down complex queries and managing research workflows."
    )
    
    # Data Collector - Fast information gathering
    agents["DataCollector"] = Agent(
        model_config=configs["gemini_flash"],
        name="DataCollector",
        description="""You are the Data Collector, specialized in quickly gathering relevant information.
        
Your responsibilities:
1. Search for relevant information using Google Search
2. Identify key sources and references
3. Extract important facts and data points
4. Organize findings by relevance and reliability
5. Return structured data for analysis

Focus on:
- Finding authoritative sources
- Recent and up-to-date information
- Diverse perspectives on the topic
- Key statistics and facts""",
        system_prompt="You are an expert at quickly finding and organizing relevant information from various sources.",
        tools=[tool_google_search_api]
    )
    
    # Analyzer - Deep analysis
    agents["Analyzer"] = Agent(
        model_config=configs["claude"],
        name="Analyzer",
        description="""You are the Analyzer, responsible for deep analysis of collected data.
        
Your responsibilities:
1. Analyze patterns and trends in the data
2. Identify key insights and implications
3. Evaluate the quality and reliability of sources
4. Synthesize multiple viewpoints
5. Draw meaningful conclusions

Your analysis should be:
- Thorough and systematic
- Evidence-based
- Balanced and objective
- Insightful and actionable""",
        system_prompt="You are an expert analyst who excels at finding patterns, drawing insights, and synthesizing complex information."
    )
    
    # Report Writer - Final report generation
    agents["ReportWriter"] = Agent(
        model_config=configs["gpt4"],
        name="ReportWriter",
        description="""You are the Report Writer, responsible for creating polished final reports.
        
Your responsibilities:
1. Structure findings into a clear, professional report
2. Use appropriate formatting (markdown)
3. Include executive summary
4. Organize content logically
5. Ensure clarity and readability

Report structure:
- Executive Summary
- Introduction
- Key Findings (with subsections)
- Analysis and Insights
- Conclusions
- References""",
        system_prompt="You are an expert report writer who creates clear, professional, and well-structured reports."
    )
    
    # Register all agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


async def run_research_workflow(topic: str) -> Dict[str, Any]:
    """Run the hub-and-spoke research workflow."""
    
    # Define the hub-and-spoke topology
    topology = {
        "agents": ["User", "ResearchCoordinator", "DataCollector", "Analyzer", "ReportWriter"],
        "flows": [
            "User -> ResearchCoordinator",
            "ResearchCoordinator <-> DataCollector",
            "ResearchCoordinator <-> Analyzer",
            "ResearchCoordinator <-> ReportWriter",
            "ResearchCoordinator -> User"
        ],
        "rules": [
            "timeout(600)",  # 10 minute timeout
            "max_steps(50)"   # Maximum 50 steps
        ]
    }
    
    # Run the workflow
    logger.info(f"Starting research workflow for topic: {topic}")
    
    try:
        result = await Orchestra.run(
            task=f"Research the following topic comprehensively: {topic}",
            topology=topology,
            context={
                "output_format": "markdown",
                "include_citations": True,
                "research_depth": "comprehensive"
            },
            max_steps=50
        )
        
        logger.info(f"Research workflow completed. Success: {result.success}")
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "duration": result.total_duration,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Research workflow failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def save_results(results: Dict[str, Any], topic: str):
    """Save the research results to files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"hub_spoke_research_{timestamp}"
    
    # Save the final report
    if results.get("success") and results.get("final_response"):
        report_path = Path(f"examples/real_world/output/{base_filename}_report.md")
        report_path.write_text(f"# Research Report: {topic}\n\n{results['final_response']}")
        logger.info(f"Report saved to: {report_path}")
    
    # Save execution details
    execution_path = Path(f"examples/real_world/output/{base_filename}_execution.json")
    execution_data = {
        "topic": topic,
        "timestamp": timestamp,
        "success": results.get("success", False),
        "total_steps": results.get("total_steps", 0),
        "duration_seconds": results.get("duration", 0),
        "metadata": results.get("metadata", {})
    }
    
    with open(execution_path, 'w') as f:
        json.dump(execution_data, f, indent=2)
    logger.info(f"Execution details saved to: {execution_path}")


async def main():
    """Main function to run the hub-and-spoke research example."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Create model configurations
    configs = create_model_configs()
    
    # Create agents
    agents = create_agents(configs)
    
    # Research topic
    topic = "Latest developments in AI safety and alignment research in 2024"
    
    logger.info("=" * 80)
    logger.info("Hub-and-Spoke Pattern - AI Research Assistant")
    logger.info("=" * 80)
    logger.info(f"Research Topic: {topic}")
    logger.info(f"Agents: {list(agents.keys())}")
    logger.info("=" * 80)
    
    # Run the research workflow
    results = await run_research_workflow(topic)
    
    # Save results
    save_results(results, topic)
    
    # Print summary
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Success: {results.get('success', False)}")
    print(f"Total Steps: {results.get('total_steps', 0)}")
    print(f"Duration: {results.get('duration', 0):.2f} seconds")
    
    if results.get('error'):
        print(f"Error: {results['error']}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())