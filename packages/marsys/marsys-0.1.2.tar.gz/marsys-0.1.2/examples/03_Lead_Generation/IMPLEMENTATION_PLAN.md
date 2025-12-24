# Lead Generation Multi-Agent System - Implementation Plan

## Status: IMPLEMENTED

## File Structure

```
examples/03_Lead_Generation/
├── IMPLEMENTATION_PLAN.md          # This file
├── default_config.yaml             # YAML configuration template
├── run_lead_generation.py          # Main file with all code
└── output/                         # Generated outputs
    └── {run_name}/
        ├── config.json
        ├── linkedin_session.json
        ├── market_research_industries.json
        ├── discovered_companies.jsonl
        ├── filtered_companies.jsonl
        ├── discarded_companies.jsonl
        ├── company_reports/
        │   └── {company_id}.md
        ├── qualification/
        │   └── {company_id}_qualification.json
        ├── qualified_companies.jsonl
        └── contacts/
            └── {company_id}_employees.jsonl
```

## Usage

```bash
# Run with default configuration
python run_lead_generation.py

# Run with custom configuration
python run_lead_generation.py --config my_config.yaml

# Skip LinkedIn authentication (use existing session)
python run_lead_generation.py --skip-auth

# Start from a specific phase (useful for resuming)
python run_lead_generation.py --start-phase 3
```

## Configuration (default_config.yaml)

Key configuration sections:
- **business**: Your company info (name, description, products, value proposition)
- **target**: Target criteria (industries, countries, company sizes, employee range)
- **contacts**: Contact criteria (departments, job titles, max per company)
- **discovery**: Number of companies to find
- **pools**: Agent pool sizes (websearch: 5, browser: 10)
- **model**: Model settings (provider: openrouter, model: anthropic/claude-sonnet-4.5)
- **session**: LinkedIn session path (optional)
- **output**: Output directory

## Phases

| Phase | Description | User Interaction |
|-------|-------------|------------------|
| 0 | LinkedIn Authentication | Manual login in browser |
| 1 | Market Research | Approve discovered industries |
| 2 | Company Discovery | Automatic |
| 3 | Initial Filtering | Automatic |
| 4 | Deep Company Research | Automatic |
| 5 | Lead Qualification | Automatic |
| 6-7 | Person Discovery | Automatic |

## Key Technical Decisions

| Feature | Implementation |
|---------|----------------|
| **Model** | `anthropic/claude-sonnet-4.5` via OpenRouter |
| **File Tools** | Using `create_file_operation_tools()` from MARSYS |
| **Session Persistence** | `SessionBrowserAgent` with Playwright `storage_state()` |
| **Non-Convergence** | `is_convergence_point=False` on deep research browser pools |
| **Pool Sizes** | WebSearch: 5, Browser: 10 (configurable) |
| **Memory** | All BrowserAgents use `memory_retention="single_run"` |
| **Orchestration** | `Orchestra.run()` for each phase |

## Agent Topology

### Phase 2: Company Discovery
```
CompanyDiscoveryAgent
    ├── WebSearchPool_Discovery (5 agents)
    └── BrowserPool_Discovery (10 agents)
```

### Phase 4: Deep Company Research
```
DeepCompanyResearchAgent
    └── WebSearchPool_DeepResearch (5 agents, non-convergent)
        └── BrowserPool_DeepResearch (10 agents, non-convergent)
```

### Phase 6-7: Person Discovery
```
PersonDiscoveryCoordinator
    └── CompanyPeopleSearchAgent
        ├── WebSearchPool_People (5 agents)
        └── BrowserPool_People (10 agents, non-convergent)
```

## Output Files

- **discovered_companies.jsonl**: All companies found (JSON Lines)
- **filtered_companies.jsonl**: Companies passing initial filter
- **discarded_companies.jsonl**: Companies failing filter with reasons
- **company_reports/{id}.md**: Comprehensive research per company
- **qualification/{id}_qualification.json**: Qualification decision per company
- **qualified_companies.jsonl**: Final qualified leads
- **contacts/{id}_employees.jsonl**: Employee profiles per company
