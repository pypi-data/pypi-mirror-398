# Patent Valuation: Backward Deduction & Agent Architecture Design

**Purpose**: Design the agent-based patent valuation system by working backwards from the final output (valuation number) to identify what each agent needs to accomplish, with what tools, and what handoff decisions they make.

**Methodology**: Backward deduction from goal → Forward agent architecture

---

## 📊 SECTION 1: BACKWARD DEDUCTION ANALYSIS

### 🎯 FINAL GOAL (Step 0)
**Output**: Patent Valuation Report with:
- **Primary**: Patent value in dollars (single number or range)
- **Secondary**: Detailed report documenting assumptions, sources, methodology, sensitivity analysis

---

### ⬅️ Step -1: What do we need to produce the final valuation number?

**Using Income Method (DCF)**:

```
Patent_Value = Σ(t=1 to T) [Adjusted_Cash_Flow_t / (1 + Discount_Rate)^t]
```

**What we need**:
1. **Adjusted_Cash_Flow_t** for each year t from 1 to T
2. **Discount_Rate** (constant or time-varying)
3. **T** (time horizon in years)

**Additional for report**:
4. **Assumption_Log**: All assumptions made with sources and rationales
5. **Sensitivity_Analysis**: Impact of ±20% changes in key assumptions
6. **Data_Quality_Metrics**: Completeness and reliability scores

**Decision Point**: None - this is calculation only
**Agent Responsible**: `ValuationCalculatorAgent` (final DCF calculation + report assembly)

---

### ⬅️ Step -2: What do we need to calculate Adjusted_Cash_Flow_t?

```
Adjusted_Cash_Flow_t = Revenue_t × Profit_Margin × IP_Contribution_Factor × Commercialization_Probability
```

**What we need**:
1. **Revenue_t**: Projected revenue at year t
2. **Profit_Margin**: Net profit margin (%)
3. **IP_Contribution_Factor**: What % of profit is attributable to this patent (0.0 to 1.0)
4. **Commercialization_Probability**: Likelihood technology reaches market (0.0 to 1.0)

**Decision Point**: None - this is calculation only (assuming inputs are ready)
**Agent Responsible**: Same agent as Step -1 (`ValuationCalculatorAgent`)

---

### ⬅️ Step -3: What do we need to calculate Discount_Rate?

```
Discount_Rate = Base_WACC + Patent_Risk_Premium
```

#### Step -3a: Base_WACC (Weighted Average Cost of Capital)

**What we need**:
1. **Industry_Classification**: Which industry does this patent belong to?
   - Source: Patent IPC/CPC codes → Industry mapping
   - Tool: Classification taxonomy (IPC → Industry)

2. **Industry_WACC**: WACC benchmark for that industry
   - Source: Damodaran's industry data (free)
   - Tool: Web scraper or manual CSV lookup

**Decision Point**: Is industry classification clear?
- If YES → Use exact industry WACC
- If NO (patent spans multiple industries) → Ask user OR use weighted average OR use closest proxy
**Agent Responsible**: `DiscountRateCalculatorAgent`

#### Step -3b: Patent_Risk_Premium

```
Patent_Risk_Premium = Technology_Maturity_Risk + Portfolio_Dependency_Risk + Litigation_Risk
```

**What we need**:

1. **Technology_Maturity_Risk**:
   - Input: Technology Readiness Level (TRL) or commercialization status
   - Mapping: TRL 1-3 → +8-12%, TRL 4-6 → +4-6%, TRL 7-9 → +2-4%
   - Source: Either user-provided OR inferred from patent data (grant date, citations, assignee activity)

2. **Portfolio_Dependency_Risk**:
   - Input: Is this a single critical patent OR one of many in portfolio?
   - Mapping: Critical single → +3-5%, One of many → +1-2%
   - Source: Portfolio information from user OR patent family analysis

3. **Litigation_Risk**:
   - Input: Litigation history, validity challenges
   - Mapping: Pending litigation → +3-5%, Prior challenges → +2-4%, Clean → +0-1%
   - Source: USPTO legal status, PACER court records

**Decision Point**: How to assess technology maturity?
- If user provides TRL → Use directly
- If not provided → Infer from patent metrics (citations, age, assignee product launches)
**Agent Responsible**: `RiskAssessmentAgent`

---

### ⬅️ Step -4: What do we need to calculate IP_Contribution_Factor?

**Context**: This is the MOST SUBJECTIVE component. Depends on whether patent is standalone or in a bundle.

#### Step -4a: Check Patent Portfolio Context

**What we need**:
1. **Portfolio_Information**: How many patents cover the product?
   - Source: User input OR patent family analysis OR assignee's patent portfolio search

**Decision Point**: Portfolio attribution required?
- If **Single Patent** → `IP_Contribution_Factor = 1.0` (100% attribution)
- If **Multiple Patents** → Need attribution method (go to Step -4b)

**Agent Responsible**: `PortfolioAnalyzerAgent`

#### Step -4b: Choose Attribution Method (if multiple patents)

**Three Methods Available**:

**Method 1: Comparable License Royalty**
- **What we need**: Comparable licensing agreements with disclosed royalty rates
- **Source**: SEC EDGAR filings, academic papers, LES surveys
- **Calculation**: `IP_Contribution_Factor = Royalty_Rate / Profit_Margin`
- **Decision**: Are comparable licenses available?
  - If YES → Use this method (most defensible)
  - If NO → Try Method 2

**Method 2: Smallest Salable Unit (SSU)**
- **What we need**:
  - Identification of smallest product component containing patented technology
  - Value/cost of that component
  - Value/cost of total product
- **Source**: Product teardown data, component pricing databases, user input
- **Calculation**: `IP_Contribution_Factor = Component_Value / Product_Value × Patent_Share_in_Component`
- **Decision**: Can we identify and value the component?
  - If YES → Use this method
  - If NO → Try Method 3

**Method 3: Feature Value Analysis**
- **What we need**:
  - List of all product features
  - Relative value/importance of each feature (survey data, conjoint analysis, expert judgment)
  - Identification of which features this patent covers
