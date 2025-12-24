#!/usr/bin/env python3
"""
Financial News Video Maker - Multi-Agent System for Viral Content Creation

Creates viral financial video scripts through:
1. Trending news discovery (24-36 hours)
2. Impact analysis and story selection
3. Deep research on selected topics
4. Viral idea generation with feedback loops
5. Script creation in Hook-Draw-Pitch format
"""
import sys

sys.path.insert(0, "/home/rezaho/research_projects/Multi-agent_AI_Learning/src")
import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.agent_pool import AgentPool
from marsys.agents.browser_agent import BrowserAgent
from marsys.agents.registry import AgentRegistry
from marsys.agents.utils import init_agent_logging
from marsys.coordination import Orchestra
from marsys.environment.tools import tool_google_search_api
from marsys.models import ModelConfig

# init_agent_logging(level=logging.INFO, clear_existing_handlers=True)

# Load environment variables
load_dotenv()


def create_model_configs() -> Dict[str, ModelConfig]:
    """Create model configurations using latest models via OpenRouter."""

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    configs = {}

    # GPT-5 Chat for natural conversational responses
    configs["gpt_chat"] = ModelConfig(
        type="api",
        name="openai/gpt-5-chat",
        provider="openrouter",
        api_key=OPENROUTER_API_KEY,
        temperature=0.7,
        max_tokens=8000,
    )

    # Gemini 2.5 Pro for research and analysis
    configs["gemini"] = ModelConfig(
        type="api",
        name="google/gemini-2.5-flash",
        provider="openrouter",
        api_key=OPENROUTER_API_KEY,
        temperature=0.7,
        max_tokens=8000,
    )

    # Claude Sonnet 4 for creative content generation
    configs["gpt"] = ModelConfig(
        type="api",
        name="openai/gpt-5-mini",
        provider="openrouter",
        api_key=OPENROUTER_API_KEY,
        temperature=0.7,
        max_tokens=8000,
    )

    return configs


# COMMENTED OUT - Replaced by tool_perigon_news
# def tool_polygon_news(ticker: str = "", limit: int = 20) -> Dict[str, Any]:
#     """
#     Fetch financial news from Polygon.io API with optional ticker filter.
#
#     Args:
#         ticker: Optional ticker symbol to filter news (e.g., "AAPL")
#         limit: Number of articles to fetch (default 20, max 100)
#
#     Returns:
#         Dictionary containing news articles with insights and sentiment
#     """
#     api_key = os.getenv("POLYGON_API_KEY")
#     if not api_key:
#         return {"error": "POLYGON_API_KEY not found in environment"}
#
#     # Build request URL
#     base_url = "https://api.polygon.io/v2/reference/news"
#
#     # Build query parameters
#     params = {
#         "apiKey": api_key,
#         "order": "desc",
#         "sort": "published_utc",
#         "limit": min(limit, 100),  # Max 100 per request
#     }
#
#     # Add ticker if provided
#     if ticker:
#         params["ticker"] = ticker.upper()
#
#     try:
#         response = requests.get(base_url, params=params, timeout=10)
#         response.raise_for_status()
#
#         data = response.json()
#
#         if data.get("status") != "OK":
#             return {"error": f"Polygon API error: {data.get('status')}"}
#
#         # Process and simplify articles
#         articles = []
#         for article in data.get("results", []):
#             # Extract insights summary
#             insights_summary = []
#             for insight in article.get("insights", []):
#                 insights_summary.append(
#                     {
#                         "ticker": insight.get("ticker"),
#                         "sentiment": insight.get("sentiment"),
#                     }
#                 )
#
#             simplified = {
#                 "title": article.get("title", ""),
#                 "published": article.get("published_utc", ""),
#                 "url": article.get("article_url", ""),
#                 "tickers": article.get("tickers", []),
#                 "description": (article.get("description", "")[:300] + "..." if len(article.get("description", "")) > 300 else article.get("description", "")),
#                 "insights": insights_summary,  # Simplified insights
#             }
#
#             articles.append(simplified)
#
#         print(f"Successfully fetched {len(articles)} news articles from Polygon")
#         return {
#             "status": "success",
#             "count": len(articles),
#             "ticker_filter": ticker if ticker else "all",
#             "articles": articles,
#         }
#
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 429:
#             return {"error": "Polygon API rate limit exceeded"}
#         elif e.response.status_code == 401:
#             return {"error": "Polygon API unauthorized - check your API key"}
#         else:
#             return {"error": f"HTTP error: {e}"}
#     except Exception as e:
#         return {"error": f"Request failed: {str(e)}"}


