# 03 - Patent Valuation Methodology Using Free Data Sources Only

**Purpose**: Comprehensive methodology for patent valuation addressing real-world complexities, using ONLY free and publicly available data sources.

**Scope**: Income Method valuation with three critical enhancements:
1. Portfolio bundling (multiple patents per product)
2. Commercialization probability assessment
3. Blocking potential valuation

**Constraint**: $0 budget - NO paid databases, NO consulting reports, NO commercial APIs

**Date**: November 2025

---

## Table of Contents

1. [Methodology Overview & Decision Framework](#1-methodology-overview--decision-framework)
2. [Portfolio Attribution (Multi-Patent Products)](#2-portfolio-attribution-multi-patent-products)
3. [Commercialization Probability Assessment](#3-commercialization-probability-assessment)
4. [Market Size Estimation (Bottom-Up ONLY)](#4-market-size-estimation-bottom-up-only)
5. [Blocking Potential Valuation](#5-blocking-potential-valuation)
6. [Complete Valuation Integration](#6-complete-valuation-integration)
7. [Free Data Sources Catalog](#7-free-data-sources-catalog)
8. [Decision Boundaries & Quality Thresholds](#8-decision-boundaries--quality-thresholds)

---

## 1. Methodology Overview & Decision Framework

### 1.1 Complete Valuation Formula

```
Patent_Value = Commercialization_Value + Blocking_Option_Value

where:

Commercialization_Value = Σ [(Revenue_t × Profit_Margin × IP_Factor × Comm_Prob) / (1 + r)^t]
                          for t = 1 to Remaining_Patent_Life

Blocking_Option_Value = Design_Around_Cost × Competitor_Probability × Capture_Rate
```

### 1.2 Required Inputs & Data Sources

| Input | Free Source | Fallback if Unavailable |
|-------|-------------|------------------------|
| **Revenue_t** | Bottom-up market sizing (Census, BLS) | Estimate from analogous markets |
| **Profit_Margin** | Public company 10-K filings | Industry averages (academic papers) |
| **IP_Factor** | SEC EDGAR licensing agreements | Feature value analysis (Section 2) |
| **Comm_Prob** | TRL/CRL assessment (patent document) | Conservative default: 50% |
| **Discount Rate** | Damodaran WACC + risk premium | Base: 12% + 6% = 18% |
| **Design_Around_Cost** | Technical analysis + R&D benchmarks | Conservative: $2M-10M |

### 1.3 Methodology Decision Tree

```
START: Patent Valuation Request
│
├─ STEP 1: Assess Data Availability
│  │
│  ├─ Is target product/market clearly defined?
│  │  ├─ NO → Ask stakeholder for clarification
│  │  └─ YES → Continue
│  │
│  ├─ Is company revenue data available?
│  │  ├─ YES → Use actual revenue + bottom-up validation
│  │  └─ NO → Build bottom-up market size (Section 4)
│  │
│  └─ Are there comparable public companies?
│     ├─ YES → Extract benchmarks from 10-K filings
│     └─ NO → Use academic papers + industry averages
│
├─ STEP 2: Portfolio Attribution (Section 2)
│  │
│  ├─ Is this a single patent product?
│  │  ├─ YES → IP_Factor = full product contribution
│  │  └─ NO → Determine portfolio contribution
│  │
│  ├─ Can we find comparable licensing agreements (SEC)?
│  │  ├─ YES → Extract royalty rates, apply attribution
│  │  └─ NO → Use Feature Value Analysis (Section 2.3)
│  │
│  └─ Classify patent type (Core/Improvement/Defensive)
│     → Apply weighting factors (Section 2.4)
│
├─ STEP 3: Commercialization Probability (Section 3)
│  │
│  ├─ Assess TRL from patent document (1-9 scale)
│  ├─ Assess CRL from company/market data (1-9 scale)
│  ├─ Calculate base probability from TRL×CRL matrix
│  └─ Apply multipliers (patent quality, assignee strength)
│
├─ STEP 4: Market Size Estimation (Section 4)
│  │
│  ├─ Define market boundaries (geography, customer segment)
│  ├─ Count customers (Census/government data)
│  ├─ Estimate ARPU (competitor pricing research)
│  ├─ Calculate TAM (customers × ARPU)
│  ├─ Apply filters for SAM (company reach)
│  └─ Estimate SOM (realistic market share)
│
├─ STEP 5: DCF Calculation
│  │
│  ├─ Project revenue over remaining patent life
│  ├─ Apply profit margin
│  ├─ Apply IP attribution factor
│  ├─ Apply commercialization probability
│  └─ Discount to present value
│
├─ STEP 6: Blocking Value (Section 5)
│  │
│  ├─ Identify potential blocked competitors
│  ├─ Assess design-around difficulty (1-5 scale)
│  ├─ Estimate design-around cost
│  ├─ Calculate probability competitor needs license
│  └─ Compute expected blocking value
│
└─ STEP 7: Total Value + Sensitivity Analysis
   │
   ├─ Sum commercialization + blocking value
   ├─ Calculate valuation range (±30% sensitivity)
   ├─ Document all assumptions
   └─ Assign confidence level (Low/Medium/High)
```

---

## 2. Portfolio Attribution (Multi-Patent Products)

### 2.1 The Reality Check

**Fact**: Products are almost never protected by a single patent.

**Examples**:
- Smartphone: 250,000+ patents
- Electric Vehicle: 50-200 patents
- Pharmaceutical drug: 5-20 patents (compound + formulation + process + delivery)
- Medical device: 10-50 patents

**Question**: If valuing Patent X that is one of 10 patents covering a product, what is Patent X's contribution?

**Answer**: Use three-step apportionment framework.

---

### 2.2 Step 1: Determine Total Portfolio Contribution

**Objective**: What is the total royalty rate (or contribution factor) for ALL patents covering the product/feature?

#### **Method 1: Feature Value Analysis** (NO data required, pure analysis)

**When to Use**: Always available, no external data needed.

**Process**:
1. Identify product features
2. Find comparable products WITH and WITHOUT the feature
3. Calculate price differential
4. Attribute differential to patent portfolio

**Example**:
```
Product: Wireless headphones

Competitor Product A (basic): $150
Competitor Product B (with noise cancellation): $280
Price premium: $130 (87%)

Analysis:
- Noise cancellation is the differentiating feature
- Feature is covered by 4 patents (including target patent)

Total Portfolio Contribution:
- If customers pay $130 more for feature → Feature value = $130
- As % of total product: $130 / $280 = 46% of product value
- Portfolio royalty equivalent: ~46% of profit margin

If profit margin = 20%, then:
Portfolio contribution = 46% × 20% = 9.2% royalty rate equivalent

Decision: Total portfolio royalty = 9.2%
```

**Boundary Conditions**:
- Feature premium must be >10% to be meaningful
- Need at least 2 comparable products (with/without feature)
- IF no comparables exist → Use conservative default: 15-25% royalty

---

#### **Method 2: SEC EDGAR Licensing Agreement Search** (FREE, higher accuracy)

**When to Use**: When comparable technology licensing exists in public companies.

**Process**:
1. Go to SEC EDGAR (https://www.sec.gov/edgar/searchedgar/companysearch.html)
2. Search for companies in same industry/technology
3. Look for Exhibit 10.* (Material Contracts) containing "license" or "royalty"
4. Extract royalty rates from disclosed agreements
5. Adjust for technology similarity and time

**Step-by-Step**:

**A. Identify Target Companies**:
```
Technology field: Wireless charging for EVs
Related public companies:
- WiTricity Corporation (if public) - wireless power transfer
- Qualcomm (10-K section on wireless charging licensing)
- Tesla (10-K for automotive technology)
- ChargePoint Holdings - EV charging infrastructure
```

**B. Search EDGAR**:
```
Search: Company name + "10-K" or "8-K"
Filter exhibits: Look for "Exhibit 10" (Material Contracts)
Keywords in exhibits: "license", "patent", "royalty", "technology"
```

**C. Extract Royalty Rates**:
```
Example from actual SEC filing:

"Licensee shall pay Licensor a royalty of [***]% of Net Sales
of Licensed Products in the Field."

Note: [***] = Redacted under confidential treatment
BUT many agreements disclose ranges or benchmarks
```

**D. Build Royalty Database** (Manual Collection):
```
| Filing Date | Company | Technology | Royalty Rate | Notes |
|-------------|---------|------------|--------------|-------|
| 2022-03-15 | TechCo | Wireless power | 3.5% | Automotive sector |
| 2023-06-20 | PowerCorp | Battery tech | 2.8% | EV batteries |
| 2021-11-10 | ChargeCo | Charging infra | 4.2% | Commercial charging |

Average royalty: (3.5% + 2.8% + 4.2%) / 3 = 3.5%
Use: 3.5% as portfolio royalty rate benchmark
```

**Boundary Conditions**:
- Need minimum 3 comparable agreements for reliability
- Agreements must be <5 years old (older = less relevant)
- IF <3 comparables found → Fall back to Method 1 or academic papers

---

#### **Method 3: Academic Papers & Industry Studies** (FREE, moderate accuracy)

**When to Use**: When Methods 1-2 insufficient, need industry benchmarks.

**Process**:
1. Search Google Scholar (scholar.google.com)
2. Keywords: "[industry] patent licensing royalty rates"
3. Filter by recent papers (last 5 years)
4. Extract reported ranges

**Example Search**:
```
Query: "automotive patent licensing royalty rates"

Result 1: Academic paper - "Patent Licensing in the Automotive Industry"
Findings: "Average royalty rates for automotive technology patents
          range from 1.5% to 4.5%, with median of 2.8%"
Source: Journal of Industrial Economics (2023)

Result 2: LES Survey Summary (free executive summary)
Findings: "High-tech sector median royalty: 5%"
Source: LES 2021 Survey press release

Result 3: PhD Dissertation
Findings: "Pharmaceutical licensing: 2-10%, average 5.5%"
Source: University thesis (2022)
```

**Industry Benchmark Table** (from research):

| Industry | Royalty Range | Median | Source |
|----------|---------------|--------|--------|
| Pharmaceuticals | 2-10% | 5.5% | Academic papers |
| Software/IT | 5-15% | 8% | LES survey (free summary) |
| Automotive | 1-5% | 2.8% | Academic papers |
| Medical Devices | 3-8% | 5% | Academic papers |
| Consumer Electronics | 2-6% | 4% | Academic papers |
| Telecom/Standards | 3-7% | 5% | Academic papers |

**Boundary Conditions**:
- Use median, not average (less influenced by outliers)
- Adjust for technology maturity (new tech +1-2%, mature tech -1%)
- IF no industry data → Conservative default: 5% royalty

---

### 2.3 Step 2: Classify Target Patent Within Portfolio

**Objective**: Is target patent Core, Improvement, Defensive, or Minor?

#### **Classification Criteria**:

| Patent Type | Claim Characteristics | Citation Pattern | Typical % of Portfolio Value |
|-------------|----------------------|------------------|------------------------------|
| **Core/Platform** | Broad independent claims (1-3), low dependency | High forward citations (>30), low backward | 40-60% |
| **Improvement** | Narrow claims citing core patent | Medium citations (10-30), high backward | 15-25% |
| **Defensive/Blocking** | Marginal innovation, specific use case | Low forward (<10), medium backward | 10-20% |
| **Minor/Incremental** | Highly specific claims, narrow scope | Very low forward (<5) | 5-10% |

#### **How to Classify** (Using FREE USPTO Data):

**A. Analyze Claims**:
```
Access: USPTO PatentsView API or Google Patents
Read: Independent claims (Claim 1, Claim 2, etc.)

Core Patent Indicators:
- Few independent claims (1-3) that are broad
- Many dependent claims (10-30) hanging off them
- Claims don't cite other patents heavily

Improvement Patent Indicators:
- Independent claims cite "as in claim X of Patent Y"
- Continuation-in-part (CIP) of earlier patent
- Specific improvements to known methods

Example:
Claim 1: "A wireless charging system comprising..."  [BROAD → Core]
vs.
Claim 1: "The system of US10123456, further comprising a safety circuit..." [NARROW → Improvement]
```

**B. Check Citation Patterns**:
```
Use: USPTO PatentsView API (free)

Forward citations (who cites this patent):
- >30 citations → Likely core patent (influential)
- 10-30 citations → Improvement patent
- <10 citations → Defensive/minor

Backward citations (what this patent cites):
- <5 citations → Novel core invention
- 5-15 citations → Building on existing art (improvement)
- >15 citations → Incremental (lots of prior art)
```

**C. Check Prosecution History**:
```
Access: USPTO Patent Center (public.resource.org/patent/)

Core Patent Indicators:
- Original application (not continuation)
- Few office action rejections (examiner found it novel)
- Allowed claims stayed broad

Improvement Patent Indicators:
- Continuation-in-part (CIP) of earlier patent
- Many office actions (struggled to differentiate)
- Final claims narrower than filed
```

**Decision Matrix**:

```
IF (Independent_Claims ≤ 3 AND Forward_Citations > 30 AND NOT_Continuation):
    Classification = CORE
    Base_Weight = 50%

ELIF (Cites_Parent_Patent AND Forward_Citations 10-30):
    Classification = IMPROVEMENT
    Base_Weight = 20%

ELIF (Forward_Citations < 10 AND Highly_Specific_Claims):
    IF (Blocks_Competitor_Approach):
        Classification = DEFENSIVE
        Base_Weight = 15%
    ELSE:
        Classification = MINOR
        Base_Weight = 8%

ELSE:
    Classification = IMPROVEMENT (default conservative)
    Base_Weight = 20%
```

---

### 2.4 Step 3: Calculate Target Patent's Contribution

**Formula**:
```
IP_Contribution_Factor = Total_Portfolio_Royalty × Normalized_Weight

where:
Normalized_Weight = (Base_Weight × Strength_Multiplier) / Sum_of_All_Patent_Weights
```

#### **Strength Multiplier Calculation**:

**Based on patent metrics** (all FREE from USPTO):

```
Strength_Multiplier = 1.0 × Citation_Factor × Family_Factor × Claim_Factor

Citation_Factor:
- High citations (>40): 1.3×
- Medium (15-40): 1.1×
- Low (<15): 0.9×

Family_Factor (INPADOC size from EPO OPS, free):
- Large family (>15 countries): 1.2×
- Medium (5-15): 1.0×
- Small (<5): 0.9×

Claim_Factor (independent claims count):
- Many (>5): 1.1×
- Normal (2-5): 1.0×
- Single (1): 0.9×

Example:
Target patent has 47 forward citations, family size 12, 3 independent claims
Strength_Multiplier = 1.0 × 1.3 × 1.0 × 1.0 = 1.3×
```

#### **Complete Example**:

```
SCENARIO: Wireless EV charging patent portfolio (5 patents)

STEP 1: Total Portfolio Royalty
Method 2 (SEC EDGAR): Found 3 comparable licenses, average 3.5%
Total_Portfolio_Royalty = 3.5%

STEP 2: Classify Each Patent
Patent 1 (target): Core power transfer → Base_Weight = 50%, Multiplier = 1.3×
Patent 2: Efficiency improvement → Base_Weight = 20%, Multiplier = 1.1×
Patent 3: Safety control → Base_Weight = 20%, Multiplier = 1.0×
Patent 4: Compact design (defensive) → Base_Weight = 15%, Multiplier = 0.9×
Patent 5: Heat dissipation (minor) → Base_Weight = 10%, Multiplier = 0.8×

STEP 3: Calculate Weighted Contributions
Patent 1: 50% × 1.3 = 65
Patent 2: 20% × 1.1 = 22
Patent 3: 20% × 1.0 = 20
Patent 4: 15% × 0.9 = 13.5
Patent 5: 10% × 0.8 = 8
Total: 128.5

STEP 4: Normalize
Patent 1 weight = 65 / 128.5 = 50.6%

STEP 5: Calculate IP Contribution Factor
IP_Factor = 3.5% × 50.6% = 1.77%

INTERPRETATION:
Out of the product's profit, 1.77% is attributable to Patent 1.
This accounts for:
- Patent 1 being core patent (50% of portfolio)
- Patent 1 being stronger than others (1.3× multiplier)
- Portfolio total value being 3.5% (from market comparables)
```

### 2.5 Decision Boundaries & Quality Gates

| Metric | Acceptable Range | Warning Level | Action if Outside |
|--------|------------------|---------------|-------------------|
| **Total Portfolio Royalty** | 1-15% | <1% or >15% | Re-verify comparables or method |
| **Number of Comparables (SEC)** | ≥3 | 1-2 | Supplement with academic data |
| **Patent Classification Confidence** | Clear indicators | Ambiguous | Use conservative (Improvement) |
| **Strength Multiplier** | 0.8-1.5× | <0.7× or >1.6× | Re-check metrics, possible outlier |
| **IP Contribution Factor (final)** | 0.5-8% | <0.3% or >10% | Red flag - review assumptions |

**Red Flags**:
- IP Factor >10%: Very rare unless single patent product or pharma
- IP Factor <0.3%: May be undervaluing, check if too many patents in bundle
- No SEC comparables AND no academic data: High uncertainty, document clearly

---

## 3. Commercialization Probability Assessment

### 3.1 Why This Matters

**Reality**: Many patents never lead to products.

**Data Point** (from research): "Being refused a patent reduced the probability of attempting market launch by 13 percentage points."

**Implication**: Must adjust expected cash flows by probability of commercialization.

---

### 3.2 TRL (Technology Readiness Level) Assessment

**Source**: Patent document analysis (FREE)

**TRL Scale** (NASA standard, 1-9):

| TRL | Description | Patent Indicators | Commercialization Probability |
|-----|-------------|------------------|-------------------------------|
| 1-2 | Basic research, concept | Abstract describes problem, no working examples | <10% |
| 3-4 | Proof of concept, lab validation | Experimental results, lab-scale embodiments | 15-25% |
| 5-6 | Prototype demonstration | Working prototype described, field testing mentioned | 40-60% |
| 7-8 | Operational prototype, system complete | Product-ready design, performance data, pilot production | 70-85% |
| 9 | Commercial product | Patent references commercial product in specification | 90-95% |

**How to Assess from Patent Document**:

```
Step 1: Read Patent Abstract & Background
Question: What problem does this solve? How mature is solution?

Step 2: Count Embodiments in Detailed Description
- 1-2 embodiments, mostly theoretical → TRL 3-4
- 3-5 embodiments, lab testing described → TRL 5-6
- 5+ embodiments, field testing, optimization → TRL 7-8

Step 3: Check for Commercial Indicators
Keywords to search in patent text:
- "prototype", "tested in", "field trial" → TRL 6-7
- "commercial", "production", "manufacturing" → TRL 8-9
- "simulation", "theoretical", "concept" → TRL 2-4

Step 4: Look at Claims Specificity
- Broad, conceptual claims → Early TRL (3-5)
- Specific, detailed claims with exact parameters → Late TRL (6-9)

Example:
Patent text includes: "A prototype system was tested in 15 electric vehicles
over 6 months, demonstrating 95% efficiency in real-world conditions."
→ TRL = 7 (operational prototype)
```

---

### 3.3 CRL (Commercial Readiness Level) Assessment

**Source**: Company/market research (FREE - web search, LinkedIn, news)

**CRL Scale** (1-9, developed by Abbas & Nomvar):

| CRL | Description | Indicators (Free Research) | Probability Boost |
|-----|-------------|---------------------------|-------------------|
| 1-2 | Hypothetical, concept | No company mentions, academic-only | +0% |
| 3-4 | Proof of concept, customer interest | Press releases mention "exploring", "pilot" | +10% |
| 5-6 | Commercial trial, early customers | News of paying customers, small revenue | +20% |
| 7-8 | Market presence, scaling production | Multiple customers, growth announcements | +30% |
| 9 | Market leader | Dominant player, sustained revenue | +35% |

**How to Assess (Free Research)**:

```
Step 1: Search Company Website + Press Releases
Look for:
- Product pages featuring the technology → CRL 6+
- "Coming soon" or "Beta testing" → CRL 4-5
- No product mention → CRL 1-3

Step 2: LinkedIn Company Page
Check:
- Job postings for "production", "manufacturing" roles → CRL 7+
- Job postings for "R&D", "research" roles only → CRL 3-5
- Company size growing → CRL 6+

Step 3: News Articles (Google News search)
Keywords: [company name] + [technology]
Positive indicators:
- "Company X launches product Y" → CRL 7+
- "Company X secures customers" → CRL 6+
- "Company X developing technology" → CRL 4-5

Step 4: SEC Filings (if public company)
Search 10-K for technology mentions:
- "Revenue from Product X" → CRL 8-9
- "Development stage" → CRL 4-6
- Not mentioned → CRL 1-3
```

---

### 3.4 Base Commercialization Probability Matrix

**Lookup Table** (TRL × CRL):

|         | CRL 1-3 | CRL 4-6 | CRL 7-9 |
|---------|---------|---------|---------|
| **TRL 1-3** | 5%  | 10% | 15% |
| **TRL 4-6** | 15% | 40% | 55% |
| **TRL 7-9** | 30% | 65% | 85% |

**Usage**:
```
Example:
TRL = 7 (from patent document analysis)
CRL = 5 (from company research - pilot customers)

Base_Probability = 65% (from matrix)
```

---

### 3.5 Adjustment Multipliers

**Apply research-based factors** to refine probability:

#### **Factor 1: Patent Quality Score** (from USPTO data)

```
Quality_Score = (Citations_Score + Family_Score + Claims_Score) / 3

Citations_Score (forward citations, normalized by age):
- (Citations / Age_in_Years) > 5 → Score = 100
- 2-5 → Score = 75
- <2 → Score = 50

Family_Score (INPADOC size from EPO OPS):
- Family > 15 countries → Score = 100
- 5-15 → Score = 75
- <5 → Score = 50

Claims_Score (independent claims):
- >5 independent claims → Score = 100
- 2-5 → Score = 75
- 1 → Score = 50

Quality_Multiplier:
- Quality_Score > 85: 1.15×
- Quality_Score 60-85: 1.05×
- Quality_Score < 60: 0.95×
```

#### **Factor 2: Assignee Strength** (free research)

```
Assignee Type:
- Fortune 500 company → 1.20×
- Mid-size company (500-5000 employees) → 1.10×
- Small company (<500 employees) → 1.00×
- Startup (<50 employees) → 0.90×
- Individual inventor → 0.70×

Source: LinkedIn company page, Wikipedia, Crunchbase (free)
```

#### **Factor 3: Market Size** (from Section 4 bottom-up analysis)

```
TAM (Total Addressable Market):
- TAM > $5B → 1.15×
- TAM $1B-5B → 1.05×
- TAM < $1B → 0.95×
```

#### **Factor 4: Complementary Portfolio** (from USPTO)

```
Number of Related Patents (same CPC code):
- >10 related patents → 1.15× (strong portfolio support)
- 3-10 related → 1.05×
- <3 related → 0.95× (isolated patent)

Source: USPTO PatentsView API search by CPC code
```

---

### 3.6 Final Commercialization Probability

**Formula**:
```
Final_Probability = Base_Probability × Quality_Mult × Assignee_Mult × Market_Mult × Portfolio_Mult

THEN: Cap at 95% maximum (never 100% certainty)
```

**Example**:
```
Base Probability (TRL 7, CRL 5): 65%
Quality Multiplier (Quality Score 73): 1.05×
Assignee Multiplier (mid-size company): 1.10×
Market Multiplier (TAM $3B): 1.05×
Portfolio Multiplier (8 related patents): 1.05×

Final = 65% × 1.05 × 1.10 × 1.05 × 1.05
      = 65% × 1.27
      = 82.6%

Use: 83% commercialization probability
```

### 3.7 Decision Boundaries

| Metric | Acceptable | Warning | Action |
|--------|------------|---------|--------|
| **Base Probability** | 15-85% | <15% or >85% | Re-check TRL/CRL assessment |
| **Final Probability** | 20-95% | <20% | Flag as high-risk, use conservative valuation |
| **TRL-CRL Gap** | ≤2 levels | >3 levels | Investigate mismatch (tech ready but no market?) |
| **Multipliers Product** | 0.85-1.35× | <0.75× or >1.5× | Re-verify each factor |

---

## 4. Market Size Estimation (Bottom-Up ONLY)

### 4.1 TAM-SAM-SOM Framework

**Definitions**:
- **TAM** (Total Addressable Market): Total demand if 100% market captured
- **SAM** (Serviceable Available Market): Realistic addressable portion
- **SOM** (Serviceable Obtainable Market): Achievable market share

**CRITICAL RULE**: ALWAYS build bottom-up. NEVER use top-down from paid reports.

---

### 4.2 Bottom-Up TAM Construction (Step-by-Step)

#### **Step 1: Define Market Boundaries**

**Questions to Answer**:
1. What is the EXACT product enabled by the patent?
2. Who are the END CUSTOMERS? (consumers, businesses, governments?)
3. What GEOGRAPHY? (US only, global, specific countries?)
4. What TIME HORIZON? (when will market reach this size?)

**Example**:
```
Patent: Wireless EV charging pad
Product: Home wireless charging installation
Customers: EV owners with home charging capability
Geography: United States only
Time Horizon: 2030 (5 years from now, within patent life)
```

---

#### **Step 2: Count Potential Customers (FREE SOURCES)**

**For Consumer Markets**:

**A. US Census Bureau** (census.gov) - FREE, HIGH QUALITY
```
Navigate to: data.census.gov
Search: Relevant demographic/household data

Example Searches:
- "Households by income bracket" → How many can afford product?
- "Homeownership rates" → How many own homes?
- "Vehicle ownership" → How many own vehicles?

Example for EV charging:
Search: "Electric vehicle registrations by state"
Alternative: "Total registered vehicles" × "EV adoption rate"

Result:
US total vehicles (2024): 280 million (Census/BLS)
EV % (2024): 1.5% = 4.2 million EVs
Projected 2030: Use historical growth rate

2019: 1.0M EVs
2024: 4.2M EVs
Growth rate: 33% CAGR

2030 projection: 4.2M × (1.33)^6 = 20 million EVs

Further filter:
Home charging capable (own home + garage): 75% of EV owners
Potential customers = 20M × 0.75 = 15 million

Source: US Census American Community Survey (free)
```

**B. Government Statistical Agencies** - FREE

| Country | Agency | URL | Data Available |
|---------|--------|-----|----------------|
| USA | Census Bureau | census.gov | Demographics, housing, business |
| USA | BLS | bls.gov | Employment, industries |
| USA | Department of Energy | energy.gov/data | Energy, vehicles, environment |
| EU | Eurostat | ec.europa.eu/eurostat | EU-wide statistics |
| UK | ONS | ons.gov.uk | UK demographics, economy |
| Global | World Bank | data.worldbank.org | Global development indicators |

**For B2B Markets**:

**C. Business Counts** - FREE
```
Source: US Census Bureau - County Business Patterns
URL: census.gov/programs-surveys/cbp.html

Search by NAICS code (industry classification):
Example: Manufacturing companies with 500+ employees

Steps:
1. Identify NAICS code for target industry
   - Search "NAICS codes" + industry name
   - Example: "NAICS code automotive manufacturing" → 3361

2. Access County Business Patterns data
   - Filter by NAICS code
   - Filter by employee size
   - Get count of establishments

Result Example:
NAICS 3361 (Motor Vehicle Manufacturing):
- Total establishments: 1,200
- Establishments with 500+ employees: 120
- Target customers: 120 companies

Alternative source: LinkedIn Sales Navigator (free browsing)
- Search: Companies in "[industry]" with "[size]" employees
- Rough count from search results
```

---

#### **Step 3: Estimate ARPU (Average Revenue Per User) - FREE**

**Method A: Competitor Pricing Research** (web scraping)

```
Process:
1. Identify 5-10 competitor products or similar products
2. Record publicly listed prices
3. Calculate average

Sources (all free):
- Company websites (product pages)
- Amazon.com (search for similar products)
- Best Buy, Walmart, etc. (retailer websites)
- Press releases announcing pricing

Example (Wireless EV Charging):
Search: "wireless EV charging pad price"

Results:
- Company A website: $1,200-1,500 (residential)
- Company B: $1,800 (premium)
- Company C: $1,000 (basic model)
- Amazon listings: $800-2,000 range

Analysis:
Low-end: $800
Mid-range: $1,200-1,500
High-end: $1,800-2,000

For TAM calculation, use mid-range: $1,400
(Conservative: assumes avg customer buys mid-tier)
```

**Method B: Value-Based Estimation**

```
When direct pricing unavailable:

1. Find ANALOGOUS product pricing
   Example: Wired EV charger = $600
   Wireless premium = 2× wired
   Estimated price = $1,200

2. Cost-plus estimation
   Component costs + Installation + Margin
   (If component costs visible on teardown sites, Alibaba, etc.)

3. Survey data from academic papers
   Search Google Scholar: "willingness to pay [product]"
   Extract price sensitivity ranges
```

**Method C: SEC 10-K Filings** (for B2B)

```
If selling to businesses, check public companies:

Search: Competitor 10-K filings
Look for: "Average selling price" or "Revenue per customer"

Example:
ChargePoint 10-K filing mentions:
"Average installation cost per commercial charger: $5,000-15,000"

Use mid-point: $10,000 for B2B ARPU
```

---

#### **Step 4: Calculate TAM**

**Formula**:
```
TAM = Customers × ARPU × Purchase_Frequency × Market_Penetration_Cap

where:
- Customers = Total potential (from Step 2)
- ARPU = Average revenue per customer (from Step 3)
- Purchase_Frequency = How often purchased (usually 1.0 for durables)
- Market_Penetration_Cap = Maximum realistic adoption (0.6-0.9 for mature markets)
```

**Example**:
```
Wireless EV Charging Market (US, 2030)

Customers: 15 million EV owners with home charging capability
ARPU: $1,400 (wireless charging pad + installation)
Purchase_Frequency: 1.0 (one-time purchase per vehicle)
Market_Penetration_Cap: 0.7 (70% adoption ceiling - some prefer wired)

TAM = 15M × $1,400 × 1.0 × 0.7
    = 15M × $980
    = $14.7 billion (2030 TAM)

For valuation, project year-by-year:
2026: 7M EVs × $980 = $6.9B
2027: 9M EVs × $980 = $8.8B
2028: 11M EVs × $980 = $10.8B
2029: 13M EVs × $980 = $12.7B
2030: 15M EVs × $980 = $14.7B
```

---

#### **Step 5: Calculate SAM (Serviceable Available Market)**

**Apply realistic constraints**:

```
SAM = TAM × Geographic_Filter × Distribution_Filter × Product_Fit_Filter

Geographic_Filter:
Question: What % of TAM geography can company actually serve?
Example:
- Company operates in 15 of 50 US states = 30% of market
- Those states have 40% of US EV owners
Geographic_Filter = 0.40

Distribution_Filter:
Question: What % of customers can company reach via current channels?
Example:
- Direct sales + 3 retail partners
- Coverage: 50% of addressable geography
Distribution_Filter = 0.50

Product_Fit_Filter:
Question: What % of market fits product profile?
Example:
- Premium product (price 2× average)
- Targets top 30% income bracket
Product_Fit_Filter = 0.30

SAM = $14.7B × 0.40 × 0.50 × 0.30
    = $14.7B × 0.06
    = $882 million
```

---

#### **Step 6: Calculate SOM (Serviceable Obtainable Market)**

**Apply competitive reality**:

```
SOM = SAM × Expected_Market_Share × Adoption_Rate

Expected_Market_Share:
Based on competitive landscape analysis (free research):

Count competitors:
- Google search: "wireless EV charging companies"
- Crunchbase (free browsing): startups in space
- LinkedIn: company counts

Example:
Found 8 competitors in wireless EV charging:
- 2 large (WiTricity, Qualcomm)
- 4 mid-size startups
- 2 small players
- + Our company = 9 total

Conservative market share estimate:
- If equal split: 100% / 9 = 11%
- But large players likely 20% each = 40% total
- Remaining 60% split among 7 players = 8.6% each
- Use conservative: 8%

Expected_Market_Share = 0.08

Adoption_Rate:
Technology adoption curve (S-curve):

For NEW technology in growth phase:
- Years 1-2: Early adopters (5-10%)
- Years 3-5: Early majority (20-40%)
- Years 6+: Late majority (50-70%)

Our timeline: Year 5 projection
Adoption_Rate = 0.40 (early majority phase)

SOM = $882M × 0.08 × 0.40
    = $28.2 million (achievable annual revenue, Year 5)
```

---

#### **Step 7: Project Revenue Over Time**

**Use growth curve**:

```
Year 1: SOM × 0.10 (10% of year 5 target) = $2.8M
Year 2: SOM × 0.25 = $7.1M
Year 3: SOM × 0.50 = $14.1M
Year 4: SOM × 0.75 = $21.2M
Year 5: SOM × 1.00 = $28.2M
Years 6-13: Hold steady or apply industry CAGR

For patent valuation:
Use these year-by-year revenues in DCF calculation
```

---

### 4.3 Free Data Sources Catalog

| Source | URL | Data Type | Quality | Use For |
|--------|-----|-----------|---------|---------|
| **US Census** | census.gov | Demographics, business counts | ★★★★★ | Customer counts (B2C & B2B) |
| **BLS** | bls.gov | Employment, wages, industries | ★★★★★ | Industry data, B2B sizing |
| **DOE** | energy.gov | Energy, vehicles | ★★★★★ | EV market, clean tech |
| **SEC EDGAR** | sec.gov/edgar | Company filings, financials | ★★★★★ | Revenue, pricing, market size |
| **Eurostat** | ec.europa.eu/eurostat | EU statistics | ★★★★★ | European markets |
| **World Bank** | data.worldbank.org | Global indicators | ★★★★ | Global markets |
| **Wikipedia** | wikipedia.org | Market size (cited) | ★★★ | Quick validation |
| **Google Scholar** | scholar.google.com | Academic market studies | ★★★★ | Market research, forecasts |
| **LinkedIn** | linkedin.com | Company counts, employee numbers | ★★★ | B2B sizing |
| **Crunchbase** | crunchbase.com (free) | Startup counts, funding | ★★★ | Competitive landscape |
| **Statista** | statista.com (free summaries) | Market size snippets | ★★ | Quick estimates (verify!) |

---

### 4.4 Decision Boundaries & Quality Gates

| Metric | Acceptable | Warning | Action |
|--------|------------|---------|--------|
| **Customer Count Source** | Government data | Wikipedia, estimates | Verify with 2nd source |
| **ARPU Data Points** | ≥5 competitor prices | <3 prices | Expand search, use range |
| **TAM Reasonableness** | Matches industry norms | 5× industry norm | Re-check calculations |
| **Market Share Assumption** | 5-15% | >20% | Justify or reduce |
| **Years to Project** | Remaining patent life or 10yr | >15 years | Cap at patent expiration |

**Red Flags**:
- No government data available → Market may be too niche or ill-defined
- ARPU varies >3× across sources → Market segmentation issue, choose segment
- Calculated TAM exceeds global GDP → Error in calculation, re-check

---

## 5. Blocking Potential Valuation

### 5.1 Concept: Value of Exclusion

**Key Insight**: Patents have value even if NEVER commercialized, because they can:
1. Block competitors (offensive)
2. Prevent being blocked (defensive)
3. Negotiate cross-licenses (strategic)

**Research Finding**: "Defensive patents restrict competitive technology use by rivals and mitigate potential legal battles."

---

### 5.2 When Blocking Value Matters

**Use Case Compatibility** (from framework document):

| Valuation Purpose | Blocking Value Relevance |
|-------------------|-------------------------|
| **Licensing Negotiation** | ★★★★★ (Critical - sets royalty floor) |
| **Litigation/Damages** | ★★★★★ (Critical - design-around cost) |
| **M&A/Portfolio Sale** | ★★★★ (High - strategic premium) |
| **Portfolio Management** | ★★★★ (High - defensive value) |
| **Financing/Collateral** | ★★★ (Medium - option value) |
| **Internal R&D** | ★★ (Low - FTO focus) |

**Decision**: Include blocking value if valuation purpose is licensing, litigation, M&A, or portfolio management.

---

### 5.3 Step-by-Step Blocking Value Calculation

#### **Step 1: Identify Potential Blocked Parties**

**Free Research Methods**:

```
A. Competitor Landscape Analysis (web search)

Search queries:
- "[technology] companies"
- "[industry] competitors developing [tech]"
- "alternatives to [technology]"

Sources (all free):
- Google search
- LinkedIn company search
- Crunchbase (free browsing)
- Industry news sites
- Academic papers on market landscape

Example:
Technology: Wireless EV charging
Search: "wireless EV charging companies" + "wireless charging startups"

Results:
- Company A: WiTricity (major player)
- Company B: Qualcomm Halo
- Company C: WAVE (transit charging)
- Company D: 5 smaller startups

Potential blocked parties: All 7 competitors

B. Product Roadmap Analysis (press releases, news)

Search: "[competitor] + product roadmap" or "plans to launch"

Example:
Found: "Company XYZ announces plan to launch wireless charging in 2027"
→ Company XYZ is potential blocked party (likely needs patent)

C. SEC 10-K Filings (public companies)

Search competitor 10-K for:
- "Research and development" section
- Mentions of technology area
- Disclosed product plans

Example:
Tesla 10-K mentions: "Exploring wireless charging for future models"
→ Tesla is potential blocked party
```

**Output**: List of 3-10 competitors who might need to license patent or design around.

---

#### **Step 2: Assess Design-Around Difficulty**

**Scoring System** (1-5 scale):

| Score | Difficulty | Claim Characteristics | Alternative Approaches | Time to Design Around |
|-------|-----------|----------------------|------------------------|----------------------|
| **5** | Impossible | Very broad claims, fundamental approach | No viable alternatives found | N/A |
| **4** | Very Hard | Broad claims, limited alternatives | Alternatives exist but inferior (2× cost or 30% performance loss) | 3-5 years |
| **3** | Moderate | Medium specificity, several alternatives | Alternatives exist with trade-offs | 2-3 years |
| **2** | Easy | Narrow claims, many alternatives | Several good alternatives | 1-2 years |
| **1** | Trivial | Very narrow claims | Many equivalent alternatives | <1 year |

**How to Assess** (FREE methods):

```
A. Claim Breadth Analysis

Read patent independent claims:

Broad Claim Example (Score 4-5):
"A system for wirelessly transferring power comprising:
 a transmitter; and a receiver;
 wherein efficiency exceeds 80%"
→ Very broad, covers ANY wireless power system >80% efficient

Narrow Claim Example (Score 2-3):
"The system of claim 1, wherein the transmitter uses a 3-coil
 resonant inductive coupling at 85 kHz, with coils arranged in
 hexagonal pattern, and safety interlock responsive to foreign object
 detection via Q-factor monitoring"
→ Very specific, easy to change any element and avoid

B. Prior Art Search (Google Patents, free)

Search: Technology keywords + "patent"
Count: How many prior art references exist?

Many prior art references (>50) → Suggests design-around options exist → Score 2-3
Few prior art references (<10) → Novel approach, hard to avoid → Score 4-5

C. Technical Alternatives Research

Search Google Scholar:
- "Alternatives to [technology approach]"
- "Comparison of [method A] vs [method B]"

Academic papers often discuss trade-offs

Example:
Paper: "Inductive vs capacitive wireless power transfer: A comparison"
Findings: "Capacitive transfer is viable alternative but requires
          larger surface area and achieves only 70% efficiency vs 90%
          for inductive"
→ Alternative exists but inferior → Score 4 (Very Hard)

D. Expert Opinion (if accessible)

Interview patent attorney (if available) or
Technical expert in field (university professor - contact via email)
Ask: "How difficult would it be to design around this patent?"
```

**Output**: Difficulty score 1-5 for target patent.

**Example**:
```
Patent: Core wireless EV charging power transfer patent
Claim breadth: Broad (covers inductive coupling generally)
Prior art: Limited (15 relevant patents found)
Alternatives: Capacitive coupling exists but 30% less efficient
Expert opinion: "Hard to avoid without performance loss"

Design-Around Difficulty Score: 4 (Very Hard)
```

---

#### **Step 3: Estimate Design-Around Cost**

**Cost Components**:

```
Design_Around_Cost = R&D_Cost + Delay_Cost + Competitive_Disadvantage_Cost

R&D_Cost:
- Engineer salaries × time
- Prototyping and testing
- Regulatory recertification (if applicable)

Delay_Cost:
- Lost revenue from market delay
- Lost market share to first-movers

Competitive_Disadvantage_Cost:
- Ongoing performance penalty (if alternative inferior)
- Higher production costs (if alternative more complex)
```

**Estimation Method** (using free data):

```
A. R&D Cost Estimation

From BLS.gov (Bureau of Labor Statistics):
- Average engineer salary: $95K/year (2024 data)
- Assume team of 5-10 engineers
- Time based on difficulty score:
  * Difficulty 5: 4-5 years
  * Difficulty 4: 2-3 years
  * Difficulty 3: 1-2 years
  * Difficulty 2: 6-12 months
  * Difficulty 1: 3-6 months

Example (Difficulty 4):
R&D_Cost = 7 engineers × $95K × 2.5 years = $1.66M
Prototyping and testing: +$500K
Total R&D: $2.16M → Round to $2M

B. Delay Cost Estimation

Time to market delay = Design-around time (from difficulty)
Annual revenue from product (from Section 4 market sizing)

Example:
Product annual revenue (from market size): $28M (Year 5 steady state)
Delay: 2.5 years
Delay_Cost = $28M × 2.5 = $70M

BUT: Use discounted value and probability
Discount by: 50% (they might license instead, or market might shift)
Realistic Delay_Cost = $70M × 0.5 = $35M

C. Competitive Disadvantage Cost

If alternative is inferior:
Performance gap × Value to customers × Years of disadvantage

Example:
Alternative is 30% less efficient
Customer values efficiency: Premium product segment
Estimated revenue loss: 20% lower sales
Years of disadvantage: 5 years (until new innovation)

Disadvantage_Cost = $28M × 20% × 5 years = $28M
Apply discount (uncertainty): $28M × 0.5 = $14M

D. Total Design-Around Cost

Total = R&D + Delay + Disadvantage
      = $2M + $35M + $14M
      = $51M

Use conservative estimate: $40-50M range
```

**Look-Up Table** (Rule of Thumb from Research):

| Difficulty Score | Typical R&D Cost | Total Design-Around Cost Range |
|-----------------|------------------|-------------------------------|
| 5 (Impossible) | N/A | N/A (must license or abandon) |
| 4 (Very Hard) | $1.5M - $3M | $20M - $80M |
| 3 (Moderate) | $800K - $2M | $5M - $20M |
| 2 (Easy) | $300K - $1M | $1M - $5M |
| 1 (Trivial) | <$200K | $500K - $2M |

---

#### **Step 4: Calculate Probability Competitor Needs License**

**Factors to Consider**:

```
Probability_Needs_License = f(Product_Overlap, Tech_Maturity, Competitor_Strategy)

A. Product Overlap
Question: Does competitor's product directly use patented technology?

Sources:
- Competitor product specs (website, press releases)
- Teardown reports (iFixit, tech blogs)
- Patent filing analysis (what are they patenting?)

Scoring:
- Direct overlap (product uses exact method): 80-90%
- High overlap (product in same category): 60-80%
- Moderate overlap (alternative approach possible): 30-50%
- Low overlap (different product, distant application): 10-20%

B. Technology Maturity
Question: How established is this as "the" way to do it?

- Standard/dominant design: 70-90%
- Emerging standard: 50-70%
- Multiple competing approaches: 30-50%
- Nascent technology: 10-30%

C. Competitor Strategy (from public statements)

Search competitor news:
- "Company X commits to [technology]" → High probability
- "Company X exploring options" → Medium probability
- No public commitment → Low probability

D. Composite Probability

Average the factors:
Example:
Product overlap: 70% (high - they're developing wireless charging)
Tech maturity: 60% (emerging standard - 3 companies use inductive)
Competitor strategy: 50% (announced plans but no commitment)

Probability = (70% + 60% + 50%) / 3 = 60%
```

---

#### **Step 5: Calculate Blocking Value**

**Scenario-Based Valuation**:

```
SCENARIO 1: Competitor Licenses Patent
Probability: 60%
Value: Licensing revenue stream

Licensing_Revenue = Royalty_Rate × Competitor_Revenue × Years

Royalty_Rate: From Section 2 (portfolio attribution)
              OR use design-around cost to set floor:
              Minimum_Royalty = (Design_Around_Cost × 0.5) / Competitor_Revenue

Example:
Design_Around_Cost: $50M
Competitor revenue (5-year): $150M
Minimum royalty = ($50M × 0.5) / $150M = 16.7%
Realistic negotiated royalty: 8-12% (split the savings)
Use: 10%

Licensing_Revenue = 10% × $150M = $15M (total 5 years)
NPV (discounted at 15%): ~$10M

Expected_Value_Scenario_1 = $10M × 60% = $6M

SCENARIO 2: Competitor Designs Around
Probability: 30%
Value: $0 (they avoid our patent)

Expected_Value_Scenario_2 = $0 × 30% = $0

SCENARIO 3: Competitor Abandons Product
Probability: 10%
Value: Market share gain

Market_Share_Gain = Competitor's market share → Captured by us
Example: Competitor would have 8% share = $28M × 0.08 = $2.2M/year
5-year value: $2.2M × 5 = $11M NPV ~$8M

Expected_Value_Scenario_3 = $8M × 10% = $0.8M

TOTAL BLOCKING VALUE (Conservative):
= Scenario_1 + Scenario_2 + Scenario_3
= $6M + $0 + $0.8M
= $6.8M
```

---

### 5.4 Real Options Approach (Advanced)

**When to Use**: Early-stage patents (TRL 1-5) with no current product, or for sophisticated valuation.

**Black-Scholes Formula**:
```
Patent_Value = S × N(d1) - X × e^(-r×T) × N(d2)

where:
S = Present value of cash flows IF commercialized (from DCF)
X = Cost to commercialize (R&D, production setup)
r = Risk-free rate (US 10-year Treasury: ~4-5%)
T = Remaining patent life
σ = Volatility (market/technology uncertainty: 30-60%)
N() = Cumulative normal distribution function
```

**Python Implementation** (FREE tools):
```python
import numpy as np
from scipy.stats import norm

def black_scholes_patent_value(S, X, r, T, sigma):
    """
    Calculate patent value using Black-Scholes real options.

    Args:
        S: PV of expected cash flows if commercialized
        X: Cost to commercialize
        r: Risk-free rate (e.g., 0.045 for 4.5%)
        T: Time to expiration (years)
        sigma: Volatility (e.g., 0.40 for 40%)

    Returns:
        Patent option value
    """
    d1 = (np.log(S/X) + (r + sigma**2/2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)

    value = S * norm.cdf(d1) - X * np.exp(-r*T) * norm.cdf(d2)
    return value

# Example
S = 15_000_000  # $15M expected NPV if commercialized
X = 5_000_000   # $5M cost to build manufacturing
r = 0.045       # 4.5% risk-free rate
T = 12          # 12 years remaining
sigma = 0.40    # 40% volatility

option_value = black_scholes_patent_value(S, X, r, T, sigma)
print(f"Patent option value: ${option_value:,.0f}")
# Output: ~$12.65M
```

**When Real Options > Traditional DCF**:
- High uncertainty (σ >30%) → Option value captures upside potential
- Long time horizon (T >10 years) → More time to decide = more valuable
- Early-stage (TRL 1-5) → Traditional DCF gives $0, options give value

---

### 5.5 Decision Boundaries

| Metric | Acceptable | Warning | Action |
|--------|------------|---------|--------|
| **Design-Around Difficulty** | 3-5 | 1-2 | Blocking value may be minimal |
| **Competitor Probability** | 30-80% | <20% or >90% | Re-verify competitive landscape |
| **Design-Around Cost** | $2M-$50M | <$500K or >$100M | Re-check calculations |
| **Blocking Value / Comm Value Ratio** | 0.2× - 5× | >10× | Investigate mismatch |

**Red Flags**:
- Blocking value >10× commercialization value → May be overestimating
- No identifiable competitors → Blocking value = $0
- Design-around score = 1-2 → Minimal blocking value

---

## 6. Complete Valuation Integration

### 6.1 Putting It All Together

**Final Formula**:
```
Total_Patent_Value = Commercialization_Value + Blocking_Value

where:

Commercialization_Value = Σ [(Revenue_t × Profit_Margin × IP_Factor × Comm_Prob) / (1 + r)^t]

Blocking_Value = Design_Around_Cost × Competitor_Prob × Capture_Rate
```

**Step-by-Step Integration**:

```
STEP 1: Portfolio Attribution (Section 2)
→ Output: IP_Contribution_Factor = X%

STEP 2: Commercialization Probability (Section 3)
→ Output: Commercialization_Probability = Y%

STEP 3: Market Size (Section 4)
→ Output: Revenue projections (Year 1 to N)

STEP 4: DCF Calculation
For each year t:
  Cash_Flow_t = Revenue_t × Profit_Margin × IP_Factor × Comm_Prob
  Present_Value_t = Cash_Flow_t / (1 + Discount_Rate)^t

Commercialization_Value = Σ Present_Value_t

STEP 5: Blocking Value (Section 5)
→ Output: Blocking_Value = $Z

STEP 6: Total Value
Total = Commercialization_Value + Blocking_Value

STEP 7: Sensitivity Analysis
Calculate Low, Base, High scenarios (±20-30% assumptions)

STEP 8: Assign Confidence Level
Based on data quality, assumption count, method alignment
```

---

### 6.2 Complete Worked Example

**Patent**: US10987654 - Wireless EV Charging System (Hypothetical)

---

**PHASE 1: DATA COLLECTION**

**Input Data**:
- Patent number: US10987654B2
- Grant date: 2019-05-15
- Remaining life: 14 years (expires 2039)
- Technology: Wireless inductive charging for EVs
- Assignee: AutoCharge Inc. (mid-size company, 800 employees)

---

**PHASE 2: PORTFOLIO ATTRIBUTION**

**Step 2.1**: Total Portfolio Royalty

Method: SEC EDGAR search
Found 3 comparable licensing agreements:
1. WiTricity license (2021): 3.8% royalty for wireless power tech
2. Qualcomm auto tech license (2022): 2.5% for automotive features
3. PowerMat license (2020): 4.1% for charging technology

Average: (3.8% + 2.5% + 4.1%) / 3 = 3.47%
**Use: 3.5% portfolio royalty**

**Step 2.2**: Classify Target Patent

Analysis from USPTO PatentsView:
- Forward citations: 42 (high for 5-year-old patent)
- Independent claims: 3 (moderate)
- Family size: 14 countries (large)
- Continuation status: Original filing (not continuation)

Classification: **CORE PATENT**
Base weight: 50%

AutoCharge portfolio (from USPTO search):
- Total patents in wireless charging (CPC H02J 50/10): 6 patents
- Target patent (US10987654): Core power transfer
- Other 5 patents: 2 improvement, 3 defensive

**Step 2.3**: Calculate Weights

```
Patent Weights:
Target (Core): 50% × 1.3 (high citations) = 65
Patent 2 (Improvement): 20% × 1.1 = 22
Patent 3 (Improvement): 20% × 1.0 = 20
Patent 4 (Defensive): 15% × 0.9 = 13.5
Patent 5 (Defensive): 15% × 0.8 = 12
Patent 6 (Defensive): 15% × 0.9 = 13.5
Total: 146

Normalized weight = 65 / 146 = 44.5%

IP_Contribution_Factor = 3.5% × 44.5% = 1.56%
```

**Output**: **IP Factor = 1.56%**

---

**PHASE 3: COMMERCIALIZATION PROBABILITY**

**Step 3.1**: TRL Assessment (from patent document)

Patent contains:
- 7 detailed embodiments
- Field testing results from 10 vehicles
- Performance data: 92% efficiency demonstrated
- References to "commercial prototype"

**TRL = 7** (operational prototype)

**Step 3.2**: CRL Assessment (from web research)

AutoCharge website:
- Product page shows "WirelessCharge Home" available for pre-order
- Press release (2024): "100 beta customers installed"
- LinkedIn: Job postings for "Production Engineer"

**CRL = 5** (commercial trial, paying customers)

**Step 3.3**: Base Probability

From matrix: TRL 7 × CRL 5 = **65% base probability**

**Step 3.4**: Apply Multipliers

```
Quality Score:
- Citations/age: 42/5 = 8.4 → Score 100
- Family size: 14 → Score 100
- Claims: 3 → Score 75
Average: (100+100+75)/3 = 91.7 → Quality multiplier = 1.15×

Assignee: Mid-size company (800 employees) → 1.10×

Market Size: TAM = $15B (calculated below) → 1.10×

Portfolio: 6 related patents → 1.05×

Final_Probability = 65% × 1.15 × 1.10 × 1.10 × 1.05
                  = 65% × 1.46
                  = 95% (capped at 95%)
```

**Output**: **Commercialization Probability = 95%**

---

**PHASE 4: MARKET SIZE ESTIMATION**

**Step 4.1**: Define Market

Product: Home wireless EV charging pads
Geography: United States
Customers: EV owners with home charging capability
Time horizon: 2025-2039 (14 years, patent life)

**Step 4.2**: Count Customers (Census data)

US EV registrations (from DOE):
- 2024: 4.2M EVs
- Historical CAGR (2019-2024): 33%
- Projected 2030: 4.2M × (1.33)^6 = 20M EVs
- Projected 2039: 20M × (1.15)^9 = 70M EVs (slowing growth assumption)

Home charging capable: 75% (Census ACS - homeownership with garage)
Potential customers (2030): 20M × 0.75 = 15M
Potential customers (2039): 70M × 0.75 = 52M

**Step 4.3**: ARPU (from competitor research)

Competitor pricing (web search):
- Plugless Power: $1,299
- WAVE: $1,500 (commercial)
- WiTricity (hypothetical): $1,800
- Average: $1,533

**Use: $1,500 ARPU**

**Step 4.4**: TAM Calculation

TAM (2030) = 15M × $1,500 × 0.70 adoption = $15.75B
TAM (2039) = 52M × $1,500 × 0.70 = $54.6B

**Step 4.5**: SAM

Geographic filter: 60% (operates in key states)
Distribution filter: 50% (limited retail presence)
Product fit: 40% (premium segment)

SAM (2030) = $15.75B × 0.60 × 0.50 × 0.40 = $1.89B
SAM (2039) = $54.6B × 0.60 × 0.50 × 0.40 = $6.55B

**Step 4.6**: SOM

Market share: 8% (competitive market, 9 players)
Adoption rate: 50% (mid-growth phase)

SOM (2030) = $1.89B × 0.08 × 0.50 = $75.6M
SOM (2039) = $6.55B × 0.08 × 0.50 = $262M

**Step 4.7**: Revenue Projection

```
Year | TAM   | SAM    | SOM   | Growth
-----|-------|--------|-------|--------
2025 | $7B   | $840M  | $34M  | Base
2026 | $9B   | $1.08B | $43M  | +27%
2027 | $12B  | $1.44B | $58M  | +35%
2028 | $14B  | $1.68B | $67M  | +16%
2029 | $15B  | $1.80B | $72M  | +7%
2030 | $16B  | $1.92B | $77M  | +7%
...  | ...   | ...    | ...   | ...
2038 | $50B  | $6.0B  | $240M | Steady
2039 | $55B  | $6.6B  | $264M | +10%

Annual revenue (steady state): ~$250M
```

**Output**: Year-by-year revenue projections

---

**PHASE 5: DCF CALCULATION**

**Inputs**:
- Revenue_t: From market sizing (above)
- Profit_Margin: 12% (automotive supplier average, from academic paper)
- IP_Factor: 1.56% (from portfolio attribution)
- Comm_Prob: 95% (from commercialization assessment)
- Discount_Rate: 16% (9.5% auto WACC + 6.5% patent risk premium)

**Cash Flow Calculation**:

```
Year 1 (2025):
Revenue: $34M
CF = $34M × 12% × 1.56% × 95% = $60,595
PV = $60,595 / (1.16)^1 = $52,237

Year 2 (2026):
Revenue: $43M
CF = $43M × 12% × 1.56% × 95% = $76,644
PV = $76,644 / (1.16)^2 = $56,973

... (continue for all 14 years)

Year 14 (2039):
Revenue: $264M
CF = $264M × 12% × 1.56% × 95% = $470,563
PV = $470,563 / (1.16)^14 = $66,082

Total NPV = $52,237 + $56,973 + ... + $66,082
          = $883,420
```

**Output**: **Commercialization Value = $883,420**

---

**PHASE 6: BLOCKING VALUE**

**Step 6.1**: Identify Competitors (web research)

Google search + Crunchbase:
- WiTricity (major competitor)
- Qualcomm (exploring wireless charging)
- Momentum Dynamics
- 4 smaller startups

**Focus on: Qualcomm** (largest potential licensee)

**Step 6.2**: Design-Around Difficulty

Claim analysis:
- Claims cover inductive coupling generally
- Specific efficiency threshold (>85%)
- Limited prior art (15 relevant patents)

Alternative: Capacitive coupling
- Trade-off: 30% less efficient, larger footprint

**Difficulty Score: 4** (Very Hard)

**Step 6.3**: Design-Around Cost

R&D: 8 engineers × $95K × 3 years = $2.28M
Delay: 3 years × $150M competitor revenue = $450M (apply 50% discount) = $225M
Competitive disadvantage: 20% revenue loss × 5 years × $150M = $150M (apply 50% discount) = $75M

**Total: $2.28M + $225M + $75M = $302M**
**Conservative estimate: $250M**

**Step 6.4**: Competitor Probability

Product overlap: 70% (Qualcomm announced wireless charging plans)
Tech maturity: 60% (emerging standard)
Strategy: 50% (exploratory, no commitment)

**Probability: 60%**

**Step 6.5**: Blocking Value Calculation

Scenario 1: Qualcomm licenses (60% probability)
Royalty: Min = ($250M × 0.5) / $750M (5-year revenue) = 16.7% floor
Negotiated: 10% realistic
Licensing revenue = 10% × $750M = $75M
NPV (discounted): ~$52M
Expected value = $52M × 60% = $31.2M

Scenario 2: Qualcomm designs around (30%)
Value: $0

Scenario 3: Qualcomm abandons (10%)
Market share gain: $25M/year × 5 = $125M NPV ~$90M
Expected value = $90M × 10% = $9M

**Total Blocking Value = $31.2M + $0 + $9M = $40.2M**

**Output**: **Blocking Value = $40,200,000**

---

**PHASE 7: TOTAL VALUATION**

**Components**:
1. Commercialization Value: $883,420
2. Blocking Value: $40,200,000

**Total Patent Value = $41,083,420**

**Valuation Range** (±25% sensitivity):
- Low: $30.8M (conservative assumptions)
- Base: $41.1M
- High: $51.4M (optimistic assumptions)

**Confidence Level: MEDIUM-HIGH**
- Data quality: Good (government data, SEC comparables, thorough research)
- Methodology: Comprehensive (all three factors integrated)
- Key risk: Competitor behavior uncertainty (blocking value dominates)

---

### 6.3 Key Insights from Example

**Finding 1**: Blocking value ($40.2M) >> Commercialization value ($883K) by **45×**

**Why?**
- Patent's IP contribution is small (1.56%) due to 6-patent portfolio
- But blocking value considers competitor's FULL cost to avoid ($250M)
- Common for strategic patents in competitive markets

**Finding 2**: Without blocking value analysis, patent would be **vastly undervalued**

Traditional DCF alone: $883K
With blocking value: $41.1M
**Undervaluation factor: 46×**

**Finding 3**: Free data sources were sufficient for comprehensive valuation

All data from:
- USPTO PatentsView API (patent metrics)
- SEC EDGAR (licensing comparables)
- DOE (EV market data)
- Census (customer counts)
- BLS (salary data)
- Web research (competitor pricing)
- Academic papers (royalty benchmarks)

**Total cost: $0**

---

## 7. Free Data Sources Catalog

### 7.1 Patent Data

| Source | URL | Data Available | API? | Quality |
|--------|-----|----------------|------|---------|
| **USPTO PatentsView** | patentsview.org | Bibliographic, citations, claims, families | ✅ REST API | ★★★★★ |
| **EPO OPS** | ops.epo.org | INPADOC families, legal status, bibliographic | ✅ REST API | ★★★★★ |
| **Google Patents** | patents.google.com | Full-text search, PDFs, prior art | ❌ (BigQuery available) | ★★★★ |
| **USPTO Patent Center** | patentcenter.uspto.gov | Prosecution history, office actions | ❌ Web only | ★★★★★ |
| **Lens.org** | lens.org | Patent search, citation network | ✅ API | ★★★★ |

**How to Use**:

```python
# Example: USPTO PatentsView API
import requests

def fetch_patent_data(patent_number):
    url = "https://api.patentsview.org/patents/query"
    query = {
        "q": {"patent_number": patent_number},
        "f": ["patent_title", "patent_date", "citedby_patent_number",
              "cpc_group_id", "inventor_first_name", "assignee_organization"]
    }
    response = requests.post(url, json=query)
    return response.json()

# Example usage
data = fetch_patent_data("10987654")
forward_citations = len(data['patents'][0]['citedby_patent_number'])
```

---

### 7.2 Market & Financial Data

| Source | URL | Data Available | Quality |
|--------|-----|----------------|---------|
| **US Census Bureau** | census.gov | Demographics, business counts, industry stats | ★★★★★ |
| **Bureau of Labor Statistics** | bls.gov | Employment, wages, industry data | ★★★★★ |
| **SEC EDGAR** | sec.gov/edgar | 10-K filings, licensing agreements, market size | ★★★★★ |
| **Department of Energy** | energy.gov/data | Energy, vehicles, clean tech data | ★★★★★ |
| **World Bank** | data.worldbank.org | Global economic indicators | ★★★★ |
| **Eurostat** | ec.europa.eu/eurostat | European Union statistics | ★★★★★ |
| **Damodaran (NYU Stern)** | pages.stern.nyu.edu/~adamodar | WACC by industry, valuation data | ★★★★★ |

---

### 7.3 Industry & Competitive Intelligence

| Source | URL | What's Free | Quality |
|--------|-----|-------------|---------|
| **Wikipedia** | wikipedia.org | Market size sections (with citations to verify) | ★★★ |
| **Statista** | statista.com | Free summary statistics (full reports paid) | ★★ |
| **LinkedIn** | linkedin.com | Company employee counts, job postings | ★★★ |
| **Crunchbase** | crunchbase.com | Startup counts, funding (free browsing) | ★★★ |
| **Google Scholar** | scholar.google.com | Academic market research papers | ★★★★ |
| **SSRN** | ssrn.com | Business research, working papers | ★★★★ |

---

### 7.4 Academic & Research

| Source | URL | Access | Content |
|--------|-----|--------|---------|
| **Google Scholar** | scholar.google.com | FREE | All academic papers |
| **ArXiv** | arxiv.org | FREE | Preprints (physics, CS, econ) |
| **PubMed** | pubmed.gov | FREE | Medical/biotech research |
| **SSRN** | ssrn.com | FREE | Business, economics, legal |
| **University Repositories** | Various .edu | FREE | Theses, dissertations |

**Search Strategies**:
```
For royalty rates:
- "[industry] patent licensing royalty rates"
- "reasonable royalty damages [industry]"
- "technology transfer licensing [field]"

For market sizing:
- "[technology] market adoption"
- "[industry] total addressable market"
- "commercialization of [technology]"

For technology analysis:
- "[technology] alternatives comparison"
- "prior art [patent approach]"
- "[field] state of the art review"
```

---

## 8. Decision Boundaries & Quality Thresholds

### 8.1 Data Quality Assessment

**Scoring Framework** (0-100):

```
Data_Quality_Score = (Completeness × 0.4) + (Source_Reliability × 0.3) + (Recency × 0.3)

Completeness:
- All key inputs available: 100
- 80-99% inputs available: 80
- 60-79% inputs: 60
- <60% inputs: 40 (red flag)

Source_Reliability:
- Government data, peer-reviewed: 100
- Public company filings: 90
- Industry associations: 70
- Wikipedia, news: 50
- Pure estimation: 30

Recency:
- Data <2 years old: 100
- 2-5 years: 80
- 5-10 years: 60
- >10 years: 40

Example:
Patent with:
- Complete USPTO data (100 completeness)
- 3 SEC comparables from 2022-2024 (90 reliability, 100 recency)
- Market size from 2023 Census (100 reliability, 100 recency)

Completeness: 100
Reliability: (100 + 90 + 100) / 3 = 96.7
Recency: (100 + 100 + 100) / 3 = 100

Data_Quality_Score = 100×0.4 + 96.7×0.3 + 100×0.3 = 99

Conclusion: EXCELLENT data quality
```

---

### 8.2 Confidence Level Assignment

| Data Quality | Methods Alignment | Assumption Count | Confidence Level |
|--------------|-------------------|------------------|------------------|
| >90 | Strong (<20% variance) | <10 high-impact | **HIGH** |
| 70-90 | Moderate (20-40% variance) | 10-20 high-impact | **MEDIUM-HIGH** |
| 50-70 | Weak (>40% variance) | 20-30 high-impact | **MEDIUM** |
| <50 | Very weak | >30 high-impact | **LOW** |

**Methods Alignment** (when using multiple approaches):
```
If Income Method = $X and Blocking Value = $Y:

Check ratio: Y/X
- If 0.5× - 2×: Strong alignment
- If 0.2× - 5×: Moderate alignment
- If <0.2× or >5×: Weak alignment (investigate)

If using Market Method too (requires paid data):
- Income vs Market variance <30%: Strong
- 30-50%: Moderate
- >50%: Weak
```

---

### 8.3 Red Flags & Warning Triggers

**Automatic Review Required If**:

| Condition | Flag Level | Action |
|-----------|-----------|--------|
| **IP Contribution Factor >10%** | 🚩 MEDIUM | Verify not a single-patent product |
| **IP Contribution Factor <0.2%** | 🚩 MEDIUM | Check if too many patents in bundle |
| **Commercialization Prob <20%** | 🚩🚩 HIGH | Flag valuation as speculative |
| **Blocking Value / Comm Value >20×** | 🚩 MEDIUM | Verify competitor analysis |
| **Zero comparable transactions found** | 🚩🚩 HIGH | Note: IP Factor based on estimation |
| **Market share assumption >25%** | 🚩🚩 HIGH | Unjustified dominance claim |
| **Discount rate <8% or >25%** | 🚩 MEDIUM | Re-check WACC + risk premium |
| **Design-around difficulty = 1-2** | ⚠️ LOW | Blocking value likely minimal |
| **No identifiable competitors** | ⚠️ LOW | Blocking value = $0 |
| **Data quality score <50** | 🚩🚩🚩 CRITICAL | Unreliable valuation, flag prominently |

---

### 8.4 Assumption Documentation Template

**Every valuation must include**:

```markdown
## Assumptions Log

### High-Impact Assumptions (Sensitivity >20%)

| # | Assumption | Value | Rationale | Source | Sensitivity | Alternatives Considered |
|---|-----------|-------|-----------|--------|-------------|------------------------|
| 1 | Discount rate | 16% | Auto industry WACC (9.5%) + patent risk (6.5%) | Damodaran + research | ±30% → $X to $Y | 14%, 18% |
| 2 | IP contribution factor | 1.56% | Core patent (44.5% of 3.5% portfolio) | SEC comparables + weighting | ±20% → $X to $Y | 1.2%, 2.0% |
| 3 | Commercialization probability | 95% | TRL 7 × CRL 5 base (65%) × 1.46 multipliers | Patent + market analysis | ±10% → $X to $Y | 85%, 100% capped |
| ... | ... | ... | ... | ... | ... | ... |

### Medium-Impact Assumptions

[Continue...]

### Data Quality Summary

- Completeness: 95%
- Source reliability: 92%
- Recency: 98%
- **Overall data quality: 95/100 (EXCELLENT)**

### Confidence Assessment

- Data quality: EXCELLENT (95/100)
- Methods used: Income + Blocking (aligned 1:45 ratio is expected for strategic patents)
- High-impact assumptions: 8
- **Final confidence level: MEDIUM-HIGH**

### Limitations

1. Blocking value depends on competitor behavior (uncertain)
2. Market projections beyond 2030 have increasing uncertainty
3. No cross-validation with Market Method (requires paid data)
4. IP contribution factor based on limited SEC comparables (n=3)

### Recommended Actions

1. Monitor competitor product announcements
2. Re-assess if market conditions change significantly
3. Update valuation annually with new market data
4. Consider purchasing RoyaltyRange subscription for Market Method validation ($5K)
```

---

## 9. Summary & Implementation Checklist

### 9.1 Core Methodology Summary

**Three-Factor Enhanced Income Method**:

1. **Portfolio Attribution** → IP Contribution Factor
   - Use SEC EDGAR for comparables (free)
   - Feature value analysis (free)
   - Academic benchmarks (free)

2. **Commercialization Probability** → Discount cash flows
   - TRL from patent document (free)
   - CRL from web research (free)
   - Quality multipliers from USPTO (free)

3. **Market Size (Bottom-Up ONLY)** → Revenue projections
   - Census/BLS customer counts (free)
   - Competitor pricing research (free)
   - Government industry data (free)

4. **Blocking Potential** → Option value
   - Competitor identification (free research)
   - Design-around difficulty scoring (free)
   - Scenario-based valuation (free)

**Total Cost: $0**

---

### 9.2 Pre-Valuation Checklist

**Before starting, gather**:

- [ ] Patent number(s)
- [ ] Product/technology description
- [ ] Industry/market definition
- [ ] Company information (if available)
- [ ] Valuation purpose (licensing, M&A, portfolio management, etc.)
- [ ] Required precision level (low, medium, high)
- [ ] Time available for analysis (quick estimate vs comprehensive)

**Data availability check**:

- [ ] Can identify product/market clearly?
- [ ] Are there public companies in same space (for comparables)?
- [ ] Is government data available for customer counts?
- [ ] Can find competitor pricing?
- [ ] Are there identifiable competitors for blocking analysis?

**IF <3 checkmarks in data availability → Expect MEDIUM-LOW confidence**

---

### 9.3 Execution Checklist

**Phase 1: Portfolio Attribution**

- [ ] Search SEC EDGAR for licensing agreements (30 min)
- [ ] Extract royalty rates from ≥3 comparables OR
- [ ] Perform feature value analysis if no comparables
- [ ] Classify target patent (Core/Improvement/Defensive)
- [ ] Calculate patent strength multipliers from USPTO data
- [ ] Compute normalized IP contribution factor
- [ ] **Output: IP Factor (e.g., 1.56%)**

**Phase 2: Commercialization Probability**

- [ ] Read patent document, assess TRL (20 min)
- [ ] Research company/product status, assess CRL (20 min)
- [ ] Look up base probability in TRL×CRL matrix
- [ ] Calculate quality multipliers from USPTO
- [ ] Apply adjustments for company, market, portfolio
- [ ] **Output: Commercialization Probability (e.g., 85%)**

**Phase 3: Market Sizing**

- [ ] Define market boundaries precisely
- [ ] Count customers using Census/government data (1 hour)
- [ ] Research competitor pricing for ARPU (30 min)
- [ ] Calculate TAM (bottom-up)
- [ ] Apply filters for SAM
- [ ] Estimate realistic market share for SOM
- [ ] Project revenue year-by-year
- [ ] **Output: Revenue projections table**

**Phase 4: DCF Calculation**

- [ ] Determine profit margin (from SEC filings or academic papers)
- [ ] Calculate discount rate (Damodaran WACC + risk premium)
- [ ] Compute cash flows: Revenue × Margin × IP Factor × Prob
- [ ] Discount to present value
- [ ] **Output: Commercialization Value**

**Phase 5: Blocking Value**

- [ ] Identify competitors (web research) (30 min)
- [ ] Assess design-around difficulty (claim analysis)
- [ ] Estimate design-around cost (rule of thumb + research)
- [ ] Calculate competitor probability
- [ ] Compute scenario-based blocking value
- [ ] **Output: Blocking Value**

**Phase 6: Integration & Reporting**

- [ ] Sum commercialization + blocking value
- [ ] Run sensitivity analysis (±20-30%)
- [ ] Document all assumptions with sources
- [ ] Assign confidence level
- [ ] Generate valuation report with limitations
- [ ] **Output: Final valuation with range and confidence**

**Total Time: 4-8 hours for comprehensive analysis**

---

### 9.4 Quality Control Checklist

**Before finalizing valuation**:

- [ ] Data quality score ≥50?
- [ ] All high-impact assumptions documented with rationale?
- [ ] Sensitivity analysis shows reasonable ranges?
- [ ] No red flags triggered (see Section 8.3)?
- [ ] Confidence level assigned based on framework?
- [ ] Limitations clearly stated?
- [ ] All free sources cited properly?
- [ ] Results pass "smell test" (not 10× industry norms)?

**IF any unchecked → Address before delivering to stakeholder**

---

### 9.5 Next Steps After Methodology Validation

**Once this methodology is approved**:

1. ✅ **Build Calculation Tools**:
   - Python functions for each calculation
   - DCF calculator
   - Probability calculator
   - Sensitivity analyzer

2. ✅ **Create Data Collection Utilities**:
   - USPTO API wrapper
   - SEC EDGAR scraper
   - Census data fetcher
   - Web search automation

3. ✅ **Design Multi-Agent System**:
   - Agent per major task (Data Collector, Portfolio Analyst, Market Sizer, etc.)
   - Topology definition (hub-and-spoke with dynamic branching)
   - Assumption tracker agent
   - Validation agent

4. ✅ **Testing & Validation**:
   - Test on 5-10 real patents
   - Validate against published valuations (if available)
   - Refine assumptions based on results

---

**END OF METHODOLOGY DOCUMENT**

This methodology provides a complete, implementable framework for patent valuation using ONLY free data sources, addressing portfolio bundling, commercialization probability, and blocking potential.
