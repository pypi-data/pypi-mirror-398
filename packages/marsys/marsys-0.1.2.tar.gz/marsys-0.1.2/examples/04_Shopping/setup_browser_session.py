#!/usr/bin/env python3
"""
Browser Session Setup Helper
=============================

Interactive script to help users log into websites and save browser sessions
for reuse in other MARSYS examples.

This script:
1. Opens a browser window (non-headless)
2. Asks which website you want to log into
3. Navigates to that website's login page
4. Waits for you to manually log in
5. Asks if you want to log into more websites
6. Saves the session when you're done

Usage:
    python setup_browser_session.py

The session will be saved to:
    examples/04_Shopping/data/browser_session.json

This session can then be loaded by other examples to access authenticated
content (e.g., Google, LinkedIn, Amazon).
"""

import asyncio
import logging
import os
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
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
SESSION_PATH = SCRIPT_DIR / "data" / "browser_session.json"

# Agent instruction
SETUP_INSTRUCTION = f"""You help users log into websites and save browser sessions for future use.

WORKFLOW:
1. Greet the user and ask: "Which website would you like to log into? (e.g., Google, LinkedIn, Amazon)"
2. When user responds with a website name, navigate to that website's login page:
   - Google: https://accounts.google.com
   - LinkedIn: https://www.linkedin.com/login
   - Amazon: https://www.amazon.com/ap/signin
   - For other sites, navigate to the main site and look for login
3. Tell the user: "I've opened the login page. Please log in manually in the browser window. Type 'done' when you've finished logging in."
4. Wait for user to type "done"
5. Ask: "Would you like to log into another website? (yes/no)"
6. If user says yes, repeat from step 1
7. If user says no or is done, save the session using the save_session tool to: {SESSION_PATH}
8. Confirm to user: "Session saved successfully! You can now use this session in other shopping examples."

IMPORTANT RULES:
- Do NOT try to enter credentials or interact with login forms - let the user do it manually
- Be patient and wait for user confirmation before proceeding
- Only save the session when the user confirms they are done with ALL websites
- Use clear, simple language in your instructions
- If the user types something other than a website name, ask for clarification
"""


async def main():
    """Main entry point for session setup."""
    # Ensure data directory exists
    SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Model configuration (haiku is sufficient for session setup)
    model_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-haiku-4.5",
        max_tokens=4096,
    )

    # Create browser agent
    session_agent = await BrowserAgent.create_safe(
        model_config=model_config,
        name="SessionSetupAgent",
        headless=False,
        mode="advanced",
        memory_retention="single_run",
        goal="Help user log into websites and save browser session",
        instruction=SETUP_INSTRUCTION,
    )

    # Topology: User <-> SessionSetupAgent
    topology = {
        "agents": ["User", "SessionSetupAgent"],
        "flows": [
            "User -> SessionSetupAgent",
            "SessionSetupAgent -> User",
        ],
        "entry_point": "SessionSetupAgent",
    }

    try:
        result = await Orchestra.run(
            task="Help me log into websites and save my browser session",
            topology=topology,
            execution_config=ExecutionConfig(
                user_interaction="terminal",
                user_first=False,
                status=StatusConfig.from_verbosity(1),
            ),
            max_steps=50,
        )

        if result.success:
            print(f"Session saved to: {SESSION_PATH}")
        else:
            print(f"Error: {result.error}")

    except KeyboardInterrupt:
        print("\nSession setup interrupted by user.")
    except Exception as e:
        logger.error(f"Session setup failed: {e}", exc_info=True)
    finally:
        await session_agent.cleanup()
        AgentRegistry.unregister("SessionSetupAgent")


if __name__ == "__main__":
    asyncio.run(main())