- **Source**: User input, competitive analysis, expert estimation
- **Calculation**: `IP_Contribution_Factor = Σ(Patented_Features_Value) / Σ(All_Features_Value)`
- **Decision**: Can we enumerate features and estimate values?
  - If YES → Use this method (least rigorous but always feasible)
  - If NO → ERROR (cannot proceed without some attribution method)

**Decision Point**: Which attribution method to use?
- Try in order: Comparable License → SSU → Feature Analysis
- If multiple methods feasible → Run all, report range
**Agent Responsible**: `AttributionEstimatorAgent`

---

### ⬅️ Step -5: What do we need to calculate Commercialization_Probability?

**Context**: Addresses "will this technology actually make it to market?"

#### Step -5a: Assess Technology & Commercial Readiness

**What we need**:

1. **Technology Readiness Level (TRL)**: 1-9 scale
   - TRL 1-3: Basic research (Probability: 0.05-0.20)
   - TRL 4-6: Prototype/pilot (Probability: 0.30-0.60)
   - TRL 7-9: Deployed/commercial (Probability: 0.80-1.00)
   - Source: User input OR inferred from patent/assignee data

2. **Commercial Readiness Level (CRL)**: 1-9 scale
   - CRL 1-3: Concept only (Low market readiness)
   - CRL 4-6: Market validation in progress
   - CRL 7-9: Established sales/distribution
   - Source: User input OR market research on assignee's products

3. **Market Validation Signals**:
   - Does assignee have products in market using this patent? (YES → increase probability)
   - Are there customer testimonials/sales data? (YES → increase probability)
   - Has technology been publicly demonstrated? (YES → increase probability)
   - Source: Web search, assignee website, press releases, product databases

**Decision Point**: Is technology already commercialized?
- If **Mature/Commercial** (TRL 7-9, products in market) → `Commercialization_Probability = 1.0`
- If **Early Stage** → Calculate probability from TRL/CRL mapping
**Agent Responsible**: `CommercializationAssessorAgent`

---

### ⬅️ Step -6: What do we need to calculate Profit_Margin?

**What we need**:
1. **Company-Specific Profit Margin** (if available)
   - Source: Company financial statements (10-K from SEC EDGAR if public)
   - Preferred: Net profit margin from most recent fiscal year

2. **Industry Benchmark Profit Margin** (if company data not available)
   - Source: Damodaran's industry data (free)
   - Use: Median net margin for the industry

**Decision Point**: Is company public with disclosed financials?
- If YES → Use company-specific margin (more accurate)
- If NO → Use industry benchmark (document as assumption)
**Agent Responsible**: `FinancialDataCollectorAgent`

---

### ⬅️ Step -7: What do we need to calculate Revenue_t (projected revenue at year t)?

**Two Approaches**:

#### Approach A: Direct Company Revenue Data (if available)

**What we need**:
1. **Current Revenue**: Company's current revenue (or product line revenue if patent is for specific product)
   - Source: Company financial statements, user input, press releases

2. **Revenue Growth Rate**: Expected annual growth
   - Source: Company guidance, analyst projections, industry growth rate

3. **Calculation**: `Revenue_t = Current_Revenue × (1 + Growth_Rate)^t`

**Decision**: Is company revenue data available and reliable?
- If YES → Use Approach A (simpler, more direct)
- If NO → Use Approach B (bottom-up market sizing)

#### Approach B: Bottom-Up Market Sizing (if no company data)

**What we need** (working backwards from SOM → SAM → TAM):

**Step -7a: Calculate SOM (Serviceable Obtainable Market)**
```
SOM = SAM × Realistic_Market_Share × Adoption_Rate
```
- **Realistic_Market_Share**: Estimated % of SAM this company/product can capture
  - Source: Competitive analysis, user input, historical market share data
- **Adoption_Rate**: % of potential customers who will actually buy
  - Source: Comparable product adoption curves, diffusion of innovation research

**Step -7b: Calculate SAM (Serviceable Available Market)**
```
SAM = TAM × Geographic_Filter × Distribution_Filter × Product_Fit_Filter
```
- **Geographic_Filter**: % of TAM in accessible geographies
  - Source: User input (which markets are targeted?), patent geographic coverage
- **Distribution_Filter**: % of market reachable via available distribution channels
  - Source: User input, assignee's distribution capabilities
- **Product_Fit_Filter**: % of market where product directly addresses needs
  - Source: Market segmentation analysis, user input

**Step -7c: Calculate TAM (Total Addressable Market)**
```
TAM = Total_Potential_Customers × Average_Revenue_Per_User × Purchase_Frequency
```
- **Total_Potential_Customers**: Size of customer base
  - Source: Census data, industry reports, trade association data (FREE)
- **Average_Revenue_Per_User (ARPU)**: Price per unit/subscription
  - Source: Competitive analysis (competitor pricing), user input
- **Purchase_Frequency**: How often customers buy (annual, one-time, etc.)
  - Source: Industry norms, comparable products

**Decision Point**: Can we estimate TAM with available free data?
- If YES → Proceed with bottom-up
- If NO → Ask user for market size estimate OR abort valuation
**Agent Responsible**: `MarketSizingAgent`

---

### ⬅️ Step -8: What do we need to calculate TAM components?

#### Step -8a: Identify Target Market(s)

**What we need**:
1. **Technology_Description**: What does this patent technology do?
   - Source: Patent abstract, claims, title

2. **Potential_Applications**: What products/services could use this technology?
   - Source: Patent claims analysis, prior art citations (what fields cite this patent?), CPC classification analysis

3. **Market_Identification**: Which industry/market segments use these applications?
   - Source: CPC → Industry mapping, SIC/NAICS codes, market research

**Decision Point**: Is the target market clear from patent data?
- If YES (single clear application) → Proceed with that market
- If NO (multiple possible applications) → Ask user which market to value OR value each separately and aggregate
**Agent Responsible**: `MarketIdentificationAgent`

---

### ⬅️ Step -9: What do we need to identify potential applications?

**What we need**:
1. **Patent_Technical_Content**:
   - Title
   - Abstract
   - Claims (especially independent claims)
   - Figures/drawings (if needed for clarity)
   - Technology classification (IPC/CPC codes)
   - Source: USPTO PatentsView API

2. **Technology_Context**:
   - What problem does this solve?
   - What are the innovative features?
   - How does it differ from prior art?
   - Source: Patent text analysis, background section, LLM analysis of claims

