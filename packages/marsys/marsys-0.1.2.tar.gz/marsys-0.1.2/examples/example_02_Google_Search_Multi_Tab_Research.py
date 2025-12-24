# Multi-Tab Google Search Research with BrowserAgent
# ====================================================
# This example demonstrates the MARSYS framework's BrowserAgent capabilities
# for automated web research workflows including:
#
# Features Demonstrated:
# 1. Automated Google search execution
# 2. Dynamic popup handling (cookies, reCAPTCHA)
# 3. Multi-tab management for parallel content extraction
# 4. Intelligent content extraction from diverse websites
# 5. Vision-based interactive element detection
# 6. Structured result compilation and reporting
#
# Workflow: Query → Google Search → Handle Popups → Open Results → Extract Content → Report

# Imports & logging -----------------------------------------------------------
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents.agents import Agent
from agents.browser_agent import BrowserAgent
from agents.utils import init_agent_logging
from models.models import ModelConfig
from utils.monitoring import default_progress_monitor

# --- Logging Configuration ---
init_agent_logging(level=logging.INFO, clear_existing_handlers=True)
notebook_logger = logging.getLogger("GoogleSearchResearch")

# --- Agent Descriptions ---
SEARCH_COORDINATOR_DESCRIPTION = (
    "You are a master research coordinator. Your goal is to oversee a multi-agent team to "
    "produce a comprehensive research report on a given topic.\n\n"
    "Your workflow is as follows:\n"
    "1.  **Receive a research query** from the user.\n"
    "2.  **Invoke the `WebSearchAgent`**: Pass the query to this agent to get a list of relevant URLs from a Google search.\n"
    "3.  **Invoke the `ContentAnalyzer`**: Pass the list of URLs to this agent. It will visit each URL, extract the cleaned content in Markdown format, and return the structured content for each URL.\n"
    "4.  **Synthesize the Final Report**: Once you receive the analyzed content from all sources, compile it into a single, well-structured, and informative research report in Markdown format. The report should include a title, an executive summary, key findings from each source, and a list of the sources.\n"
    "5.  **Provide the Final Answer**: Your final action must be `final_response` with the complete report in the 'response' field."
)

WEB_SEARCH_DESCRIPTION = (
    "You are a specialized Web Search Agent using a browser. Your single responsibility is to "
    "take a search query, perform a Google search, and return a list of the top organic "
    "search result URLs.\n\n"
    "Your workflow:\n"
    "1. Navigate to google.com.\n"
    "2. Handle any popups.\n"
    "3. Enter the search query and execute the search.\n"
    "4. Scrape the search result links from the page using the `get_attribute_all` tool on relevant selectors (e.g., 'h3 a', 'a[data-ved]').\n"
    "5. Clean the URLs to remove any Google tracking or redirect parameters.\n"
    "6. Return a JSON object containing a list of the clean URLs in the `search_results_urls` field."
)

CONTENT_ANALYZER_DESCRIPTION = (
    "You are a specialized Content Analyzer Agent using a browser. Your responsibility is to take "
    "a list of URLs and extract the main content in clean Markdown format for each one.\n\n"
    "For each URL in the provided list, you must use the `extract_content_from_url` tool. "
    "This tool handles navigation, HTML cleaning, and conversion to Markdown automatically.\n\n"
    "After processing all URLs, return a structured list of the results. Each item in the list "
    "should be a dictionary containing the 'url', 'title', and 'content' for a page."
)

