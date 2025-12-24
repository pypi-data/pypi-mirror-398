#!/usr/bin/env python3
"""
Single Browser Shopping Assistant
==================================

Direct User <-> BrowserAgent shopping workflow.

Key design decisions:
    - No coordinator agent (unnecessary middleman)
    - Agent MUST use Google to discover stores (never types URLs directly)
    - Agent MUST describe what it sees before each action (prevents hallucination)
    - Session memory for multi-turn conversation

Example prompts:
    - "Find me running shoes under $150, size 43, black, good cushioning"
    - "I need a wireless keyboard under $100 with RGB lighting"

Usage:
    python example_single_browser_shopping.py
"""

import asyncio

# import logging
from pathlib import Path

from dotenv import load_dotenv

from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig
from marsys.models import ModelConfig

# Load environment variables
load_dotenv()

# Setup logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
SESSION_PATH = SCRIPT_DIR / "data" / "browser_session.json"
OUTPUT_DIR = SCRIPT_DIR / "output"

# ============================================================================
# AGENT INSTRUCTIONS
# ============================================================================

BROWSER_GOAL = "Find and purchase products for the user"

BROWSER_INSTRUCTION = """You are a shopping assistant. You navigate websites by looking at screenshots.

## MANDATORY: DESCRIBE BEFORE ACTING
Before EVERY action, you MUST first describe what you see in the screenshot:
"I see: [describe the current page - is it Google? A store? A product page?]"
Then decide your next action based on what you actually see.

## CRITICAL RULES

1. NEVER use the search_page tool - navigate visually using screenshots only

2. NEVER type a store URL directly (no amazon.com, nike.com, etc.)
   - You don't know what country the user is in
   - You MUST discover stores through Google search results

3. ALWAYS verify the screenshot after each action
   - If screenshot still shows Google after clicking = your click FAILED
   - Retry with different coordinates until you actually leave Google

4. Use Google effectively:
   - Click the "Shopping" tab for product comparisons
   - Sponsored results and ads often have good deals
   - Click on actual store links in results, not just product titles

## IMPORTANT: HOW ONLINE SHOPPING WORKS

Google search results show GENERAL product info:
- Brand, product name, price range, store name

Specific variants are selected ON THE RETAILER'S PRODUCT PAGE:
- Size, color, storage capacity, quantity, etc.

You CANNOT verify size/color availability from Google results.
You MUST visit the store and select options on the product page.

## WORKFLOW

1. Go to google.com, search for the product (brand + type is enough)
2. Click "Shopping" tab OR click a store link from results
3. VERIFY: Did the page change? Describe what you now see.
4. If still on Google, your click failed - try again
5. On the store site: handle cookie popups, navigate to the product
6. On the PRODUCT PAGE: select the specific options (size, color, etc.)
7. Verify that specific variant is in stock and within budget
8. Present the confirmed option to user
9. If user approves: proceed to checkout

## CLICKING LINKS
- Find the link text visually
- Click the CENTER of the text
- Check next screenshot - if page didn't change, retry with adjusted coordinates

## COOKIE POPUPS
If you see a popup, close it first (click Accept/Decline/X) before continuing.

## ASKING USER (IMPORTANT)
When you need information or want user input, you MUST invoke the User node.
Do NOT return a final response when waiting for user input.
Examples of when to invoke User:
- "I found a product, do you want to proceed?"
- "I need your shipping address"
- "Which size do you prefer?"
- "Would you like to fill this in yourself?"

## REMEMBER
- Describe what you see BEFORE each action
- Never assume you're on a page - verify from screenshot
- Never go directly to store URLs - use Google to find stores
- When asking user anything, INVOKE User node - don't end the conversation
"""


async def main():
    """Main entry point for single browser shopping example."""
    # Check for session file
    session_path = str(SESSION_PATH) if SESSION_PATH.exists() else None

    # Create output directory for screenshots
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Screenshots will be saved to: {OUTPUT_DIR / 'screenshots'}")

    browser_model_config = ModelConfig(
        type="api",
        provider="openai",
        name="gpt-5.1-codex",
        # thinking_budget=200,
        reasoning_effort="minimal",
        max_tokens=2000,
    )

    # Create browser agent with session memory for multi-turn conversation
    browser_agent = await BrowserAgent.create_safe(
        model_config=browser_model_config,
        name="ShoppingBrowserAgent",
        mode="advanced",  # Advanced mode for visual interaction
        headless=False,  # Set to True for background operation
        session_path=session_path,
        memory_retention="session",  # Remember conversation across turns
        goal=BROWSER_GOAL,
        instruction=BROWSER_INSTRUCTION,
        auto_screenshot=True,  # Enable automatic screenshots after each step
        element_detection_mode="none",  # Disable vision-based element detection
        tmp_dir=str(OUTPUT_DIR),  # Save screenshots to output directory
    )

    # Simple topology: User <-> BrowserAgent (direct interaction)
    topology = {
        "agents": ["User", "ShoppingBrowserAgent"],
        "flows": [
            "User -> ShoppingBrowserAgent",
            "ShoppingBrowserAgent -> User",
        ],
        "entry_point": "ShoppingBrowserAgent",
    }

    try:
        result = await Orchestra.run(
            task="Help the user find and purchase products online",
            topology=topology,
            execution_config=ExecutionConfig(
                user_interaction="terminal",
                user_first=False,
                convergence_timeout=600.0,
                status=StatusConfig.from_verbosity(2),
            ),
            max_steps=100,
        )

        if result.success:
            print(f"\n{result.final_response}")
        else:
            print(f"Error: {result.error}")

    except KeyboardInterrupt:
        print("\nShopping session interrupted by user.")
    except Exception as e:
        print(f"Shopping session failed: {e}", exc_info=True)
    finally:
        await browser_agent.cleanup()
        AgentRegistry.unregister("ShoppingBrowserAgent")


if __name__ == "__main__":
    asyncio.run(main())
