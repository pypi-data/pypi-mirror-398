#!/usr/bin/env python3
"""
Multi-Level Mixed Pattern - Content Creation Pipeline
==================================================

This example demonstrates a complex multi-level topology that combines:
- Parallel execution (research phase)
- Sequential processing (writing and editing)
- Conversation loops (between writer and editor)
- Multiple convergence points

Pattern characteristics:
- Mixed parallel and sequential execution
- Conversation loops for iterative improvement
- Multiple specialist agents with different roles
- Tool integration (Google Search for research)

Agents:
- ContentPlanner (GPT-4): High-level content strategy
- Researcher (Gemini-flash + Google Search): Fast research with web search
- Writer (Claude-Sonnet): Creative content writing
- Editor (GPT-4): Content editing and refinement
- SEOOptimizer (Grok): SEO optimization
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
            name="gpt-4",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2500
            }
        ),
        "gemini_flash": ModelConfig(
            type="api",
            name="google/gemini-2.0-flash-exp:free",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.8,
                "max_tokens": 2000
            }
        ),
        "claude": ModelConfig(
            type="api",
            name="anthropic/claude-3.5-sonnet",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.8,
                "max_tokens": 3000
            }
        ),
        "grok": ModelConfig(
            type="api",
            name="x-ai/grok-2-1212",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.6,
                "max_tokens": 1500
            }
        )
    }
    return configs


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create the content creation pipeline agents."""
    agents = {}
    
    # Content Planner - Strategy and coordination
    agents["ContentPlanner"] = Agent(
        model_config=configs["gpt4"],
        name="ContentPlanner",
        description="""You are the Content Planner, responsible for content strategy and coordination.
        
Your responsibilities:
1. Analyze content requests and create a comprehensive content plan
2. Define target audience, key messages, and content structure
3. Coordinate the content creation pipeline
4. Ensure all pieces work together cohesively
5. Review final output before publication

When planning content:
- First invoke Researcher to gather relevant information
- Then invoke Writer to create the initial draft
- Monitor the Writer-Editor conversation for quality
- Finally invoke SEOOptimizer for search optimization
- Review and approve the final content""",
        system_prompt="You are a strategic content planner who excels at creating engaging content strategies."
    )
    
    # Researcher - Fast research with web search
    agents["Researcher"] = Agent(
        model_config=configs["gemini_flash"],
        name="Researcher",
        description="""You are the Researcher, specialized in gathering comprehensive information.
        
Your responsibilities:
1. Use Google Search to find relevant, up-to-date information
2. Identify authoritative sources and statistics
3. Gather diverse perspectives on the topic
4. Find compelling examples and case studies
5. Organize research findings clearly

Research approach:
- Perform multiple targeted searches
- Prioritize recent and authoritative sources
- Include statistics and data points
- Find unique angles and insights
- Provide source citations""",
        system_prompt="You are an expert researcher who finds comprehensive, relevant information quickly.",
        tools=[tool_google_search_api]
    )
    
    # Writer - Creative content creation
    agents["Writer"] = Agent(
        model_config=configs["claude"],
        name="Writer",
        description="""You are the Writer, responsible for creating engaging content.
        
Your responsibilities:
1. Transform research into compelling content
2. Write in an engaging, accessible style
3. Structure content logically with clear sections
4. Include storytelling elements where appropriate
5. Collaborate with Editor for improvements

Writing guidelines:
- Hook readers with strong introductions
- Use clear, concise language
- Include examples and anecdotes
- Create smooth transitions
- End with actionable takeaways

When Editor provides feedback, revise accordingly and resubmit.""",
        system_prompt="You are a talented writer who creates engaging, informative content."
    )
    
    # Editor - Content refinement
    agents["Editor"] = Agent(
        model_config=configs["gpt4"],
        name="Editor",
        description="""You are the Editor, responsible for refining and improving content.
        
Your responsibilities:
1. Review content for clarity, accuracy, and engagement
2. Suggest structural improvements
3. Ensure consistent tone and voice
4. Check facts and citations
5. Collaborate with Writer for revisions

Editing focus:
- Clarity and readability
- Logical flow and structure
- Grammar and style consistency
- Fact-checking and accuracy
- Engagement and impact

Provide specific, actionable feedback to the Writer. If content needs revision, clearly explain what needs improvement.""",
        system_prompt="You are an expert editor who enhances content quality and clarity."
    )
    
    # SEO Optimizer - Search optimization
    agents["SEOOptimizer"] = Agent(
        model_config=configs["grok"],
        name="SEOOptimizer",
        description="""You are the SEO Optimizer, responsible for search engine optimization.
        
Your responsibilities:
1. Optimize content for search engines
2. Suggest relevant keywords naturally
3. Improve meta descriptions and headers
4. Enhance content structure for SEO
5. Maintain readability while optimizing

SEO optimization approach:
- Identify primary and secondary keywords
- Optimize headers (H1, H2, H3)
- Create compelling meta description
- Ensure keyword density is natural
- Add internal linking suggestions
- Optimize for featured snippets

Return the SEO-optimized version with a summary of changes made.""",
        system_prompt="You are an SEO expert who optimizes content for search visibility."
    )
    
    # Register all agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


