#!/usr/bin/env python3
"""
Lead Generation Multi-Agent System
===================================

A comprehensive B2B lead generation pipeline using MARSYS Orchestra.

Phases:
    0. LinkedIn Authentication (save session for future use)
    1. Market Research (optional - if industries not specified, with user approval)
    2. Company Discovery (find companies matching criteria)
    3. Initial Filtering (filter by basic criteria)
    4. Deep Company Research (comprehensive company profiles)
    5. Lead Qualification (qualify based on business fit)
    6-7. Person Discovery & Profile Building (find and profile contacts)

Usage:
    python run_lead_generation.py                              # Use default_config.yaml
    python run_lead_generation.py --config my_config.yaml      # Use custom config

Output Structure:
    output/{run_name}/
    ├── config.json                          # Saved configuration
    ├── browser_session.json                 # Saved browser session (LinkedIn + Google)
    ├── discovered_companies.jsonl           # Phase 2 output
    ├── filtered_companies.jsonl             # Phase 3 output (passed filter)
    ├── discarded_companies.jsonl            # Phase 3 output (failed filter)
    ├── company_reports/                     # Phase 4 output
    │   └── {company_id}.md
    ├── qualification/                       # Phase 5 output
    │   └── {company_id}_qualification.json
    ├── qualified_companies.jsonl            # Phase 5 output (qualified leads)
    └── contacts/                            # Phase 6-7 output
        └── {company_id}_employees.jsonl
"""

import argparse
import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

from marsys.agents import Agent, AgentPool
from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.registry import AgentRegistry
from marsys.agents.web_search_agent import WebSearchAgent
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig
from marsys.environment.file_operations import FileOperationConfig, create_file_operation_tools
from marsys.models import ModelConfig

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class LeadGenConfig:
    """Configuration for lead generation run."""

    # Run identification
    run_name: str = "lead_gen_run"

    # Business info
    business_name: str = ""
    business_description: str = ""
    products_services: List[str] = field(default_factory=list)
    value_proposition: str = ""
    ideal_use_cases: List[str] = field(default_factory=list)

    # Target criteria
    target_industries: List[str] = field(default_factory=list)
    target_countries: List[str] = field(default_factory=lambda: ["USA"])
    company_sizes: List[str] = field(default_factory=lambda: ["medium", "large"])
    employee_count_min: int = 50
    employee_count_max: int = 10000
    exclude_industries: List[str] = field(default_factory=list)

    # Contact criteria
    target_departments: List[str] = field(default_factory=lambda: ["Operations", "IT"])
    target_job_titles: List[str] = field(default_factory=lambda: ["Director", "VP", "Manager"])
    max_contacts_per_company: int = 5

    # Discovery settings
    num_companies_to_find: int = 50

    # Pool sizes
    websearch_pool_size: int = 5
    browser_pool_size: int = 10

    # Model settings
    model_provider: str = "openrouter"
    model_name: str = "anthropic/claude-sonnet-4.5"
    browser_model_name: str = "anthropic/claude-sonnet-4.5"

    # Session
    browser_session_path: Optional[str] = None

    # Output
    output_directory: str = "examples/03_Lead_Generation/output"


def load_config(yaml_path: str) -> LeadGenConfig:
    """Load configuration from YAML file."""
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    return LeadGenConfig(
        run_name=data.get("run_name", "lead_gen_run"),
        # Business
        business_name=data.get("business", {}).get("name", ""),
        business_description=data.get("business", {}).get("description", ""),
        products_services=data.get("business", {}).get("products_services", []),
        value_proposition=data.get("business", {}).get("value_proposition", ""),
        ideal_use_cases=data.get("business", {}).get("ideal_use_cases", []),
        # Target
        target_industries=data.get("target", {}).get("industries", []),
        target_countries=data.get("target", {}).get("countries", ["USA"]),
        company_sizes=data.get("target", {}).get("company_sizes", ["medium", "large"]),
        employee_count_min=data.get("target", {}).get("employee_count_range", {}).get("min", 50),
        employee_count_max=data.get("target", {}).get("employee_count_range", {}).get("max", 10000),
        exclude_industries=data.get("target", {}).get("exclude_industries", []),
        # Contacts
        target_departments=data.get("contacts", {}).get("target_departments", []),
        target_job_titles=data.get("contacts", {}).get("target_job_titles", []),
        max_contacts_per_company=data.get("contacts", {}).get("max_per_company", 5),
        # Discovery
        num_companies_to_find=data.get("discovery", {}).get("num_companies_to_find", 50),
        # Pools
        websearch_pool_size=data.get("pools", {}).get("websearch_size", 5),
        browser_pool_size=data.get("pools", {}).get("browser_size", 10),
        # Model
        model_provider=data.get("model", {}).get("provider", "openrouter"),
        model_name=data.get("model", {}).get("name", "anthropic/claude-sonnet-4.5"),
        browser_model_name=data.get("model", {}).get("browser_model", "anthropic/claude-sonnet-4.5"),
        # Session
        browser_session_path=data.get("session", {}).get("browser_session_path"),
        # Output
        output_directory=data.get("output", {}).get("directory", "examples/03_Lead_Generation/output"),
    )


# ============================================================================
# TOOLS
# ============================================================================


def generate_company_id(company_name: str, country: str) -> str:
    """
    Generate a standardized company ID from name and country.

    Format: company-name-lowercase_country-lowercase
    Example: "Acme Corp" + "USA" -> "acme-corp_usa"

    Args:
        company_name: Name of the company
        country: Country where company is located

    Returns:
        Standardized company ID string
    """
    clean_name = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    clean_country = country.lower().replace(" ", "-")
    return f"{clean_name}_{clean_country}"


