"""Advanced Multi-Agent Deep Research System

This example demonstrates a sophisticated multi-agent research workflow with:
- User interaction for query clarification
- Critical analysis of user intent
- Parallel research orchestration (3 independent research streams)
- Web and academic search (Google + Semantic Scholar)
- Browser-based content extraction
- Multi-report synthesis and comparison
- Final unified report generation

The system creates comprehensive research reports by running 3 parallel research
workflows and then critically comparing and synthesizing the results.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests
from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.agent_pool import AgentPool
from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.registry import AgentRegistry
from marsys.agents.utils import init_agent_logging
from marsys.coordination import Orchestra
from marsys.environment.tools import tool_google_search_api
from marsys.models.models import ModelConfig

# init_agent_logging(level=logging.INFO, clear_existing_handlers=True)


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================


def tool_semantic_scholar_search(
    query: str, num_results: int = 10, year_filter: str = None
) -> str:
    """
    Search academic papers using Semantic Scholar API.

    Args:
        query: Search query for academic papers
        num_results: Number of results to return (default: 10)
        year_filter: Optional year filter (e.g., "2020-" for 2020 onwards)

    Returns:
        JSON string with search results
    """
    url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"

    params = {
        "query": query,
        "fields": "title,url,abstract,year,authors,citationCount,publicationDate,venue",
        "limit": min(num_results, 100),
    }

    if year_filter:
        params["year"] = year_filter

    # API key optional but recommended for higher rate limits
    headers = {}
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for paper in data.get("data", []):
            results.append(
                {
                    "title": paper.get("title", "N/A"),
                    "url": paper.get("url", ""),
                    "abstract": paper.get("abstract", "")[:500],  # Truncate abstract
                    "year": paper.get("year"),
                    "authors": [
                        a.get("name", "") for a in paper.get("authors", [])[:3]
                    ],  # First 3 authors
                    "citations": paper.get("citationCount", 0),
                    "venue": paper.get("venue", ""),
                }
            )

        return json.dumps({"results": results, "total": len(results)})

    except Exception as e:
        return json.dumps({"error": f"Semantic Scholar search failed: {str(e)}"})


def write_to_scratch_pad(url: str, title: str, content: str, scratch_pad_file: str):
    """Write extracted content to scratch pad file in JSONL format."""
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

        # Ensure directory exists
        Path(scratch_pad_file).parent.mkdir(parents=True, exist_ok=True)

        with open(scratch_pad_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        return {"success": True, "source_id": source_id, "file": scratch_pad_file}
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
    return {"sources": sources, "total": len(sources)}


def write_file(file_path: str, content: str):
    """Write content to a file."""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "file_path": file_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_file(file_path: str):
    """Read content from a file."""
    try:
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"success": True, "content": content, "file_path": file_path}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# AGENT DESCRIPTIONS
# ============================================================================

QUERY_ANALYZER_DESC = """You interact with the user to understand their research needs.

Your role:
1. Ask the user about their research topic and what they want to learn
2. Send the user's response to UserIntentAgent for analysis
3. Receive feedback about what additional information is needed
4. Ask user follow-up questions if UserIntentAgent identifies gaps (max 2 rounds)
5. Once all information is collected, send everything to ResearchStatementAgent

When communicating with the user, be friendly and clear. When you receive feedback
from UserIntentAgent about needing more information, ask the user those questions.
After the second round of questions (if needed), proceed to ResearchStatementAgent
regardless of whether you have perfect information."""

USER_INTENT_DESC = """You critically analyze user input to understand research intent.

Your role:
1. Analyze what the user has said about their research needs
2. Identify what information you already understand
3. Determine what additional information is needed for a complete research plan
4. Return your analysis to QueryAnalyzer with:
   - What you understand so far
   - What specific information is still needed (if any)
   - Whether you have enough to proceed

Be thorough but practical. If critical information is missing (scope, focus areas,
desired depth), clearly identify it. If you have enough for a good research plan,
say so."""

RESEARCH_STATEMENT_DESC = """You create a detailed research statement from user input.