async def run_content_pipeline(topic: str, content_type: str) -> Dict[str, Any]:
    """Run the mixed content creation pipeline."""
    
    # Define the complex mixed topology
    topology = {
        "agents": ["User", "ContentPlanner", "Researcher", "Writer", "Editor", "SEOOptimizer"],
        "flows": [
            "User -> ContentPlanner",
            "ContentPlanner -> Researcher",
            "Researcher -> ContentPlanner",
            "ContentPlanner -> Writer",
            "Writer <-> Editor",  # Conversation loop for revisions
            "Writer -> ContentPlanner",
            "ContentPlanner -> SEOOptimizer",
            "SEOOptimizer -> ContentPlanner",
            "ContentPlanner -> User"
        ],
        "rules": [
            "timeout(900)",  # 15 minute timeout
            "max_steps(60)",  # Maximum 60 steps
            "max_turns(Writer <-> Editor, 3)"  # Limit revision cycles
        ]
    }
    
    # Prepare the content creation task
    task = f"""Create a high-quality {content_type} about: {topic}

Requirements:
1. Thoroughly research the topic with current information
2. Create engaging, well-structured content
3. Ensure accuracy and clarity through editing
4. Optimize for search engines
5. Target audience: Business professionals and decision makers

The final output should be publication-ready."""
    
    logger.info(f"Starting content pipeline for: {topic}")
    
    try:
        result = await Orchestra.run(
            task=task,
            topology=topology,
            context={
                "topic": topic,
                "content_type": content_type,
                "target_audience": "business professionals",
                "tone": "professional yet engaging",
                "length": "1500-2000 words"
            },
            max_steps=60
        )
        
        logger.info(f"Content pipeline completed. Success: {result.success}")
        
        # Count conversation turns between Writer and Editor
        conversation_turns = 0
        for branch in result.branch_results:
            if "Writer" in branch.branch_id and "Editor" in branch.branch_id:
                conversation_turns = max(conversation_turns, branch.total_steps // 2)
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "duration": result.total_duration,
            "conversation_turns": conversation_turns,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Content pipeline failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def save_results(results: Dict[str, Any], topic: str, content_type: str):
    """Save the content creation results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"mixed_content_pipeline_{timestamp}"
    
    # Save the final content
    if results.get("success") and results.get("final_response"):
        content_path = Path(f"examples/real_world/output/{base_filename}_content.md")
        content_header = f"""---
title: {topic}
type: {content_type}
date: {datetime.now().strftime("%Y-%m-%d")}
pipeline: Multi-Level Mixed Pattern
---

"""
        content_path.write_text(content_header + results['final_response'])
        logger.info(f"Content saved to: {content_path}")
    
    # Save execution details
    execution_path = Path(f"examples/real_world/output/{base_filename}_execution.json")
    execution_data = {
        "topic": topic,
        "content_type": content_type,
        "timestamp": timestamp,
        "success": results.get("success", False),
        "total_steps": results.get("total_steps", 0),
        "duration_seconds": results.get("duration", 0),
        "conversation_turns": results.get("conversation_turns", 0),
        "metadata": results.get("metadata", {})
    }
    
    with open(execution_path, 'w') as f:
        json.dump(execution_data, f, indent=2)
    logger.info(f"Execution details saved to: {execution_path}")


async def main():
    """Main function to run the mixed content pipeline example."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Create model configurations
    configs = create_model_configs()
    
    # Create agents
    agents = create_agents(configs)
    
    # Content parameters
    topic = "The Future of AI in Healthcare: Opportunities and Challenges in 2024"
    content_type = "comprehensive blog post"
    
    logger.info("=" * 80)
    logger.info("Multi-Level Mixed Pattern - Content Creation Pipeline")
    logger.info("=" * 80)
    logger.info(f"Topic: {topic}")
    logger.info(f"Content Type: {content_type}")
    logger.info(f"Agents: {list(agents.keys())}")
    logger.info("Pipeline: Research → Writing → Editing (iterative) → SEO")
    logger.info("=" * 80)
    
    # Run the content pipeline
    results = await run_content_pipeline(topic, content_type)
    
    # Save results
    save_results(results, topic, content_type)
    
    # Print summary
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"Success: {results.get('success', False)}")
    print(f"Total Steps: {results.get('total_steps', 0)}")
    print(f"Writer-Editor Conversation Turns: {results.get('conversation_turns', 0)}")
    print(f"Duration: {results.get('duration', 0):.2f} seconds")
    
    if results.get('error'):
        print(f"Error: {results['error']}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())