# ============================================================================
# PHASE STATUS TRACKING
# ============================================================================

PHASE_OUTPUT_FILES = {
    0: ["browser_session.json"],
    1: ["market_research_industries.json"],
    2: ["discovered_companies.jsonl"],
    3: ["filtered_companies.jsonl", "discarded_companies.jsonl"],
    4: ["company_reports/"],
    5: ["qualified_companies.jsonl", "qualification/"],
    6: ["contacts/"],
}


def is_phase_complete(output_path: Path, phase: int) -> bool:
    """Check if phase completion marker exists."""
    return (output_path / f".phase_{phase}_complete").exists()


def mark_phase_complete(output_path: Path, phase: int) -> None:
    """Create phase completion marker."""
    (output_path / f".phase_{phase}_complete").write_text(datetime.utcnow().isoformat())


def cleanup_phase_files(output_path: Path, phase: int) -> None:
    """Remove partial output files for a phase before re-running."""
    import shutil

    for f in PHASE_OUTPUT_FILES.get(phase, []):
        path = output_path / f
        if f.endswith("/") and path.is_dir():
            for item in path.iterdir():
                shutil.rmtree(item) if item.is_dir() else item.unlink()
        elif path.exists():
            path.unlink()
    marker = output_path / f".phase_{phase}_complete"
    if marker.exists():
        marker.unlink()


# ============================================================================
# AGENT INSTRUCTIONS
# ============================================================================

# --- Market Research Agent ---
MARKET_RESEARCH_GOAL = "Discover potential industries and use cases for the business"

MARKET_RESEARCH_INSTRUCTION = """You are a market research specialist. Your task is to discover
potential industries and use cases that could benefit from the business's products/services.

Business Information:
- Name: {business_name}
- Description: {business_description}
- Products/Services: {products_services}
- Value Proposition: {value_proposition}

Your Tasks:
1. Use web search to find industries that commonly need these products/services
2. Identify specific use cases and pain points in different industries
3. Research market trends and growing sectors
4. Rank opportunities by potential fit and market size

Return your findings as a structured response with:
- discovered_industries: List of promising industries
- use_cases: List of specific use cases per industry
- recommended_industries: Top 3-5 industries to target
- reasoning: Why these industries are good targets
"""

# --- Company Discovery Agent ---
COMPANY_DISCOVERY_GOAL = "Find and collect information about target companies"

COMPANY_DISCOVERY_INSTRUCTION = """You are responsible for discovering companies that match the target criteria.

Target Criteria:
- Industries: {industries}
- Countries: {countries}
- Company Sizes: {sizes}
- Employee Range: {employee_min} - {employee_max}
- Exclude Industries: {exclude}
- Number of Companies to Find: {num_companies}

Output Path: {output_path}

Your Workflow:
1. Generate diverse search queries based on industries, countries, and company characteristics
2. Invoke WebSearchAgents (max {websearch_pool_size} parallel) with different queries
3. Collect URLs and initial company information from search results
4. For each unique company found, invoke ONE BrowserAgent with ALL its relevant URLs
5. BrowserAgents will extract detailed info and save to: {output_path}/discovered_companies.jsonl

IMPORTANT Rules:
- ONE BrowserAgent call per company (include ALL URLs for that company in the request)
- Generate company ID using format: company-name-lowercase-with-dashes_country (use generate_company_id tool)
- Continue search cycles until {num_companies} companies found or searches exhausted
- A few failed BrowserAgent calls should NOT stop the workflow - focus on majority success
- Track progress and avoid duplicate companies

For writing to JSONL file, use write_file tool with mode="append" and ensure each entry is a valid JSON object on a single line.

Company JSON Schema:
{{
    "id": "acme-corp_usa",
    "name": "Acme Corp",
    "website": "https://example.com",
    "country": "USA",
    "industry": "Technology",
    "employee_count_estimate": 500,
    "description": "Brief description of what the company does",
    "source_urls": ["url1", "url2"],
    "linkedin_url": "https://linkedin.com/company/...",
    "discovery_confidence": 0.8
}}

When finished, report: total companies found, success rate, output file path.
"""

# --- Browser Agent for Company Discovery ---
BROWSER_DISCOVERY_GOAL = "Extract company information from provided URLs"

BROWSER_DISCOVERY_INSTRUCTION = """You are extracting company information from web pages.

You will receive:
- company_name: Name of the company to research
- urls: List of URLs to visit
- output_file: Path to JSONL file for output

Your Tasks:
1. Visit each provided URL
2. Extract: company name, website, country, industry, employee count, description
3. Look for LinkedIn company page URL if available
4. Generate company ID using generate_company_id tool
5. Use write_file tool with mode="append" to save the company data as a JSON line
6. Return success/failed status

If information is not found for a field, use null.
Focus on accuracy - only include information you're confident about.
"""

# --- Initial Filter Agent ---
INITIAL_FILTER_GOAL = "Filter discovered companies based on basic criteria"

INITIAL_FILTER_INSTRUCTION = """You are filtering discovered companies based on criteria.

Input File: {input_path}/discovered_companies.jsonl
Output Files:
- {output_path}/filtered_companies.jsonl (companies that pass filter)
- {output_path}/discarded_companies.jsonl (companies that fail filter)

Filter Criteria:
- Allowed Countries: {countries}
- Employee Range: {employee_min} - {employee_max}
- Excluded Industries: {exclude}

Your Tasks:
1. Read all companies from discovered_companies.jsonl using read_file tool
2. Parse each line as JSON
3. For each company, check if it matches criteria
4. If PASSES: append to filtered_companies.jsonl using write_file with mode="append"
5. If FAILS: append to discarded_companies.jsonl with "discard_reason" field using write_file with mode="append"

Be lenient on missing data - if employee_count is null but other criteria pass, include it.
Report final counts: total processed, passed, discarded.
"""