3. **Citation_Analysis**:
   - Forward citations: What later patents cite this one? (indicates application domains)
   - Backward citations: What prior art does this build on? (indicates technology lineage)
   - Source: USPTO PatentsView API

4. **Patent_Family_Analysis**:
   - Where else has this been filed? (geographic scope)
   - Are there continuation/divisional patents? (broader technology scope)
   - Source: EPO OPS API (INPADOC family)

**Decision Point**: Can we parse and understand the technology from patent text?
- If YES → Proceed with automated analysis
- If NO (highly technical, unclear) → Ask user to provide technology description
**Agent Responsible**: `PatentAnalyzerAgent`

---

### ⬅️ Step -10: What do we need to retrieve patent data?

**What we need**:
1. **Patent_Number**: The specific patent to value
   - Source: User input (initial request)

2. **API_Access**: USPTO PatentsView API, EPO OPS API
   - Authentication: None for USPTO, OAuth for EPO (free registration)

3. **Data_Validation**: Verify patent exists, is granted (not abandoned), is active (fees paid)
   - Source: USPTO Patent Center, PatentsView API

**Decision Point**: Is the patent valid and active?
- If YES → Proceed with valuation
- If NO (abandoned, expired, invalid) → Flag warning to user, ask if they want to proceed anyway
**Agent Responsible**: `PatentDataCollectorAgent`

---

### ⬅️ Step -11: What do we need from user to start?

**Minimum Required Inputs**:
1. **Patent_Number**: Which patent to value (e.g., "US10123456B2")
2. **Valuation_Context**: Why are we valuing this? (litigation, M&A, portfolio management, licensing)
   - Determines precision requirements and reporting format

**Optional Inputs** (improve accuracy if provided):
3. **Revenue_Data**: Company or product line revenue data
4. **Portfolio_Context**: Is this a standalone patent or part of bundle? How many patents total?
5. **Target_Market**: Which market/product is this patent for?
6. **Technology_Stage**: TRL/CRL levels if known
7. **Use_Case**: Is this for licensing negotiation? (determines if blocking potential is relevant)

**Decision Point**: Is minimum input sufficient to proceed?
- If YES → Start valuation workflow
- If NO (missing patent number or context) → Ask user for required inputs
**Agent Responsible**: `IntakeAgent`

---

### 🎯 BACKWARD DEDUCTION SUMMARY

Working backwards from final goal, we identified **11 steps** with clear dependencies:

```
Step -11: User Input (Patent #, Context)
   ↓
Step -10: Retrieve Patent Data (USPTO/EPO APIs)
   ↓
Step -9: Analyze Patent Technology (claims, classifications, citations)
   ↓
Step -8: Identify Target Markets (technology → applications → markets)
   ↓
Step -7: Calculate Revenue_t (company data OR bottom-up TAM/SAM/SOM)
   ↓
Step -6: Get Profit Margin (company data OR industry benchmark)
   ↓
Step -5: Assess Commercialization Probability (TRL/CRL analysis)
   ↓
Step -4: Calculate IP Contribution Factor (attribution method selection & calculation)
   ↓
Step -3: Calculate Discount Rate (Industry WACC + Patent Risk Premium)
   ↓
Step -2: Calculate Adjusted Cash Flows (Revenue × Margin × Attribution × Commercialization)
   ↓
Step -1: Calculate DCF (NPV of adjusted cash flows)
   ↓
Step 0: Generate Report (valuation + assumptions + sensitivity + limitations)
```

---

## 🤖 SECTION 2: FORWARD-LOOKING AGENT ARCHITECTURE

Now we design the agents working **forward** from user request to final output, based on the backward analysis.

### 🏗️ Agent Definitions

#### **Agent 0: CoordinatorAgent** (Hub - Orchestrates All Other Agents)
**Role**: Central coordinator that maintains full context, orchestrates specialist agents, and builds the complete valuation narrative

**Inputs**:
- User request (patent number + context)
- Results from all specialist agents

**Tools**:
- No direct tools - delegates to specialist agents
- Agent invocation logic
- Context aggregation functions

**Memory**:
- User's original request
- Complete history of all agent results
- Running assumption log (aggregated from all agents)
- Data quality tracking
- Decision rationale at each step

**Responsibilities**:
1. **Receive and Parse User Request** (like IntakeAgent role)
2. **Orchestrate Specialist Agents**:
   - Invoke IntakeAgent → PatentDataCollector → PatentAnalyzer
   - Invoke 3 parallel agents (MarketSizing, Financial, PatentStrength)
   - Wait for convergence, then invoke Attribution → Commercialization → DiscountRate → Valuation
3. **Maintain Complete Context**:
   - Store ALL intermediate results
   - Build cumulative assumption log
   - Track data quality flags
   - Document decision rationale at each step
4. **Invoke ReportGenerator with Full Story**:
   - Pass ALL agent results (not just final numbers)
   - Include narrative of what happened at each step
   - Include all assumptions, sources, quality flags
   - Include decision points and why certain paths were chosen

**Decision/Handoff**:
- Coordinator never returns "final_response" until ReportGenerator completes
- Coordinator invokes agents sequentially and in parallel as needed
- Coordinator passes complete context to ReportGenerator

**Output Message** (to ReportGenerator):
```json
{
  "next_action": "invoke_agent",
  "action_input": "ReportGeneratorAgent",
  "full_context": {
    "user_request": {
      "patent_number": "US10123456B2",
      "context": "portfolio_management",
      "optional_data": {...}
    },
    "patent_data": {...},
    "technology_analysis": {...},
    "market_sizing_results": {...},
    "financial_data_results": {...},
    "patent_strength_results": {...},
    "attribution_results": {...},
    "commercialization_results": {...},
    "discount_rate_results": {...},
    "valuation_results": {...},
    "all_assumptions": [...],
    "all_data_sources": [...],
    "all_quality_flags": [...],
    "decision_narrative": [
      "Step 1: User requested valuation for portfolio management (medium precision)",
      "Step 2: Patent data retrieved with 92% completeness",
      "Step 3: Technology identified as EV wireless charging",
      "Step 4: Parallel data collection initiated...",
      "Step 5: Attribution method chosen: Comparable License (royalty data available)",
      ...
    ]
  }
}
```

