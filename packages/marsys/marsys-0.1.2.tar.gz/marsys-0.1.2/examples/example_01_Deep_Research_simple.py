"""Simplified Multi-Agent Deep Research System"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from marsys.agents.agents import Agent
from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.utils import init_agent_logging
from marsys.environment.tools import tool_google_search_api
from marsys.models.models import ModelConfig

init_agent_logging(level=logging.INFO, clear_existing_handlers=True)
logger = logging.getLogger("DeepResearchExample")


def write_to_scratch_pad(url: str, title: str, content: str, scratch_pad_file: str):
    """Write extracted content to scratch pad file."""
    try:
        source_id = 1
        if os.path.exists(scratch_pad_file):
            with open(scratch_pad_file, "r", encoding="utf-8") as f:
                source_id = sum(1 for line in f if line.strip()) + 1
        data = {
            "source_id": source_id,
            "url": url,
            "title": title,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        with open(scratch_pad_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        return {"success": True, "source_id": source_id}
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_scratch_pad_content(scratch_pad_file: str):
    """Read all content from scratch pad file."""
    sources = []
    if os.path.exists(scratch_pad_file):
        with open(scratch_pad_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    sources.append(json.loads(line.strip()))
    return sources


def write_file(file_path: str, content: str):
    """Write content to a file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"success": True, "file_path": file_path}


async def main():
    load_dotenv()

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY required")

    print("\n🔍 DEEP RESEARCH MULTI-AGENT SYSTEM")
    research_query = input("📝 Enter your research query: ").strip()

    research_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_directory = f"tmp/research_output_{research_id}"
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # Model configuration - using Gemini Pro for all agents
    model_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="google/gemini-2.5-pro",
        temperature=0.2,
        max_tokens=6000,
        api_key=OPENROUTER_API_KEY,
    )

    # Agent descriptions (simplified to 4 lines each)
    ORCHESTRATOR_DESC = """You manage a comprehensive research workflow.
You must understand the research topic that the user is asking and then write a proper query to the RetrievalAgent.
Understand how many sources user expects to have in the final report and communicate that to the RetrievalAgent when calling it.
In addition, provide the output_directory to RetrievalAgent for organizing research files. After sources are collected,
provide BOTH the scratch_pad_location AND the output_directory to SynthesizerAgent for report creation.
IMPORTANT: The SynthesizerAgent needs both parameters: {"scratch_pad_location": "path/to/scratch.jsonl", "output_directory": "path/to/output"}"""

    RETRIEVAL_DESC = """Your role is to find and collect relevant research sources.
When you receive a query and output_directory, search the web for diverse and quality sources.
Create a scratch pad path as: output_directory + "/research_scratch_pad.jsonl" (use the actual path provided, not the literal string).
For only two URLs, invokes BrowserAgent individually with that URL and the scratch pad file path (you just need to extract contents for two URLs and then you can go back to the OrchestratorAgent).
If the browser agent cannot retrieve content from a source, do not try again.
Returns scratch pad location to OrchestratorAgent when all sources are processed."""

    BROWSER_DESC = """Your role is to extract content from a single web page.
Once you receive a URL and scratch pad file path, you must first extract the content from the URL. Then, you need to clean the content into a markdown format (only useful text and urls, no html tags or unusable characters) 
and appends it to the scratch pad file using the provided tools. Return the result of the extraction (success or fail) to RetrievalAgent once done."""

    SYNTHESIZER_DESC = """Your role is to create a comprehensive research report based on the provided sources.
You will receive TWO parameters in your request: scratch_pad_location (path to the sources file) and output_directory (where to save the report).
First read all the contents from scratch_pad_location using read_scratch_pad_content tool. Synthesize the report by thinking hard about the topics of the sources and their contents.
Once you have created the backbone of the report, create a markdown report with citations to the references.
Save the final report using write_file tool to: output_directory + "/final_research_report.md" (use the actual output_directory path from your request, not the literal string)."""

    # Create agents
    orchestrator = Agent(
        model_config=model_config,
        description=ORCHESTRATOR_DESC,
        agent_name="OrchestratorAgent",
        allowed_peers=["RetrievalAgent", "SynthesizerAgent"],
    )

    retrieval_agent = Agent(
        model_config=model_config,
        description=RETRIEVAL_DESC,
        agent_name="RetrievalAgent",
        allowed_peers=["BrowserAgent"],
        tools={"tool_google_search_api": tool_google_search_api},
    )

    browser_agent = await BrowserAgent.create_safe(
        model_config=model_config,
        description=BROWSER_DESC,
        agent_name="BrowserAgent",
        headless=True,
        memory_retention="single_run",
        tools={"write_to_scratch_pad": write_to_scratch_pad},
    )

    synthesizer_agent = Agent(
        model_config=model_config,
        description=SYNTHESIZER_DESC,
        agent_name="SynthesizerAgent",
        tools={
            "read_scratch_pad_content": read_scratch_pad_content,
            "write_file": write_file,
        },
    )

    # Run the multi-agent system
    try:
        result = await orchestrator.auto_run(
            initial_request={
                "query": research_query,
                "output_directory": output_directory,
            },
            max_steps=50,
            timeout=1800,
            steering_mode="never",
        )

        print("\n✅ RESEARCH COMPLETED!")
        print(f"Results: {str(result)[:500]}...")
        print(f"Output directory: {output_directory}")

    finally:
        if hasattr(browser_agent, "close"):
            await browser_agent.close()


if __name__ == "__main__":
    asyncio.run(main())