# --- Deep Company Research Agent ---
DEEP_RESEARCH_GOAL = "Conduct comprehensive research on filtered companies"

DEEP_RESEARCH_INSTRUCTION = """You coordinate deep research on filtered companies.

Input File: {input_path}/filtered_companies.jsonl
Output Directory: {output_path}/company_reports/

Your Workflow:
1. Read filtered companies using read_file tool
2. For each company, invoke a WebSearchAgent with the company's JSON data
3. Maximum {websearch_pool_size} parallel company researches at once
4. Each WebSearchAgent will search for detailed info and invoke BrowserAgents
5. Final output: One markdown report per company at company_reports/{{company_id}}.md

Pass to each WebSearchAgent:
- Company JSON object
- Output path for the report
- Instructions to research: products, services, customers, reviews, news, technology

WebSearchAgents operate independently - do not wait for all to converge.
Each branch represents one company's research.
"""

# --- WebSearch Agent for Deep Research ---
WEBSEARCH_DEEP_GOAL = "Search and research a single company comprehensively"

WEBSEARCH_DEEP_INSTRUCTION = """You are researching this company comprehensively:

Company Data:
{company_json}

Output File: {output_path}/company_reports/{company_id}.md

Your Tasks:
1. Search for detailed information about this company:
   - Products and services they offer
   - Target customers and case studies
   - Recent news and press releases
   - Reviews and ratings (G2, Capterra, Glassdoor)
   - Technology stack if discoverable
   - Key team members and leadership

2. Invoke BrowserAgents (max 5 parallel) to extract from URLs you find
3. Compile all information into a comprehensive markdown report
4. Use write_file tool to save the report

Report Structure:
# {{Company Name}} - Research Report

## Basic Information
- Website: ...
- Industry: ...
- Location: ...
- Employee Count: ...

## Products & Services
...

## Target Customers
...

## Recent News & Developments
...

## Reviews & Reputation
...

## Technology Stack
...

## Potential Fit Analysis
Based on what we learned, this company may be a good fit because...
"""

# --- Lead Qualification Agent ---
QUALIFICATION_GOAL = "Qualify leads based on fit with our business offering"

QUALIFICATION_INSTRUCTION = """You are qualifying companies as potential leads.

Our Business:
- Name: {business_name}
- Products/Services: {products_services}
- Value Proposition: {value_proposition}

Input: Read reports from {input_path}/company_reports/
Output:
- {output_path}/qualification/{{company_id}}_qualification.json (per company)
- {output_path}/qualified_companies.jsonl (list of qualified leads)

Your Tasks:
1. Use search_files tool to find all company reports in company_reports/
2. For each report, use read_file tool to read the content
3. Analyze fit with our offering:
   - Do they have pain points we can solve?
   - Are they in a growth stage that needs our solution?
   - Is there evidence they could use our product?
   - Any concerns or red flags?
4. Decide: KEEP (qualified lead) or DISCARD (not a fit)
5. Write qualification JSON using write_file tool
6. If KEEP, append to qualified_companies.jsonl using write_file with mode="append"

Qualification JSON Schema:
{{
    "company_id": "...",
    "company_name": "...",
    "decision": "KEEP" or "DISCARD",
    "confidence": 0.85,
    "reasoning": {{
        "pain_points_match": ["pain point 1", "pain point 2"],
        "use_case_fit": "How our product could help them",
        "growth_indicators": ["indicator 1", "indicator 2"],
        "concerns": ["concern 1"]
    }},
    "recommended_approach": "How to approach this lead",
    "priority": "high" or "medium" or "low"
}}

Focus on quality over quantity - be selective.
"""

# --- Person Discovery Coordinator ---
PERSON_DISCOVERY_GOAL = "Coordinate finding contacts at qualified companies in batches"

PERSON_DISCOVERY_INSTRUCTION = """You coordinate finding decision-maker contacts at qualified companies.

INPUT: {input_path}/qualified_companies.jsonl
OUTPUT: {output_path}/contacts/

WORKFLOW:
1. Read qualified companies from the input file
2. Process companies in BATCHES of maximum 3 companies at a time
3. For each batch, invoke CompanyPeopleSearch for each company (max 3 parallel invocations)
4. WAIT for all CompanyPeopleSearch agents to return before processing the next batch
5. Track which companies have been processed
6. Continue with the next batch of 3 companies until all are done
7. Once ALL companies are processed, give a final_response with completion summary

Target job titles: {job_titles}
Target departments: {departments}
Max contacts per company: {max_contacts}

CRITICAL:
- NEVER invoke more than 3 CompanyPeopleSearch agents at once
- Wait for current batch to complete before starting next batch
- Only give final_response when ALL companies have been processed
"""

# --- Company People Search Agent ---
PEOPLE_SEARCH_GOAL = "Find relevant employees at a company and dispatch profile extraction"

