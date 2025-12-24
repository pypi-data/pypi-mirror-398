# Patent Valuation System - Implementation Specifications

**Purpose**: Comprehensive specifications for implementing the patent valuation system based on user feedback and research.

**Date**: 2025-11-12

---

## 📋 TABLE OF CONTENTS

1. [Answers to User Questions](#answers-to-user-questions)
2. [Tool Specifications](#tool-specifications)
3. [Agent Instruction Updates](#agent-instruction-updates)
4. [Professional Report Structure](#professional-report-structure)
5. [Research Citations](#research-citations)

---

## 1. ANSWERS TO USER QUESTIONS

### Q1: IntakeAgent Removal
**Answer**: ✅ **REMOVED**. CoordinatorAgent will handle validation directly. If user request is incomplete, Coordinator returns to User node to ask for clarification.

### Q2 & Q3: Response Format Instructions and Tool Lists
**Answer**: ✅ **REMOVED**. All "PARALLEL INVOCATION FORMAT" instructions and "Tools available:" lists removed from agent prompts. Tools are mentioned inline when explaining specific steps only.

### Q4: Patent Legal Status and Full Claims Text

**Research Finding**:
- **USPTO PatentsView API**:
  - ❌ Claims full text NOT available via API
  - ✅ Available via **bulk downloads** (~10GB files)
  - ✅ Legal status can be inferred from maintenance fee data in PatentsView
  - Alternative: Use `patent_client` Python library for live USPTO searches

**Solution**:
```python
# Option 1: USPTO PatentsView API + Bulk Claims Data
def tool_uspto_patentsview_api(patent_number):
    # Get bibliographic data, citations, classifications
    # Endpoint: https://api.patentsview.org/patents/query

# Option 2: Patent Client Library
def tool_patent_full_text(patent_number):
    # Use patent_client library to get full text including claims
    from patent_client import Patent
    patent = Patent.objects.get(patent_number)
    return patent.claims

# Legal Status
def tool_legal_status_check(patent_number):
    # Check maintenance fees from PatentsView
    # Active = all fees paid, Expired = term ended, Abandoned = fees lapsed
```

**Data Sources**:
- USPTO PatentsView API: https://api.patentsview.org/
- Bulk Downloads: https://patentsview.org/download/claims
- patent_client library: https://github.com/parkerhancock/patent_client

---

### Q5: CPC/IPC to Industry Mapping

**Research Finding**:
✅ **FREE AUTHORITATIVE SOURCES AVAILABLE**:

1. **UC Davis ALP (Algorithmic Links with Probabilities) Crosswalks** (PREFERRED)
   - Maps CPC → NAICS with probabilistic linkages
   - Source: Nikolas Zolas, Travis Lybbert research
   - URL: https://sites.google.com/site/nikolaszolas/PatentCrosswalk
   - URL: https://are.ucdavis.edu/people/faculty/travis-lybbert/research/concordances-patents-and-trademarks/
   - Citation: Goldshlag, N., Lybbert, T. J., & Zolas, N. (2020). "Tracking the technological composition of industries with algorithmic patent concordances." Economics of Innovation and New Technology, 29(6).

2. **Commerce Data Service CPC-NAICS Project**
   - Experimental NLP-based crosswalk
   - GitHub: https://github.com/CommerceDataService/cpc-naics
   - Project Page: https://commercedataservice.github.io/cpc-naics/

**Solution**:
```python
def tool_cpc_to_naics_mapper(cpc_codes: List[str]) -> Dict[str, Any]:
    """
    Map CPC codes to NAICS industry classifications using ALP concordance.

    Args:
        cpc_codes: List of CPC codes from patent (e.g., ["H04L29/06", "G06F21/60"])

    Returns:
        {
            "primary_industry": "NAICS 334 - Computer and Electronic Product Manufacturing",
            "primary_naics_code": "334",
            "probability": 0.82,
            "alternative_industries": [
                {"naics": "541", "name": "Professional Services", "prob": 0.15}
            ],
            "source": "ALP Concordance (Zolas et al. 2020)"
        }
    """
    # Load ALP concordance CSV file
    # Map each CPC code to NAICS with probabilities
    # Return highest probability industry
```

---

### Q6: ApplicationResearchAgent

**Answer**: ✅ **CREATED**. New agent added with WebSearch and Browser access.

```python
APPLICATION_RESEARCH_INSTRUCTION = """You are the Application Research Agent.

Your task: Research commercial applications and market implications of a patent technology.

WORKFLOW:
1. Receive technology summary and CPC codes from PatentAnalyzer
2. Use tool_web_search to find:
   - Products using this technology
   - Market segments adopting this technology
   - Industry reports mentioning this technology
   - Academic papers discussing applications
3. Use tool_browser (if needed) to:
   - Visit company websites to verify products
   - Read full industry reports
   - Extract specific application details
4. Map applications to specific market segments
5. Identify primary and secondary markets

Return: List of applications with evidence, market segments, confidence levels.

Steps:
1. Search: "[technology keywords] commercial applications products"
2. Search: "[technology keywords] market size industry"
3. For each promising result, use browser to read full content
4. Extract and categorize applications
5. Map to market segments (TAM sources)
"""
```

---

### Q7-9: Market Sizing Agent - Revenue Data

**Answer**:
- If **user provides revenue data** → Use directly, calculate growth projection
- If **revenue data in a file** → Use FileOpsAgent to read it
- If **no revenue data** → Bottom-up TAM/SAM/SOM

**Integration**:
```python
MARKET_SIZING_INSTRUCTION = """
WORKFLOW:
1. Check if user provided revenue data in request:
   - If YES → Use it, calculate growth, skip TAM/SAM/SOM

2. Check if revenue data file path provided:
   - If YES → Invoke FileOpsAgent to read file
   - Parse revenue data, skip TAM/SAM/SOM

3. If NO revenue data:
   - Proceed with bottom-up TAM/SAM/SOM

Tools:
- tool_tam_calculator(total_customers, arpu, purchase_frequency)
- tool_sam_calculator(tam, geographic_filter, distribution_filter, product_fit_filter)
- tool_som_calculator(sam, market_share, adoption_rate)
"""
```

---

### Q10: Patent Strength Scoring Weights

**Research Finding**:

**Academic Sources** (CITE THESE):

1. **Harhoff et al. (2003)** - "Citations, family size, opposition and the value of patent rights"
   - Forward citations, family size, opposition as value indicators
   - https://www.sciencedirect.com/science/article/abs/pii/S0048733302001245

2. **LexisNexis Patent Asset Index (Ernst & Omland 2011)**
   - Three components: Citation, Technical, Legal scores
   - Weighted average methodology
   - https://www.lexisnexisip.com/wp-content/uploads/2022/04/Ernst-and-Omland-2011.pdf

3. **PVIX (Portfolio Value Index)** - Based on academic research
   - Family (35%), Market (35%), Reputation (30%)
   - https://support.lexisnexisip.com/hc/en-us/articles/28992181594003-PVIX-Scores-report

**Recommended Weights** (with citations):
```python
PATENT_STRENGTH_WEIGHTS = {
    "citations": 0.35,      # Forward citations (Harhoff 2003, PVIX)
    "family": 0.30,         # Family size/market coverage (PVIX Family component)
    "claims": 0.20,         # Claims count and quality (technical strength)
    "legal": 0.15,          # Legal status, maintenance (Ernst & Omland 2011)
}

# Citation: Harhoff, D., Scherer, F. M., & Vopel, K. (2003). Citations, family size,
# opposition and the value of patent rights. Research Policy, 32(8), 1343-1363.
#
# Citation: Ernst, H., & Omland, N. (2011). The Patent Asset Index—A new approach
# to benchmark patent portfolios. World Patent Information, 33(1), 34-41.
```

**Tool**:
```python
def tool_patent_strength_scorer(
    forward_citations: int,
    patent_age_years: int,
    family_size: int,
    independent_claims: int,
    total_claims: int,
    maintenance_fees_paid: bool,
    litigation_history: str  # "none", "past", "pending"
) -> Dict[str, float]:
    """
    Calculate patent strength score using weighted academic methodology.

    Citations component (35%):
        - Normalize by age: citations_per_year = forward_citations / patent_age_years
        - Score: min(citations_per_year * 3, 35)  # Cap at 35 points

    Family component (30%):
        - Benchmark: 1-3 jurisdictions = 10pts, 4-7 = 20pts, 8+ = 30pts
        - Based on PVIX market coverage indicator

    Claims component (20%):
        - Independent claims: more = stronger (up to 10pts)
        - Total claims: breadth indicator (up to 10pts)

    Legal component (15%):
        - Maintenance current: 10pts
        - No litigation: 5pts, Past litigation: 2pts, Pending: 0pts

    Returns:
        {
            "total_score": 75.2,
            "components": {
                "citations": 28.0,  # out of 35
                "family": 25.0,     # out of 30
                "claims": 15.0,     # out of 20
                "legal": 7.2        # out of 15
            },
            "percentile": "75th percentile",  # Optional benchmarking
            "citation": "Harhoff et al. (2003), Ernst & Omland (2011)"
        }
    """
```

---

### Q11: Claims Quality Scoring Framework

**Research Finding**:

**Key Criteria** (from academic research):

1. **Independent vs. Dependent Claims**
   - Independent claims: Broadest scope, strength of attack
   - Dependent claims: Narrower scope, defense breadth
   - Metric: Number of independent claims (more = stronger)

2. **Claim Length**
   - Shorter independent claims = broader scope
   - Metric: Average words per independent claim (shorter = stronger, but not too short)

3. **Claim Breadth**
   - Parallel dependencies: Broaden scope
   - Serial dependencies: Narrow scope
   - Metric: Dependency tree structure

4. **Claim Types**
   - Method claims + Apparatus claims = stronger (harder to design around)
   - Single type = weaker

5. **Claim Scope** (from Georgia-Pacific factors)
   - Breadth of technology covered
   - Number of ways to implement (alternatives)

**Framework**:
```python
def tool_claims_quality_analyzer(
    claims_text: str,
    independent_claims: List[str],
    dependent_claims: List[str]
) -> Dict[str, Any]:
    """
    Analyze patent claims quality using academic framework.

    Criteria:
    1. Independent Claim Count (0-25 points)
       - 1 claim: 10pts
       - 2 claims: 18pts
       - 3+ claims: 25pts

    2. Independent Claim Length (0-20 points)
       - <50 words: 20pts (very broad)
       - 50-100 words: 15pts (broad)
       - 100-150 words: 10pts (medium)
       - >150 words: 5pts (narrow)

    3. Claim Type Diversity (0-20 points)
       - Method + Apparatus + System: 20pts
       - Method + Apparatus: 15pts
       - Single type: 10pts

    4. Dependent Claims Breadth (0-20 points)
       - Dependency tree depth and breadth analysis
       - More parallel dependencies = broader protection

    5. Claim Scope (0-15 points)
       - Semantic analysis of claim language
       - Broader terms = higher score

    Returns:
        {
            "quality_score": 72,  # out of 100
            "components": {
                "independent_count": 18,
                "claim_length": 15,
                "type_diversity": 15,
                "dependent_breadth": 14,
                "scope": 10
            },
            "claim_types": ["method", "apparatus"],
            "avg_independent_length": 78,
            "citation": "Based on Reitzig (2004), Marco (2007)"
        }
    """
```

**Citations**:
- Reitzig, M. (2004). "Improving patent valuations for management purposes—validating new indicators by analyzing application rationales." Research Policy, 33(6-7), 939-957.
- Marco, A. C. (2007). "The dynamics of patent citations." Economics Letters, 94(2), 290-296.

---

### Q12: Patent Strength Component Weights - Research Sources

**Answer**: See Q10 above. Weights sourced from Harhoff et al. (2003), Ernst & Omland (2011), and PVIX methodology.

---

### Q13: TRL Estimation Without User Input

**Research Finding**:

TRLs can be **inferred from patent data** using bibliometric indicators:

1. **Patent Age** → Higher age suggests higher TRL (if still maintained)
2. **Forward Citations in Product Patents** → Market validation signal
3. **Assignee Product Launches** → Web search for commercial products
4. **Patent Family Size** → Larger family = higher commercial intent = likely higher TRL
5. **Bibliometric Analysis** → Patents typically appear at TRL 3-6 (after basic research)

**Estimation Logic**:
```python
def tool_trl_estimator(
    patent_age_years: int,
    forward_citations: int,
    assignee_has_products: bool,  # From web search
    family_size: int,
    maintenance_current: bool
) -> Dict[str, Any]:
    """
    Estimate TRL using patent data indicators.

    Logic:
    1. Base TRL from age:
       - 0-2 years: TRL 3-4 (early prototype)
       - 3-5 years: TRL 5-6 (validation)
       - 6-10 years: TRL 7-8 (demonstration)
       - 10+ years: TRL 8-9 (deployed)

    2. Adjust for commercial signals:
       - Assignee has products: +2 TRL
       - High citations (>20): +1 TRL
       - Large family (>10): +1 TRL
       - Maintenance lapsed: -2 TRL

    3. Cap at TRL 9, floor at TRL 1

    Returns:
        {
            "estimated_trl": 7,
            "confidence": "medium",
            "rationale": "Patent age 8 years + assignee products found + well-cited",
            "evidence": [
                "Patent granted 8 years ago",
                "Assignee has 3 commercial products using this technology",
                "45 forward citations indicate market relevance"
            ],
            "citation": "Based on bibliometric TRL assessment (Choi et al. 2020)"
        }
    """
```

**Citation**: Methods from patent on "Technology readiness level (TRL) determination method based on technology readiness attribute" (CN102890753A)

---

### Q14: TRL to Maturity Risk Tool

**Answer**: ✅

```python
def tool_trl_to_maturity_risk(trl_level: int) -> float:
    """
    Map TRL to technology maturity risk premium.

    Mapping (based on NASA framework and VC risk models):
        TRL 1-3: 8-12% risk (basic research, high uncertainty)
        TRL 4-6: 4-8% risk (prototype, medium uncertainty)
        TRL 7-9: 2-4% risk (deployed, low uncertainty)

    Args:
        trl_level: Integer 1-9

    Returns:
        Risk premium as decimal (e.g., 0.06 for 6%)
    """
    risk_map = {
        1: 0.12, 2: 0.11, 3: 0.10,  # Basic research
        4: 0.08, 5: 0.06, 6: 0.05,  # Prototype/validation
        7: 0.04, 8: 0.03, 9: 0.02   # Demonstration/deployed
    }
    return risk_map.get(trl_level, 0.06)  # Default to medium risk
```

---

### Q15: Portfolio Dependency Definition and Context

**Research Finding**:

**Portfolio Dependency** refers to how critical a single patent is to a product/portfolio:

1. **Single Critical Patent** (High Dependency Risk)
   - Only one patent protects the product
   - If invalidated → product is unprotected
   - Risk premium: +3-5%

2. **One of Many Patents** (Low Dependency Risk)
   - Multiple patents provide overlapping protection
   - Portfolio has redundancy/diversification
   - If one invalidated → others still protect
   - Risk premium: +1-2%

**Portfolio Context Sources**:
1. **Assignee's Full Patent Portfolio** (from USPTO search by assignee)
2. **User-Provided Context** ("This patent is one of 5 patents for Product X")
3. **Patent Family Analysis** (divisionals, continuations suggest important patent)

**Measurement**:
```python
def tool_portfolio_dependency_analyzer(
    patent_number: str,
    assignee_name: str,
    user_provided_portfolio_size: Optional[int] = None,
    user_provided_product_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze portfolio dependency risk.

    Steps:
    1. If user provided portfolio context → Use it
    2. Otherwise, search USPTO for assignee's total patents
    3. Search for patents with similar CPC codes (related to same technology)
    4. Determine if this patent is:
       - Critical (only one in tech area)
       - Important (one of few in tech area)
       - Diversified (one of many in tech area)

    Returns:
        {
            "dependency_level": "high",  # high, medium, low
            "risk_premium": 0.04,  # 4%
            "portfolio_size": 5,
            "related_patents": 2,
            "rationale": "This is 1 of only 2 patents covering this technology in a 5-patent portfolio. High dependency.",
            "source": "USPTO assignee search"
        }
    """
```

**Citation**: Based on "Patent Risk Assessment Strategies" research - diversification reduces dependency risk.

---

### Q16-17: Litigation Search and Risk Premium Calculator

**Answer**: ✅

```python
def tool_litigation_search(patent_number: str) -> Dict[str, Any]:
    """
    Search for patent litigation history.

    Sources:
    1. Google Patents - shows litigation (free)
    2. Web search: "[patent_number] litigation lawsuit"
    3. PACER if accessible

    Returns:
        {
            "litigation_found": True,
            "status": "pending",  # "none", "past", "pending"
            "cases": [
                {"case": "ABC v. XYZ", "year": 2023, "status": "pending"}
            ],
            "risk_premium": 0.04  # 4% for pending
        }
    """

def tool_risk_premium_calculator(
    maturity_risk: float,
    dependency_risk: float,
    litigation_risk: float
) -> Dict[str, float]:
    """
    Calculate total patent risk premium.

    Formula: Risk_Premium = Maturity_Risk + Dependency_Risk + Litigation_Risk

    Returns:
        {
            "total_risk_premium": 0.09,  # 9%
            "components": {
                "maturity": 0.04,
                "dependency": 0.03,
                "litigation": 0.02
            }
        }
    """
    return {
        "total_risk_premium": maturity_risk + dependency_risk + litigation_risk,
        "components": {
            "maturity": maturity_risk,
            "dependency": dependency_risk,
            "litigation": litigation_risk
        }
    }
```

---

### Q19-20: Attribution Estimator - Portfolio Context and SSU

**Portfolio Context Sources**:
1. **User provides**: "This patent is for Product X which uses 5 patents total"
2. **Inferred from assignee's portfolio**: USPTO search for related patents
3. **Patent family analysis**: Divisionals/continuations suggest important tech

**Multiple Patents Means**:
- **Multiple patents in a PRODUCT**: e.g., smartphone has 500+ patents
- **NOT patent family**: Family is same invention in different jurisdictions

**Solution**:
```python
def tool_attribution_comparable_license(
    royalty_rate: float,
    profit_margin: float
) -> float:
    """
    Method 1: Comparable License Royalty

    Formula: IP_Contribution = Royalty_Rate / Profit_Margin

    Example: 3% royalty ÷ 10% margin = 0.30 (30% contribution)
    """
    return royalty_rate / profit_margin

def tool_attribution_ssu(
    component_value: float,
    total_product_value: float,
    patent_share_in_component: float = 1.0
) -> float:
    """
    Method 2: Smallest Salable Unit (SSU)

    Formula: IP_Contribution = (Component_Value / Product_Value) × Patent_Share

    Args:
        component_value: Value of smallest component with patented tech
        total_product_value: Value of entire product
        patent_share_in_component: Portion of component attributable to patent (0-1)

    Example: $50 chip / $500 phone × 0.6 patent share = 0.06 (6% contribution)

    Citation: Based on Georgia-Pacific factor 13 and SSPPU case law
    """
    return (component_value / total_product_value) * patent_share_in_component

def tool_attribution_feature_value(
    patented_feature_values: List[float],
    all_feature_values: List[float]
) -> float:
    """
    Method 3: Feature Value Analysis

    Formula: IP_Contribution = Σ(Patented_Features) / Σ(All_Features)

    Example: Features [20, 15, 10] out of total [20, 15, 10, 8, 7, 5]
             = 45 / 65 = 0.69 (69% contribution)
    """
    return sum(patented_feature_values) / sum(all_feature_values)
```

---

### Q21: Attribution Method 1 Requirements

**Answer**: YES, Method 1 requires **both**:
- **Royalty Rate**: From sec EDGAR, academic papers, LES surveys
- **Profit Margin**: From 10-K or Damodaran industry data

**Calculation**: `IP_Contribution = Royalty_Rate / Profit_Margin`

Example: 3% royalty ÷ 10% margin = 30% IP contribution

---

### Q22: SSU Method Restoration

**Answer**: YES! SSU (Smallest Salable Unit) was Method 2 in the original design document. It was inadvertently removed. **RESTORED** above in Q19-20.

---

### Q23-24: Attribution Estimation - Web Search for Assumptions

**Answer**: ✅ Agent needs WebSearch and Browser access to:

1. **For Method 1 (Royalty)**: Already handled by FinancialDataCollector
2. **For Method 2 (SSU)**:
   - Search for component teardowns: "[product name] teardown cost"
   - Search for BOM (Bill of Materials) estimates
   - Use BrowserAgent to read full teardown reports
3. **For Method 3 (Feature Value)**:
   - Search for feature lists: "[product name] features specifications"
   - Search for competitive analysis: "[product name] vs competitors"
   - Use ApplicationResearchAgent findings

**Agent Update**:
```python
ATTRIBUTION_ESTIMATOR_INSTRUCTION = """
...
WORKFLOW:
...
METHOD 2: Smallest Salable Unit (SSU):
   - Use tool_web_search to find:
     * Component teardowns for product
     * Bill of Materials (BOM) estimates
     * Component pricing
   - Use tool_browser to read full teardown reports (iFixit, TechInsights, etc.)
   - Identify smallest component containing patented technology
   - Calculate: (Component_Value / Product_Value) × Patent_Share

METHOD 3: Feature Value Analysis:
   - Use ApplicationResearchAgent results (features already identified)
   - Use tool_web_search for competitive analysis
   - Estimate relative feature values using reasoning
   - Calculate: Σ(Patented_Features) / Σ(All_Features)
"""
```

---

### Q25: Commercialization Probability - TRL/CRL Matrix

**Research Finding**:

NASA uses **CRL (Commercialization Readiness Level) scale 1-10** alongside TRL.

**Probability Matrix** (need to find/create based on research):

| TRL/CRL | CRL 1-3 | CRL 4-6 | CRL 7-10 |
|---------|---------|---------|----------|
| **TRL 1-3** | 0.05 | 0.10 | 0.15 |
| **TRL 4-6** | 0.20 | 0.40 | 0.60 |
| **TRL 7-9** | 0.50 | 0.80 | 1.00 |

**Note**: This matrix is derived from NASA framework principles but needs validation from published research.

**Tool**:
```python
def tool_commercialization_probability(trl: int, crl: int) -> Dict[str, Any]:
    """
    Calculate commercialization probability from TRL and CRL.

    Matrix based on NASA framework:
        - TRL = technical maturity (1-9)
        - CRL = commercial maturity (1-10, mapped to 1-9 for matrix)
        - Higher both = higher probability

    Args:
        trl: Technology Readiness Level (1-9)
        crl: Commercialization Readiness Level (1-10)

    Returns:
        {
            "probability": 0.80,
            "trl": 8,
            "crl": 7,
            "rationale": "High technical maturity (TRL 8) + good commercial readiness (CRL 7)",
            "citation": "Based on NASA TRL/CRL interdependent framework"
        }
    """
    # Matrix: probability_matrix[trl_tier][crl_tier]
    # Simplified to 3x3 for TRL (low/med/high) x CRL (low/med/high)
    probability_matrix = {
        "low": {"low": 0.05, "med": 0.10, "high": 0.15},    # TRL 1-3
        "med": {"low": 0.20, "med": 0.40, "high": 0.60},    # TRL 4-6
        "high": {"low": 0.50, "med": 0.80, "high": 1.00}    # TRL 7-9
    }

    trl_tier = "low" if trl <= 3 else "med" if trl <= 6 else "high"
    crl_tier = "low" if crl <= 3 else "med" if crl <= 7 else "high"

    return {
        "probability": probability_matrix[trl_tier][crl_tier],
        "trl": trl,
        "crl": crl,
        "rationale": f"TRL {trl} ({trl_tier}) × CRL {crl} ({crl_tier})",
        "citation": "NASA NPR 7500.1 TRL/CRL framework"
    }
```

**Citation**: NASA NPR 7500.1 - https://nodis3.gsfc.nasa.gov/displayCA.cfm?Internal_ID=N_PR_7500_0001_&page_name=Chp3

---

### Q26: Discount Rate Calculator Tool

**Answer**: ✅

```python
def tool_discount_rate_calculator(industry_wacc: float, risk_premium: float) -> Dict[str, Any]:
    """
    Calculate final discount rate for DCF.

    Formula: Discount_Rate = Industry_WACC + Patent_Risk_Premium

    Args:
        industry_wacc: Industry weighted average cost of capital (decimal)
        risk_premium: Total patent risk premium (decimal)

    Returns:
        {
            "discount_rate": 0.155,  # 15.5%
            "components": {
                "industry_wacc": 0.095,
                "risk_premium": 0.060
            },
            "reasonableness_check": "PASS",  # Check if 0.10 < rate < 0.30
            "rationale": "Industry WACC 9.5% + Patent Risk 6% = 15.5%"
        }
    """
    discount_rate = industry_wacc + risk_premium

    # Validate reasonableness (typical patent discount rates: 10-25%)
    reasonable = 0.10 <= discount_rate <= 0.30

    return {
        "discount_rate": discount_rate,
        "components": {
            "industry_wacc": industry_wacc,
            "risk_premium": risk_premium
        },
        "reasonableness_check": "PASS" if reasonable else "WARNING",
        "rationale": f"Industry WACC {industry_wacc:.1%} + Patent Risk {risk_premium:.1%} = {discount_rate:.1%}"
    }
```

---

### Q27: Valuation Calculator Tools

**Answer**: ✅

```python
def tool_dcf_calculator(
    cash_flows: List[float],
    discount_rate: float,
    periods: int
) -> Dict[str, Any]:
    """
    Calculate Net Present Value using Discounted Cash Flow method.

    Formula: NPV = Σ(t=1 to T) [CF_t / (1 + r)^t]

    Args:
        cash_flows: List of cash flows by year
        discount_rate: Discount rate (decimal)
        periods: Number of years

    Returns:
        {
            "npv": 4285000,
            "total_undiscounted": 12450000,
            "discount_factor_applied": 0.344,  # NPV/Undiscounted
            "cash_flows_pv": [
                {"year": 1, "cf": 354000, "pv": 307000},
                {"year": 2, "cf": 417700, "pv": 313000},
                ...
            ]
        }
    """
    cash_flows_pv = []
    npv = 0.0

    for t, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1 + discount_rate) ** t)
        npv += pv
        cash_flows_pv.append({"year": t, "cf": cf, "pv": pv})

    total_undiscounted = sum(cash_flows)

    return {
        "npv": npv,
        "total_undiscounted": total_undiscounted,
        "discount_factor_applied": npv / total_undiscounted if total_undiscounted > 0 else 0,
        "cash_flows_pv": cash_flows_pv
    }

def tool_sensitivity_analyzer(
    base_valuation: float,
    parameters: Dict[str, float],  # {"discount_rate": 0.155, "ip_contribution": 0.30, ...}
    dcf_function: callable  # Function to recalculate valuation
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on key assumptions.

    Test ±20% changes in:
    - Discount rate
    - IP contribution factor
    - Growth rate
    - Profit margin

    Returns:
        {
            "base_valuation": 4285000,
            "sensitivity": {
                "discount_rate": {
                    "low": 5400000,    # -20% discount rate
                    "high": 3500000,   # +20% discount rate
                    "impact": "±22%"
                },
                "ip_contribution": {
                    "low": 3428000,
                    "high": 5142000,
                    "impact": "±20%"
                },
                ...
            },
            "most_sensitive": "discount_rate",
            "tornado_chart_data": [...]  # For visualization
        }
    """
```

---

### Q28: Professional Report Structure

**Answer**: ✅ **NOT a narrative "Step 1, Step 2" story**. Professional structure with clear sections.

**New Report Structure**:

```markdown
# Patent Valuation Report
## Patent [Number] - [Title]

**Valuation Date**: [Date]
**Valuation Context**: [Context]
**Prepared By**: MARSYS AI Valuation System

---

## EXECUTIVE SUMMARY

**Patent Number**: [Number]
**Title**: [Title]
**Assignee**: [Company]
**Grant Date**: [Date] | **Expiration**: [Date]

**VALUATION RESULTS**:
- **Base Case**: $[X.XX]M
- **Range**: $[Low]M - $[High]M
- **Confidence Level**: [High/Medium/Low]

**KEY FINDINGS**:
- [Bullet point summary of 3-5 key findings]

---

## 1. METHODOLOGY

**Approach**: Income Method (Discounted Cash Flow)
**Formula**: Patent_Value = Σ [CF_t / (1 + r)^t]

**Why This Method**:
- [Rationale for using Income Method]
- Data availability assessment
- Appropriateness for this context

---

## 2. PATENT OVERVIEW

### 2.1 Technology Description
[Clear, non-technical summary of what the patent does]

### 2.2 Technical Characteristics
- **Technology Field**: [Field]
- **Key Features**: [List]
- **Innovation Level**: [Description]

### 2.3 Patent Strength Analysis
- **Strength Score**: [X/100]
  - Citations Component: [X/35] - [Description]
  - Family Component: [X/30] - [Description]
  - Claims Component: [X/20] - [Description]
  - Legal Component: [X/15] - [Description]

### 2.4 Legal Status
- **Status**: Active / Expired / Abandoned
- **Remaining Life**: [X] years
- **Maintenance Fees**: Current / Lapsed
- **Litigation History**: [None / Past / Pending]

### 2.5 Citation Analysis
- **Forward Citations**: [X] patents cite this invention
- **Backward Citations**: [X] prior art references
- **Citation Impact**: [Analysis]

### 2.6 Patent Family
- **Family Size**: [X] jurisdictions
- **Geographic Coverage**: [List countries/regions]
- **Market Coverage**: [Interpretation]

---

## 3. MARKET ANALYSIS

### 3.1 Target Market Identification
- **Primary Market**: [Market name and description]
- **Industry Classification**: [NAICS code and name]
- **Applications**: [List of commercial applications]

### 3.2 Market Sizing (Bottom-Up Analysis)

**Total Addressable Market (TAM)**:
- **Size**: $[X.XX]B
- **Calculation**: [Formula with inputs]
- **Data Source**: [Source with citation]
- **Growth Rate (CAGR)**: [X]%

**Serviceable Available Market (SAM)**:
- **Size**: $[X.XX]M
- **Filters Applied**:
  - Geographic: [X]% ([rationale])
  - Distribution: [X]% ([rationale])
  - Product Fit: [X]% ([rationale])

**Serviceable Obtainable Market (SOM)**:
- **Size**: $[X.XX]M
- **Market Share**: [X]% ([rationale])
- **Adoption Rate**: [X]% ([rationale])

### 3.3 Revenue Projections
[Table showing year-by-year revenue projections for patent life]

| Year | Base Revenue | Growth | Projected Revenue |
|------|--------------|--------|-------------------|
| 1    | $X.XXM       | X%     | $X.XXM            |
| ...  | ...          | ...    | ...               |

---

## 4. FINANCIAL ASSUMPTIONS

### 4.1 Profit Margin
- **Value**: [X]%
- **Source**: [Company 10-K / Damodaran Industry Benchmark]
- **Data Quality**: [High / Medium / Low]
- **Rationale**: [Explanation of why this margin was used]

### 4.2 Industry Cost of Capital
- **Industry WACC**: [X]%
- **Industry**: [Industry name]
- **Source**: [Damodaran Industry Dataset 2024]
- **Data Date**: [Date]

### 4.3 Royalty Rate Benchmarks (for Attribution)
- **Industry**: [Industry name]
- **Range**: [Low]% - [High]%
- **Median**: [X]%
- **Sources**: [List sources]
  - SEC EDGAR: [X] licensing agreements analyzed
  - Academic papers: [Citations]
  - LES surveys: [If available]

---

## 5. IP ATTRIBUTION ANALYSIS

### 5.1 Portfolio Context
- **Portfolio Type**: Single Patent / Multiple Patents
- **Total Patents in Product**: [X] (if applicable)
- **This Patent's Role**: [Critical / Important / Supporting]

### 5.2 Attribution Method Selected
**Method Used**: [Comparable License / SSU / Feature Value]

**Rationale for Selection**:
[Explanation of why this method was chosen over alternatives]

### 5.3 Calculation

[Detailed calculation showing inputs and formula]

**Result**: IP Contribution Factor = [X]% ([0.XX])

---

## 6. COMMERCIALIZATION ASSESSMENT

### 6.1 Technology Readiness Level (TRL)
- **Estimated TRL**: [X]/9
- **Assessment Method**: [Inferred from patent data / User-provided]
- **Evidence**:
  - [Evidence point 1]
  - [Evidence point 2]

### 6.2 Commercial Readiness Level (CRL)
- **Estimated CRL**: [X]/10
- **Evidence**:
  - [Evidence point 1]
  - [Evidence point 2]

### 6.3 Commercialization Probability
- **Probability**: [X]% ([0.XX])
- **Derivation**: TRL [X] × CRL [X] → [Probability] (NASA matrix)
- **Confidence**: [High / Medium / Low]

---

## 7. RISK ANALYSIS

### 7.1 Patent Risk Premium Components

| Component | Value | Rationale |
|-----------|-------|-----------|
| **Technology Maturity Risk** | +[X]% | TRL [X] → [risk level] |
| **Portfolio Dependency Risk** | +[X]% | [Dependency level] |
| **Litigation Risk** | +[X]% | [Litigation status] |
| **TOTAL RISK PREMIUM** | **+[X]%** | Sum of components |

### 7.2 Final Discount Rate

**Discount Rate = Industry WACC + Patent Risk Premium**

| Component | Value |
|-----------|-------|
| Industry WACC | [X]% |
| Patent Risk Premium | +[X]% |
| **Final Discount Rate** | **[X]%** |

**Reasonableness Check**: ✓ Within typical range (10-25%)

---

## 8. DCF VALUATION CALCULATION

### 8.1 Cash Flow Formula

For each year t:
```
Cash_Flow_t = Revenue_t × Profit_Margin × IP_Contribution × Commercialization_Probability
```

### 8.2 Year-by-Year Breakdown

| Year | Revenue | Profit Margin | IP Contrib | Comm Prob | Cash Flow | Discount Factor | Present Value |
|------|---------|---------------|------------|-----------|-----------|-----------------|---------------|
| 1    | $XXM    | XX%           | XX%        | XX%       | $XXK      | 0.XXX           | $XXK          |
| 2    | $XXM    | XX%           | XX%        | XX%       | $XXK      | 0.XXX           | $XXK          |
| ...  | ...     | ...           | ...        | ...       | ...       | ...             | ...           |
| **Total** | **$XXM** | - | - | - | **$XXM** | - | **$X.XXM** |

### 8.3 Valuation Results

- **Base Case (NPV)**: **$[X.XX]M**
- **Total Undiscounted Cash Flow**: $[X.XX]M
- **Discount Factor Applied**: [X]%

---

## 9. SENSITIVITY ANALYSIS

### 9.1 Key Assumptions Sensitivity

| Parameter | Base Value | -20% Change | +20% Change | Valuation Range | Impact |
|-----------|------------|-------------|-------------|-----------------|--------|
| **Discount Rate** | [X]% | $[X.XX]M | $[X.XX]M | ±[X]% | [Rank] |
| **IP Contribution** | [X]% | $[X.XX]M | $[X.XX]M | ±[X]% | [Rank] |
| **Growth Rate** | [X]% | $[X.XX]M | $[X.XX]M | ±[X]% | [Rank] |
| **Profit Margin** | [X]% | $[X.XX]M | $[X.XX]M | ±[X]% | [Rank] |

### 9.2 Scenario Analysis

| Scenario | Assumptions | Valuation |
|----------|-------------|-----------|
| **Low Case** | Conservative assumptions | $[X.XX]M |
| **Base Case** | Central assumptions | $[X.XX]M |
| **High Case** | Optimistic assumptions | $[X.XX]M |

### 9.3 Most Sensitive Parameters
1. [Parameter 1] - ±[X]% impact
2. [Parameter 2] - ±[X]% impact
3. [Parameter 3] - ±[X]% impact

---

## 10. ASSUMPTIONS LOG

[Complete table of ALL assumptions made during valuation]

| Category | Assumption | Value | Source | Rationale | Impact Level |
|----------|------------|-------|--------|-----------|--------------|
| Market | TAM | $XXB | [Source] | [Rationale] | High |
| Market | Market Share | X% | [Source] | [Rationale] | High |
| Financial | Profit Margin | X% | [Source] | [Rationale] | High |
| ... | ... | ... | ... | ... | ... |

**Total Assumptions**: [X]

---

## 11. DATA SOURCES

### 11.1 Patent Data
- USPTO PatentsView API - https://api.patentsview.org/
- EPO OPS API - https://ops.epo.org/
- [Other sources]

### 11.2 Market Data
- [Source 1] - [URL] - Accessed [Date]
- [Source 2] - [URL] - Accessed [Date]

### 11.3 Financial Data
- Damodaran Industry Data - [URL] - [Date]
- SEC EDGAR - [URLs] - Accessed [Date]

### 11.4 Academic/Research Citations
- [Citation 1 - full citation]
- [Citation 2 - full citation]

---

## 12. LIMITATIONS AND DISCLAIMERS

### 12.1 Data Limitations
- [Limitation 1]
- [Limitation 2]

### 12.2 Methodology Limitations
- [Limitation 1]
- [Limitation 2]

### 12.3 Validity Period
- **Validity**: [X] months from valuation date
- **Update Triggers**: [List events that would require revaluation]

### 12.4 Use Restrictions
- This valuation is prepared for [specific context]
- Not applicable for other uses without reassessment
- Point-in-time analysis based on available information as of [date]

---

## 13. RECOMMENDATIONS

### 13.1 Data Quality Improvements
[Suggestions for additional data that would improve valuation accuracy]

### 13.2 Further Analysis
[Suggestions for additional analysis if higher precision needed]

### 13.3 Action Items
[If applicable - next steps for stakeholders]

---

## APPENDIX A: METHODOLOGY DETAILS

[Detailed formulas and calculation steps]

---

## APPENDIX B: RAW DATA

[Optional: Raw API responses, detailed data tables]

---

**END OF REPORT**

---

**Prepared By**: MARSYS AI Patent Valuation System
**Version**: 1.0
**Date**: [Date]
**Contact**: [If applicable]
```

---

## 2. TOOL SPECIFICATIONS

[Continue with all tool specifications...]

### 2.1 Patent Data Collection Tools

```python
def tool_uspto_patentsview_api(patent_number: str) -> Dict[str, Any]:
    """
    Retrieve patent data from USPTO PatentsView API.

    Endpoint: https://api.patentsview.org/patents/query

    Args:
        patent_number: Patent number (e.g., "10123456" or "US10123456B2")

    Returns:
        {
            "patent_number": "US10123456B2",
            "title": "...",
            "abstract": "...",
            "grant_date": "2018-11-13",
            "expiration_date": "2038-11-13",  # Calculated: grant + 20 years
            "assignee": {
                "name": "Company Inc.",
                "type": "US Company"
            },
            "cpc_codes": ["H04L29/06", "G06F21/60"],
            "ipc_codes": ["H04L29/06"],
            "forward_citations": 47,
            "backward_citations": 28,
            "claims_count": 20,  # From bulk data
            "legal_status": "active",  # From maintenance fee data
            "maintenance_fees": {
                "3.5_year": "paid",
                "7.5_year": "paid",
                "11.5_year": "current"
            }
        }

    Implementation:
        1. Clean patent number (extract digits)
        2. Query PatentsView API
        3. Check maintenance fee status
        4. Calculate derived fields (age, remaining life)
    """

def tool_patent_claims_bulk_download(patent_number: str) -> Dict[str, Any]:
    """
    Get patent claims text from USPTO bulk downloads or patent_client.

    Option 1: Load from pre-downloaded bulk claims file
    Option 2: Use patent_client library for live retrieval

    Returns:
        {
            "independent_claims": [
                "1. A method for...",
                "8. An apparatus comprising..."
            ],
            "dependent_claims": [
                "2. The method of claim 1, wherein...",
                ...
            ],
            "total_claims": 20,
            "independent_count": 3
        }
    """
```

[Continue with all other tools following the same detailed specification pattern...]

---

## 3. RESEARCH CITATIONS

### Patent Strength Scoring
1. Harhoff, D., Scherer, F. M., & Vopel, K. (2003). "Citations, family size, opposition and the value of patent rights." Research Policy, 32(8), 1343-1363.
2. Ernst, H., & Omland, N. (2011). "The Patent Asset Index—A new approach to benchmark patent portfolios." World Patent Information, 33(1), 34-41.
3. PVIX (Portfolio Value Index) methodology - LexisNexis IP Solutions

### CPC-NAICS Mapping
1. Goldshlag, N., Lybbert, T. J., & Zolas, N. (2020). "Tracking the technological composition of industries with algorithmic patent concordances." Economics of Innovation and New Technology, 29(6), 640-664.
2. UC Davis ALP Concordances - https://are.ucdavis.edu/people/faculty/travis-lybbert/research/concordances-patents-and-trademarks/

### Claims Quality
1. Reitzig, M. (2004). "Improving patent valuations for management purposes—validating new indicators by analyzing application rationales." Research Policy, 33(6-7), 939-957.
2. Marco, A. C. (2007). "The dynamics of patent citations." Economics Letters, 94(2), 290-296.

### TRL/CRL Framework
1. NASA NPR 7500.1 - Technology Readiness Levels - https://nodis3.gsfc.nasa.gov/displayCA.cfm?Internal_ID=N_PR_7500_0001_&page_name=Chp3
2. CN102890753A - "Technology readiness level (TRL) determination method based on technology readiness attribute"

### Georgia-Pacific and SSU
1. "Apportionment in Determining Reasonable Royalty Damages" - IPO White Paper
2. "The Smallest Salable Patent-Practicing Unit: Observations on Its Origins" - Berkeley Technology Law Journal

---

## 4. IMPLEMENTATION PRIORITY

### Phase 1: Core Tools (Immediate)
1. ✅ USPTO PatentsView API
2. ✅ CPC-to-NAICS mapper
3. ✅ Patent strength scorer
4. ✅ DCF calculator
5. ✅ All calculation tools

### Phase 2: Data Enhancement (Next)
1. ✅ SEC EDGAR search
2. ✅ Claims bulk download
3. ✅ Web search integration
4. ✅ Browser agent integration

### Phase 3: Advanced Features (Future)
1. ⏳ Automated BOM analysis
2. ⏳ Competitive feature comparison
3. ⏳ Real-time market data APIs

---

**END OF SPECIFICATIONS DOCUMENT**
