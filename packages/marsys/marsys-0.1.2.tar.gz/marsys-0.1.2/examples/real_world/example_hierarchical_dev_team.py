#!/usr/bin/env python3
"""
Hierarchical Team Pattern - Software Development Team
==================================================

This example demonstrates a hierarchical multi-agent pattern that simulates
a software development team working on a feature implementation.

Pattern characteristics:
- Multi-level hierarchy (PM → Team Leads → Developers)
- Nested parallel execution at multiple levels
- Task delegation and result aggregation
- Realistic software development workflow

Agents:
- ProjectManager (GPT-4): Breaks down requirements and coordinates
- FrontendLead (Claude): Manages frontend architecture and tasks
- BackendLead (Gemini-Pro): Manages backend architecture and tasks
- UIDevs, APIDevs, DBDevs: Individual developers using mixed models
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
    """Create model configurations for the development team."""
    configs = {
        "gpt4": ModelConfig(
            type="api",
            name="gpt-4",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        ),
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
        "gemini_pro": ModelConfig(
            type="api",
            name="google/gemini-pro-1.5",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 2000
            }
        ),
        "gpt4_mini": ModelConfig(
            type="api",
            name="gpt-4o-mini",
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 1500
            }
        ),
        "gemini_flash": ModelConfig(
            type="api",
            name="google/gemini-2.0-flash-exp:free",
            provider="openrouter",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            parameters={
                "temperature": 0.7,
                "max_tokens": 1500
            }
        )
    }
    return configs


def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create the hierarchical development team."""
    agents = {}
    
    # Project Manager - Top of hierarchy
    agents["ProjectManager"] = Agent(
        model_config=configs["gpt4"],
        name="ProjectManager",
        description="""You are the Project Manager, responsible for breaking down features and coordinating the team.
        
Your responsibilities:
1. Analyze feature requirements and create technical specifications
2. Break down work into frontend and backend tasks
3. Delegate tasks to team leads using parallel execution
4. Monitor progress and aggregate results
5. Ensure all components integrate properly

When you receive a feature request:
- Break it down into frontend and backend requirements
- Use parallel_invoke to delegate to both team leads:
  {
    "next_action": "parallel_invoke",
    "agents": ["FrontendLead", "BackendLead"],
    "action_input": {
      "FrontendLead": "Frontend requirements: [specific tasks]",
      "BackendLead": "Backend requirements: [specific tasks]"
    }
  }
- Review and integrate the results from both teams""",
        system_prompt="You are an experienced project manager who excels at breaking down complex features."
    )
    
    # Frontend Lead
    agents["FrontendLead"] = Agent(
        model_config=configs["claude"],
        name="FrontendLead",
        description="""You are the Frontend Lead, responsible for frontend architecture and task delegation.
        
Your responsibilities:
1. Design frontend architecture for features
2. Break down frontend work into UI and UX tasks
3. Delegate to frontend developers in parallel
4. Review and integrate frontend components
5. Ensure consistency and best practices

When you receive frontend requirements:
- Design the component architecture
- Use parallel_invoke to delegate to UI developers:
  {
    "next_action": "parallel_invoke",
    "agents": ["UIDesigner", "UIImplementer"],
    "action_input": {
      "UIDesigner": "Design task: [specific UI elements]",
      "UIImplementer": "Implementation task: [specific components]"
    }
  }
- Integrate and review the work""",
        system_prompt="You are an expert frontend architect who ensures high-quality user interfaces."
    )
    
    # Backend Lead
    agents["BackendLead"] = Agent(
        model_config=configs["gemini_pro"],
        name="BackendLead",
        description="""You are the Backend Lead, responsible for backend architecture and task delegation.
        
Your responsibilities:
1. Design backend architecture and APIs
2. Break down backend work into API and database tasks
3. Delegate to backend developers in parallel
4. Ensure scalability and performance
5. Review integration points

When you receive backend requirements:
- Design the system architecture
- Use parallel_invoke to delegate to backend developers:
  {
    "next_action": "parallel_invoke",
    "agents": ["APIDeveloper", "DatabaseDeveloper"],
    "action_input": {
      "APIDeveloper": "API task: [specific endpoints]",
      "DatabaseDeveloper": "Database task: [specific schema/queries]"
    }
  }
- Review and integrate the components""",
        system_prompt="You are an expert backend architect focused on scalable systems."
    )
    
    # Frontend Developers
    agents["UIDesigner"] = Agent(
        model_config=configs["gpt4_mini"],
        name="UIDesigner",
        description="""You are the UI Designer, responsible for creating user interface designs.
        
Your tasks:
1. Create detailed UI component designs
2. Define styling and visual hierarchy
3. Ensure accessibility standards
4. Create responsive designs
5. Document design decisions

Provide detailed specifications including:
- Component structure
- Styling guidelines
- Interaction patterns
- Accessibility considerations""",
        system_prompt="You are a skilled UI designer focused on user experience."
    )
    
    agents["UIImplementer"] = Agent(
        model_config=configs["gemini_flash"],
        name="UIImplementer",
        description="""You are the UI Implementer, responsible for implementing UI components.
        
Your tasks:
1. Implement React/Vue/Angular components
2. Write clean, maintainable code
3. Ensure responsive behavior
4. Add proper event handling
5. Write component tests

Provide code implementations including:
- Component code
- Styling (CSS/SCSS)
- Event handlers
- Basic unit tests""",
        system_prompt="You are a frontend developer who writes clean, efficient code."
    )
    
    # Backend Developers
    agents["APIDeveloper"] = Agent(
        model_config=configs["gpt4_mini"],
        name="APIDeveloper",
        description="""You are the API Developer, responsible for implementing REST/GraphQL APIs.
        
Your tasks:
1. Design and implement API endpoints
2. Handle authentication and authorization
3. Implement request validation
4. Write API documentation
5. Create integration tests

Provide implementations including:
- Endpoint definitions
- Request/response schemas
- Error handling
- API documentation""",
        system_prompt="You are a backend developer specializing in API development."
    )
    
    agents["DatabaseDeveloper"] = Agent(
        model_config=configs["gemini_flash"],
        name="DatabaseDeveloper",
        description="""You are the Database Developer, responsible for database design and optimization.
        
Your tasks:
1. Design database schemas
2. Write efficient queries
3. Implement data migrations
4. Optimize performance
5. Ensure data integrity

Provide implementations including:
- Schema definitions
- SQL queries
- Migration scripts
- Indexes and optimization""",
        system_prompt="You are a database expert focused on performance and reliability."
    )
    
    # Register all agents
    for agent in agents.values():
        AgentRegistry.register(agent)
    
    return agents