PEOPLE_SEARCH_INSTRUCTION = """You find decision-makers at a specific company and their LinkedIn profile URLs.

You receive: company_name, company_id, company_website, country

WORKFLOW:
1. Search for employees with LinkedIn URLs:
   - Use queries like "[company name] [job title] site:linkedin.com/in"
   - Or "[company name] Director linkedin" or "[company name] Head of linkedin"
   - Look for search results that contain linkedin.com/in/ URLs directly

2. From search results, extract up to {max_contacts} people:
   - Extract person name AND their LinkedIn URL (e.g., linkedin.com/in/john-doe)
   - Must work at the specified company
   - Should have titles matching: {job_titles}
   - Should be in departments: {departments}

3. For EACH person found with a LinkedIn URL, invoke PeopleBrowserAgent with:
   - person_name: Full name of the person
   - linkedin_url: The LinkedIn profile URL you found (e.g., https://www.linkedin.com/in/john-doe)
   - company_name: The company they work at
   - company_id: ID for output file naming
   - output_file: {output_path}/contacts/{{company_id}}_employees.jsonl

4. After all PeopleBrowserAgent invocations complete, invoke PersonDiscoveryCoordinator with:
   - company_name: The company you searched
   - status: "completed" or "no_contacts_found"
   - contacts_found: Number of contacts discovered

CRITICAL RULES:
- You MUST find the LinkedIn URL for each person from search results
- You MUST invoke PeopleBrowserAgent for each person found (one invocation per person)
- If you find NO suitable candidates, invoke PersonDiscoveryCoordinator with status="no_contacts_found"
- You are NOT allowed to give a final response - you MUST always invoke either PeopleBrowserAgent or PersonDiscoveryCoordinator
"""

# --- Browser Agent for Person Profile ---
BROWSER_PERSON_GOAL = "Visit a LinkedIn profile and extract key information"

BROWSER_PERSON_INSTRUCTION = """You visit a LinkedIn profile URL and extract professional information.

You receive: person_name, linkedin_url, company_name, company_id, output_file

TIME LIMIT: Complete within 5-10 actions. This is a simple extraction task.
After each action, write down what you see - screenshots disappear after your next action.

SIMPLE WORKFLOW:
1. Navigate directly to the provided linkedin_url using go_to_url
2. Verify it's the right person (name and company should match)
3. Scroll once or twice to see: name, title, company, location, summary, skills
4. Extract the information you see on the page
5. Save to output_file using write_file
6. Invoke CompanyPeopleSearch with person_name and status="profile_extracted"

SAVING DATA - IMPORTANT:
You MUST use mode="append" when calling write_file to add to existing data:
    write_file(path=output_file, content=json_line + "\\n", mode="append")

JSON SCHEMA (one JSON object per line, each ending with newline):
{{
    "person_name": "Full Name",
    "job_title": "Title",
    "company_name": "Company",
    "company_id": "company-id",
    "linkedin_url": "the linkedin_url you visited",
    "email": null,
    "location": "City, Country or null",
    "skills": ["Skill1", "Skill2"],
    "profile_summary": "1-2 sentence summary from their About section",
    "outreach_hooks": ["Hook 1", "Hook 2"]
}}

CRITICAL:
- DO NOT search for anything - go directly to the linkedin_url provided
- BE FAST - just extract what you see, don't explore other pages
- Save results to output_file BEFORE invoking CompanyPeopleSearch
- You MUST invoke CompanyPeopleSearch when done (with person_name and status)
- NEVER give final_response - always invoke CompanyPeopleSearch
"""


# ============================================================================
# PHASE FUNCTIONS
# ============================================================================


async def run_auth_phase(config: LeadGenConfig, output_path: Path) -> str:
    """
    Phase 0: Authentication (LinkedIn + Google).

    Opens a browser for user to manually log into LinkedIn and Google,
    then saves the session for future use. Google auth is needed for
    browser agents to perform Google searches without CAPTCHA issues.

    Returns:
        Path to saved session file
    """
    session_path = str(output_path / "browser_session.json")

    # Check if session already exists
    if config.browser_session_path and Path(config.browser_session_path).exists():
        logger.info(f"Using existing session: {config.browser_session_path}")
        return config.browser_session_path

    if Path(session_path).exists():
        logger.info(f"Using existing session: {session_path}")
        return session_path

    print("\n" + "=" * 60)
    print("PHASE 0: AUTHENTICATION")
    print("=" * 60)
    print("A browser window will open.")
    print("You will need to log into TWO services:")
    print("  1. LinkedIn - for accessing professional profiles")
    print("  2. Google - for performing searches without CAPTCHA")
    print("The session will be saved for future use.")
    print("=" * 60 + "\n")

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.browser_model_name,
    )

    auth_agent = await BrowserAgent.create_safe(
        model_config=model_config,
        name="AuthAgent",
        headless=False,
        mode="advanced",
        memory_retention="single_run",
        goal="Help user authenticate with LinkedIn and Google, then save session",
        instruction=f"""Help the user authenticate with LinkedIn and Google.

WORKFLOW:
1. First, navigate to https://www.linkedin.com/login
2. Tell the user to log in to LinkedIn
3. Wait for user confirmation that they've logged in (check for feed/home page)
4. Then navigate to https://accounts.google.com
5. Tell the user to log in to Google
6. Wait for user confirmation that they've logged in
7. Once BOTH logins are complete, save the session to: {session_path}
8. Report success

IMPORTANT:
- Do NOT enter credentials - let the user do it manually
- Navigate to login pages and wait for user
- Save session only after BOTH services are authenticated
""",
    )

    topology = {"agents": ["User", "AuthAgent"], "flows": ["User -> AuthAgent", "AuthAgent -> User"], "entry_point": "AuthAgent"}

    try:
        result = await Orchestra.run(
            task=f"Authenticate with LinkedIn and Google, then save session to {session_path}",
            topology=topology,
            execution_config=ExecutionConfig(user_interaction="terminal", user_first=False, status=StatusConfig.from_verbosity(1)),
            max_steps=25,
        )
        logger.info(f"Auth result: {result.final_response}")
        return session_path
    finally:
        await auth_agent.cleanup()
        AgentRegistry.unregister("AuthAgent")