async def main():
    """Main function to demonstrate automated Google search research."""
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Google Search Research Example")
    
    web_search_agent = None
    content_analyzer = None

    try:
        # Load environment variables from .env file if it exists
        env_file_path = Path(__file__).parent / ".env"
        if env_file_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file_path)
                logger.info(f"Loaded environment variables from {env_file_path}")
            except ImportError:
                logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")
                logger.info("Proceeding with system environment variables only")
            except Exception as e:
                logger.warning(f"Failed to load .env file: {e}")
        else:
            logger.info("No .env file found, using system environment variables")

        # Get API keys from environment
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY environment variable not set")
            logger.info("Please set OPENAI_API_KEY in your environment or create a .env file with:")
            logger.info("OPENAI_API_KEY=your_api_key_here")
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # --- Model Configurations ---
        try:
            # Main browser agent - for navigation and interaction
            browser_model_config = ModelConfig(
                type="api",
                provider="openai", 
                name="gpt-4.1-mini",
                temperature=0.1,  # Low temperature for precise actions
                max_tokens=4000,
                api_key=OPENAI_API_KEY,
            )
            
            # Vision agent - for interactive element detection
            vision_model_config = ModelConfig(
                type="api",
                provider="openai",
                name="gpt-4.1-mini",  # Vision-capable model
                temperature=0.2,
                max_tokens=2000,
                api_key=OPENAI_API_KEY,
            )
            
            # Content analysis agent - for intelligent content extraction
            content_model_config = ModelConfig(
                type="api",
                provider="openai",
                name="gpt-4.1-mini",
                temperature=0.3,
                max_tokens=8000,
                api_key=OPENAI_API_KEY,
            )
            
        except ValueError as e:
            logger.error(f"Failed to create ModelConfig: {e}")
            raise

        # --- Agent Initialization ---
        logger.info("Initializing agents...")

        # Define proper JSON schemas
        coordinator_input_schema = {
            "type": "object",
            "properties": {
                "research_query": {"type": "string", "description": "The research query to search for"},
                "max_results": {"type": "integer", "description": "Maximum number of search results to analyze"}
            },
            "required": ["research_query", "max_results"]
        }

        coordinator_output_schema = {
            "type": "object",
            "properties": {
                "final_report": {"type": "string", "description": "The comprehensive research report"},
                "sources_analyzed": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs analyzed"
                }
            },
            "required": ["final_report", "sources_analyzed"]
        }

        web_search_input_schema = {
            "type": "object",
            "properties": {
                "search_query": {"type": "string", "description": "The search query to execute on Google"},
                "num_results": {"type": "integer", "description": "Number of results to return"}
            },
            "required": ["search_query"]
        }

        web_search_output_schema = {
            "type": "object",
            "properties": {
                "search_results_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of clean URLs from search results"
                }
            },
            "required": ["search_results_urls"]
        }

        content_analyzer_input_schema = {
            "type": "object",
            "properties": {
                "urls_to_analyze": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs to analyze and extract content from"
                }
            },
            "required": ["urls_to_analyze"]
        }

        content_analyzer_output_schema = {
            "type": "object",
            "properties": {
                "analyzed_contents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["url", "title", "content"]
                    },
                    "description": "List of analyzed content from each URL"
                }
            },
            "required": ["analyzed_contents"]
        }

        # Create Search Coordinator Agent
        search_coordinator = Agent(
            agent_name="SearchCoordinator",
            model_config=browser_model_config,
            description=SEARCH_COORDINATOR_DESCRIPTION,
            allowed_peers=["WebSearchAgent", "ContentAnalyzer"],
            input_schema=coordinator_input_schema,
            output_schema=coordinator_output_schema,
        )

        # Create Web Search Agent with vision capabilities
        web_search_agent = await BrowserAgent.create_safe(
            model_config=browser_model_config,
            vision_model_config=vision_model_config,  # Enable vision analysis
            description=WEB_SEARCH_DESCRIPTION,
            agent_name="WebSearchAgent",
            headless=True,  # Set to False for debugging
            browser_channel="chrome",  # Use system Chrome if available
            input_schema=web_search_input_schema,
            output_schema=web_search_output_schema,
        )

        # Create Content Analyzer Agent (BrowserAgent with content extraction capabilities)
        content_analyzer = await BrowserAgent.create_safe(
            model_config=content_model_config,
            description=CONTENT_ANALYZER_DESCRIPTION,
            agent_name="ContentAnalyzer",
            headless=True,
            browser_channel="chrome",
            input_schema=content_analyzer_input_schema,
            output_schema=content_analyzer_output_schema,
        )

        logger.info("All agents initialized successfully")

        # --- Research Query ---
        research_query = "latest developments in artificial intelligence 2024"
        max_results = 3  # Keep it small for the example

        logger.info(f"Research Query: '{research_query}'")
        logger.info(f"Target Results: {max_results}")

        # --- Execute Research Workflow via Coordinator ---
        logger.info("Starting automated research workflow via SearchCoordinator...")

        # The coordinator will now handle the entire workflow internally by invoking other agents.
        final_report_data = await search_coordinator.auto_run(
            initial_request={
                "research_query": research_query,
                "max_results": max_results,
            },
            max_steps=25,  # Allow enough steps for multiple agent invocations
        )

        # --- Output final results ---
        logger.info("Research workflow completed successfully!")
        print("\n" + "="*80)
        print("AUTOMATED RESEARCH REPORT")
        print("="*80)
        
        if isinstance(final_report_data, dict) and "final_report" in final_report_data:
            print(final_report_data["final_report"])
            if "sources_analyzed" in final_report_data and final_report_data["sources_analyzed"]:
                print("\n\n--- Sources Analyzed ---")
                for url in final_report_data["sources_analyzed"]:
                    print(f"- {url}")
        else:
            # Fallback for string or other unexpected format from auto_run
            print(final_report_data)

        print("\n" + "="*80)

    except Exception as e:
        logger.error(f"Error during research workflow: {e}", exc_info=True)
        
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        cleanup_tasks = []
        
        # Close web search agent
        if web_search_agent:
            cleanup_tasks.append(("WebSearchAgent", web_search_agent.close()))
        
        # Close content analyzer agent  
        if content_analyzer:
            cleanup_tasks.append(("ContentAnalyzer", content_analyzer.close()))
        
        # Execute cleanup tasks
        for agent_name, cleanup_task in cleanup_tasks:
            try:
                await cleanup_task
                logger.info(f"{agent_name} closed successfully")
            except Exception as e:
                logger.warning(f"Error closing {agent_name}: {e}")


# Main Execution Logic
if __name__ == "__main__":
    print("Google Search Research Example")
    print("==============================")
    print("This example demonstrates automated web research using BrowserAgent")
    print("Features: Google search, popup handling, multi-tab management, content extraction")
    print("")
    print("Setup:")
    print("1. Set OPENAI_API_KEY environment variable, or")
    print("2. Create a .env file with: OPENAI_API_KEY=your_api_key_here")
    print("3. Optionally install: pip install python-dotenv")
    print("")
    
    # Run the example
    asyncio.run(main()) 