---

#### **Agent 1: IntakeAgent** (Specialist - Called by Coordinator)
**Role**: Parse and validate user inputs

**Inputs**:
- User message with patent number and context

**Tools**:
- Input validation function
- Context classification function (map user intent → precision level)

**Memory**:
- User's original request
- Extracted patent number
- Valuation context
- Optional user-provided data

**Responsibilities**:
1. Parse user request for patent number
2. Identify valuation context (litigation, M&A, portfolio, etc.)
3. Set precision requirements (high/medium/low)
4. Extract any optional data provided (revenue, TRL, portfolio info)
5. Validate minimum inputs present

**Decision/Handoff**:
- Return parsed data to Coordinator
- If inputs invalid/missing → Return error to Coordinator (which asks user)

**Output Message** (to Coordinator):
```json
{
  "next_action": "final_response",
  "content": {
    "patent_number": "US10123456B2",
    "context": "portfolio_management",
    "precision": "medium",
    "optional_data": {
      "revenue": null,
      "portfolio_size": 5,
      "target_market": "electric vehicles"
    },
    "status": "success"
  }
}
```

---

#### **Agent 2: PatentDataCollectorAgent** (Specialist - Called by Coordinator)
**Role**: Retrieve all patent data from USPTO and EPO APIs

**Inputs**:
- Patent number from Coordinator

**Tools**:
- `tool_uspto_patentsview_api(patent_number)` → Returns patent bibliographic data, citations, classifications
- `tool_epo_ops_api(patent_number)` → Returns INPADOC family data
- `tool_patent_validation(patent_number)` → Checks legal status (active/expired/abandoned)

**Memory**:
- Raw API responses
- Parsed patent data structure

**Responsibilities**:
1. Call USPTO PatentsView API for patent details
2. Call EPO OPS API for patent family
3. Validate patent is active and granted
4. Parse and structure patent data
5. Calculate basic metrics (age, remaining life, citation count, family size)
6. Assess data quality (completeness score)

**Decision/Handoff**:
- Return patent data to Coordinator
- If patent invalid/expired → Flag warning in response
- Include data quality score

**Output Message** (to Coordinator):
```json
{
  "patent_data": {
    "patent_number": "US10123456B2",
    "title": "Wireless Power Transfer System...",
    "grant_date": "2018-11-13",
    "expiration_date": "2038-11-13",
    "remaining_life_years": 13,
    "cpc_codes": ["H02J 50/10", "H01M 10/44"],
    "forward_citations": 47,
    "backward_citations": 28,
    "family_size": 12,
    "assignee": "AutoTech Inc.",
    "abstract": "...",
    "claims": [...],
    "legal_status": "active"
  },
  "data_quality_score": 92,
  "warnings": [],
  "next_action": "final_response",
  "content": "Patent data collection complete"
}
```

---

#### **Agent 3: PatentAnalyzerAgent** (Specialist - Called by Coordinator)
**Role**: Understand technology, identify applications, map to markets

**Inputs**:
- Patent data from PatentDataCollectorAgent
- Optional target market from user (IntakeAgent)

**Tools**:
- `tool_claim_parser(claims_text)` → Extract key technical features
- `tool_cpc_to_industry_mapper(cpc_codes)` → Map classification to industries
- `tool_citation_network_analyzer(forward_citations, backward_citations)` → Identify application domains
- LLM with technology analysis prompt

**Memory**:
- Patent technical summary
- Identified applications
- Target markets

**Responsibilities**:
1. Analyze patent claims to understand what technology does
2. Map CPC codes to industry categories
3. Analyze forward citations to see where technology is used
4. Identify potential applications and products
5. Map applications to market segments
6. Generate technology summary

**Decision/Handoff**:
- Return technology analysis to Coordinator
- If multiple markets possible and user didn't specify → Flag need for user input
- Coordinator will then invoke 3 parallel agents

**Output Message** (to Coordinator):
```json
{
  "technology_summary": "Wireless inductive charging system for electric vehicles using resonant coupling at 85 kHz frequency",
  "key_features": ["Resonant inductive coupling", "Foreign object detection", "Dynamic alignment compensation"],
  "potential_applications": [
    "Electric vehicle wireless charging",
    "Consumer electronics wireless charging",
    "Industrial equipment wireless power"
  ],
  "target_market": "Electric vehicle wireless charging infrastructure",
  "industry_classification": "Automotive - Electric Vehicles",
  "market_rationale": "Primary application based on claims focus and assignee product line",
  "next_action": "final_response",
  "content": "Technology analysis complete"
}
```

**Note**: Coordinator will then invoke 3 agents in parallel using `parallel_invoke`.

---

#### **Agent 4: MarketSizingAgent** (Specialist - Called by Coordinator in Parallel)
**Role**: Estimate revenue using bottom-up TAM/SAM/SOM approach

**Inputs**:
- Target market from PatentAnalyzerAgent
- Optional revenue data from user

**Tools**:
- `tool_web_search(query)` → Search for market size data
- `tool_census_data_api(naics_code)` → Get customer counts
- `tool_competitor_pricing_scraper(market)` → Get ARPU estimates
- LLM with market research prompt

**Memory**:
- Market size data sources
- TAM/SAM/SOM calculations
- Revenue projections by year

**Responsibilities**:
1. **Check if user provided revenue data**:
   - If YES → Use it directly, calculate growth projection, skip TAM/SAM/SOM
   - If NO → Proceed with bottom-up

2. **Calculate TAM**:
   - Search for market size data (free sources: industry reports, Wikipedia, trade associations)
   - If not found → Estimate from: Total_Customers × ARPU × Frequency
   - Validate data is recent (<2 years old)
   - Find market growth rate (CAGR)

3. **Calculate SAM**:
   - Apply geographic filter (where can product be sold?)
   - Apply distribution filter (what channels are accessible?)
   - Apply product fit filter (what % of TAM is addressable?)

4. **Calculate SOM**:
   - Estimate realistic market share
   - Apply adoption rate (penetration curve)

5. **Project Revenue**:
   - Calculate `Revenue_t = SOM × (1 + CAGR)^t` for each year t