async def run_phase1_market_research(config: LeadGenConfig, output_path: Path) -> List[str]:
    """
    Phase 1: Market Research (with User approval).

    Discovers potential industries if not specified in config.

    Returns:
        List of approved industries
    """
    # If industries already specified, skip
    if config.target_industries:
        logger.info(f"Using configured industries: {config.target_industries}")
        return config.target_industries

    print("\n" + "=" * 60)
    print("PHASE 1: MARKET RESEARCH")
    print("=" * 60)

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    # Create market research agent (uses web search to discover industries)
    market_agent = WebSearchAgent(
        model_config=model_config,
        name="MarketResearchAgent",
        goal=MARKET_RESEARCH_GOAL,
        instruction=MARKET_RESEARCH_INSTRUCTION.format(
            business_name=config.business_name,
            business_description=config.business_description,
            products_services=", ".join(config.products_services),
            value_proposition=config.value_proposition,
        ),
    )

    # Create coordinator for this phase
    coordinator = Agent(
        model_config=model_config,
        name="Coordinator",
        goal="Coordinate market research and present findings for user approval",
        instruction="""You coordinate market research.

1. Invoke MarketResearchAgent to discover potential industries
2. Present the findings clearly to the User
3. Ask User to approve or modify the recommended industries
4. Return the final approved list

Format your presentation to the User clearly with:
- Discovered industries and why they're good targets
- Recommended top industries to focus on
- Ask for approval or modifications
""",
    )

    topology = {"agents": ["User", "Coordinator", "MarketResearchAgent"], "flows": ["User -> Coordinator", "Coordinator -> MarketResearchAgent", "MarketResearchAgent -> Coordinator", "Coordinator -> User"], "entry_point": "Coordinator"}

    try:
        result = await Orchestra.run(
            task=f"Research potential industries for {config.business_name} and get user approval",
            topology=topology,
            execution_config=ExecutionConfig(user_interaction="terminal", user_first=False, status=StatusConfig.from_verbosity(1)),
            max_steps=30,
        )

        logger.info(f"Market research result: {result.final_response}")
    finally:
        pass

    # Get user input for final industries
    print("\n" + "-" * 40)
    industries_input = input("Enter approved industries (comma-separated): ").strip()
    industries = [i.strip() for i in industries_input.split(",") if i.strip()]

    if not industries:
        raise ValueError("No industries specified. Cannot proceed.")

    # Save to output
    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())
    await file_tools["write_file"](output_path / "market_research_industries.json", json.dumps({"approved_industries": industries}, indent=2))

    return industries


async def run_phase2_company_discovery(config: LeadGenConfig, output_path: Path, industries: List[str]) -> bool:
    """
    Phase 2: Company Discovery.

    Finds companies matching criteria using WebSearch and Browser agents.

    Returns:
        True if successful
    """
    print("\n" + "=" * 60)
    print("PHASE 2: COMPANY DISCOVERY")
    print("=" * 60)
    print(f"Finding {config.num_companies_to_find} companies...")
    print(f"Industries: {industries}")
    print(f"Countries: {config.target_countries}")

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    browser_model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.browser_model_name,
    )

    # Get file tools
    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())

    # Create agent pools
    websearch_pool = AgentPool(
        agent_class=WebSearchAgent,
        num_instances=config.websearch_pool_size,
        model_config=model_config,
        name="WebSearchPool_Discovery",
        goal="Search for companies matching criteria",
        instruction="Search the web for companies in specified industries and countries. Return relevant URLs and company information found.",
        memory_retention="single_run",
    )

    # Combine file_tools with generate_company_id for browser pool
    browser_discovery_tools = {**file_tools, "generate_company_id": generate_company_id}

    browser_pool = await AgentPool.create_async(
        agent_class=BrowserAgent,
        num_instances=config.browser_pool_size,
        model_config=browser_model_config,
        name="BrowserPool_Discovery",
        mode="primitive",
        headless=True,
        memory_retention="single_run",
        goal=BROWSER_DISCOVERY_GOAL,
        instruction=BROWSER_DISCOVERY_INSTRUCTION,
        tools=browser_discovery_tools,
    )

    # Register pools with Orchestra
    AgentRegistry.register_pool(websearch_pool)
    AgentRegistry.register_pool(browser_pool)

    # Create discovery agent
    discovery_agent = Agent(
        model_config=model_config,
        name="CompanyDiscoveryAgent",
        goal=COMPANY_DISCOVERY_GOAL,
        instruction=COMPANY_DISCOVERY_INSTRUCTION.format(
            industries=", ".join(industries),
            countries=", ".join(config.target_countries),
            sizes=", ".join(config.company_sizes),
            employee_min=config.employee_count_min,
            employee_max=config.employee_count_max,
            exclude=", ".join(config.exclude_industries) or "None",
            num_companies=config.num_companies_to_find,
            websearch_pool_size=config.websearch_pool_size,
            output_path=output_path,
        ),
        tools={
            **file_tools,
            "generate_company_id": generate_company_id,
        },
    )

    topology = {
        "agents": ["CompanyDiscoveryAgent", "WebSearchPool_Discovery", "BrowserPool_Discovery"],
        "flows": [
            "CompanyDiscoveryAgent -> WebSearchPool_Discovery",
            "WebSearchPool_Discovery -> CompanyDiscoveryAgent",
            "CompanyDiscoveryAgent -> BrowserPool_Discovery",
            "BrowserPool_Discovery -> CompanyDiscoveryAgent",
        ],
        "entry_point": "CompanyDiscoveryAgent",
        "exit_points": ["CompanyDiscoveryAgent"],
    }

    try:
        result = await Orchestra.run(
            task=f"Find {config.num_companies_to_find} companies matching criteria. Save to {output_path}/discovered_companies.jsonl",
            topology=topology,
            execution_config=ExecutionConfig(user_interaction="none", convergence_timeout=1800.0, status=StatusConfig.from_verbosity(1)),
            max_steps=150,
        )

        logger.info(f"Company discovery completed: {result.success}")
        print(f"\nCompany Discovery: {'SUCCESS' if result.success else 'FAILED'}")

        # Count discovered companies
        discovered_file = output_path / "discovered_companies.jsonl"
        if discovered_file.exists():
            count = sum(1 for _ in open(discovered_file))
            print(f"Companies discovered: {count}")

        return result.success

    finally:
        await websearch_pool.cleanup()
        await browser_pool.cleanup()
        AgentRegistry.unregister("CompanyDiscoveryAgent")


