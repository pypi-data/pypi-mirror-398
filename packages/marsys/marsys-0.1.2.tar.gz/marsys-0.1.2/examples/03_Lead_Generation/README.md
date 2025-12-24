# Lead Generation Multi-Agent System

An AI-powered lead generation pipeline that discovers companies, researches them, qualifies leads, and finds decision-maker contacts using MARSYS multi-agent orchestration.

## Overview

This system runs through 7 phases to generate qualified B2B leads:

| Phase | Name | Description |
|-------|------|-------------|
| 0 | LinkedIn Auth | Authenticate with LinkedIn (saves session for reuse) |
| 1 | Market Research | Discover target industries (skipped if pre-configured) |
| 2 | Company Discovery | Find companies matching your criteria |
| 3 | Initial Filtering | Filter companies by size, industry, location |
| 4 | Deep Research | Generate detailed company reports |
| 5 | Lead Qualification | Score and qualify leads for your business |
| 6 | Person Discovery | Find decision-maker contacts at qualified companies |

## Prerequisites

### 1. Install Dependencies

```bash
# From the repository root
pip install -e .

# Install browser automation
playwright install chromium
```

### 2. Set API Keys

Create a `.env` file or export environment variables:

```bash
# Required - at least one search API
export OPENROUTER_API_KEY="your-key"  # For LLM access

# Optional - for web search (improves company discovery)
export GOOGLE_SEARCH_API_KEY="your-key"
export GOOGLE_CSE_ID_GENERIC="your-cse-id"
# OR
export BING_SEARCH_API_KEY="your-key"
```

## Quick Start

### 1. Copy and customize the config

```bash
cp default_config.yaml my_config.yaml
# Edit my_config.yaml with your business info and target criteria
```

### 2. Run the pipeline

```bash
# Use default config
python run_lead_generation.py

# Use custom config
python run_lead_generation.py --config my_config.yaml

# Skip LinkedIn auth (if you don't need contact discovery)
python run_lead_generation.py --skip-auth

# Start from a specific phase (useful for resuming)
python run_lead_generation.py --start-phase 2
```

## Configuration Guide

### Business Info (`business:`)

```yaml
business:
  name: "Your Company"
  description: "What your company does..."
  products_services:
    - "Service 1"
    - "Service 2"
  value_proposition: "Why customers choose you..."
```

This information helps the AI understand what leads to look for and how to qualify them.

### Target Criteria (`target:`)

```yaml
target:
  # Leave empty [] to auto-discover via market research (Phase 1)
  # Or specify directly to skip Phase 1
  industries:
    - "Finance"
    - "Healthcare"

  countries:
    - "USA"
    - "Germany"

  company_sizes:
    - "small"      # 1-50 employees
    - "medium"     # 51-500 employees
    - "large"      # 501-5000 employees
    - "enterprise" # 5000+ employees

  employee_count_range:
    min: 50
    max: 5000

  # Optional: industries to exclude
  exclude_industries:
    - "Government"
    - "Non-profit"
```

### Contact Criteria (`contacts:`)

```yaml
contacts:
  target_departments:
    - "IT"
    - "Engineering"
    - "Operations"

  target_job_titles:
    - "VP"
    - "Director"
    - "Head of"
    - "Manager"

  max_per_company: 5
```

### Discovery Settings (`discovery:`)

```yaml
discovery:
  num_companies: 50           # Target number of companies to find
  websearch_pool_size: 5      # Parallel web search agents
  browser_pool_size: 10       # Parallel browser agents
```

### Model Settings (`model:`)

```yaml
model:
  provider: "openrouter"      # openrouter, openai, anthropic, google
  name: "anthropic/claude-sonnet-4-20250514"
  browser_model: "anthropic/claude-sonnet-4-20250514"
```

## Output Files

All outputs are saved to `output/<run_name>/`:

```
output/lead_gen_demo/
├── config.json                    # Saved configuration
├── linkedin_session.json          # LinkedIn auth session (reusable)
├── market_research_industries.json # Discovered industries (Phase 1)
├── discovered_companies.jsonl     # Raw discovered companies (Phase 2)
├── filtered_companies.jsonl       # Companies passing initial filter (Phase 3)
├── discarded_companies.jsonl      # Companies that didn't pass filter
├── company_reports/               # Detailed company reports (Phase 4)
│   ├── company-name_country.md
│   └── ...
├── qualification/                 # Qualification details (Phase 5)
│   ├── company-name_country.json
│   └── ...
├── qualified_companies.jsonl      # Final qualified leads
├── contacts/                      # Contact info (Phase 6)
│   ├── company-name_country.json
│   └── ...
└── .phase_X_complete              # Phase completion markers
```

## Phase Completion & Resuming

The system tracks completed phases with `.phase_X_complete` marker files:

- **Completed phases are skipped** on re-run
- **Failed/interrupted phases** are cleaned up and re-run from scratch
- **To re-run a specific phase**, delete its marker file:
  ```bash
  rm output/lead_gen_demo/.phase_2_complete
  ```

### Start from a specific phase

```bash
# Skip to Phase 3 (requires Phase 2 output to exist)
python run_lead_generation.py --start-phase 3
```

## Tips

### For Best Results

1. **Be specific about your business** - The AI uses this to qualify leads
2. **Start with fewer companies** - Test with `num_companies: 10` first
3. **Use targeted industries** - Pre-configure industries for faster results
4. **LinkedIn session** - Log in once, session is saved for future runs

### Performance

- **WebSearch pool size**: More agents = faster discovery but higher API costs
- **Browser pool size**: More agents = faster scraping but more memory usage
- Recommended: Start with `websearch_pool_size: 3`, `browser_pool_size: 5`

### Troubleshooting

**Phase fails and won't restart:**
```bash
# Delete the phase marker to force re-run
rm output/<run_name>/.phase_X_complete
```

**LinkedIn auth issues:**
```bash
# Delete session and re-authenticate
rm output/<run_name>/linkedin_session.json
rm output/<run_name>/.phase_0_complete
```

**API rate limits:**
- Reduce pool sizes in config
- The system has built-in retry with exponential backoff

**Empty results:**
- Check your target criteria aren't too restrictive
- Verify API keys are set correctly
- Check logs for specific errors

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                        │
│              (run_lead_generation.py)                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌─────────┐        ┌─────────────┐       ┌─────────────┐
│ Phase 0 │        │  Phase 1-2  │       │  Phase 3-6  │
│LinkedIn │        │  Discovery  │       │  Research   │
│  Auth   │        │             │       │  & Qualify  │
└─────────┘        └──────┬──────┘       └──────┬──────┘
                          │                     │
              ┌───────────┼───────────┐         │
              ▼           ▼           ▼         ▼
         ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
         │WebSearch│  │WebSearch│  │Browser │  │Browser │
         │ Pool   │  │ Pool   │  │ Pool   │  │ Pool   │
         └────────┘  └────────┘  └────────┘  └────────┘
```

Each phase uses **Orchestra.run()** to coordinate agents with defined topologies, enabling parallel execution and automatic error handling.

## License

Part of the MARSYS Framework - Apache 2.0 License