async def run_dev_team_workflow(feature_request: str) -> Dict[str, Any]:
    """Run the hierarchical development team workflow."""
    
    # Define the hierarchical topology
    topology = {
        "agents": [
            "User", "ProjectManager", 
            "FrontendLead", "BackendLead",
            "UIDesigner", "UIImplementer",
            "APIDeveloper", "DatabaseDeveloper"
        ],
        "flows": [
            # User to PM
            "User -> ProjectManager",
            # PM to Team Leads
            "ProjectManager -> FrontendLead",
            "ProjectManager -> BackendLead",
            # Frontend hierarchy
            "FrontendLead -> UIDesigner",
            "FrontendLead -> UIImplementer",
            # Backend hierarchy
            "BackendLead -> APIDeveloper",
            "BackendLead -> DatabaseDeveloper",
            # Returns
            "UIDesigner -> FrontendLead",
            "UIImplementer -> FrontendLead",
            "APIDeveloper -> BackendLead",
            "DatabaseDeveloper -> BackendLead",
            "FrontendLead -> ProjectManager",
            "BackendLead -> ProjectManager",
            "ProjectManager -> User"
        ],
        "rules": [
            "timeout(720)",  # 12 minute timeout
            "max_steps(80)",  # Maximum 80 steps
            # Enable parallel execution at multiple levels
            "parallel(FrontendLead, BackendLead)",
            "parallel(UIDesigner, UIImplementer)",
            "parallel(APIDeveloper, DatabaseDeveloper)"
        ]
    }
    
    logger.info(f"Starting development workflow for: {feature_request}")
    
    try:
        result = await Orchestra.run(
            task=f"Implement the following feature: {feature_request}",
            topology=topology,
            context={
                "feature": feature_request,
                "tech_stack": {
                    "frontend": "React with TypeScript",
                    "backend": "Python FastAPI",
                    "database": "PostgreSQL"
                },
                "requirements": {
                    "performance": "high",
                    "scalability": "must handle 10k concurrent users",
                    "security": "implement proper authentication"
                }
            },
            max_steps=80
        )
        
        logger.info(f"Development workflow completed. Success: {result.success}")
        
        # Count parallel branches at different levels
        parallel_stats = {
            "team_leads": 0,
            "frontend_devs": 0,
            "backend_devs": 0
        }
        
        for branch in result.branch_results:
            if "FrontendLead" in branch.branch_id and "BackendLead" in branch.branch_id:
                parallel_stats["team_leads"] += 1
            elif "UIDesigner" in branch.branch_id or "UIImplementer" in branch.branch_id:
                parallel_stats["frontend_devs"] += 1
            elif "APIDeveloper" in branch.branch_id or "DatabaseDeveloper" in branch.branch_id:
                parallel_stats["backend_devs"] += 1
        
        return {
            "success": result.success,
            "final_response": result.final_response,
            "total_steps": result.total_steps,
            "duration": result.total_duration,
            "parallel_stats": parallel_stats,
            "metadata": result.metadata
        }
        
    except Exception as e:
        logger.error(f"Development workflow failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def save_results(results: Dict[str, Any], feature_request: str):
    """Save the development workflow results."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"hierarchical_dev_team_{timestamp}"
    
    # Save the implementation plan
    if results.get("success") and results.get("final_response"):
        plan_path = Path(f"examples/real_world/output/{base_filename}_implementation.md")
        plan_content = f"""# Feature Implementation Plan

**Feature**: {feature_request}  
**Date**: {datetime.now().strftime("%Y-%m-%d")}  
**Pattern**: Hierarchical Team Structure

---

{results['final_response']}
"""
        plan_path.write_text(plan_content)
        logger.info(f"Implementation plan saved to: {plan_path}")
    
    # Save execution details
    execution_path = Path(f"examples/real_world/output/{base_filename}_execution.json")
    execution_data = {
        "feature_request": feature_request,
        "timestamp": timestamp,
        "success": results.get("success", False),
        "total_steps": results.get("total_steps", 0),
        "duration_seconds": results.get("duration", 0),
        "parallel_execution": results.get("parallel_stats", {}),
        "metadata": results.get("metadata", {})
    }
    
    with open(execution_path, 'w') as f:
        json.dump(execution_data, f, indent=2)
    logger.info(f"Execution details saved to: {execution_path}")


async def main():
    """Main function to run the hierarchical dev team example."""
    # Clear any existing agents
    AgentRegistry.clear()
    
    # Create model configurations
    configs = create_model_configs()
    
    # Create agents
    agents = create_agents(configs)
    
    # Feature request
    feature_request = """
    User Authentication System with Social Login
    
    Requirements:
    - Email/password authentication
    - OAuth2 integration (Google, GitHub)
    - JWT token management
    - User profile management
    - Password reset functionality
    - Rate limiting for security
    - Frontend login/signup UI
    - Admin dashboard for user management
    """
    
    logger.info("=" * 80)
    logger.info("Hierarchical Team Pattern - Software Development Team")
    logger.info("=" * 80)
    logger.info(f"Feature Request: {feature_request.strip()}")
    logger.info(f"Team Structure:")
    logger.info("  - ProjectManager (GPT-4)")
    logger.info("    ├── FrontendLead (Claude)")
    logger.info("    │   ├── UIDesigner (GPT-4-mini)")
    logger.info("    │   └── UIImplementer (Gemini-flash)")
    logger.info("    └── BackendLead (Gemini-Pro)")
    logger.info("        ├── APIDeveloper (GPT-4-mini)")
    logger.info("        └── DatabaseDeveloper (Gemini-flash)")
    logger.info("=" * 80)
    
    # Run the development workflow
    results = await run_dev_team_workflow(feature_request)
    
    # Save results
    save_results(results, feature_request)
    
    # Print summary
    print("\n" + "=" * 80)
    print("WORKFLOW SUMMARY")
    print("=" * 80)
    print(f"Success: {results.get('success', False)}")
    print(f"Total Steps: {results.get('total_steps', 0)}")
    print(f"Duration: {results.get('duration', 0):.2f} seconds")
    
    if results.get('parallel_stats'):
        print("\nParallel Execution Statistics:")
        print(f"  - Team Leads in parallel: {results['parallel_stats']['team_leads']}")
        print(f"  - Frontend devs in parallel: {results['parallel_stats']['frontend_devs']}")
        print(f"  - Backend devs in parallel: {results['parallel_stats']['backend_devs']}")
    
    if results.get('error'):
        print(f"\nError: {results['error']}")
    
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())