async def run_phase3_initial_filter(config: LeadGenConfig, output_path: Path) -> bool:
    """
    Phase 3: Initial Filtering.

    Filters discovered companies based on basic criteria.

    Returns:
        True if successful
    """
    print("\n" + "=" * 60)
    print("PHASE 3: INITIAL FILTERING")
    print("=" * 60)

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())

    filter_agent = Agent(
        model_config=model_config,
        name="InitialFilterAgent",
        goal=INITIAL_FILTER_GOAL,
        instruction=INITIAL_FILTER_INSTRUCTION.format(
            input_path=output_path,
            output_path=output_path,
            countries=", ".join(config.target_countries),
            employee_min=config.employee_count_min,
            employee_max=config.employee_count_max,
            exclude=", ".join(config.exclude_industries) or "None",
        ),
        tools=file_tools,
    )

    topology = {"agents": ["InitialFilterAgent"], "flows": []}

    try:
        result = await Orchestra.run(
            task=f"Filter companies from {output_path}/discovered_companies.jsonl based on criteria", topology=topology, execution_config=ExecutionConfig(user_interaction="none", status=StatusConfig.from_verbosity(1)), max_steps=30
        )

        logger.info(f"Initial filtering completed: {result.success}")
        print(f"\nInitial Filtering: {'SUCCESS' if result.success else 'FAILED'}")

        # Count filtered companies
        filtered_file = output_path / "filtered_companies.jsonl"
        if filtered_file.exists():
            count = sum(1 for _ in open(filtered_file))
            print(f"Companies passed filter: {count}")

        return result.success

    finally:
        AgentRegistry.unregister("InitialFilterAgent")


async def run_phase4_deep_research(config: LeadGenConfig, output_path: Path) -> bool:
    """
    Phase 4: Deep Company Research.

    Conducts comprehensive research on filtered companies.

    Returns:
        True if successful
    """
    print("\n" + "=" * 60)
    print("PHASE 4: DEEP COMPANY RESEARCH")
    print("=" * 60)

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    browser_model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.browser_model_name,
    )

    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())

    # Create pools for deep research
    websearch_pool = AgentPool(
        agent_class=WebSearchAgent,
        num_instances=config.websearch_pool_size,
        model_config=model_config,
        name="WebSearchPool_DeepResearch",
        goal=WEBSEARCH_DEEP_GOAL,
        instruction="Research a company comprehensively and write a detailed report.",
        memory_retention="single_run",
        tools=file_tools,
    )

    browser_pool = await AgentPool.create_async(
        agent_class=BrowserAgent,
        num_instances=config.browser_pool_size,
        model_config=browser_model_config,
        name="BrowserPool_DeepResearch",
        mode="primitive",
        headless=True,
        memory_retention="single_run",
        goal="Extract detailed information from web pages",
        instruction="Visit URLs and extract detailed company information for research reports.",
        tools=file_tools,
    )

    # Register pools with Orchestra
    AgentRegistry.register_pool(websearch_pool)
    AgentRegistry.register_pool(browser_pool)

    # Create deep research coordinator
    deep_research_agent = Agent(
        model_config=model_config,
        name="DeepCompanyResearchAgent",
        goal=DEEP_RESEARCH_GOAL,
        instruction=DEEP_RESEARCH_INSTRUCTION.format(
            input_path=output_path,
            output_path=output_path,
            websearch_pool_size=config.websearch_pool_size,
        ),
        tools=file_tools,
    )

    topology = {
        "agents": ["DeepCompanyResearchAgent", "WebSearchPool_DeepResearch", "BrowserPool_DeepResearch"],
        "flows": [
            "DeepCompanyResearchAgent -> WebSearchPool_DeepResearch",
            "WebSearchPool_DeepResearch -> BrowserPool_DeepResearch",
            "BrowserPool_DeepResearch -> WebSearchPool_DeepResearch",
        ],
        "entry_point": "DeepCompanyResearchAgent",
        "exit_points": ["DeepCompanyResearchAgent"],
    }

    try:
        result = await Orchestra.run(
            task=f"Research filtered companies from {output_path}/filtered_companies.jsonl",
            topology=topology,
            execution_config=ExecutionConfig(user_interaction="none", convergence_timeout=3600.0, status=StatusConfig.from_verbosity(1)),
            max_steps=300,
        )

        logger.info(f"Deep research completed: {result.success}")
        print(f"\nDeep Research: {'SUCCESS' if result.success else 'FAILED'}")

        # Count reports
        reports_dir = output_path / "company_reports"
        if reports_dir.exists():
            count = len(list(reports_dir.glob("*.md")))
            print(f"Company reports created: {count}")

        return result.success

    finally:
        await websearch_pool.cleanup()
        await browser_pool.cleanup()
        AgentRegistry.unregister("DeepCompanyResearchAgent")