6. **Assess data quality**:
   - Flag if market data is old (>2 years)
   - Flag if estimates are used instead of actual data

**Decision/Handoff**:
- If data quality good → Return revenue projections
- If data quality poor → Flag warning, return best estimate with wide range
- Return to parent (convergence point)

**Output Message**:
```json
{
  "revenue_projection": {
    "base_year_revenue": 10000000,
    "growth_rate_cagr": 0.18,
    "projections_by_year": [
      {"year": 1, "revenue": 11800000},
      {"year": 2, "revenue": 13924000},
      ...
    ]
  },
  "tam_sam_som": {
    "tam": 1200000000,
    "sam": 300000000,
    "som": 10000000,
    "market_share": 0.033
  },
  "data_sources": [
    {"source": "Allied Market Research", "year": 2024, "metric": "TAM", "quality": "high"},
    {"source": "Estimated from competitor analysis", "metric": "Market Share", "quality": "medium"}
  ],
  "data_quality_flags": [
    "Market share is estimated (no actual sales data available)"
  ],
  "assumptions": [
    {"assumption": "Market CAGR", "value": "18%", "source": "Allied Market Research 2024", "rationale": "Industry growth projection 2024-2030"}
  ],
  "next_action": "final_response",
  "content": "Revenue projection complete"
}
```

---

#### **Agent 5: FinancialDataCollectorAgent** (Specialist - Called by Coordinator in Parallel)
**Role**: Collect profit margin and WACC data

**Inputs**:
- Industry classification from PatentAnalyzerAgent
- Optional company name (from patent assignee)

**Tools**:
- `tool_sec_edgar_search(company_name)` → Search for 10-K filings
- `tool_sec_edgar_parser(filing_url)` → Extract financials from 10-K
- `tool_damodaran_data_lookup(industry)` → Get industry benchmarks
- `tool_royalty_rate_search(industry)` → Search academic papers, SEC exhibits for royalty rates

**Memory**:
- Company financials (if available)
- Industry benchmarks
- Royalty rate data

**Responsibilities**:
1. **Get Profit Margin**:
   - Try to find company 10-K filing (if assignee is public)
   - If found → Extract net profit margin
   - If not found → Use Damodaran industry benchmark
   - Document which source used

2. **Get Industry WACC**:
   - Lookup industry in Damodaran dataset
   - Get base WACC for industry
   - Document source

3. **Get Royalty Rate Benchmarks** (for IP contribution factor):
   - Search SEC EDGAR for licensing agreements in this industry
   - Search academic papers for royalty rate ranges
   - Compile typical range (low, median, high)

**Decision/Handoff**:
- Return financial data to parent (convergence point)

**Output Message**:
```json
{
  "profit_margin": {
    "value": 0.10,
    "source": "Industry benchmark - Damodaran Automotive 2024",
    "company_specific": false,
    "quality": "medium"
  },
  "industry_wacc": {
    "value": 0.095,
    "source": "Damodaran Automotive Industry WACC 2024",
    "quality": "high"
  },
  "royalty_rates": {
    "industry": "Automotive",
    "low": 0.01,
    "median": 0.03,
    "high": 0.05,
    "sources": [
      "SEC EDGAR exhibits analysis (15 agreements)",
      "LES Gold Book 2023 summary"
    ],
    "quality": "medium"
  },
  "assumptions": [
    {"assumption": "Profit Margin", "value": "10%", "source": "Damodaran industry average", "rationale": "Company-specific data not available (private company)"}
  ],
  "next_action": "final_response",
  "content": "Financial data collection complete"
}
```

---

#### **Agent 6: PatentStrengthAnalyzerAgent** (Specialist - Called by Coordinator in Parallel)
**Role**: Assess patent strength and calculate risk premium

**Inputs**:
- Patent data from PatentDataCollectorAgent
- Optional TRL/CRL from user

**Tools**:
- `tool_citation_strength_scorer(forward_citations, age)` → Normalize citations by age
- `tool_family_strength_scorer(family_size)` → Geographic coverage score
- `tool_claims_analyzer(claims)` → Count independent claims, assess breadth
- `tool_litigation_search(patent_number)` → Search PACER for litigation history

**Memory**:
- Patent strength score
- Risk premium components
- Litigation history

**Responsibilities**:
1. **Calculate Patent Strength Score**:
   - Citations component: Normalize forward citations by patent age
   - Family component: Score based on INPADOC family size
   - Claims component: Count independent claims (more = stronger)
   - Legal component: Check if all maintenance fees paid, no litigation

2. **Assess Technology Maturity** (for risk premium):
   - If user provided TRL → Use it
   - If not → Infer from patent data:
     - Patent age + assignee product launches → Estimate TRL
     - Forward citations in product patents → Market validation signal

3. **Assess Portfolio Dependency**:
   - If user provided portfolio size → Calculate dependency
   - If single patent → High dependency (+3-5% risk)
   - If one of many → Low dependency (+1-2% risk)

4. **Assess Litigation Risk**:
   - Search for litigation involving this patent
   - If pending → High risk (+3-5%)
   - If prior challenges → Medium risk (+2-4%)
   - If clean → Low risk (+0-1%)

5. **Calculate Patent Risk Premium**:
   ```
   Risk_Premium = Maturity_Risk + Dependency_Risk + Litigation_Risk
   ```

**Decision/Handoff**:
- Return strength analysis and risk premium to parent (convergence point)

**Output Message**:
```json
{
  "patent_strength_score": 75.1,
  "strength_components": {
    "citations": 24.0,
    "family": 18.75,
    "claims": 20.0,
    "legal": 13.0
  },
  "risk_premium": {
    "total": 0.06,
    "components": {
      "technology_maturity_risk": 0.03,
      "portfolio_dependency_risk": 0.02,
      "litigation_risk": 0.01
    }
  },
  "trl_assessment": {
    "estimated_trl": 8,
    "rationale": "Patent granted 7 years ago, assignee has commercial products using this technology (based on product literature)",
    "source": "Inferred from patent age and assignee activity"
  },
  "litigation_history": {
    "status": "No litigation found",
    "risk_level": "Low"
  },
  "assumptions": [
    {"assumption": "Technology Maturity Risk", "value": "+3%", "source": "TRL 8 (mature technology)", "rationale": "Commercial products exist using this patent"},
    {"assumption": "Portfolio Dependency Risk", "value": "+2%", "source": "User indicated 5 patents total", "rationale": "Core patent in small portfolio"}
  ],
  "next_action": "final_response",
  "content": "Patent strength analysis complete"
}
```