def tool_economic_calendar() -> Dict[str, Any]:
    """
    Fetch this week's high-impact economic events from investing.com calendar.

    Returns:
        Dictionary containing upcoming economic events with market impact ratings
    """
    try:
        # Headers to mimic browser request
        headers = {
            "accept": "*/*",
            "accept-language": "en,fa;q=0.9,fr-CH;q=0.8,fr;q=0.7,de;q=0.6",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.investing.com",
            "referer": "https://www.investing.com/economic-calendar/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-requested-with": "XMLHttpRequest",
        }

        # Data for POST request - high importance events from major economies
        data = {
            "country[]": [
                "37",
                "72",
                "35",
                "12",
                "4",
                "5",
            ],  # China, UK, EU, Germany, US, Japan
            "importance[]": ["3"],  # Only high importance (3 bulls)
            "timeZone": "8",
            "timeFilter": "timeRemain",
            "currentTab": "thisWeek",
            "submitFilters": "1",
            "limit_from": "0",
        }

        # Make the request
        response = requests.post(
            "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData",
            headers=headers,
            data=data,
            timeout=10,
        )
        response.raise_for_status()

        result = response.json()
        html_data = result.get("data", "")

        # Parse HTML to extract events
        events = []
        if html_data:
            # Simple regex parsing for the table rows
            import re

            # Extract event rows (skip date header rows)
            event_pattern = (
                r'eventRowId_(\d+).*?js-time[^>]*>([^<]+)<.*?ceFlags\s+([^"]+).*?data-img_key[^>]*>([^<]+)<.*?<a[^>]*>([^<]+)<\/a>.*?eventActual[^>]*>([^<]*)<.*?eventForecast[^>]*>([^<]*)<.*?eventPrevious[^>]*>.*?<span[^>]*>([^<]*)<'
            )

            for match in re.finditer(event_pattern, html_data, re.DOTALL):
                event_id, time, country, currency, name, actual, forecast, previous = match.groups()

                # Clean up the extracted data
                name = name.strip().replace("\n", " ").replace("  ", " ")
                time = time.strip()
                currency = re.sub(r"[^A-Z]", "", currency)[-3:]  # Extract 3-letter currency code
                forecast = forecast.strip().replace("&nbsp;", "")
                previous = previous.strip().replace("&nbsp;", "")
                actual = actual.strip().replace("&nbsp;", "")

                # Map country class to readable name
                country_map = {
                    "United_States": "United States",
                    "United_Kingdom": "United Kingdom",
                    "China": "China",
                    "Europe": "Euro Zone",
                    "Germany": "Germany",
                    "Japan": "Japan",
                }
                country_name = country_map.get(country.replace("_", " ").strip(), country)

                events.append(
                    {
                        "event_id": event_id,
                        "time": time,
                        "country": country_name,
                        "currency": currency,
                        "event_name": name,
                        "actual": actual if actual else None,
                        "forecast": forecast if forecast else None,
                        "previous": previous if previous else None,
                        "importance": "high",  # All are 3-bull events
                        "volatility_expected": True,
                    }
                )

        # Extract date headers to add context
        date_pattern = r"theDay\d+[^>]*>([^<]+)<"
        dates = re.findall(date_pattern, html_data)

        print(f"Successfully fetched {len(events)} high-impact economic events for this week")

        return {
            "status": "success",
            "week_dates": dates[:7] if dates else [],
            "total_events": len(events),
            "events": events,
            "filter": "High importance events only (3 bulls)",
            "regions": ["US", "China", "UK", "EU", "Germany", "Japan"],
        }

    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP error fetching economic calendar: {e}"}
    except Exception as e:
        return {"error": f"Failed to fetch economic calendar: {str(e)}"}