async def run_phase5_qualification(config: LeadGenConfig, output_path: Path) -> bool:
    """
    Phase 5: Lead Qualification.

    Qualifies leads based on fit with business offering.

    Returns:
        True if successful
    """
    print("\n" + "=" * 60)
    print("PHASE 5: LEAD QUALIFICATION")
    print("=" * 60)

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())

    qualification_agent = Agent(
        model_config=model_config,
        name="LeadQualificationAgent",
        goal=QUALIFICATION_GOAL,
        instruction=QUALIFICATION_INSTRUCTION.format(
            business_name=config.business_name,
            products_services=", ".join(config.products_services),
            value_proposition=config.value_proposition,
            input_path=output_path,
            output_path=output_path,
        ),
        tools=file_tools,
    )

    topology = {"agents": ["LeadQualificationAgent"], "flows": []}

    try:
        result = await Orchestra.run(
            task=f"Qualify leads from company reports in {output_path}/company_reports/", topology=topology, execution_config=ExecutionConfig(user_interaction="none", status=StatusConfig.from_verbosity(1)), max_steps=100
        )

        logger.info(f"Lead qualification completed: {result.success}")
        print(f"\nLead Qualification: {'SUCCESS' if result.success else 'FAILED'}")

        # Count qualified leads
        qualified_file = output_path / "qualified_companies.jsonl"
        if qualified_file.exists():
            count = sum(1 for _ in open(qualified_file))
            print(f"Qualified leads: {count}")

        return result.success

    finally:
        AgentRegistry.unregister("LeadQualificationAgent")


async def run_phase6_person_discovery(config: LeadGenConfig, output_path: Path, session_path: str) -> bool:
    """
    Phase 6: Person Discovery & Profile Building.

    Architecture:
    - PersonDiscoveryCoordinator (convergence): Reads companies, dispatches batches of max 3 to CompanyPeopleSearch
    - CompanyPeopleSearch (convergence): Finds people at a company AND their LinkedIn URLs, dispatches to PeopleBrowserAgent
    - PeopleBrowserAgent: Visits the LinkedIn URL directly, extracts profile info, saves to file

    Returns:
        True if successful
    """
    print("\n" + "=" * 60)
    print("PHASE 6: PERSON DISCOVERY")
    print("=" * 60)

    model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.model_name,
    )

    browser_model_config = ModelConfig(
        type="api",
        provider=config.model_provider,
        name=config.browser_model_name,
    )

    file_tools = create_file_operation_tools(FileOperationConfig.create_permissive())

    # CompanyPeopleSearch: WebSearchAgent pool that finds people at companies
    # Uses web search to identify decision-makers, then dispatches BrowserAgent for each
    company_people_search = AgentPool(
        agent_class=WebSearchAgent,
        num_instances=3, #config.websearch_pool_size,
        model_config=model_config,
        name="CompanyPeopleSearch",
        goal=PEOPLE_SEARCH_GOAL,
        instruction=PEOPLE_SEARCH_INSTRUCTION.format(
            output_path=output_path,
            job_titles=", ".join(config.target_job_titles),
            departments=", ".join(config.target_departments),
            max_contacts=config.max_contacts_per_company,
        ),
        memory_retention="single_run",
    )

    # PeopleBrowserAgent: Pool of browser agents that visit LinkedIn profiles
    # Each agent navigates directly to the provided LinkedIn URL, extracts profile info, saves to file
    # Pass file_tools during creation so tools_schema is generated correctly
    people_browser_agent = await AgentPool.create_async(
        agent_class=BrowserAgent,
        num_instances=6, #config.browser_pool_size,
        model_config=browser_model_config,
        name="PeopleBrowserAgent",
        session_path=session_path,
        mode="advanced",
        headless=False,
        memory_retention="single_run",
        goal=BROWSER_PERSON_GOAL,
        instruction=BROWSER_PERSON_INSTRUCTION,
        tools=file_tools,
    )

    # Register pools
    AgentRegistry.register_pool(company_people_search)
    AgentRegistry.register_pool(people_browser_agent)

    # PersonDiscoveryCoordinator: Orchestrates the whole process
    person_coordinator = Agent(
        model_config=model_config,
        name="PersonDiscoveryCoordinator",
        goal=PERSON_DISCOVERY_GOAL,
        instruction=PERSON_DISCOVERY_INSTRUCTION.format(
            input_path=output_path,
            output_path=output_path,
            job_titles=", ".join(config.target_job_titles),
            departments=", ".join(config.target_departments),
            max_contacts=config.max_contacts_per_company,
        ),
        tools=file_tools,
    )

    # Topology with convergence points:
    # Coordinator -> CompanyPeopleSearch -> PeopleBrowserAgent -> CompanyPeopleSearch -> Coordinator
    topology = {
        "agents": [
            {"name": "PersonDiscoveryCoordinator", "is_convergence_point": True},
            {"name": "CompanyPeopleSearch", "is_convergence_point": True},
            "PeopleBrowserAgent",
        ],
        "flows": [
            "PersonDiscoveryCoordinator -> CompanyPeopleSearch",
            "CompanyPeopleSearch -> PeopleBrowserAgent",
            "PeopleBrowserAgent -> CompanyPeopleSearch",
            "CompanyPeopleSearch -> PersonDiscoveryCoordinator",
        ],
        "entry_point": "PersonDiscoveryCoordinator",
        "exit_points": ["PersonDiscoveryCoordinator"],
    }

    try:
        result = await Orchestra.run(
            task=f"Find contacts at qualified companies from {output_path}/qualified_companies.jsonl",
            topology=topology,
            execution_config=ExecutionConfig(user_interaction="none", convergence_timeout=3600.0, agent_acquisition_timeout=600.0, status=StatusConfig.from_verbosity(1)),
            max_steps=500,
        )

        logger.info(f"Person discovery completed: {result.success}")
        print(f"\nPerson Discovery: {'SUCCESS' if result.success else 'FAILED'}")

        # Count contacts
        contacts_dir = output_path / "contacts"
        if contacts_dir.exists():
            total_contacts = 0
            for f in contacts_dir.glob("*_employees.jsonl"):
                total_contacts += sum(1 for _ in open(f))
            print(f"Total contacts found: {total_contacts}")

        return result.success

    finally:
        await company_people_search.cleanup()
        await people_browser_agent.cleanup()
        AgentRegistry.unregister("PersonDiscoveryCoordinator")