---

#### **Agent 7: AttributionEstimatorAgent** (Specialist - Called by Coordinator After Convergence)
**Role**: Calculate IP contribution factor using best available method

**Inputs** (from Coordinator, which collected from parallel agents):
- Royalty rate data from FinancialDataCollectorAgent (via Coordinator)
- Profit margin from FinancialDataCollectorAgent (via Coordinator)
- Portfolio context from user (via Coordinator)
- Patent data from PatentDataCollectorAgent (via Coordinator)

**Tools**:
- `tool_royalty_to_attribution(royalty_rate, profit_margin)` → Calculate IP contribution
- `tool_feature_value_estimator(patent_features, product_features)` → Feature analysis
- LLM with attribution reasoning prompt

**Memory**:
- Attribution method used
- IP contribution factor
- Calculation rationale

**Responsibilities**:
1. **Check Portfolio Context**:
   - If single patent → `IP_Contribution_Factor = 1.0` (done)
   - If multiple patents → Need attribution method

2. **Try Attribution Methods in Order**:

   **Method 1: Comparable License Royalty** (try first):
   - If royalty rate data available from FinancialDataCollectorAgent
   - Calculate: `IP_Contribution = Royalty_Rate / Profit_Margin`
   - Example: 3% royalty ÷ 10% margin = 0.30 (30% contribution)
   - Use this if royalty data quality is "medium" or higher

   **Method 2: Feature Value Analysis** (fallback):
   - Identify key patented features from patent claims
   - Estimate % of product value from these features
   - Use LLM to reason about feature importance
   - More subjective, but always feasible

3. **Validate Reasonableness**:
   - Check if IP contribution factor is in reasonable range (0.05 to 0.90)
   - If outside range → Flag warning

4. **Document Method Used**:
   - Log which method, why, what data sources

**Decision/Handoff**:
- Return IP contribution factor to Coordinator
- If calculation failed → Flag error for Coordinator to ask user

**Output Message** (to Coordinator):
```json
{
  "ip_contribution_factor": 0.30,
  "attribution_method": "Comparable License Royalty",
  "calculation": {
    "royalty_rate": 0.03,
    "profit_margin": 0.10,
    "result": 0.30
  },
  "rationale": "Industry royalty rates for automotive advanced features range 2-4%. Using median 3% divided by 10% profit margin yields 30% IP contribution. Conservative estimate given this is core technology patent in 5-patent portfolio.",
  "data_quality": "medium",
  "assumptions": [
    {"assumption": "IP Contribution Factor", "value": "30%", "source": "Royalty rate method (3% ÷ 10%)", "rationale": "Based on automotive industry licensing benchmarks"}
  ],
  "next_action": "final_response",
  "content": "IP attribution complete"
}
```

---

#### **Agent 8: CommercializationAssessorAgent** (Specialist - Called by Coordinator)
**Role**: Assess probability technology reaches market

**Inputs** (from Coordinator):
- TRL assessment from PatentStrengthAnalyzerAgent (via Coordinator)
- Technology summary from PatentAnalyzerAgent (via Coordinator)
- Assignee information from patent data (via Coordinator)

**Tools**:
- `tool_trl_to_probability_mapper(trl_level)` → Map TRL to probability
- `tool_assignee_product_search(assignee, technology)` → Search for commercial products
- `tool_web_search(assignee + product)` → Validate products exist

**Memory**:
- Commercialization probability
- Supporting evidence
- TRL/CRL assessment

**Responsibilities**:
1. **Check if Technology Already Commercialized**:
   - Search for assignee products using this technology
   - Check patent legal status (if being maintained → likely valuable)
   - If products found → `Commercialization_Probability = 1.0`

2. **If Not Yet Commercialized**:
   - Use TRL from PatentStrengthAnalyzerAgent (or ask user)
   - Map TRL to probability:
     - TRL 1-3 → 0.05-0.20
     - TRL 4-6 → 0.30-0.60
     - TRL 7-9 → 0.80-1.00

3. **Refine with Market Signals**:
   - Look for: press releases, product announcements, partnerships
   - Each positive signal → increase probability slightly
   - Each negative signal (competitors dominating) → decrease slightly

4. **Document Assessment**:
   - Log TRL/CRL level, probability, evidence

**Decision/Handoff**:
- Return commercialization probability to Coordinator

**Output Message** (to Coordinator):
```json
{
  "commercialization_probability": 1.0,
  "assessment_basis": "Technology already commercialized",
  "evidence": [
    "Assignee (AutoTech Inc.) has wireless charging products in market since 2020",
    "Patent maintained (all fees paid)",
    "Multiple press releases referencing this technology"
  ],
  "trl_level": 9,
  "assumptions": [
    {"assumption": "Commercialization Probability", "value": "100%", "source": "Commercial products exist", "rationale": "Technology deployed in assignee's product line"}
  ],
  "next_action": "final_response",
  "content": "Commercialization assessment complete"
}
```

---

#### **Agent 9: DiscountRateCalculatorAgent** (Specialist - Called by Coordinator)
**Role**: Calculate final discount rate

**Inputs** (from Coordinator):
- Industry WACC from FinancialDataCollectorAgent (via Coordinator)
- Risk premium from PatentStrengthAnalyzerAgent (via Coordinator)

**Tools**:
- `tool_discount_rate_calculator(wacc, risk_premium)` → Simple addition

**Memory**:
- Final discount rate
- Components

**Responsibilities**:
1. Calculate: `Discount_Rate = Industry_WACC + Patent_Risk_Premium`
2. Validate reasonableness (typically 10-25%)
3. Document components

**Decision/Handoff**:
- Return discount rate to Coordinator

