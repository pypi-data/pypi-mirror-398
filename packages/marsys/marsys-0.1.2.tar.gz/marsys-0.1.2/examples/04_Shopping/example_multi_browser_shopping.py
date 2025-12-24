#!/usr/bin/env python3
"""
Multi-Browser Shopping Assistant
=================================

Demonstrates MARSYS's Orchestrator + WebSearchAgent + parallel BrowserAgent
architecture for comprehensive multi-source product comparison.

Architecture:
    - ShoppingCoordinator (Agent): Manages workflow, dispatches tasks, aggregates results
    - ShoppingSearchAgent (WebSearchAgent): Searches Google to find retailer product URLs
    - RetailerBrowserPool (AgentPool, 3 instances): Browse retailer websites in parallel

How it works:
    1. User provides shopping request
    2. Coordinator invokes WebSearchAgent with product query
    3. WebSearchAgent searches Google with site-specific queries
       (e.g., "4K monitor USB-C" site:amazon.com OR site:bestbuy.com)
    4. WebSearchAgent returns list of retailer URLs with product links
    5. Coordinator invokes up to 3 BrowserAgents in parallel:
       - Each browser visits a different retailer URL
       - Browsers navigate to products, extract details
    6. Each BrowserAgent returns:
       - product_url: Final product page URL
       - product_name: Item name
       - product_specs: Specifications matching user criteria
       - match_status: "found" or "not_found"
    7. Coordinator aggregates results and presents price comparison to user

Example prompts to try:
    - "Find me a 4K monitor under $400 with USB-C and at least 27 inches. Compare prices across different retailers."
    - "I need a laptop under $1000 with 16GB RAM and SSD. Show me options
       from Amazon, Best Buy, and Newegg."
    - "Find wireless noise-cancelling headphones under $300. Compare Sony,
       Bose, and Apple AirPods Max prices across stores."

Usage:
    python example_multi_browser_shopping.py

Requirements:
    - Run setup_browser_session.py first to create a logged-in session
    - Or provide your own session at data/browser_session.json
"""

import asyncio

# import logging
from pathlib import Path

from dotenv import load_dotenv

from marsys.agents import Agent, AgentPool
from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.registry import AgentRegistry
from marsys.agents.web_search_agent import WebSearchAgent
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig
from marsys.models import ModelConfig

# Load environment variables
load_dotenv()

# # Setup logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
SESSION_PATH = SCRIPT_DIR / "data" / "browser_session.json"

# ============================================================================
# AGENT INSTRUCTIONS
# ============================================================================

COORDINATOR_GOAL = "Coordinate multi-source product searches and aggregate price comparisons"

COORDINATOR_INSTRUCTION = """You are a shopping coordinator that orchestrates multi-retailer product searches.

YOUR WORKFLOW:

STEP 0: First, greet the user and ask what product they want to find and compare across retailers. Wait for their response.

STEP 1: Analyze the request and invoke ShoppingSearchAgent
- Extract: product type, price limit, required features, preferred brands
- Send a search request to ShoppingSearchAgent including:
  - product_query: what to search for
  - price_limit: maximum budget
  - required_features: list of must-have features
  - preferred_retailers: list of retailers to check (amazon.com, bestbuy.com, newegg.com, etc.)

STEP 2: When ShoppingSearchAgent returns retailer URLs
- Select up to 3 most promising retailer URLs
- Use parallel_invoke to dispatch browser agents to RetailerBrowserPool
- Each browser should receive a retailer_url and the product_criteria to verify

STEP 3: Aggregate browser results
- Collect product details from each retailer
- Create a price comparison table
- Highlight best value and any trade-offs

STEP 4: Present final results to user
- Show comparison with product name and URL for each retailer
- Include price at each retailer and key specifications
- Provide recommendation based on price/value

IMPORTANT:
- Maximum 3 browser agents per search to avoid overwhelming retailers
- If a retailer doesn't have matching products, note it in the comparison
- Always verify prices are within user's budget before including
"""

SEARCH_AGENT_GOAL = "Search Google to find product pages from major retailers"