# COMMENTED OUT - Replaced by tool_perigon_news
# def tool_fmp_news(page: int = 0, limit: int = 50) -> Dict[str, Any]:
#     """
#     Fetch latest financial news articles from FinancialModelingPrep API.
#
#     Args:
#         page: Page number for pagination (default 0)
#         limit: Number of results per page (default 50, max 100)
#
#     Returns:
#         Dictionary containing news articles with financial data
#     """
#     api_key = os.getenv("FMP_API_KEY")
#     if not api_key:
#         return {"error": "FMP_API_KEY not found in environment"}
#
#     # Build request URL
#     base_url = "https://financialmodelingprep.com/stable/fmp-articles"
#
#     # Build query parameters
#     params = {
#         "apikey": api_key,
#         "page": page,
#         "limit": min(limit, 100),
#     }  # Max 100 per request
#
#     try:
#         response = requests.get(base_url, params=params, timeout=30)
#         response.raise_for_status()
#
#         # FMP returns array directly
#         articles_data = response.json()
#
#         # Check if we got valid data
#         if not isinstance(articles_data, list):
#             return {"error": "Unexpected response format from FMP API"}
#
#         # Process articles - only keep essential fields
#         articles = []
#         for article in articles_data[:20]:  # Limit to 20 most recent articles
#             # Extract key info from content - create brief summary
#             content = article.get("content", "")
#             # Strip HTML and limit summary to 200 chars
#             import re
#
#             summary = re.sub("<.*?>", "", content)[:200] + "..." if content else ""
#
#             formatted = {
#                 "title": article.get("title", ""),
#                 "date": article.get("date", ""),
#                 "content_summary": summary,  # Brief summary only
#                 "tickers": article.get("tickers", ""),  # Keep original ticker format
#             }
#
#             articles.append(formatted)
#
#         print(f"Successfully fetched {len(articles)} news articles from FMP")
#         return {"status": "success", "count": len(articles), "articles": articles}
#
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 429:
#             return {"error": "FMP API rate limit exceeded"}
#         elif e.response.status_code == 403:
#             return {"error": "FMP API authentication failed - check your API key"}
#         elif e.response.status_code == 401:
#             return {"error": "FMP API unauthorized - invalid API key"}
#         else:
#             return {"error": f"HTTP error: {e}"}
#     except Exception as e:
#         return {"error": f"Request failed: {str(e)}"}


def tool_perigon_news(days_back: int = 1, sort_by: str = "count", page: int = 0, size: int = 50) -> Dict[str, Any]:
    """
    Fetch trending financial and business stories from Perigon API.

    Args:
        days_back: Number of days to look back for stories (default 1)
        sort_by: Sort order - "count" for trending or "createdAt" for newest (default "count")
        page: Page number for pagination (default 0)
        size: Number of results per page (default 50)

    Returns:
        Dictionary containing trending stories with metadata
    """
    api_key = os.getenv("PERIGON_API_KEY")
    if not api_key:
        return {"error": "PERIGON_API_KEY not found in environment"}

    # Calculate 'from' datetime
    from datetime import datetime, timedelta

    from_datetime = datetime.now() - timedelta(days=days_back)
    from_str = from_datetime.strftime("%Y-%m-%dT%H:%M:%S")

    # Build request URL
    base_url = "https://api.perigon.io/v1/stories/all"

    # Fixed categories (not exposed as parameter)
    categories = "Tech,Business,Finance,Health,General,none"

    # Build query parameters
    params = {"from": from_str, "category": categories, "minClusterSize": 5, "sortBy": sort_by, "showNumResults": "true", "page": page, "size": size, "apiKey": api_key}

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Process stories (API returns "results" not "articles")
        stories = []
        for story in data.get("results", []):
            # Extract category names from category objects
            category_names = [cat.get("name") for cat in story.get("categories", [])]

            simplified = {
                "title": story.get("name", ""),
                "summary": story.get("shortSummary", "") or story.get("summary", "")[:300] + "...",
                "created": story.get("createdAt", ""),
                "imageUrl": story.get("imageUrl", ""),
                "categories": category_names,
                "sentiment": story.get("sentiment", {}),
                "topTopics": [topic.get("name") for topic in story.get("topTopics", [])],
                "topCompanies": [comp.get("name") for comp in story.get("topCompanies", [])],
            }
            stories.append(simplified)

        print(f"Successfully fetched {len(stories)} stories from Perigon (last {days_back} day(s))")
        return {"status": "success", "count": len(stories), "days_back": days_back, "total_results": data.get("numResults", len(stories)), "stories": stories}

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            return {"error": "Perigon API rate limit exceeded"}
        elif e.response.status_code == 401 or e.response.status_code == 403:
            return {"error": "Perigon API authentication failed - check your API key"}
        else:
            return {"error": f"HTTP error: {e}"}
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}