**Output Message** (to Coordinator):
```json
{
  "discount_rate": 0.155,
  "components": {
    "industry_wacc": 0.095,
    "patent_risk_premium": 0.06
  },
  "assumptions": [
    {"assumption": "Discount Rate", "value": "15.5%", "source": "WACC 9.5% + Risk Premium 6%", "rationale": "Industry base rate plus patent-specific risks (maturity, dependency, litigation)"}
  ],
  "next_action": "final_response",
  "content": "Discount rate calculation complete"
}
```

---

#### **Agent 10: ValuationCalculatorAgent** (Specialist - Called by Coordinator)
**Role**: Calculate final DCF valuation

**Inputs** (from Coordinator):
- Revenue projections from MarketSizingAgent (via Coordinator)
- Profit margin from FinancialDataCollectorAgent (via Coordinator)
- IP contribution factor from AttributionEstimatorAgent (via Coordinator)
- Commercialization probability from CommercializationAssessorAgent (via Coordinator)
- Discount rate from DiscountRateCalculatorAgent (via Coordinator)
- Remaining patent life from PatentDataCollectorAgent (via Coordinator)

**Tools**:
- `tool_dcf_calculator(cash_flows, discount_rate, periods)` → NPV calculation
- `tool_sensitivity_analyzer(valuation, assumptions)` → ±20% sensitivity

**Memory**:
- Cash flow projections by year
- DCF calculation
- Valuation result

**Responsibilities**:
1. **Calculate Adjusted Cash Flows for Each Year**:
   ```
   For t = 1 to Remaining_Life:
     Revenue_t = Base_Revenue × (1 + Growth_Rate)^t
     Cash_Flow_t = Revenue_t × Profit_Margin × IP_Contribution × Commercialization_Probability
   ```

2. **Calculate NPV**:
   ```
   Patent_Value = Σ(t=1 to T) [Cash_Flow_t / (1 + Discount_Rate)^t]
   ```

3. **Run Sensitivity Analysis**:
   - Test ±20% changes in:
     - Discount rate
     - IP contribution factor
     - Growth rate
     - Profit margin
   - Calculate impact on valuation

4. **Generate Valuation Range**:
   - Low: Use conservative assumptions (high discount rate, low IP contribution)
   - Base: Use central assumptions
   - High: Use optimistic assumptions (low discount rate, high IP contribution)

**Decision/Handoff**:
- Return valuation results to Coordinator
- Coordinator will then invoke ReportGenerator with FULL context

**Output Message** (to Coordinator):
```json
{
  "valuation": {
    "base_case": 4285000,
    "low_case": 3420000,
    "high_case": 5350000,
    "currency": "USD"
  },
  "cash_flows_by_year": [
    {"year": 1, "revenue": 11800000, "cash_flow": 354000, "pv": 307000},
    {"year": 2, "revenue": 13924000, "cash_flow": 417700, "pv": 313000},
    ...
  ],
  "sensitivity_analysis": {
    "discount_rate": {"low": 5400000, "high": 3500000, "impact": "±22%"},
    "ip_contribution": {"low": 3428000, "high": 5142000, "impact": "±20%"},
    "growth_rate": {"low": 3700000, "high": 5100000, "impact": "±19%"},
    "profit_margin": {"low": 3428000, "high": 5142000, "impact": "±20%"}
  },
  "calculation_summary": {
    "method": "Income Method (Discounted Cash Flow)",
    "time_horizon_years": 13,
    "total_undiscounted_cash_flow": 12450000,
    "present_value": 4285000
  },
  "next_action": "final_response",
  "content": "Valuation calculation complete"
}
```

---

#### **Agent 11: ReportGeneratorAgent** (Specialist - Called by Coordinator with Full Context)
**Role**: Compile final report with valuation, assumptions, sources, sensitivity, AND complete narrative

**Inputs** (from Coordinator - this is the key difference):
- **FULL_CONTEXT**: All results from all agents (not just final numbers!)
  - User request
  - Patent data
  - Technology analysis
  - Market sizing results
  - Financial data results
  - Patent strength results
  - Attribution results
  - Commercialization results
  - Discount rate results
  - Valuation results
- **NARRATIVE**: Step-by-step story of decisions made
- **ALL_ASSUMPTIONS**: Aggregated from all agents
- **ALL_DATA_SOURCES**: Complete reference list
- **ALL_QUALITY_FLAGS**: Warnings and limitations

**Tools**:
- `tool_assumption_aggregator(all_agent_outputs)` → Collect all assumptions
- `tool_markdown_report_generator(template, data)` → Generate formatted report
- `tool_pdf_generator(markdown)` → Optional PDF export

**Memory**:
- Complete assumption log
- Data sources list
- Report structure

**Responsibilities**:
1. **Receive Full Context from Coordinator**:
   - ALL intermediate agent results (not just summaries)
   - Complete narrative of what happened
   - All assumptions already aggregated
   - All data sources already collected
   - All quality flags already compiled

2. **Generate Report Sections with Story**:
   - **Executive Summary**: Valuation range + confidence level + key findings
   - **Methodology Overview**: Why Income Method, what it means
   - **The Valuation Journey** (NARRATIVE SECTION - This is the key!):
     - "Step 1: We received your request to value patent US10123456B2 for portfolio management..."
     - "Step 2: We retrieved patent data from USPTO. The patent was granted in 2018..."
     - "Step 3: We analyzed the technology and identified it as wireless EV charging..."
     - "Step 4: We needed three pieces of information, so we searched in parallel..."
     - "Step 5: For market sizing, we found free market research showing TAM of $1.2B..."
     - "Step 6: For financial data, we used Damodaran's industry benchmarks because..."
     - "Step 7: For patent strength, we analyzed 47 forward citations and..."
     - "Step 8: We then calculated IP contribution. We tried to find comparable licenses..."
     - "Step 9: We assessed commercialization probability and found products already..."
     - "Step 10: We calculated the discount rate by adding industry WACC (9.5%) to..."
     - "Step 11: Finally, we calculated the valuation using all these inputs..."
   - **Detailed Results**:
     - Patent Overview
     - Market Analysis (with all intermediate calculations)
     - Financial Assumptions (with all lookups and sources)
     - Attribution Analysis (with method selection rationale)
     - Commercialization Assessment (with evidence)
     - Risk Analysis (with component breakdown)
     - Valuation Calculation (step-by-step DCF)
   - **Sensitivity Analysis**: Tables and charts
   - **Assumptions Log**: Complete table with categories
   - **Data Sources**: Complete reference list with URLs and dates
   - **Limitations**: What we couldn't do and why
   - **Appendix**: Raw data, API responses

