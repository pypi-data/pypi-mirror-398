# Patent Valuation: Data Requirements, Sources, and Calculation Methodology

**Purpose**: This document establishes the foundational understanding of what data is needed for patent valuation, where it comes from, and how it's used in calculations. This is a prerequisite to designing any multi-agent system.

**Scope**: Focused on **Market Method** and **Income Method** only (excluding Cost Method as requested).

---

## Table of Contents

1. [Valuation Methods Overview](#1-valuation-methods-overview)
2. [Income Method: Data Requirements](#2-income-method-data-requirements)
3. [Market Method: Data Requirements](#3-market-method-data-requirements)
4. [Data Source Verification](#4-data-source-verification)
5. [Critical Gaps and Challenges](#5-critical-gaps-and-challenges)
6. [Step-by-Step Calculation Walkthrough](#6-step-by-step-calculation-walkthrough)

---

## 1. Valuation Methods Overview

### 1.1 Income Method (DCF)

**Core Concept**: Calculate the present value of future cash flows attributable to the patent.

**Formula**:
```
Patent Value = Σ [Cash Flow_year_t / (1 + Discount_Rate)^t] + Terminal_Value
```

**When Used**:
- Revenue projections are available or can be reasonably estimated
- Patent has clear commercial application
- Product/service revenue can be attributed to the patent

**Advantages**:
- Forward-looking (captures future economic benefit)
- Aligns with how businesses think about value
- Can be customized to specific circumstances

**Disadvantages**:
- Highly dependent on assumptions (revenue growth, discount rate)
- Requires multiple uncertain inputs
- Future projections inherently uncertain

---

### 1.2 Market Method (Comparables)

**Core Concept**: Use actual market transactions of similar patents as benchmarks, then adjust for differences.

**Formula**:
```
Patent Value = Comparable_Transaction_Value × Adjustment_Factors
```

**When Used**:
- Comparable patent transactions exist and are accessible
- Sufficient similarity between target and comparable patents
- Transaction data includes pricing information

**Advantages**:
- Based on real market transactions (actual prices paid)
- Less dependent on future projections
- Reflects market supply/demand dynamics

**Disadvantages**:
- Comparable data is scarce and often confidential
- Requires subjective similarity judgments
- Market conditions may have changed since transaction
- Many adjustments needed (technology, time, market size, etc.)

---

## 2. Income Method: Data Requirements

### 2.1 Patent-Specific Data

| Data Point | Why Needed | Where Used in Calculation | How to Obtain |
|------------|------------|--------------------------|---------------|
| **Grant Date** | Determines patent age | Not directly in formula, but used for citation normalization | USPTO PatentsView API (free) |
| **Expiration Date** | Defines cash flow projection period | Determines number of years (t) in DCF formula | Calculated: Grant Date + 20 years for utility patents |
| **Remaining Patent Life** | Limits projection horizon | Sets upper bound on t in Σ formula | Current Date → Expiration Date |
| **Claims (text)** | Used for claim breadth analysis | Not in calculation, but helps assess IP strength | USPTO PatentsView API |
| **Independent Claims Count** | Indicates patent strength/breadth | Used in patent strength scoring (affects risk assessment → discount rate) | Count from claims text |
| **Forward Citations** | Indicates patent influence/importance | Patent strength score → affects discount rate selection | USPTO PatentsView API (citedby_patent_number) |
| **Patent Family Size (INPADOC)** | Shows geographic coverage/value | Patent strength score → affects discount rate | EPO OPS API (free, requires registration) |
| **Technology Classification (IPC/CPC)** | Identifies technology field | Industry categorization → affects profit margin, discount rate benchmarks | USPTO PatentsView API |

**Critical Insight**: Patent-specific data is **freely available** from government APIs. No commercial subscriptions needed for this category.

---

### 2.2 Financial/Revenue Data

| Data Point | Why Needed | Where Used in Calculation | How to Obtain | **Critical Challenge** |
|------------|------------|--------------------------|---------------|----------------------|
| **Revenue Projections (Years 1-N)** | Core input to cash flow | Numerator of DCF: CF = Revenue × ... | **PRIMARY ISSUE**: Requires company data OR market estimation | ⚠️ If company private/uncooperative: Must estimate from market size |
| **Profit Margin** | Converts revenue to profit | CF = Revenue × **Profit_Margin** × IP_Factor | Industry benchmarks (public) OR company financials | ⚠️ Industry average is okay, company-specific is better |
| **IP Contribution Factor** | Isolates patent's contribution to revenue | CF = Revenue × Profit_Margin × **IP_Contribution_Factor** | **MOST DIFFICULT**: See dedicated section below | ⚠️ Highly subjective, largest source of variance |
| **Market Size (TAM)** | Used to estimate revenue if company data unavailable | Revenue = Market_Size × Market_Share × Growth | Market research reports (often paid) | ⚠️ Free sources exist but may be outdated |
| **Market Growth Rate (CAGR)** | Projects revenue growth over time | Revenue_year_t = Revenue_base × (1 + CAGR)^t | Market research reports | ⚠️ Same as market size |
| **Discount Rate** | Time value of money adjustment | Denominator: (1 + **Discount_Rate**)^t | Calculated from WACC + risk premium | ⚠️ Composition is complex (see below) |

---

#### 2.2.1 IP Contribution Factor: The Critical Challenge

**Definition**: What percentage of the product's value/revenue is attributable to this specific patent?

**Why This Is Hard**:
- Most products are covered by **multiple patents** (especially in tech/manufacturing)
- Patent may cover only one feature of a multi-feature product
- Difficult to isolate value of one patent from the bundle

**Research Findings** (from web search):

From patent apportionment case law and practice:
- **Legal Standard**: "Patentee must carefully tie proof of damages to the claimed invention's footprint in the market place" (Federal Circuit)
- **Apportionment Required**: Must reduce revenue to reflect only the portion relating to the asserted patent(s)
- **Overcompensation Risk**: Using full product revenue overstates patent value

**Methodologies** (from research):

1. **Smallest Salable Unit Approach**:
   - Identify the smallest component containing the patented technology
   - Use that component's value as the base (not the entire product)
   - Example: If patent covers a charging port design in an EV, use port value, not car value

2. **Comparable License Approach**:
   - If comparable licenses exist with disclosed royalty rates, use those
   - Example: If similar patents licensed at 3% of product revenue, use 3% as contribution factor
   - Federal Circuit accepts this as "built-in apportionment"

3. **Feature Analysis Approach**:
   - List all product features
   - Estimate value contribution of each feature
   - Patent's contribution = (Patented features' value / Total value)
   - Subjective but structured

**Typical Ranges** (from research):
- **Single critical patent** (rare, e.g., pharma drug): 50-90%
- **Important feature patent**: 10-30%
- **One patent in portfolio**: 5-15%
- **Minor improvement patent**: 1-5%

**For Valuation Purposes**:
- **Conservative assumption**: Use lower end of range (defensible)
- **Document rationale**: Explain why chosen percentage is appropriate
- **Sensitivity test**: Show valuation at ±50% of chosen value

**Data Sources for IP Contribution Factor**:
1. **Best**: Comparable licensing agreements with disclosed royalty rates (from ktMINE/RoyaltyRange)
2. **Good**: Expert opinion from patent attorney or valuator
3. **Acceptable**: Structured feature analysis with documentation
4. **Weak**: Estimate without rationale (not defensible)

---

#### 2.2.2 Discount Rate: Composition and Sources

**Formula**:
```
Discount_Rate = Base_WACC + Patent_Risk_Premium
```

**Base WACC (Weighted Average Cost of Capital)**:

**Where to Get It**:
1. **If public company**: Calculate from financial statements
   - WACC = (E/V × Cost_of_Equity) + (D/V × Cost_of_Debt × (1 - Tax_Rate))
   - Data source: Company 10-K filings (free from SEC EDGAR)

2. **If private company or no company data**: Use industry average
   - **Data Source**: Damodaran's Industry Data (NYU Stern, free)
   - URL: https://pages.stern.nyu.edu/~adamodar/
   - Provides WACC by industry sector (updated annually)

**Example Industry WACCs** (from Damodaran 2024):
- Automotive: 9.5%
- Software: 14.0%
- Pharmaceuticals: 11.0%
- Semiconductors: 12.5%
- Manufacturing: 9.0%

**Patent Risk Premium**:

Patents are riskier than the overall business because:
- May be invalidated (prior art, legal challenges)
- May be designed around (competitors create alternatives)
- Technology may become obsolete
- Uncertain commercial adoption

**Components** (from research):

1. **Technology Maturity Risk**:
   - Early-stage (pre-commercialization): +8-12%
   - Growth stage (proven but scaling): +4-6%
   - Mature (established market): +2-4%

2. **Portfolio Dependency Risk**:
   - Single critical patent (high dependency): +3-5%
   - One of many patents (diversified): +1-2%

3. **Litigation/Invalidity Risk**:
   - Pending litigation: +3-5%
   - Prior invalidation attempts: +2-4%
   - No litigation history: +0-1%

**Total Patent Risk Premium Range**: 5-15% (typical)

**Example Calculation**:
```
Industry: Automotive (Base WACC = 9.5%)
Technology: Mature wireless charging (Maturity = +3%)
Portfolio: One of 10 related patents (Dependency = +1%)
Litigation: None (Risk = +0%)

Total Discount Rate = 9.5% + 3% + 1% + 0% = 13.5%
```

**Critical Note**: Discount rate has **massive impact** on valuation. A 5% change in discount rate can change valuation by 30-50%.

---

### 2.3 Patent Strength Assessment Data

**Purpose**: Assess patent quality/strength to inform risk assessment (affects discount rate).

| Data Point | Why Needed | Where Used | Source | Free? |
|------------|------------|-----------|---------|-------|
| **Forward Citations Count** | More citations = more influential = stronger | Strength score | USPTO PatentsView API | ✅ Yes |
| **INPADOC Family Size** | Broader geographic coverage = more valuable | Strength score | EPO OPS API | ✅ Yes |
| **Maintenance Fee Status** | All fees paid = owner believes in value | Strength indicator | USPTO Patent Center (manual lookup) | ✅ Yes |
| **Litigation History** | Litigation = commercial importance (positive) | Strength score | PACER (US court records), manual search | ⚠️ Partial (PACER has fees) |
| **Prior Art Quality** | Strong prior art = invalidation risk | Validity assessment | Manual search, Google Patents | ✅ Yes |

**How Strength Affects Valuation**:
- Higher strength → Lower risk → Lower discount rate → Higher valuation
- Lower strength → Higher risk → Higher discount rate → Lower valuation

**Strength Scoring Formula** (composite, research-based):
```
Strength Score = (Citations × 0.30) + (Family × 0.25) + (Claims × 0.25) + (Legal × 0.20)

where each component is normalized 0-100
```

**Example**:
- Patent with 50 forward citations, family size 15, 8 independent claims, all fees paid
- Citations: min(50/age_years, 10) × 10 = ~80 points × 0.30 = 24
- Family: min(15, 20) × 5 = 75 points × 0.25 = 18.75
- Claims: min(8, 10) × 10 = 80 points × 0.25 = 20
- Legal: All fees paid + no litigation = 65 points × 0.20 = 13
- **Total Strength: 75.75/100** → Strong patent → Use lower end of risk premium range

---

## 3. Market Method: Data Requirements

### 3.1 Comparable Transaction Data

**What We Need**:
- Recent patent sale or licensing transactions
- For patents in similar technology fields
- With disclosed transaction values or royalty rates

**The Central Challenge**: Most patent transactions are **confidential**. Publicly disclosed transactions are rare.

**Where This Data Comes From**:

| Source | What It Provides | Access | Cost | Reliability |
|--------|-----------------|--------|------|------------|
| **ktMINE** | 500,000+ licensed patents from SEC filings, litigation | Commercial database + API | ~$10K-30K/year subscription | HIGH (sourced from public filings) |
| **RoyaltyRange** | Patent licensing agreements with royalty rates | Commercial database + API | ~$5K-15K/year subscription | HIGH (verified public sources only) |
| **USPTO Patent Assignment Database** | 10.5M patent ownership transfers since 1970 | Free bulk download | FREE | LOW for valuation (no prices disclosed) |
| **SEC EDGAR Filings** | M&A deals, material contracts (if disclosed) | Free search | FREE | MEDIUM (incomplete, requires manual search) |
| **Court Records (PACER)** | Litigation settlements with damages | Per-document fees | ~$0.10/page | MEDIUM (settlements often confidential) |

**Critical Finding**: To use Market Method properly, **commercial subscription to ktMINE or RoyaltyRange is essentially required**. Free sources provide transaction records but rarely include pricing.

---

### 3.2 Comparable Patent Characteristics Data

For each comparable transaction found, we need patent data to assess similarity:

| Data Point | Why Needed | Where Used | Source |
|------------|------------|-----------|---------|
| **IPC/CPC Classifications** | Technology similarity scoring | Classification overlap calculation | USPTO PatentsView, EPO OPS |
| **Citations (backward & forward)** | Citation overlap scoring | Citation network analysis | USPTO PatentsView |
| **Claims Text** | Semantic similarity | NLP text similarity (TF-IDF, cosine) | USPTO PatentsView |
| **Grant Date** | Time adjustment factor | Age normalization | USPTO PatentsView |
| **Remaining Life at Transaction** | Life ratio adjustment | Adjustment factor calculation | Grant date + transaction date |
| **Market Size at Transaction** | Market size differential | Adjustment factor | Historical market research |

**All patent characteristic data is freely available** from USPTO/EPO APIs.

---

### 3.3 Adjustment Factors

Once comparables are found, they must be adjusted for differences:

| Adjustment Factor | Formula/Range | Data Needed | Source | Challenge Level |
|-------------------|---------------|-------------|--------|-----------------|
| **Technology Similarity** | 0.5 - 1.5x multiplier | Patent characteristics (above) | USPTO/EPO APIs | MEDIUM (calculation is complex) |
| **Market Size Differential** | (Target_Market / Comp_Market) | Market size data for both | Market research reports | MEDIUM (need historical data) |
| **Time Adjustment** | (1 + inflation)^years_since | Transaction date, inflation rate | Federal Reserve data (free) | EASY |
| **Remaining Life Ratio** | Target_Life / Comp_Life | Expiration dates | Calculated from grant dates | EASY |

**Technology Similarity Calculation** (detailed):

Research-based weighted formula:
```
Similarity = (IPC_Overlap × 0.40) + (Citation_Overlap × 0.30) + (Claim_Similarity × 0.20) + (Industry_Match × 0.10)
```

Where:
- **IPC_Overlap**: Jaccard similarity of classification codes
  - Formula: |Intersection| / |Union|
  - Example: Target has [H01M, H02J], Comp has [H01M, H02G] → 1/3 = 0.33

- **Citation_Overlap**: Jaccard similarity of cited patents
  - Same formula on backward citation lists

- **Claim_Similarity**: TF-IDF cosine similarity of claim text
  - NLP technique (scikit-learn in Python)
  - Range: 0 (no common words) to 1 (identical)

- **Industry_Match**: Binary (1 if same industry, 0 if different)

**Example**:
```
Target Patent: Wireless EV charging (H02J 50/10, H01M 50/20)
Comparable: Wireless phone charging (H02J 50/10, H02J 7/00)

IPC Overlap: {H02J 50/10} ∩ → 1/3 = 0.33
Citation Overlap: 15 shared citations out of 40 total → 15/40 = 0.375
Claim Similarity: TF-IDF cosine = 0.68
Industry: Both consumer electronics → 1.0

Similarity Score = (0.33 × 0.40) + (0.375 × 0.30) + (0.68 × 0.20) + (1.0 × 0.10)
                = 0.132 + 0.113 + 0.136 + 0.10
                = 0.481 (48.1% similar)
```

**Interpretation**: 48% similarity is **weak** for a comparable. Best practice: Use comparables with >60% similarity.

---

### 3.4 Royalty Rate Benchmarks

Even without specific transactions, royalty rate benchmarks help validate income method assumptions.

**What We Need**:
- Typical royalty rates for the technology field/industry
- Range (low, median, high)

**Sources**:

| Source | Coverage | Access | Cost |
|--------|----------|--------|------|
| **ktMINE Royalty Rates** | Industry averages from 500K+ agreements | Subscription database | $10K-30K/year |
| **RoyaltyRange** | Royalty statistics by industry | Subscription database | $5K-15K/year |
| **LES (Licensing Executives Society) Royalty Survey** | Biennial survey with industry breakdowns | Published report (LES members) | ~$200-500 for report |
| **Academic Papers** | Case studies, industry analyses | Google Scholar (free) | FREE but may be dated |
| **UpCounsel / General Publications** | General ranges by industry | Web search | FREE but less rigorous |

**Typical Royalty Rates by Industry** (from web search):

| Industry | Typical Range | Notes |
|----------|---------------|-------|
| Software | 10-15% | Higher due to high margins |
| Pharmaceuticals/Biotech | 5-10% | High value but long development |
| Medical Devices | 3-7% | Moderate |
| Automotive | 1-3% | Low margins, competitive |
| Consumer Electronics | 2-5% | Volume dependent |
| Manufacturing | 2-4% | Low margins |
| Telecommunications | 3-6% | Standards-essential patents higher |

**How Royalty Rates Connect to Valuation**:

In Income Method:
```
If we know the typical royalty rate for the industry, we can use it to estimate IP Contribution Factor:

IP_Contribution_Factor ≈ Royalty_Rate / Profit_Margin

Example:
Industry royalty rate: 5%
Company profit margin: 25%
IP Contribution Factor = 5% / 25% = 0.20 (20% of profits attributable to patent)
```

This provides a **market-based anchor** for the IP contribution factor assumption.

---

## 4. Data Source Verification

### 4.1 Free Government/Public Sources

| Source | URL | Authentication | Rate Limits | Data Quality | Verified? |
|--------|-----|----------------|-------------|--------------|-----------|
| **USPTO PatentsView** | https://api.patentsview.org | None | Fair use (no hard limit) | HIGH | ✅ VERIFIED (tested) |
| **EPO OPS** | https://ops.epo.org | OAuth (free registration) | 10 req/min, 5000/month | HIGH | ✅ VERIFIED (documented) |
| **Google Patents** | https://patents.google.com | None (BigQuery needs GCP) | None for web, GCP pricing for BigQuery | HIGH | ✅ VERIFIED |
| **Damodaran Industry Data** | https://pages.stern.nyu.edu/~adamodar/ | None | None | HIGH (academic source) | ✅ VERIFIED |
| **USPTO Assignment Database** | https://assignment.uspto.gov/patent/index.html | None | Bulk download | MEDIUM (no prices) | ✅ VERIFIED |

**Conclusion**: All basic patent data and financial benchmarks are **freely accessible**.

---

### 4.2 Commercial Sources (Subscription Required)

| Source | What's Critical | Annual Cost (Est.) | Workaround if Not Available |
|--------|-----------------|-------------------|----------------------------|
| **ktMINE** | Comparable transaction values, royalty rates | $10K-30K | Use Income Method only; manual SEC search for comparables |
| **RoyaltyRange** | Royalty rate benchmarks | $5K-15K | Academic papers, LES survey (less comprehensive) |
| **Market Research Firms** (Gartner, Forrester, etc.) | Market size, growth rates | $1K-5K per report | Free sources (Wikipedia, industry associations), less reliable |

**Critical Assessment**:

**Can we do patent valuation WITHOUT commercial subscriptions?**
- ✅ **YES for Income Method**: All required data available from free sources
  - Exception: Revenue projections (need company cooperation OR market estimation)
- ⚠️ **DIFFICULT for Market Method**: Comparables are mostly in paid databases
  - Workaround: Manual search of SEC filings, but very time-consuming and incomplete
- ✅ **YES for Hybrid Validation**: Can use free royalty rate ranges from academic sources to sanity-check income method

**Recommendation**: Start with **Income Method using free data**. Add Market Method later if budget allows for ktMINE/RoyaltyRange.

---

## 5. Critical Gaps and Challenges

### 5.1 Data Availability Gaps

| Gap | Impact | Frequency | Mitigation |
|-----|--------|-----------|------------|
| **No comparable transactions found** | Cannot use Market Method | COMMON (most transactions confidential) | Fallback to Income Method only |
| **Company won't share revenue data** | Must estimate from market size | COMMON for private companies | Use market size × estimated share |
| **No market size data for niche tech** | Hard to project revenue | OCCASIONAL | Use broader category as proxy |
| **IP contribution factor uncertain** | High variance in valuation | VERY COMMON | Use conservative estimate + sensitivity analysis |

### 5.2 Assumption Sensitivity

**Most Sensitive Assumptions** (ranked by impact on valuation):

1. **Discount Rate**: ±5% → ±30-50% valuation change
2. **IP Contribution Factor**: ±0.1 → ±20-30% valuation change
3. **Revenue Growth Rate**: ±5% CAGR → ±15-25% valuation change
4. **Profit Margin**: ±5% → ±5-10% valuation change

**Implication**: Since these assumptions are often estimates, valuation ranges (low-base-high) are more appropriate than point estimates.

### 5.3 Data Quality Issues

| Issue | Example | How to Address |
|-------|---------|----------------|
| **Outdated market data** | Market report from 2020 used for 2025 valuation | Adjust for known industry changes; flag as limitation |
| **Low similarity comparables** | Best comparable is only 45% similar | Flag as weak comparable; widen valuation range |
| **Missing patent data** | Some citations not in database | Note data completeness %; flag if <80% complete |
| **Conflicting sources** | Two market reports give different market sizes | Use average; show range; document both sources |

---

## 6. Step-by-Step Calculation Walkthrough

### Scenario: Valuing Patent US10123456B2

**Patent**: Wireless charging system for electric vehicles
**Assignee**: AutoTech Inc. (private company)
**Context**: Internal portfolio valuation (medium precision)

---

### STEP 1: Gather Patent Data (Free Sources)

**USPTO PatentsView API Call**:
```json
{
  "q": {"patent_number": "10123456"},
  "f": ["patent_title", "patent_date", "patent_abstract",
        "cpc_group_id", "citedby_patent_number", "claim_text",
        "inventor_first_name", "assignee_organization"]
}
```

**Data Retrieved**:
- **Title**: "Wireless Power Transfer System for Electric Vehicles"
- **Grant Date**: 2018-11-13
- **Expiration Date**: 2038-11-13 (Grant + 20 years)
- **Remaining Life**: 13 years (2025 to 2038)
- **CPC Codes**: [H02J 50/10, H01M 10/44, B60L 53/12]
- **Forward Citations**: 47 citations
- **Independent Claims**: 6
- **Assignee**: AutoTech Inc.

**EPO OPS API Call** (for family):
- **INPADOC Family Size**: 12 (US, EP, CN, JP, KR filings)

**Patent Strength Score**:
```
Citations: (47 / 7 years) × 10 = 67 × 0.30 = 20.1
Family: min(12, 20) × 5 = 60 × 0.25 = 15
Claims: min(6, 10) × 10 = 60 × 0.25 = 15
Legal: All fees paid (verified) = 75 × 0.20 = 15
Total Strength: 65.1/100 (MEDIUM-HIGH)
```

---

### STEP 2: Market & Financial Data (Mixed Sources)

**Market Size** (web search: "electric vehicle wireless charging market size"):
- Source: Allied Market Research (2024)
- Current Market: $1.2 billion (2024)
- Projected CAGR: 18% (2024-2030)

**Industry Data** (Damodaran):
- Industry: Automotive
- Base WACC: 9.5%

**Company Data** (provided by stakeholder):
- AutoTech Inc. Revenue: $50 million (2024)
- Product Line: EV charging infrastructure (wireless + wired)
- This patent covers: Wireless charging product line only

**Profit Margin** (industry benchmark):
- Automotive suppliers: 8-12% net margin (typical)
- Use: 10% (conservative)

---

### STEP 3: Calculate IP Contribution Factor

**Challenge**: How much of AutoTech's wireless charging revenue is due to THIS patent?

**Analysis**:
- AutoTech has 3 patents total in wireless charging
- This patent (US10123456B2) is the **core technology patent**
- Other 2 patents are improvements/variants

**Method**: Feature analysis + industry benchmarks

**Royalty Rate Benchmark** (from web search):
- Automotive licensing: 1-3% typical
- Advanced technology features: 2-4%
- Use: 3% (middle range for advanced feature)

**Calculation**:
```
IP Contribution Factor = Royalty_Rate / Profit_Margin
                       = 3% / 10%
                       = 0.30 (30% of profits attributable to patent)
```

**Rationale**:
- Core technology patent (not minor improvement) → Higher contribution
- Part of 3-patent portfolio → Not 100% of value
- Wireless charging is a premium feature → Supports higher rate
- Conservative: Use 30% (could argue 40-50% for core patent)

**ASSUMPTION LOGGED**: "IP Contribution Factor = 0.30 based on 3% royalty rate benchmark (automotive advanced features) divided by 10% profit margin. Conservative estimate given this is core technology patent in 3-patent portfolio."

---

### STEP 4: Calculate Discount Rate

**Base WACC**: 9.5% (automotive industry, Damodaran 2024)

**Patent Risk Premium Components**:
1. **Technology Maturity**: Mature (commercial products exist) → +3%
2. **Portfolio Dependency**: Core patent but with 2 supporting patents → +2%
3. **Litigation Risk**: No litigation history → +1%

**Total Discount Rate**: 9.5% + 6% = **15.5%**

**ASSUMPTION LOGGED**: "Discount rate 15.5% = Base WACC 9.5% (automotive industry) + Patent risk premium 6% (mature tech +3%, moderate dependency +2%, low litigation risk +1%)."

---

### STEP 5: Project Revenue (Income Method)

**Revenue Attribution**:
- AutoTech total revenue: $50M
- Wireless charging product line: ~20% of revenue = $10M
- Revenue attributable to this patent: $10M (entire product line, since it's core patent)

**Growth Projection**:
- Market CAGR: 18%
- Assume AutoTech grows with market
- Revenue_year_t = $10M × (1.18)^t

**Projection Table** (13 years remaining):

| Year | Revenue | Profit (10%) | IP Cash Flow (30%) | Discount Factor | Present Value |
|------|---------|--------------|---------------------|-----------------|---------------|
| 1 | $11.8M | $1.18M | $354K | 0.866 | $307K |
| 2 | $13.9M | $1.39M | $417K | 0.750 | $313K |
| 3 | $16.4M | $1.64M | $492K | 0.649 | $319K |
| 4 | $19.4M | $1.94M | $582K | 0.562 | $327K |
| 5 | $22.9M | $2.29M | $687K | 0.487 | $335K |
| ... | ... | ... | ... | ... | ... |
| 13 | $64.5M | $6.45M | $1.94M | 0.163 | $316K |

**Terminal Value** (beyond year 13, patent expires):
- No terminal value (patent protection ends)

**Total NPV**: $4,285,000

**ASSUMPTION LOGGED**: "Revenue projection: $10M base (wireless charging product line) growing at 18% CAGR (market growth). Conservative: assumes AutoTech maintains market position."

---

### STEP 6: Sensitivity Analysis

Test ±20% changes in key assumptions:

| Variable | Base Value | Low (-20%) | High (+20%) | Valuation Change |
|----------|-----------|------------|-------------|------------------|
| **Discount Rate** | 15.5% | 12.4% | 18.6% | $5.4M to $3.5M (-18% to +22%) |
| **IP Contribution** | 0.30 | 0.24 | 0.36 | $3.4M to $5.1M (-20% to +20%) |
| **Growth Rate** | 18% | 14.4% | 21.6% | $3.7M to $5.1M (-14% to +19%) |
| **Profit Margin** | 10% | 8% | 12% | $3.4M to $5.1M (-20% to +20%) |

**Key Finding**: Valuation ranges from **$3.4M to $5.4M** depending on assumptions.

---

### STEP 7: Market Method (if comparables available)

**Data Source**: ktMINE search (hypothetical - requires subscription)

**Search Parameters**:
- Technology: Wireless power transfer (H02J 50/10)
- Date range: 2020-2024
- Transaction type: License or sale

**Results** (hypothetical):
- 3 comparable transactions found
- Average transaction value (adjusted): $4.8M
- Technology similarity scores: 0.68, 0.72, 0.61

**Market Method Valuation**: $4.8M (average of comparables)

**Cross-Validation**:
- Income Method: $4.3M
- Market Method: $4.8M
- Difference: 11% (strong alignment)

**Recommended Valuation**: $4.5M (average of both methods)
**Confidence**: HIGH (methods align, good data quality)

---

### STEP 8: Final Valuation Report

**Patent**: US10123456B2 - Wireless Power Transfer System for EVs
**Date**: 2025-11-11
**Context**: Internal portfolio valuation

**Recommended Valuation**: $4.5 million
**Valuation Range**: $3.4M - $5.4M (low - high)
**Confidence Level**: Medium-High

**Methodology**:
- Primary: Income Method (DCF)
- Validation: Market Method (comparables)
- Methods aligned within 11%

**Key Assumptions** (High Impact):
1. Discount rate: 15.5% (industry WACC + patent risk)
2. IP contribution factor: 30% (based on 3% royalty benchmark)
3. Revenue growth: 18% CAGR (market growth rate)
4. Profit margin: 10% (industry average)

**Data Sources**:
- Patent data: USPTO PatentsView API
- Market size: Allied Market Research (2024)
- Industry benchmarks: Damodaran (NYU Stern)
- Comparables: ktMINE database (3 transactions)

**Sensitivity**:
- Most sensitive to discount rate (±5% → ±30% valuation)
- Valuation range reflects ±20% assumption variance

**Limitations**:
- Point-in-time valuation (valid for 6 months)
- Based on market size estimates (not company-specific guidance)
- IP contribution factor estimated (no licensing data)
- Technology/market conditions may change

---

## Summary: What Data We Actually Need

### Absolutely Required (Cannot Value Without):
1. ✅ **Patent number** (to look up everything else)
2. ✅ **Grant date** (to calculate remaining life)
3. ✅ **Technology field** (IPC/CPC codes) - for industry benchmarks
4. ⚠️ **Revenue OR Market size** - to project cash flows
5. ⚠️ **Discount rate components** - WACC + risk premium

### Highly Valuable (Significantly Improves Quality):
6. ✅ **Forward citations** - for strength assessment
7. ✅ **Patent family size** - for strength/coverage assessment
8. ⚠️ **Comparable transactions** - for market method validation
9. ⚠️ **Royalty rate benchmarks** - for IP contribution anchor
10. ⚠️ **Profit margins** - for cash flow calculation

### Nice to Have (Refines Assumptions):
11. ✅ **Litigation history** - for risk assessment
12. ✅ **Claims analysis** - for strength/breadth
13. ⚠️ **Company-specific financials** - better than estimates
14. ⚠️ **Technology lifecycle stage** - refines risk premium

**Legend**:
- ✅ Available from FREE sources
- ⚠️ May require PAID sources or ESTIMATION

---

## Critical Insights for System Design

1. **Income Method is Fully Feasible with Free Data** - IF we can estimate or obtain revenue projections
2. **Market Method Requires Commercial Subscription** - ktMINE or RoyaltyRange essential for quality comparables
3. **IP Contribution Factor is the Weakest Link** - Most subjective, highest impact, hardest to validate
4. **Valuation Ranges > Point Estimates** - Given uncertainty, always provide low-base-high
5. **Assumption Documentation is Non-Negotiable** - Every assumption must have rationale and source
6. **Sensitivity Analysis is Essential** - Show how valuation changes with assumption changes
7. **Cross-Validation Increases Confidence** - Using both methods (when possible) provides validation

---

**Next Step**: With this data foundation established, we can now thoughtfully design:
- What agents are needed (one per data source type?)
- How to handle estimation when data is missing
- How to structure assumption tracking
- How to orchestrate data gathering and calculation

But those are questions for AFTER we've agreed this data foundation is correct.