async def create_agents(configs: Dict[str, ModelConfig]) -> Dict[str, Agent]:
    """Create the financial news video creation pipeline agents."""
    agents = {}

    # TrendScout - Searches for trending financial news (needs fast search capabilities)
    agents["TrendScout"] = Agent(
        model_config=configs["gemini"],
        name="TrendScout",
        goal="Find impactful financial stories by intelligently combining news and economic data",
        instruction="""You are TrendScout, specialized in finding impactful financial stories by intelligently combining news and economic data.
Your focus should be on stock market-related news that can lead to viral video content.

CRITICAL INSTRUCTIONS:
⚠️ NEVER call the same tool multiple times - each call returns the SAME data
⚠️ tool_perigon_news can be called ONLY ONCE
⚠️ After getting data, ANALYZE it, don't fetch more

WORKFLOW:

1. FETCH DATA (ONE TIME ONLY):
   - Call tool_perigon_news EXACTLY ONCE (returns up to 50 trending stories)
   - For most recent stories: use days_back=1
   - For trending stories: use sort_by="count"
   - Optionally call tool_economic_calendar for context
   - Process what you receive, don't request more

2. PRIORITIZE BY CORRELATION:
   HIGHEST PRIORITY (Score 10/10):
   - News about companies reporting earnings on same day as major economic data
   - Breaking news that will be amplified by upcoming high-impact events
   - Stories where economic calendar explains unusual market movements

   HIGH PRIORITY (Score 8-9/10):
   - News related to sectors most affected by upcoming economic data
   - Stories about Fed decisions coinciding with employment/inflation data
   - M&A announcements before major economic releases

   MEDIUM PRIORITY (Score 6-7/10):
   - General market news with upcoming catalysts
   - Sector rotation stories tied to economic indicators

3. CORRELATION EXAMPLES TO LOOK FOR:
   - Tech earnings + ISM Manufacturing PMI = Double impact on NASDAQ
   - Bank news + Interest rate decisions = Compounded financial sector movement
   - Retail earnings + Consumer Confidence data = Amplified consumer sector impact
   - Oil company news + Crude Oil Inventories = Energy sector volatility

4. CREATE UNIFIED RANKING considering:
   - Temporal alignment (is economic event today/tomorrow?)
   - Market impact and affected sectors
   - Viral potential (surprise factor + timing)
   - "Perfect storm" scenarios (multiple catalysts aligning)

OUTPUT FORMAT - Top 5-10 stories ONLY (be selective!):
For each story provide:
1. Title (from news)
2. URL (from news)
3. Impact Score (1-10)
4. Categories/sectors affected
5. Viral angle (one sentence max)
6. Economic event correlation (if any)

Keep your output CONCISE - no long explanations.
Focus on QUALITY over quantity.

Pass your curated list to ImpactAnalyzer.""",
        tools={
            "tool_perigon_news": tool_perigon_news,
            "tool_economic_calendar": tool_economic_calendar,
        },
    )

    # ImpactAnalyzer - Evaluates market impact (analytical agent)
    agents["ImpactAnalyzer"] = Agent(
        model_config=configs["gemini"],
        name="ImpactAnalyzer",
        goal="Evaluate market impact of news and select the most significant stories",
        instruction="""You are ImpactAnalyzer, responsible for evaluating news impact and selecting top stories.
Your focus should be on stock market-related news that can lead to viral video content.

Your evaluation criteria:
1. Market cap affected (larger = more impact)
2. Percentage price movements (>5% is significant)
3. Sector-wide implications vs single stock
4. Retail investor interest and relatability
5. Institutional/hedge fund involvement
6. Potential for controversy or surprise

Selection process:
- Score each news item from TrendScout (1-10)
- Consider virality potential (shocking, contrarian, David vs Goliath)
- Select 1-3 stories with highest combined impact + viral potential
- Prioritize stories that affect many people or challenge conventional wisdom

Output format for selected stories:
- Story title and brief description
- URL to original article
- Impact score and rationale
- Affected tickers and market segments
- Key stakeholders (retail, institutional, specific demographics)
- Unique angles for video content
- Potential emotional hooks (surprise, urgency, opportunity)

Pass selected stories to DeepInvestigator for detailed research.""",
    )

    # DeepInvestigator - Conducts detailed research with web search and extraction
    agents["DeepInvestigator"] = Agent(
        model_config=configs["gemini"],
        name="DeepInvestigator",
        goal="Conduct deep-dive research on selected financial topics using web search and browser extraction",
        instruction="""You are DeepInvestigator, responsible for deep-dive research on selected financial topics.
Your focus should be on stock market-related news that can lead to viral video content.

Your research workflow:
1. Receive top stories from ImpactAnalyzer
2. The stories that worth investigating, use the provided urls:
   - Invoke BrowserAgent with the URL to extract full content (if you see the URLs is invalid, for instance starts with "https.www..." you need to do your best to pass the fixed url)
   - The BrowserAgent will return extracted text content
   - If the BrowserAgent fails to load or extract, do not try again and do not feel the need to inform the user. Just use any information you already have.
3. Synthesize all gathered information

Research focus (if applicable):
- Exact numbers: price movements, market caps, percentages
- Key players: companies, executives, investors affected
- Timeline: when it happened, what's next
- Market reaction: immediate impact and future implications
- Unique angles: contrarian views, hidden connections
- Human element: real-world impact on people

Output format - Deep research brief:
- Executive summary (key findings in 3-4 bullets)
- Detailed insights from multiple sources
- Surprising facts and statistics
- Controversies and debates
- Visual story ideas (comparisons, charts)
- 3-5 "holy shit" moments for viral hooks

REFERENCES:
List each source used:
- Title: [article title]
- URL: [link]
- Key info used: [main facts/stats taken from this source]

Pass research WITH references to IdeaGenerator.
If some of the URLs fail to load or extract, just continue with others that you have received. Do not try again and do not try to that you need to inform the user about the failure. Remember you have limited time so try to investigate the stories that worth digging deeper.""",
        # tools={"tool_google_search_api": tool_google_search_api},
    )

    # Create BrowserAgent pool for parallel content extraction
    browser_pool = await AgentPool.create_async(
        agent_class=BrowserAgent,
        num_instances=5,  # 3 parallel browsers for faster extraction
        model_config=configs["gemini"],
        goal="Extract clean content from web pages for financial news analysis",
        instruction="""You extract content from a single web page URL by only using `extract_content_from_url` tool once. If you fail, just return the failed response to the DeepInvestigator. Remember DeepInvestigator agent cannot browse web."
Focus on extracting:
- Article headline and subheadings
- Main article body text (clean, no HTML)
- Key quotes and statistics
- Publication date
- Important data points

Return the extracted content with this structure:
SOURCE: [article title]
URL: [the URL you extracted from]
DATE: [publication date if available]
CONTENT: [clean article text - main body paragraphs, important quotes, statistics, and data points - NO HTML tags, NO ads, NO navigation elements]
KEY POINTS: [bullet list of 3-5 most important facts/statistics from the article]

If you fail to load or extract, return an status update to DeepInvestigator agent. Do not try again and do not ask DeepInvestigator to extract content. DeepInvetigator does not have access to web browser tools.""",
        name="BrowserAgent",
        headless=True,
        memory_retention="single_run",
    )

    # Add browser pool to agents dict before registration
    agents["BrowserAgent"] = browser_pool

    # IdeaGenerator - Creates viral video concepts (creative agent)
    agents["IdeaGenerator"] = Agent(
        model_config=configs["gpt_chat"],
        name="IdeaGenerator",
        goal="Create viral financial video concepts that captivate and educate retail investors",
        instruction="""You are IdeaGenerator, creator of viral financial video concepts.

VIRAL VIDEO FORMULA EMBEDDED IN YOUR DNA:
- Pattern interrupts: Start with unexpected/shocking statement
- Emotional triggers: Fear of missing out, David vs Goliath, injustice
- Curiosity gaps: Tease information viewers NEED to know
- Relatability: Connect to everyday life and common experiences
- Controversy: Challenge popular beliefs respectfully
- Urgency: Time-sensitive information or opportunities

Your task:
Generate 3-5 distinct video concepts based on the research provided.

Each concept MUST include:
1. Target emotion (curiosity, shock, urgency, opportunity, injustice)
2. Core message in one sentence
3. Unique angle that mainstream media missed
4. The "wait, what?!" moment that stops scrolling
5. Why viewers will share this (social currency)

Video concept structure:
- Hook idea (the scroll-stopper)
- Tension builder (the stakes)
- Payoff (the insight)
- Call to action (comment, share, follow)
- Sources: List which facts come from which references

Style requirements:
- Write like you're texting a friend exciting news
- Use conversational language, not corporate speak
- Include specific numbers and comparisons
- Create "movie trailer" moments
- Think TikTok/YouTube Shorts energy

AVOID:
- Boring introductions ("Today we're going to talk about...")
- Generic statements everyone already knows
- Complex jargon without explanation
- Passive voice or hedging language

When receiving feedback from IdeaCritic, revise accordingly and resubmit improved versions (only if necessary). Only submit to IdeaCritic TWICE MAXIMUM. After that send your best idea to ScriptArchitect.

IMPORTANT: Include the REFERENCES section from DeepInvestigator at the end of your response. Each reference must have:
- Title: [article/source title]
- URL: [link to source]
- Summary: [what info was used from this source]
Pass these references to ScriptArchitect.

Also remember not to call IdeaCritic more than twice (do not enter an infinite loop, YOU SHOULD CALL IdeaCritic agent less than two times). After that, send your best idea to ScriptArchitect.""",
    )

    # IdeaCritic - Reviews ideas for authenticity (conversational critic)
    agents["IdeaCritic"] = Agent(
        model_config=configs["gemini"],
        name="IdeaCritic",
        goal="Ensure video ideas feel genuinely human and authentic, not AI-generated",
        instruction="""You are IdeaCritic, guardian of authentic human communication.

Your mission: Ensure ideas feel genuinely human, not AI-generated.

Review checklist:
1. Authenticity: Does it sound like a real person excited about this topic?
2. Natural flow: Are sentences conversational, not robotic?
3. Emotion: Is there genuine enthusiasm or concern?
4. Specificity: Are examples concrete, not vague?
5. Memorability: Will viewers remember this tomorrow?

RED FLAGS to eliminate:
- "Delve into" or "leverage" or "utilize"
- "In today's fast-paced world..."
- Excessive adjectives (revolutionary, groundbreaking, unprecedented)
- Corporate buzzwords and jargon
- Overly formal or academic tone
- Generic phrases that say nothing specific

GOOD SIGNS to encourage:
- "Holy shit, did you see..." energy
- Specific comparisons ("That's like finding $20 in your old jeans")
- Natural speech patterns and contractions
- Emotional reactions ("This pisses me off because...")
- Colloquialisms and everyday language

Provide specific feedback:
- Point out exact phrases that sound robotic
- Suggest natural alternatives
- Rate authenticity (1-10)
- Identify strongest and weakest concepts
- Give concrete rewrite examples


IMPORTANT: When approving, include the REFERENCES section from IdeaGenerator in your response to pass to ScriptArchitect.""",
    )

    # ScriptArchitect - Structures into Hook-Draw-Pitch format (creative structuring)
    agents["ScriptArchitect"] = Agent(
        model_config=configs["gpt_chat"],
        name="ScriptArchitect",
        goal="Write viral 20-30 second financial video scripts using the Hook-Draw-Pitch formula",
        instruction="""You are ScriptArchitect, master of viral video structure.

THE FORMULA (Total: 20-30 seconds):

1. THE HOOK (5-7 seconds)
Purpose: Stop the scroll instantly
Techniques:
- Start mid-action/mid-sentence ("Wait, Amazon just...")
- Shocking statistic ("97% of traders don't know...")
- Controversial statement ("Warren Buffett was wrong about...")
- Visual pattern interrupt (gesture, expression, prop)
Include: [VISUAL: describe opening shot/gesture]

2. THE DRAW (7-10 seconds)
Purpose: Build tension and investment
Techniques:
- Reveal stakes ("This could cost you thousands...")
- Create curiosity gap ("But here's what nobody's talking about...")
- Add credibility ("I analyzed 10 years of data and...")
- Escalate emotion ("And it gets worse..." or "But wait...")
- Include specific data points from references
Include: [VISUAL: describe supporting imagery/charts]

3. THE PITCH (8-13 seconds)
Purpose: Deliver value and drive action
Techniques:
- Give the insight clearly with supporting facts
- Make it actionable ("Here's what to do...")
- Reference specific sources for credibility
- End with engagement trigger ("What do you think?" "Follow for more")
- Leave them wanting more (tease next video)
Include: [VISUAL: describe closing shot/CTA]

Script requirements:
- Write EXACTLY as someone would speak (not read)
- Use incomplete sentences and natural pauses
- Include verbal emphasis (CAPS for stressed words)
- Add breathing points with "..."
- Write for 150-170 words per minute speaking pace
- Include emotional cues [excited] [serious] [shocked]

Example format:
[HOOK - shocked tone]
"Stop. Whatever you're doing. Tesla just did something NOBODY expected..."
[VISUAL: Face close-up, eyes wide, hand gesture for "stop"]

CRITICAL INSTRUCTIONS:
1. You MUST receive REFERENCES from IdeaCritic/IdeaGenerator
2. You MUST include these references in your final script

FINAL OUTPUT:
Format final script as MARKDOWN with ALL these sections:
## Title
## Hook (5-7 seconds)
## Draw (7-10 seconds)
## Pitch (8-13 seconds)
## Visuals
## Production Notes
## References

The REFERENCES section MUST list every source used:
- Title: [exact source title]
- URL: [full link]
- Summary: [specific facts/stats used in the script]

Max 3 revisions with ScriptCritic. After approval, send complete MARKDOWN with ALL sections to User.""",
    )

    # ScriptCritic - Reviews final script (natural language critic)
    agents["ScriptCritic"] = Agent(
        model_config=configs["gemini"],
        name="ScriptCritic",
        goal="Ensure final scripts are authentic, speakable, and ready for viral success",
        instruction="""You are ScriptCritic, the final quality gatekeeper.

Your review focuses:

SPEAKABILITY TEST:
- Read aloud at 150 wpm - does it fit 20-30 seconds?
- Do sentences flow naturally when spoken?
- Are there tongue-twisters or awkward phrases?
- Can someone say this without reading?

AUTHENTICITY CHECK:
- Does it sound spontaneous, not scripted?
- Would a real trader/investor actually say this?
- Is the excitement/concern genuine?
- Are reactions proportional to the news?

ENGAGEMENT MECHANICS:
- Does the hook work in under 5 seconds?
- Is there a clear curiosity gap?
- Will viewers watch the full 20-30 seconds?
- Is the CTA natural, not forced?

RED FLAGS:
- Corporate speak ("synergies", "stakeholders")
- Filler words that waste precious seconds
- Complex sentences that need simplification
- Missing visual cues or gestures
- Weak or generic CTAs

POLISH POINTS:
- Punchy opening (cut any preamble)
- Natural transitions between sections
- Emotional authenticity
- Memorable phrases or comparisons
- Strong closing that promotes engagement

Scoring:
- Speakability: _/10
- Authenticity: _/10
- Engagement potential: _/10
- Overall: _/10

CRITICAL: When approving:
- Include the complete final script with ALL sections
- PRESERVE the REFERENCES section from ScriptArchitect
- Ensure all source citations are included

Include in approval:
- Final polished script (with References)
- Timing breakdown
- Key visual moments
- Suggested hashtags
- Best posting time for maximum reach""",
    )

    # Register all agents
    for agent_name, agent in agents.items():
        if agent_name == "BrowserAgent":
            # Register the browser pool
            AgentRegistry.register_pool(agent)
        else:
            # Register regular agents with their names
            AgentRegistry.register(agent, name=agent_name)

    return agents