Your role:
1. Receive all collected user information from QueryAnalyzer
2. Synthesize it into a clear, comprehensive research statement
3. Include: research topic, key questions, scope, and desired outcomes
4. Send the research statement to ALL THREE orchestrators in parallel

Use parallel_invoke to send to: Orchestrator1, Orchestrator2, Orchestrator3
Provide each with the research statement and their unique file paths."""

ORCHESTRATOR_DESC = """You manage one research workflow stream.

Your role:
1. Receive research statement and your file paths (scratch_pad_path, report_path)
2. Send research statement to WebRetrievalAgent with your scratch_pad_path
3. Wait for WebRetrievalAgent to complete
4. Send scratch_pad_path and report_path to SynthesizerAgent  
5. Wait for SynthesizerAgent to complete
6. **After Synthesizer completes, invoke FinalReportCritic with completion signal**

You coordinate: WebRetrieval → Synthesis → FinalReportCritic
Pass correct file paths to each agent."""

WEB_RETRIEVAL_DESC = """You find and collect research sources from web and academic databases.

Your role:
1. Receive research statement and scratch_pad_path
2. Create 1-2 diverse search queries for Google search
3. Create 1-2 academic-focused queries for Semantic Scholar
4. Execute searches using both tools
5. Select 5-8 most relevant URLs from combined results
6. Invoke BrowserAgent for each URL (can invoke multiple in parallel)
7. Wait for the BrowserAgents to complete and save content to scratch_pad (if they fail, don't invoke them again unless none of the BrowserAgents succeeded. In that case you need to search with another keyword and try again. But you can maximum try twice)
7. Return completion status to Orchestrator

Provide BrowserAgent with: url, scratch_pad_path, and what to extract.
Only call three URLs total."""

BROWSER_DESC = """You extract content from a single web page.

Your role:
1. Receive URL and scratch_pad_path
2. Extract content from the URL
3. Clean and format content (markdown format, relevant text only)
4. Save to scratch_pad using write_to_scratch_pad tool
5. Return success/failure status

Extract only content relevant to the research topic. If extraction fails, report failure to WebRetrieval agent and do not retry."""

SYNTHESIZER_DESC = """You create a comprehensive research report from collected sources.

Your role:
1. Receive scratch_pad_path and report_path
2. Read all sources using read_scratch_pad_content tool
3. Analyze and organize the information by themes
4. Create a well-structured markdown report with:
   - Executive summary
   - Main findings organized by topic
   - Citations to sources (use [source_id] format)
   - References section listing all sources
5. Save report using write_file tool to report_path

IMPORTANT: You MUST call the write_file tool yourself to save the report. Execute the tool call
directly and verify it succeeds before returning to Orchestrator.

Once done return to Orchestrator with success status and report_path."""

FINAL_CRITIC_DESC = """You critically analyze and compare multiple research reports.

Your role:
1. Receive paths to all three research reports (report_1.md, report_2.md, report_3.md)
2. Read each report using read_file tool
3. Analyze each report for:
   - Quality and depth of research
   - Coverage of research topic
   - Unique insights or perspectives
   - Strengths and weaknesses
4. Compare reports to identify:
   - Common themes and consistent findings
   - Unique contributions from each report
   - Conflicting information or perspectives
   - Gaps in overall coverage
5. Send your critical analysis to FinalReportSynthesizer

Provide specific, actionable insights about how to create the best final report."""

FINAL_SYNTHESIZER_DESC = """You create the ultimate research report from multiple sources.

Your role:
1. Receive research statement, report paths, and critic's analysis
2. Read all three reports using read_file tool (note: some may be missing)
3. Synthesize the BEST final report by:
   - Incorporating strongest insights from all available reports
   - Addressing gaps identified by the critic
   - Resolving any conflicts in information
   - Creating a coherent, comprehensive narrative
4. Structure with:
   - Executive Summary
   - Research Overview
   - Key Findings (organized thematically)
   - Detailed Analysis
   - Conclusions and Recommendations
   - Complete References
5. Save to final_report_path using write_file tool

IMPORTANT: You MUST call the write_file tool to save the final report, even if some
individual reports are missing. Work with whatever reports are available and create
the best synthesis possible. Do NOT return a final_response without first executing
the write_file tool call to persist the report to disk.

Create a publication-quality research report that represents the best synthesis
of all research streams."""


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def run_advanced_research():
    """Run the advanced multi-agent research workflow."""

    load_dotenv()

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY required")

    # Single model configuration - Gemini 2.5 Flash
    model_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="google/gemini-2.5-pro",
        temperature=0.2,
        thinking_budget=2000,
        max_tokens=12000,
        api_key=OPENROUTER_API_KEY,
    )
    browser_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="google/gemini-2.5-flash",
        temperature=0.2,
        thinking_budget=2000,
        max_tokens=12000,
        api_key=OPENROUTER_API_KEY,
    )

    # Create output directory
    research_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_directory = f"./tmp/research_{research_id}"
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Research directory: {output_directory}")

    # File paths for 3 parallel research streams
    scratch_paths = [
        f"{output_directory}/scratch_pad_1.jsonl",
        f"{output_directory}/scratch_pad_2.jsonl",
        f"{output_directory}/scratch_pad_3.jsonl",
    ]
    report_paths = [
        f"{output_directory}/report_1.md",
        f"{output_directory}/report_2.md",
        f"{output_directory}/report_3.md",
    ]
    final_report_path = f"{output_directory}/final_report.md"

    # Create agents
    print("\n🤖 Creating agents...")

    query_analyzer = Agent(
        model_config=model_config,
        goal="Interact with users to understand research needs",
        instruction=QUERY_ANALYZER_DESC,
        name="QueryAnalyzer",
    )

    user_intent_agent = Agent(
        model_config=model_config,
        goal="Critically analyze user input to understand research intent",
        instruction=USER_INTENT_DESC,
        name="UserIntentAgent",
    )

    research_statement_agent = Agent(
        model_config=model_config,
        goal="Create detailed research statements from user input",
        instruction=RESEARCH_STATEMENT_DESC,
        name="ResearchStatementAgent",
    )

    # Create 3 orchestrator instances
    orchestrators = []
    for i in range(1, 4):
        orchestrators.append(
            Agent(
                model_config=model_config,
                goal="Manage one research workflow stream",
                instruction=ORCHESTRATOR_DESC,
                name=f"Orchestrator{i}",
                memory_retention="session",
            )
        )


    # Web retrieval agents
    web_retrieval_agents = []
    for i in range(1, 4):
        web_retrieval_agents.append(
            Agent(
                model_config=model_config,
                goal="Find and collect research sources from web and academic databases",
                instruction=WEB_RETRIEVAL_DESC,
                name=f"WebRetrieval{i}",
                tools={
                    "tool_google_search_api": tool_google_search_api,
                    "tool_semantic_scholar_search": tool_semantic_scholar_search,
                },
            )
        )

    # Browser agent pool
    browser_pools = []
    for i in range(1, 4):
        browser_pool = await AgentPool.create_async(
            agent_class=BrowserAgent,
            num_instances=5,
            model_config=browser_config,
            goal="Extract content from web pages",
            instruction=BROWSER_DESC,
            name=f"BrowserAgent{i}",
            headless=True,
            memory_retention="single_run",
            tools={"write_to_scratch_pad": write_to_scratch_pad},
        )
        AgentRegistry.register_pool(browser_pool)
        browser_pools.append(browser_pool)

    # Synthesizer agents
    synthesizers = []
    for i in range(1, 4):
        synthesizers.append(
            Agent(
                model_config=model_config,
                goal="Create comprehensive research reports from collected sources",
                instruction=SYNTHESIZER_DESC,
                name=f"Synthesizer{i}",
                tools={
                    "read_scratch_pad_content": read_scratch_pad_content,
                    "write_file": write_file,
                },
            )
        )

    # Final analysis agents
    final_critic = Agent(
        model_config=model_config,
        goal="Critically analyze and compare multiple research reports",
        instruction=FINAL_CRITIC_DESC,
        name="FinalReportCritic",
        tools={"read_file": read_file},
    )

    final_synthesizer = Agent(
        model_config=model_config,
        goal="Create the ultimate research report from multiple sources",
        instruction=FINAL_SYNTHESIZER_DESC,
        name="FinalReportSynthesizer",
        tools={"read_file": read_file, "write_file": write_file},
    )
        # Helper: surface filesystem context to each orchestrator once
    def _attach_workspace_context():
        for idx, orchestrator in enumerate(orchestrators, start=1):
            stream_note = (
                f"You run stream #{idx}\n"
                f"output_directory: {output_directory}\n"
                f"scratch_pad_path: {scratch_paths[idx - 1]}\n"
                f"report_path: {report_paths[idx - 1]}\n"
                f"final_report_path: {final_report_path}"
            )
            message_id = orchestrator.memory.add(role="system", content=stream_note)
            orchestrator._context_selector.save_selection(
                {"message_ids": [message_id]},
                key="workspace_paths",
            )
            # Attaching cotext to final_critic and final_synthesizer as well
        critic_note = (
            f"You will analyze reports at paths:\n"
            f"1: {report_paths[0]}\n"
            f"2: {report_paths[1]}\n"
            f"3: {report_paths[2]}"
        )
        message_id = final_critic.memory.add(role="system", content=critic_note)
        final_critic._context_selector.save_selection(
            {"message_ids": [message_id]}, key="workspace_paths"
        )
        synthesizer_note = (
            f"You will create the final report at path:\n"
            f"{final_report_path}"
        )
        message_id = final_synthesizer.memory.add(role="system", content=synthesizer_note)
        final_synthesizer._context_selector.save_selection(
            {"message_ids": [message_id]}, key="workspace_paths"
        )

    _attach_workspace_context()

    # Define topology
    print("\n🔗 Defining topology...")

    topology = {
        "agents": [
            {"name": "User", "type": "user"},
            "QueryAnalyzer",
            "UserIntentAgent",
            "ResearchStatementAgent",
            "Orchestrator1",
            "Orchestrator2",
            "Orchestrator3",
            "WebRetrieval1",
            "WebRetrieval2",
            "WebRetrieval3",
            "BrowserAgent1",
            "BrowserAgent2",
            "BrowserAgent3",
            "Synthesizer1",
            "Synthesizer2",
            "Synthesizer3",
            "FinalReportCritic",
            "FinalReportSynthesizer",
        ],
        "flows": [
            # User interaction phase
            "User -> QueryAnalyzer",
            "QueryAnalyzer -> User",
            "QueryAnalyzer -> UserIntentAgent",
            "UserIntentAgent -> QueryAnalyzer",
            # Research statement creation
            "QueryAnalyzer -> ResearchStatementAgent",
            # Parallel orchestration
            "ResearchStatementAgent -> Orchestrator1",
            "ResearchStatementAgent -> Orchestrator2",
            "ResearchStatementAgent -> Orchestrator3",
            # Each orchestrator's workflow
            "Orchestrator1 -> WebRetrieval1",
            "WebRetrieval1 -> Orchestrator1",
            "WebRetrieval1 -> BrowserAgent1",
            "BrowserAgent1 -> WebRetrieval1",
            "Orchestrator1 -> Synthesizer1",
            "Synthesizer1 -> Orchestrator1",
            "Orchestrator2 -> WebRetrieval2",
            "WebRetrieval2 -> Orchestrator2",
            "WebRetrieval2 -> BrowserAgent2",
            "BrowserAgent2 -> WebRetrieval2",
            "Orchestrator2 -> Synthesizer2",
            "Synthesizer2 -> Orchestrator2",
            "Orchestrator3 -> WebRetrieval3",
            "WebRetrieval3 -> Orchestrator3",
            "WebRetrieval3 -> BrowserAgent3",
            "BrowserAgent3 -> WebRetrieval3",
            "Orchestrator3 -> Synthesizer3",
            "Synthesizer3 -> Orchestrator3",
            # Convergence to final critic
            "Orchestrator1 -> FinalReportCritic",
            "Orchestrator2 -> FinalReportCritic",
            "Orchestrator3 -> FinalReportCritic",
            # Final synthesis
            "FinalReportCritic -> FinalReportSynthesizer",
            "FinalReportSynthesizer -> User",
        ],
        "rules": [
            "timeout(3600)",  # 1 hour timeout
            "max_steps(200)",
        ],
    }

    # Run research workflow
    print("\n🚀 Starting research workflow...\n")

    try:
        # Prepare context with all file paths
        context = {
            "output_directory": output_directory,
            "scratch_paths": scratch_paths,
            "report_paths": report_paths,
            "final_report_path": final_report_path,
            "research_id": research_id,
        }

        # Run with Orchestra (auto-creates CommunicationManager for user interaction)
        from marsys.coordination.config import ExecutionConfig, StatusConfig

        execution_config = ExecutionConfig(
            user_interaction="terminal",  # Auto-creates CommunicationManager
            user_first=True,
            initial_user_msg="Hello! I'll help you conduct comprehensive research. What topic would you like to research?",
            status=StatusConfig.from_verbosity(1),
            convergence_timeout=600.0,  # 10 min for parallel workflows
            # Convergence policy: Controls behavior when parallel branches timeout
            # "strict": All branches must converge (100%), workflow fails if timeout
            # Other options: 0.67 (67%), "majority" (51%), "any" (0%)
            convergence_policy="strict",  # All 3 research workflows must complete
        )

        result = await Orchestra.run(
            task="Begin research workflow",
            topology=topology,
            agent_registry=AgentRegistry,
            context={"request_context":context},
            execution_config=execution_config,
            max_steps=200,
        )

        # Display results
        print("\n" + "=" * 80)
        print("📊 RESEARCH COMPLETE")
        print("=" * 80)
        print(f"Success: {result.success}")
        print(f"Total steps: {result.total_steps}")
        print(f"Duration: {result.total_duration:.2f}s")
        print(f"Branches executed: {len(result.branch_results)}")

        if result.success:
            print(f"\n✅ Final report saved to: {final_report_path}")
            print(f"\n📄 Individual reports:")
            for i, path in enumerate(report_paths, 1):
                if os.path.exists(path):
                    print(f"   - Report {i}: {path}")

        # Browser pool statistics
        stats = browser_pool.get_statistics()
        print("\n🌐 Browser Pool Statistics:")
        print(f"   - Total allocations: {stats['total_allocations']}")
        print(f"   - Peak concurrent usage: {stats['peak_concurrent_usage']}")
        print(f"   - Average wait time: {stats['average_wait_time']:.2f}s")

    except KeyboardInterrupt:
        print("\n\n⚠️ Research interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        cleanup_tasks = [browser_pool.cleanup()]
        for agent in [
            query_analyzer,
            user_intent_agent,
            research_statement_agent,
            final_critic,
            final_synthesizer,
        ] + orchestrators + web_retrieval_agents + synthesizers:
            if hasattr(agent, "cleanup"):
                cleanup_tasks.append(agent.cleanup())

        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        print("✅ Cleanup complete\n")


def main():
    """Main entry point."""
    print("\n🔬 Advanced Multi-Agent Deep Research System")
    print("=" * 80)
    print("This system conducts research through 3 parallel workflows,")
    print("then synthesizes the results into a comprehensive final report.")
    print("=" * 80)

    asyncio.run(run_advanced_research())


if __name__ == "__main__":
    main()