SEARCH_AGENT_INSTRUCTION = """You are a shopping search specialist that finds product pages on retailer websites.

When you receive a search request from the Coordinator:
1. Extract the product query and preferred retailers
2. Use tool_google_search_api to search for products with site-specific queries:
   - Query format: "product name features" site:retailer1.com OR site:retailer2.com
   - Example: "4K USB-C monitor 27 inch" site:amazon.com OR site:bestbuy.com OR site:newegg.com

3. From the search results, extract URLs that look like product pages (not category pages):
   - Amazon: Look for URLs containing /dp/ or /gp/product/
   - Best Buy: Look for URLs containing /site/ with product names
   - Newegg: Look for URLs containing /p/
   - Walmart: Look for URLs containing /ip/

4. Return results to Coordinator including:
   - search_status: whether products were found or not
   - query_used: the Google search query you used
   - retailer_urls: list of found product URLs, each with retailer name, URL, title from search, and snippet
   - total_found: count of product URLs found

5. If no matching products found, include the reason why (e.g., no products on specified retailers)

SEARCH TIPS:
- Try multiple query variations if initial search yields few results
- Include key features in the query (USB-C, 4K, etc.)
- Limit to 2-3 retailers per search for focused results
"""

BROWSER_GOAL = "Visit retailer websites and extract product details"

BROWSER_INSTRUCTION = """You are a browser agent that extracts product information from retailer websites.

IMPORTANT: You MUST navigate to the actual website and extract real data. Do NOT rely on your internal knowledge - it is outdated and prices/stock change constantly.

WORKFLOW:
1. Navigate to the retailer URL provided by the Coordinator.
2. Cookie popups: click "Reject All" or close button; accept only as last resort.
3. If on category page, scroll and click on the most relevant product.
4. On product page, select the exact variant (size/color/specs) and verify stock availability.

REPORTING:
- Found: retailer name, product URL, name, current price, selected variant, stock status, whether it meets criteria
- Not found: retailer name, reason (out of stock, over budget), closest match if any

RULES:
- ALWAYS verify the specific variant is in stock before reporting
- Extract actual price, not MSRP; note any discounts
"""


async def main():
    """Main entry point for multi-browser shopping example."""
    # Check for session file
    session_path = str(SESSION_PATH) if SESSION_PATH.exists() else None

    # Model configurations (haiku 4.5 for all agents)
    model_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-haiku-4.5",
        max_tokens=4000,
    )

    browser_model_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-haiku-4.5",
        max_tokens=4000,
    )

    # Create coordinator agent
    coordinator = Agent(
        model_config=model_config,
        name="ShoppingCoordinator",
        goal=COORDINATOR_GOAL,
        instruction=COORDINATOR_INSTRUCTION,
        memory_retention="session",
    )

    # Create web search agent
    search_agent = WebSearchAgent(
        model_config=model_config,
        name="ShoppingSearchAgent",
        goal=SEARCH_AGENT_GOAL,
        instruction=SEARCH_AGENT_INSTRUCTION,
        search_mode="web",
        include_google=True,
        memory_retention="single_run",
    )

    # Create browser pool with 3 instances
    browser_pool = await AgentPool.create_async(
        agent_class=BrowserAgent,
        num_instances=3,
        model_config=browser_model_config,
        name="RetailerBrowserPool",
        mode="advanced",
        headless=False,
        session_path=session_path,
        memory_retention="single_run",
        goal=BROWSER_GOAL,
        instruction=BROWSER_INSTRUCTION,
        auto_screenshot=True,  # Enable automatic screenshots after each step
        element_detection_mode="none",  # Disable vision-based element detection
    )

    # Register pool with Orchestra
    AgentRegistry.register_pool(browser_pool)

    # Topology: User <-> Coordinator <-> SearchAgent / BrowserPool
    topology = {
        "agents": ["User", "ShoppingCoordinator", "ShoppingSearchAgent", "RetailerBrowserPool"],
        "flows": [
            "User -> ShoppingCoordinator",
            "ShoppingCoordinator -> User",
            "ShoppingCoordinator -> ShoppingSearchAgent",
            "ShoppingSearchAgent -> ShoppingCoordinator",
            "ShoppingCoordinator -> RetailerBrowserPool",
            "RetailerBrowserPool -> ShoppingCoordinator",
        ],
        "entry_point": "ShoppingCoordinator",
    }

    try:
        result = await Orchestra.run(
            task="Help the user find and compare products across multiple retailers",
            topology=topology,
            execution_config=ExecutionConfig(
                user_interaction="terminal",
                user_first=False,
                convergence_timeout=900.0,
                status=StatusConfig.from_verbosity(1),
            ),
            max_steps=50,
        )

        if result.success:
            print(f"\n{result.final_response}")
        else:
            print(f"Error: {result.error}")

    except KeyboardInterrupt:
        print("\n\nSearch interrupted by user.")
    except Exception as e:
        print(f"Search failed: {e}", exc_info=True)
    finally:
        # Cleanup
        print("Cleaning up agents...")
        await browser_pool.cleanup()
        AgentRegistry.unregister("ShoppingCoordinator")
        AgentRegistry.unregister("ShoppingSearchAgent")


if __name__ == "__main__":
    asyncio.run(main())