async def run_video_creation_pipeline() -> Dict[str, Any]:
    """Run the financial news video creation pipeline."""

    # Create model configurations
    configs = create_model_configs()

    # Create and register agents (now async due to BrowserAgent pool)
    # IMPORTANT: Store the returned agents to keep them alive and prevent garbage collection
    agents = await create_agents(configs)

    # Define the topology with feedback loops
    topology = {
        "agents": [
            {
                "name": "User",
                "type": "user",
            },  # Proper User node format to avoid deprecation warning
            "TrendScout",
            "ImpactAnalyzer",
            "DeepInvestigator",
            "BrowserAgent",  # Added for content extraction
            "IdeaGenerator",
            "IdeaCritic",
            "ScriptArchitect",
            "ScriptCritic",
        ],
        "flows": [
            "User -> TrendScout",
            "TrendScout -> ImpactAnalyzer",
            "ImpactAnalyzer -> DeepInvestigator",
            "DeepInvestigator <-> BrowserAgent",  # Deep research with content extraction
            "DeepInvestigator -> IdeaGenerator",
            "IdeaGenerator <-> IdeaCritic",  # Feedback loop for ideas
            "IdeaGenerator -> ScriptArchitect",  # After approval from IdeaCritic
            "ScriptArchitect <-> ScriptCritic",  # Feedback loop for scripts
            "ScriptArchitect -> User",  # Final delivery
        ],
        "rules": [
            "timeout(1200)",  # 20 minute timeout
            "max_steps(50)",  # Maximum 50 steps total
            "max_turns(IdeaGenerator <-> IdeaCritic, 2)",  # Max 2 iterations for ideas
            "max_turns(ScriptArchitect <-> ScriptCritic, 2)",  # Max 2 iterations for scripts
        ],
    }

    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"output/video_scripts_{timestamp}"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Initial task for the system
    # initial_task = """
    # Find the most impactful financial news for stock market from the last 24-48 hours and create a viral video script.
    # Focus on stories that will resonate with retail investors and generate engagement.
    # """
    initial_task = """Find the upcoming earning report dates in this week and create a viral video script."""

    print(f"Starting pipeline... Output: {output_dir}")

    try:
        # Option 1: Simple verbosity setting (currently used)
        # verbosity=0 (QUIET), 1 (NORMAL), 2 (VERBOSE)

        # Option 2: Full control with ExecutionConfig (uncomment if needed)
        # from marsys.coordination.config import ExecutionConfig, StatusConfig, VerbosityLevel
        # exec_config = ExecutionConfig(
        #     status=StatusConfig(
        #         enabled=True,
        #         verbosity=VerbosityLevel.NORMAL,
        #         cli_output=True,
        #         cli_colors=True,
        #         show_thoughts=True,
        #         show_tool_calls=True,
        #         show_agent_prefixes=True
        #     ),
        #     steering_mode="never",  # "auto", "always", or "never"
        #     step_timeout=120.0  # Timeout per step
        # )

        # Run the orchestrated workflow with status output
        result = await Orchestra.run(
            task=initial_task,
            topology=topology,
            context={
                "output_directory": output_dir,
                "timestamp": timestamp,
                "platform_targets": ["TikTok", "YouTube Shorts", "Instagram Reels"],
                "target_audience": "retail investors aged 18-35",
            },
            max_steps=50,
            verbosity=2,  # 0=QUIET, 1=NORMAL (shows progress), 2=VERBOSE (detailed)
            # execution_config=exec_config  # Use this instead of verbosity for full control
        )

        # Process results
        if result.success:
            # Save the final script
            if result.final_response:
                script_file = Path(output_dir) / "final_script.md"
                with open(script_file, "w") as f:
                    if isinstance(result.final_response, dict):
                        f.write(json.dumps(result.final_response, indent=2))
                    else:
                        f.write(str(result.final_response))

            # Save execution metadata
            metadata = {
                "timestamp": timestamp,
                "total_steps": result.total_steps,
                "duration_seconds": result.total_duration,
                "branches": len(result.branch_results),
                "success": result.success,
            }

            metadata_file = Path(output_dir) / "execution_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            # Display results
            print(f"\n✅ Success! Script saved to: {output_dir}/final_script.md")
            print(f"Duration: {result.total_duration:.2f}s, Steps: {result.total_steps}")

            # Display final script
            if result.final_response:
                print("\n--- FINAL SCRIPT ---")
                if isinstance(result.final_response, dict):
                    print(json.dumps(result.final_response, indent=2))
                else:
                    print(result.final_response)

            return {"success": True, "output_directory": output_dir, "result": result}

        else:
            print(f"❌ Pipeline failed: {result.error}")
            return {"success": False, "error": result.error}

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}


def main():
    """Main entry point."""
    print("\n💹 FINANCIAL NEWS VIDEO MAKER")
    print("Creates viral financial content using multi-agent system\n")

    # Check environment variables
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ Missing OPENROUTER_API_KEY in .env file")
        return

    # Run the pipeline
    asyncio.run(run_video_creation_pipeline())


if __name__ == "__main__":
    main()