# ============================================================================
# MAIN
# ============================================================================


async def main():
    """Main entry point for lead generation workflow."""
    parser = argparse.ArgumentParser(
        description="Lead Generation Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_lead_generation.py
    python run_lead_generation.py --config my_config.yaml
    python run_lead_generation.py --skip-auth
    python run_lead_generation.py --start-phase 3
        """,
    )
    parser.add_argument("--config", type=str, default="default_config.yaml", help="Path to YAML configuration file (default: default_config.yaml)")
    parser.add_argument("--skip-auth", action="store_true", help="Skip LinkedIn authentication (use existing session)")
    parser.add_argument("--start-phase", type=int, default=0, help="Start from a specific phase (0-6)")

    args = parser.parse_args()

    # Resolve config path
    script_dir = Path(__file__).parent
    config_path = script_dir / args.config
    if not config_path.exists():
        # Try absolute path
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}")
            return 1

    # Load configuration
    config = load_config(str(config_path))

    # Create output directory
    output_path = Path(config.output_directory) / config.run_name
    output_path.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (output_path / "company_reports").mkdir(exist_ok=True)
    (output_path / "qualification").mkdir(exist_ok=True)
    (output_path / "contacts").mkdir(exist_ok=True)

    # Save config as JSON
    config_dict = {
        "run_name": config.run_name,
        "business": {
            "name": config.business_name,
            "description": config.business_description,
            "products_services": config.products_services,
            "value_proposition": config.value_proposition,
        },
        "target": {
            "industries": config.target_industries,
            "countries": config.target_countries,
            "company_sizes": config.company_sizes,
            "employee_range": {
                "min": config.employee_count_min,
                "max": config.employee_count_max,
            },
        },
        "contacts": {
            "departments": config.target_departments,
            "job_titles": config.target_job_titles,
            "max_per_company": config.max_contacts_per_company,
        },
        "discovery": {
            "num_companies": config.num_companies_to_find,
        },
        "pools": {
            "websearch_size": config.websearch_pool_size,
            "browser_size": config.browser_pool_size,
        },
        "model": {
            "provider": config.model_provider,
            "name": config.model_name,
            "browser_model": config.browser_model_name,
        },
        "created_at": datetime.utcnow().isoformat(),
    }
    with open(output_path / "config.json", "w") as f:
        json.dump(config_dict, f, indent=2)

    # Print banner
    print("\n" + "=" * 60)
    print("LEAD GENERATION MULTI-AGENT SYSTEM")
    print("=" * 60)
    print(f"Run Name: {config.run_name}")
    print(f"Business: {config.business_name}")
    print(f"Output Directory: {output_path}")
    print("=" * 60)

    try:
        session_path = config.browser_session_path or str(output_path / "browser_session.json")

        # Phase 0: LinkedIn Authentication
        if not args.skip_auth and args.start_phase <= 0 and not is_phase_complete(output_path, 0):
            cleanup_phase_files(output_path, 0)
            session_path = await run_auth_phase(config, output_path)
            mark_phase_complete(output_path, 0)

        # Phase 1: Market Research (skip if industries pre-configured)
        industries = config.target_industries
        if industries:
            logger.info(f"Using pre-configured industries: {industries}")
        elif args.start_phase <= 1 and not is_phase_complete(output_path, 1):
            cleanup_phase_files(output_path, 1)
            industries = await run_phase1_market_research(config, output_path)
            mark_phase_complete(output_path, 1)
        elif is_phase_complete(output_path, 1):
            # Load saved industries
            industries_file = output_path / "market_research_industries.json"
            if industries_file.exists():
                industries = json.load(open(industries_file)).get("approved_industries", [])
            if not industries:
                raise ValueError("Phase 1 complete but no industries found. Delete .phase_1_complete to re-run.")

        # Phase 2: Company Discovery
        if args.start_phase <= 2 and not is_phase_complete(output_path, 2):
            cleanup_phase_files(output_path, 2)
            if not await run_phase2_company_discovery(config, output_path, industries):
                return 1
            mark_phase_complete(output_path, 2)

        # Phase 3: Initial Filtering
        if args.start_phase <= 3 and not is_phase_complete(output_path, 3):
            cleanup_phase_files(output_path, 3)
            if not await run_phase3_initial_filter(config, output_path):
                return 1
            mark_phase_complete(output_path, 3)

        # Phase 4: Deep Company Research
        if args.start_phase <= 4 and not is_phase_complete(output_path, 4):
            cleanup_phase_files(output_path, 4)
            if not await run_phase4_deep_research(config, output_path):
                return 1
            mark_phase_complete(output_path, 4)

        # Phase 5: Lead Qualification
        if args.start_phase <= 5 and not is_phase_complete(output_path, 5):
            cleanup_phase_files(output_path, 5)
            if not await run_phase5_qualification(config, output_path):
                return 1
            mark_phase_complete(output_path, 5)

        # Phase 6-7: Person Discovery
        if args.start_phase <= 6 and not is_phase_complete(output_path, 6):
            cleanup_phase_files(output_path, 6)
            if not await run_phase6_person_discovery(config, output_path, session_path):
                return 1
            mark_phase_complete(output_path, 6)

        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETE")
        print(f"Results saved to: {output_path}")
        print("=" * 60)
        return 0

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