3. **Format Output**:
   - Generate Markdown version
   - Optionally generate PDF
   - Optionally generate JSON (machine-readable)

**Decision/Handoff**:
- Final output → Return to user
- If user has follow-up questions → Route back to appropriate agent

**Output Message**:
```json
{
  "next_action": "final_response",
  "content": {
    "valuation_summary": {
      "patent_number": "US10123456B2",
      "valuation_base": "$4.29M",
      "valuation_range": "$3.42M - $5.35M",
      "confidence_level": "Medium-High",
      "method": "Income Method (DCF)",
      "date": "2025-11-12"
    },
    "report_markdown": "# Patent Valuation Report\n\n## Executive Summary\n\nPatent **US10123456B2** (Wireless Power Transfer System for Electric Vehicles) is valued at **$4.29 million** (base case) with a range of **$3.42M to $5.35M**...",
    "report_url": "/reports/US10123456B2_valuation_2025-11-12.md",
    "report_pdf": "/reports/US10123456B2_valuation_2025-11-12.pdf",
    "assumption_count": 18,
    "data_sources_count": 12,
    "data_quality_overall": 82
  }
}
```

---

### 🔄 Agent Flow Summary (Forward Execution with Coordinator)

```
USER INPUT
   ↓
[0] CoordinatorAgent (receives request)
   ↓
   ├─→ [1] IntakeAgent (parse inputs) → return to Coordinator
   ↓
   ├─→ [2] PatentDataCollectorAgent (get patent data) → return to Coordinator
   ↓
   ├─→ [3] PatentAnalyzerAgent (analyze technology) → return to Coordinator
   ↓
   ├─→ (Coordinator invokes 3 agents in parallel)
   ├─→ [4] MarketSizingAgent ──────────────┐
   ├─→ [5] FinancialDataCollectorAgent ────┼─→ return to Coordinator
   └─→ [6] PatentStrengthAnalyzerAgent ────┘
   ↓
   ├─→ [7] AttributionEstimatorAgent → return to Coordinator
   ↓
   ├─→ [8] CommercializationAssessorAgent → return to Coordinator
   ↓
   ├─→ [9] DiscountRateCalculatorAgent → return to Coordinator
   ↓
   ├─→ [10] ValuationCalculatorAgent → return to Coordinator
   ↓
   └─→ [11] ReportGeneratorAgent (receives FULL context from Coordinator)
       ↓
       Generate complete narrative report
       ↓
   ↓
CoordinatorAgent returns final report to User
   ↓
USER OUTPUT (Report + Valuation + Complete Story)
```

**Key Difference**: Coordinator maintains ALL context and passes the complete story to ReportGenerator, not just final numbers.

---

### 🏛️ Topology Structure (Marsys) - Hub-and-Spoke with Coordinator

```python
topology = {
    "agents": [
        "User",
        "CoordinatorAgent",  # Hub
        "IntakeAgent",
        "PatentDataCollectorAgent",
        "PatentAnalyzerAgent",
        "MarketSizingAgent",
        "FinancialDataCollectorAgent",
        "PatentStrengthAnalyzerAgent",
        "AttributionEstimatorAgent",
        "CommercializationAssessorAgent",
        "DiscountRateCalculatorAgent",
        "ValuationCalculatorAgent",
        "ReportGeneratorAgent"
    ],
    "flows": [
        # User <-> Coordinator
        "User -> CoordinatorAgent",
        "CoordinatorAgent -> User",

        # Coordinator -> Specialist Agents (hub-and-spoke)
        "CoordinatorAgent -> IntakeAgent",
        "IntakeAgent -> CoordinatorAgent",

        "CoordinatorAgent -> PatentDataCollectorAgent",
        "PatentDataCollectorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> PatentAnalyzerAgent",
        "PatentAnalyzerAgent -> CoordinatorAgent",

        "CoordinatorAgent -> MarketSizingAgent",
        "MarketSizingAgent -> CoordinatorAgent",

        "CoordinatorAgent -> FinancialDataCollectorAgent",
        "FinancialDataCollectorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> PatentStrengthAnalyzerAgent",
        "PatentStrengthAnalyzerAgent -> CoordinatorAgent",

        "CoordinatorAgent -> AttributionEstimatorAgent",
        "AttributionEstimatorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> CommercializationAssessorAgent",
        "CommercializationAssessorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> DiscountRateCalculatorAgent",
        "DiscountRateCalculatorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> ValuationCalculatorAgent",
        "ValuationCalculatorAgent -> CoordinatorAgent",

        "CoordinatorAgent -> ReportGeneratorAgent",
        "ReportGeneratorAgent -> CoordinatorAgent"
    ],
    "rules": [
        "timeout(600)",  # 10 minute max
        "max_agents(20)"  # Increased for parallel execution
    ]
}
```

**Pattern**: Pure hub-and-spoke with CoordinatorAgent as the central hub. All specialist agents return results to Coordinator, which maintains context and orchestrates the workflow.

---

### 🎯 Key Design Decisions Captured

1. **Parallel Data Collection**: PatentAnalyzerAgent spawns 3 parallel agents (MarketSizing, Financial, Strength) for efficiency

2. **Convergence Point**: AttributionEstimatorAgent waits for all 3 parallel branches before proceeding

3. **Sequential Processing**: After convergence, remainder is sequential (each agent needs output of previous)

4. **User Interaction Points**:
   - IntakeAgent: Get missing inputs
   - PatentDataCollectorAgent: Warn if patent invalid
   - PatentAnalyzerAgent: Clarify target market if ambiguous
   - All quality warnings route through User node for approval

5. **Memory Strategy**: Each agent maintains conversation memory with previous agents' outputs, allowing assumption aggregation at the end

6. **Tool Distribution**: Each agent has specific tools for its task (API calls, calculations, web search, LLM analysis)

7. **Error Handling**: Quality flags propagate through the system, accumulated in final report

---

**Document Status**: ✅ Complete - Ready for Review and Refinement
**Next Action**: Review backward deduction logic and forward agent design, iterate as needed, then implement
