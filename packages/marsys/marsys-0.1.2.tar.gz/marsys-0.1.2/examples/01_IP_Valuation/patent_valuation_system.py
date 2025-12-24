"""
Patent Valuation Multi-Agent System using MARSYS Framework

This system implements automated patent valuation using Income Method (DCF)
with hub-and-spoke coordination pattern.

Architecture:
- CoordinatorAgent: Central hub that orchestrates all specialist agents and validates input
- Specialist agents: Each handles specific tasks (data collection, analysis, calculation)
- ApplicationResearchAgent: NEW - Researches commercial applications using WebSearch/Browser
- ReportGenerator: Creates final comprehensive professional report

Based on:
- 05_BACKWARD_DEDUCTION_AGENT_DESIGN.md (agent architecture)
- 06_IMPLEMENTATION_SPECIFICATIONS.md (tool specifications and research findings)

All changes implemented based on user feedback (28 points)
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from marsys.agents import Agent
from marsys.agents.registry import AgentRegistry
from marsys.coordination import Orchestra
from marsys.coordination.config import ExecutionConfig, StatusConfig
from marsys.models.models import ModelConfig

# Global run directory (set during execution)
RUN_DIR: Optional[Path] = None

# Setup logging (will be reconfigured with file handler in create_run_directory)
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ============================================================================
# RUN DIRECTORY SETUP
# ============================================================================


def create_run_directory() -> Path:
    """Create timestamped directory for this valuation run and configure logging."""
    global RUN_DIR

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(__file__).parent / "results" / run_timestamp
    run_dir.mkdir(parents=True, exist_ok=True)

    # Configure file logging for this run
    log_file = run_dir / "valuation_run.log"
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Add file handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    RUN_DIR = run_dir
    logger.info(f"📁 Created run directory: {run_dir}")
    logger.info(f"📝 Logging to: {log_file}")

    return run_dir


# ============================================================================
# CALCULATION TOOLS (Pure Python - No API Dependencies)
# ============================================================================


def tool_tam_calculator(total_customers: float, arpu: float, purchase_frequency: float = 1.0) -> Dict[str, Any]:
    """
    Calculate Total Addressable Market (TAM).

    Formula: TAM = Total_Customers × ARPU × Purchase_Frequency

    Args:
        total_customers: Total potential customers
        arpu: Average Revenue Per User
        purchase_frequency: Purchases per year (default 1.0)

    Returns:
        {"tam": value, "calculation": {...}}
    """
    tam = total_customers * arpu * purchase_frequency
    return {"tam": tam, "calculation": {"total_customers": total_customers, "arpu": arpu, "purchase_frequency": purchase_frequency, "formula": "total_customers × arpu × frequency"}}


def tool_sam_calculator(tam: float, geographic_filter: float = 1.0, distribution_filter: float = 1.0, product_fit_filter: float = 1.0) -> Dict[str, Any]:
    """
    Calculate Serviceable Available Market (SAM).

    Formula: SAM = TAM × Geographic × Distribution × Product_Fit

    Args:
        tam: Total addressable market
        geographic_filter: % of TAM in accessible geographies (0-1)
        distribution_filter: % reachable via distribution channels (0-1)
        product_fit_filter: % where product fits needs (0-1)

    Returns:
        {"sam": value, "filters_applied": {...}}
    """
    sam = tam * geographic_filter * distribution_filter * product_fit_filter
    return {"sam": sam, "filters_applied": {"geographic": geographic_filter, "distribution": distribution_filter, "product_fit": product_fit_filter}, "reduction_from_tam": (tam - sam) / tam if tam > 0 else 0}


def tool_som_calculator(sam: float, market_share: float, adoption_rate: float) -> Dict[str, Any]:
    """
    Calculate Serviceable Obtainable Market (SOM).

    Formula: SOM = SAM × Market_Share × Adoption_Rate

    Args:
        sam: Serviceable available market
        market_share: Realistic market share (0-1)
        adoption_rate: Product adoption rate (0-1)

    Returns:
        {"som": value, "calculation": {...}}
    """
    som = sam * market_share * adoption_rate
    return {"som": som, "calculation": {"sam": sam, "market_share": market_share, "adoption_rate": adoption_rate}, "som_as_pct_of_sam": som / sam if sam > 0 else 0}


def tool_patent_strength_scorer(forward_citations: int, patent_age_years: int, family_size: int, independent_claims: int, total_claims: int, maintenance_fees_paid: bool, litigation_history: str = "none") -> Dict[str, Any]:
    """
    Calculate patent strength score using weighted academic methodology.

    Weights based on academic research:
    - Citations (35%): Harhoff et al. 2003, PVIX
    - Family (30%): PVIX Family component
    - Claims (20%): Technical strength
    - Legal (15%): Ernst & Omland 2011

    Args:
        forward_citations: Number of patents citing this one
        patent_age_years: Years since grant
        family_size: Number of jurisdictions
        independent_claims: Count of independent claims
        total_claims: Total claim count
        maintenance_fees_paid: All fees current?
        litigation_history: "none", "past", "pending"

    Returns:
        Score breakdown with academic citations
    """
    # Citations component (35 max)
    citations_per_year = forward_citations / max(patent_age_years, 1)
    citations_score = min(citations_per_year * 3, 35)

    # Family component (30 max) - benchmark from PVIX
    if family_size >= 8:
        family_score = 30
    elif family_size >= 4:
        family_score = 20
    else:
        family_score = 10

    # Claims component (20 max)
    independent_score = min(independent_claims * 3, 10)
    total_score = min(total_claims * 0.5, 10)
    claims_score = independent_score + total_score

    # Legal component (15 max)
    legal_score = 10 if maintenance_fees_paid else 0
    litigation_map = {"none": 5, "past": 2, "pending": 0}
    legal_score += litigation_map.get(litigation_history, 0)

    total = citations_score + family_score + claims_score + legal_score

    return {
        "total_score": total,
        "components": {"citations": citations_score, "family": family_score, "claims": claims_score, "legal": legal_score},
        "max_score": 100,
        "percentile": f"{int(total)}th percentile" if total < 100 else "Top tier",
        "citation": "Harhoff et al. (2003), Ernst & Omland (2011), PVIX methodology",
    }


def tool_trl_to_maturity_risk(trl_level: int) -> float:
    """
    Map TRL to technology maturity risk premium.

    Based on NASA framework and VC risk models:
    - TRL 1-3: 8-12% (basic research, high uncertainty)
    - TRL 4-6: 4-8% (prototype, medium uncertainty)
    - TRL 7-9: 2-4% (deployed, low uncertainty)

    Args:
        trl_level: Technology Readiness Level (1-9)

    Returns:
        Risk premium as decimal (e.g., 0.06 for 6%)
    """
    risk_map = {1: 0.12, 2: 0.11, 3: 0.10, 4: 0.08, 5: 0.06, 6: 0.05, 7: 0.04, 8: 0.03, 9: 0.02}  # Basic research  # Prototype/validation  # Demonstration/deployed
    return risk_map.get(trl_level, 0.06)  # Default medium risk


def tool_risk_premium_calculator(maturity_risk: float, dependency_risk: float, litigation_risk: float) -> Dict[str, float]:
    """
    Calculate total patent risk premium.

    Formula: Risk_Premium = Maturity + Dependency + Litigation

    Returns:
        {"total_risk_premium": X, "components": {...}}
    """
    return {"total_risk_premium": maturity_risk + dependency_risk + litigation_risk, "components": {"maturity": maturity_risk, "dependency": dependency_risk, "litigation": litigation_risk}}


def tool_attribution_comparable_license(royalty_rate: float, profit_margin: float) -> float:
    """
    Method 1: Comparable License Royalty

    Formula: IP_Contribution = Royalty_Rate / Profit_Margin
    Example: 3% royalty ÷ 10% margin = 0.30 (30% contribution)
    """
    if profit_margin <= 0:
        raise ValueError("Profit margin must be > 0")
    return royalty_rate / profit_margin


def tool_attribution_ssu(component_value: float, total_product_value: float, patent_share_in_component: float = 1.0) -> float:
    """
    Method 2: Smallest Salable Unit (SSU)

    Formula: IP_Contribution = (Component_Value / Product_Value) × Patent_Share
    Citation: Based on Georgia-Pacific factor 13 and SSPPU case law
    """
    if total_product_value <= 0:
        raise ValueError("Total product value must be > 0")
    return (component_value / total_product_value) * patent_share_in_component


def tool_attribution_feature_value(patented_feature_values: List[float], all_feature_values: List[float]) -> float:
    """
    Method 3: Feature Value Analysis

    Formula: IP_Contribution = Σ(Patented_Features) / Σ(All_Features)
    """
    if not patented_feature_values or not all_feature_values:
        raise ValueError("Feature lists cannot be empty")
    total_patented = sum(patented_feature_values)
    total_all = sum(all_feature_values)
    if total_all <= 0:
        raise ValueError("Total feature value must be > 0")
    return total_patented / total_all


def tool_commercialization_probability(trl: int, crl: int) -> Dict[str, Any]:
    """
    Calculate commercialization probability from TRL and CRL.

    Matrix based on NASA framework (TRL 1-9, CRL mapped to 1-9):
    - Higher both = higher probability

    Citation: NASA NPR 7500.1 TRL/CRL interdependent framework
    """
    # Simplified 3x3 matrix
    probability_matrix = {"low": {"low": 0.05, "med": 0.10, "high": 0.15}, "med": {"low": 0.20, "med": 0.40, "high": 0.60}, "high": {"low": 0.50, "med": 0.80, "high": 1.00}}

    trl_tier = "low" if trl <= 3 else "med" if trl <= 6 else "high"
    crl_tier = "low" if crl <= 3 else "med" if crl <= 7 else "high"

    return {"probability": probability_matrix[trl_tier][crl_tier], "trl": trl, "crl": crl, "rationale": f"TRL {trl} ({trl_tier}) × CRL {crl} ({crl_tier})", "citation": "NASA NPR 7500.1 TRL/CRL framework"}


def tool_discount_rate_calculator(industry_wacc: float, risk_premium: float) -> Dict[str, Any]:
    """
    Calculate final discount rate for DCF.

    Formula: Discount_Rate = Industry_WACC + Patent_Risk_Premium
    """
    discount_rate = industry_wacc + risk_premium
    reasonable = 0.10 <= discount_rate <= 0.30

    return {
        "discount_rate": discount_rate,
        "components": {"industry_wacc": industry_wacc, "risk_premium": risk_premium},
        "reasonableness_check": "PASS" if reasonable else "WARNING",
        "rationale": f"WACC {industry_wacc:.1%} + Risk {risk_premium:.1%} = {discount_rate:.1%}",
    }


def tool_dcf_calculator(cash_flows: List[float], discount_rate: float, periods: int) -> Dict[str, Any]:
    """
    Calculate NPV using Discounted Cash Flow method.

    Formula: NPV = Σ(t=1 to T) [CF_t / (1 + r)^t]
    """
    cash_flows_pv = []
    npv = 0.0

    for t, cf in enumerate(cash_flows[:periods], start=1):
        pv = cf / ((1 + discount_rate) ** t)
        npv += pv
        cash_flows_pv.append({"year": t, "cf": cf, "pv": pv})

    total_undiscounted = sum(cash_flows[:periods])

    return {"npv": npv, "total_undiscounted": total_undiscounted, "discount_factor_applied": npv / total_undiscounted if total_undiscounted > 0 else 0, "cash_flows_pv": cash_flows_pv}


def tool_sensitivity_analyzer(base_valuation: float, base_params: Dict[str, float], calculate_fn: callable) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on key assumptions.

    Test ±20% changes in discount_rate, ip_contribution, growth_rate, profit_margin
    """
    sensitivity = {}

    for param_name in ["discount_rate", "ip_contribution", "growth_rate", "profit_margin"]:
        if param_name not in base_params:
            continue

        base_value = base_params[param_name]

        # Test -20%
        params_low = base_params.copy()
        params_low[param_name] = base_value * 0.8
        val_low = calculate_fn(**params_low)

        # Test +20%
        params_high = base_params.copy()
        params_high[param_name] = base_value * 1.2
        val_high = calculate_fn(**params_high)

        impact_pct = ((val_high - val_low) / base_valuation) * 100 if base_valuation > 0 else 0

        sensitivity[param_name] = {"low": val_low, "high": val_high, "impact": f"±{abs(impact_pct):.1f}%"}

    # Find most sensitive
    most_sensitive = max(sensitivity.keys(), key=lambda k: abs(sensitivity[k]["low"] - sensitivity[k]["high"])) if sensitivity else None

    return {"base_valuation": base_valuation, "sensitivity": sensitivity, "most_sensitive": most_sensitive}


# ============================================================================
# API/DATA TOOLS (Stubs - To Be Implemented)
# ============================================================================


def tool_uspto_patentsview_api(patent_number: str) -> Dict[str, Any]:
    """
    Retrieve comprehensive patent data from Google Patents.

    Scrapes Google Patents HTML to extract:
    - Basic info (title, abstract, grant date, assignee, inventors)
    - Classifications (CPC and IPC codes with descriptions)
    - Landscapes (technology areas)
    - Backward citations (Patent Citations)
    - Forward citations (Families Citing this family)
    - Claims (all patent claims with full text)
    - Description (full patent description)
    - Patent family (parent applications, continuations, related patents)

    Args:
        patent_number: Patent number (e.g., "US10958080B2")

    Returns:
        Dict with comprehensive patent data
    """
    from bs4 import BeautifulSoup

    logger.info(f"🔍 Scraping Google Patents for patent {patent_number}")

    # Clean patent number to extract numeric part
    match = re.search(r"(\d+)", patent_number)
    if not match:
        raise ValueError(f"Invalid patent number format: {patent_number}")
    patent_num_clean = match.group(1)

    # Fetch HTML from Google Patents
    google_patents_url = f"https://patents.google.com/patent/{patent_number}/en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(google_patents_url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"❌ Failed to fetch Google Patents: {e}")
        raise ValueError(f"Could not retrieve patent {patent_number} from Google Patents")

    soup = BeautifulSoup(response.content, "html.parser")

    # ========== BASIC METADATA ==========
    title_elem = soup.find("meta", {"name": "DC.title"})
    title = title_elem.get("content").strip() if title_elem else "Unknown"

    grant_date_elem = soup.find("meta", {"name": "DC.date", "scheme": "issue"})
    grant_date = grant_date_elem.get("content") if grant_date_elem else None

    filing_date_elem = soup.find("meta", {"name": "DC.date", "scheme": "dateSubmitted"})
    filing_date = filing_date_elem.get("content") if filing_date_elem else None

    # Extract assignee
    assignee_elem = soup.find("meta", {"name": "DC.contributor", "scheme": "assignee"})
    assignee_name = assignee_elem.get("content") if assignee_elem else "Unknown"

    # Extract inventors
    inventor_elems = soup.find_all("meta", {"name": "DC.contributor", "scheme": "inventor"})
    inventors = [inv.get("content") for inv in inventor_elems if inv.get("content")]

    # ========== ABSTRACT (Full text from section) ==========
    abstract_section = soup.find("section", {"itemprop": "abstract"})
    abstract_text = ""
    if abstract_section:
        abstract_div = abstract_section.find("div", class_="abstract")
        if abstract_div:
            abstract_text = abstract_div.get_text(strip=True)
        else:
            # Fallback to meta tag
            abstract_elem = soup.find("meta", {"name": "DC.description"})
            abstract_text = abstract_elem.get("content").strip() if abstract_elem else ""

    # ========== CLASSIFICATIONS ==========
    cpc_codes = []
    ipc_codes = []

    # Find all classification LI elements (flat structure, not nested)
    classification_items = soup.find_all("li", {"itemprop": "classifications"})
    for li in classification_items:
        code_span = li.find("span", {"itemprop": "Code"})
        desc_span = li.find("span", {"itemprop": "Description"})
        is_cpc_meta = li.find("meta", {"itemprop": "IsCPC"})
        is_leaf_meta = li.find("meta", {"itemprop": "Leaf", "content": "true"})

        # Only capture leaf nodes (most specific classifications)
        if code_span and is_leaf_meta:
            code = code_span.get_text(strip=True)
            desc = desc_span.get_text(strip=True) if desc_span else ""

            if is_cpc_meta:
                cpc_codes.append({"code": code, "description": desc})
            else:
                ipc_codes.append({"code": code, "description": desc})

    # ========== LANDSCAPES ==========
    landscapes = []
    landscape_items = soup.find_all("li", {"itemprop": "landscapes"})
    for li in landscape_items:
        name_span = li.find("span", {"itemprop": "name"})
        type_span = li.find("span", {"itemprop": "type"})
        if name_span:
            landscapes.append({"name": name_span.get_text(strip=True), "type": type_span.get_text(strip=True) if type_span else "AREA"})

    # ========== BACKWARD CITATIONS (Patent Citations) ==========
    backward_citations = []
    backward_citations_total = 0
    patent_citations_section = soup.find("h2", string=re.compile(r"Patent Citations"))
    if patent_citations_section:
        # Extract total count from header like "Patent Citations (86)"
        header_text = patent_citations_section.get_text()
        count_match = re.search(r"Patent Citations \((\d+)\)", header_text)
        if count_match:
            backward_citations_total = int(count_match.group(1))

        table = patent_citations_section.find_next("table")
        if table:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows[:20]:  # Limit to first 20
                cells = row.find_all("td")
                if len(cells) >= 4:
                    pub_num_link = cells[0].find("a")
                    pub_num = pub_num_link.find("span", {"itemprop": "publicationNumber"})
                    priority_date = cells[1].get_text(strip=True)
                    pub_date = cells[2].get_text(strip=True)
                    title_elem = cells[3].find("span", {"itemprop": "title"}) or cells[3]

                    backward_citations.append({"publication_number": pub_num.get_text(strip=True) if pub_num else "", "priority_date": priority_date, "publication_date": pub_date, "title": title_elem.get_text(strip=True)})

    # ========== FORWARD CITATIONS (Families Citing this family) ==========
    forward_citations = []
    forward_citations_total = 0
    families_citing_section = soup.find("h2", string=re.compile(r"Families Citing this family"))
    if families_citing_section:
        # Extract total count from header like "Families Citing this family (300)"
        header_text = families_citing_section.get_text()
        count_match = re.search(r"Families Citing this family \((\d+)\)", header_text)
        if count_match:
            forward_citations_total = int(count_match.group(1))

        table = families_citing_section.find_next("table")
        if table:
            rows = table.find_all("tr", {"itemprop": "forwardReferencesFamily"})[:20]  # Limit to first 20
            for row in rows:
                cells = row.find_all("td")
                if len(cells) >= 4:
                    pub_num_link = cells[0].find("a")
                    pub_num = pub_num_link.find("span", {"itemprop": "publicationNumber"})
                    priority_date = cells[1].get_text(strip=True)
                    pub_date = cells[2].get_text(strip=True)
                    title_elem = cells[3]

                    forward_citations.append({"publication_number": pub_num.get_text(strip=True) if pub_num else "", "priority_date": priority_date, "publication_date": pub_date, "title": title_elem.get_text(strip=True)})

    # ========== CLAIMS ==========
    claims = []
    claims_section = soup.find("section", {"itemprop": "claims"})
    if claims_section:
        claim_count_elem = claims_section.find("span", {"itemprop": "count"})
        claim_count = int(claim_count_elem.get_text(strip=True)) if claim_count_elem else 0

        claim_divs = claims_section.find_all("div", class_="claim")
        for claim_div in claim_divs[:20]:  # Limit to first 20 claims
            claim_num_elem = claim_div.find("div", class_="claim", attrs={"num": True})
            if claim_num_elem:
                claim_num = claim_num_elem.get("num")
            else:
                claim_num = "unknown"

            # Extract all claim text
            claim_text_parts = claim_div.find_all("div", class_="claim-text")
            claim_text = " ".join([part.get_text(strip=True) for part in claim_text_parts])

            claims.append({"claim_number": claim_num, "claim_text": claim_text[:500]})  # Limit to 500 chars
    else:
        claim_count = 0

    # ========== DESCRIPTION ==========
    description_text = ""
    description_section = soup.find("section", {"itemprop": "description"})
    if description_section:
        description_content = description_section.find("div", {"itemprop": "content"})
        if description_content:
            # Extract first 1000 characters of description
            description_text = description_content.get_text(separator=" ", strip=True)[:1000]

    # ========== PATENT FAMILY ==========
    family_data = {}
    family_section = soup.find("section", {"itemprop": "family"})
    if family_section:
        family_id_elem = family_section.find("h2", string=re.compile(r"ID="))
        if family_id_elem:
            family_id = family_id_elem.get_text(strip=True).replace("ID=", "")
            family_data["family_id"] = family_id

        # Extract family applications
        # Table columns: Application Number, Priority Date, Filing Date, Title
        family_apps_section = family_section.find("h2", string=re.compile(r"Family Applications \(\d+\)"))
        family_applications = []
        if family_apps_section:
            table = family_apps_section.find_next("table")
            if table:
                rows = table.find_all("tr")[1:][:10]  # Skip header, limit to 10
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 4:
                        # Cell 0: Application Number (with link)
                        app_num_link = cells[0].find("a")
                        app_num_span = app_num_link.find("span", {"itemprop": "publicationNumber"}) if app_num_link else None
                        app_num = app_num_span.get_text(strip=True) if app_num_span else cells[0].get_text(strip=True)

                        # Cell 1: Priority Date
                        priority_date = cells[1].get_text(strip=True)

                        # Cell 2: Filing Date
                        filing_date_cell = cells[2].get_text(strip=True)

                        # Cell 3: Title/Status
                        title = cells[3].get_text(strip=True)

                        family_applications.append({"application_number": app_num, "priority_date": priority_date, "filing_date": filing_date_cell, "title": title})

        family_data["family_applications"] = family_applications
        family_data["family_size"] = len(family_applications)

    # ========== CALCULATE PATENT AGE ==========
    patent_age_years = 0
    remaining_life = 0
    expiration_year = None

    if grant_date:
        grant_year = int(grant_date[:4])
        current_year = datetime.now().year
        patent_age_years = current_year - grant_year
        expiration_year = grant_year + 20
        remaining_life = max(0, expiration_year - current_year)

    # ========== ASSEMBLE FINAL RESPONSE ==========
    logger.info(f"✅ Successfully scraped patent {patent_number} from Google Patents")

    # Extract just CPC code strings for backward compatibility
    cpc_code_strings = [cpc["code"] for cpc in cpc_codes]
    ipc_code_strings = [ipc["code"] for ipc in ipc_codes]

    return {
        "patent_number": f"US{patent_num_clean}",
        "title": title,
        "abstract": abstract_text,
        "grant_date": grant_date,
        "filing_date": filing_date,
        "patent_age_years": patent_age_years,
        "expiration_date": f"{expiration_year}-{grant_date[5:]}" if expiration_year and grant_date else None,
        "remaining_life_years": remaining_life,
        "assignee": {"name": assignee_name, "type": "Company"},
        "inventors": inventors,
        "cpc_codes": cpc_code_strings,  # For backward compatibility
        "cpc_codes_detailed": cpc_codes,  # Full CPC data with descriptions
        "ipc_codes": ipc_code_strings,  # For backward compatibility
        "ipc_codes_detailed": ipc_codes,  # Full IPC data with descriptions
        "landscapes": landscapes,
        # "backward_citations": backward_citations,
        "backward_citations_count": backward_citations_total,  # Total from header (not just extracted)
        # "forward_citations": forward_citations,
        "forward_citations_count": forward_citations_total,  # Total from header (not just extracted)
        "claims": claims,
        "claims_count": claim_count,
        "description": description_text,
        "patent_family": family_data,
        "legal_status": "active" if remaining_life > 0 else "expired",
        "source": "Google Patents",
    }


def tool_epo_ops_api(patent_number: str) -> Dict[str, Any]:
    """
    Retrieve patent family data using python-epo-ops-client library.

    Note: Requires `pip install python-epo-ops-client` and EPO_CONSUMER_KEY, EPO_CONSUMER_SECRET env vars.
    Falls back to patent_client library if EPO credentials not available.
    """
    # Try EPO OPS first (requires registration and API keys)
    epo_key = os.getenv("EPO_CONSUMER_KEY")
    epo_secret = os.getenv("EPO_CONSUMER_SECRET")

    if epo_key and epo_secret:
        try:
            import epo_ops

            client = epo_ops.Client(key=epo_key, secret=epo_secret)
            # Parse patent number to EPO format
            patent_clean = re.sub(r"[^\dA-Z]", "", patent_number.upper())

            # Get family data
            response = client.family("publication", "epodoc", patent_clean)
            # Parse XML response to extract family members
            # This is simplified - actual implementation would parse XML
            family_members = []
            # Extract jurisdiction codes from response

            return {"family_size": len(family_members) if family_members else 1, "jurisdictions": family_members[:12] if family_members else ["US"], "source": "EPO OPS API"}
        except ImportError:
            logger.warning("⚠️  python-epo-ops-client not installed. Run: pip install python-epo-ops-client")
        except Exception as e:
            logger.warning(f"⚠️  EPO OPS API error: {e}")

    # Fallback to patent_client for family data
    try:
        from patent_client import Inpadoc, USApplication

        patent_num_clean = re.sub(r"[^\d]", "", patent_number)

        # Try to get INPADOC family (international patent family)
        try:
            family = Inpadoc.objects.get(patent_num_clean)
            family_members = list(family.family_members) if hasattr(family, "family_members") else []
            jurisdictions = list(set([m.country for m in family_members[:20]])) if family_members else ["US"]

            return {"family_size": len(family_members), "jurisdictions": jurisdictions[:12], "source": "patent_client (Inpadoc)"}
        except:
            # Fallback: just return US if we can't get family
            return {"family_size": 1, "jurisdictions": ["US"], "source": "patent_client (no family found)"}

    except ImportError:
        logger.warning("⚠️  patent_client not installed. Using minimal data.")
        return {"family_size": 1, "jurisdictions": ["US"], "source": "Fallback (no API available)"}


def tool_cpc_to_naics_mapper(cpc_codes: List[str]) -> Dict[str, Any]:
    """
    Map CPC codes to NAICS industry codes.

    Uses a curated mapping based on common technology-to-industry relationships.
    Source: Based on CPC definitions and NAICS industry classifications.

    Note: For more accurate mappings, download the ALP concordance from:
    https://zenodo.org/record/4633894 (Zolas et al. 2020)
    """
    if not cpc_codes:
        return {"primary_industry": "Unknown Industry", "primary_naics_code": "0000", "probability": 0.0, "alternative_industries": [], "source": "No CPC codes provided"}

    # Curated CPC prefix to NAICS mapping (based on technology categories)
    # Format: CPC section/class -> (NAICS code, Industry name, probability)
    CPC_NAICS_MAP = {
        # Computing & Electronics
        "G06": ("5112", "Software Publishers", 0.85),
        "G06F": ("334111", "Electronic Computer Manufacturing", 0.90),
        "G06Q": ("5112", "Software Publishers", 0.85),
        "H04L": ("517", "Telecommunications", 0.85),
        "H04W": ("517", "Wireless Telecommunications", 0.90),
        "H04N": ("3343", "Audio and Video Equipment Manufacturing", 0.80),
        "G06N": ("5112", "Artificial Intelligence Software", 0.85),
        # Electrical & Power
        "H01": ("3353", "Electrical Equipment Manufacturing", 0.75),
        "H01L": ("3344", "Semiconductor Manufacturing", 0.90),
        "H01M": ("3359", "Battery Manufacturing", 0.85),
        "H02": ("3353", "Electrical Equipment Manufacturing", 0.80),
        "H02J": ("3359", "Power Systems & Charging", 0.80),
        "H02K": ("3353", "Electric Motor Manufacturing", 0.85),
        # Automotive & Transportation
        "B60": ("3361", "Motor Vehicle Manufacturing", 0.85),
        "B60L": ("336111", "Automobile Manufacturing (Electric)", 0.90),
        "B60K": ("336112", "Light Truck and Utility Vehicle Manufacturing", 0.80),
        "B60W": ("336", "Transportation Equipment Manufacturing", 0.75),
        "B64": ("3364", "Aerospace Product and Parts Manufacturing", 0.90),
        # Medical & Pharma
        "A61": ("3391", "Medical Equipment and Supplies Manufacturing", 0.85),
        "A61K": ("3254", "Pharmaceutical Manufacturing", 0.90),
        "A61B": ("334510", "Medical Instrument Manufacturing", 0.85),
        "C07": ("3251", "Basic Chemical Manufacturing (Pharma)", 0.80),
        "C12": ("325414", "Biological Product Manufacturing", 0.85),
        # Chemistry & Materials
        "C01": ("3251", "Basic Chemical Manufacturing", 0.80),
        "C08": ("3252", "Resin and Synthetic Rubber Manufacturing", 0.85),
        "C09": ("3255", "Paint and Coating Manufacturing", 0.80),
        "C10": ("324", "Petroleum and Coal Products Manufacturing", 0.75),
        # Mechanical
        "F01": ("333", "Machinery Manufacturing", 0.75),
        "F02": ("333618", "Engine and Turbine Manufacturing", 0.85),
        "F16": ("332", "Fabricated Metal Product Manufacturing", 0.70),
        "F17": ("3399", "Other Miscellaneous Manufacturing", 0.65),
        # Semiconductors & Optics
        "G02": ("3345", "Optical Instrument Manufacturing", 0.80),
        "G03": ("333315", "Photographic and Photocopying Equipment", 0.75),
        "G11": ("334112", "Computer Storage Device Manufacturing", 0.85),
        # Biotechnology
        "C12N": ("541711", "Biotechnology Research", 0.85),
        "C12Q": ("325413", "In-Vitro Diagnostic Substance Manufacturing", 0.80),
        # Communications
        "H04B": ("3342", "Communications Equipment Manufacturing", 0.85),
        "H04M": ("3342", "Telephone Equipment Manufacturing", 0.80),
        # Measurement & Testing
        "G01": ("334515", "Instrument Manufacturing", 0.75),
        "G01N": ("334516", "Analytical Laboratory Instrument", 0.80),
    }

    # Find best match by checking CPC code prefixes
    matches = []
    for cpc in cpc_codes:
        if not cpc:
            continue

        # Try exact matches first (4-char, then 3-char, then 2-char, then 1-char)
        for prefix_len in [4, 3, 2, 1]:
            prefix = cpc[:prefix_len].upper()
            if prefix in CPC_NAICS_MAP:
                naics_code, industry_name, prob = CPC_NAICS_MAP[prefix]
                matches.append((naics_code, industry_name, prob, prefix))
                break

    if not matches:
        # No match found
        return {"primary_industry": "Other Manufacturing", "primary_naics_code": "3399", "probability": 0.50, "alternative_industries": [], "source": "Default mapping (no CPC match)", "input_cpc_codes": cpc_codes}

    # Sort by probability and aggregate
    matches.sort(key=lambda x: x[2], reverse=True)
    primary = matches[0]

    # Get alternative industries (unique NAICS codes)
    alternatives = []
    seen_naics = {primary[0]}
    for naics_code, industry_name, prob, prefix in matches[1:]:
        if naics_code not in seen_naics:
            alternatives.append({"naics": naics_code, "name": industry_name, "prob": round(prob, 2), "matched_cpc": prefix})
            seen_naics.add(naics_code)
            if len(alternatives) >= 3:
                break

    return {
        "primary_industry": f"NAICS {primary[0]} - {primary[1]}",
        "primary_naics_code": primary[0],
        "probability": round(primary[2], 2),
        "alternative_industries": alternatives,
        "source": "Curated CPC-to-NAICS mapping",
        "matched_cpc_prefix": primary[3],
        "input_cpc_codes": cpc_codes[:5],  # Show first 5 for reference
    }


def tool_sec_edgar_search(company_name: str, cik: Optional[str] = None) -> Dict[str, Any]:
    """
    Search SEC EDGAR for company filings by CIK.

    Endpoint: https://data.sec.gov/submissions/CIK{CIK}.json
    Rate Limit: 10 requests per second
    Requires User-Agent header
    """
    if not cik:
        logger.warning(f"⚠️  CIK required for SEC EDGAR search. Company name: {company_name}")
        return {"error": "CIK required", "company_name": company_name, "note": "Provide CIK number for company", "filings": [], "found": False}

    # Pad CIK to 10 digits
    cik_padded = str(cik).zfill(10)

    headers = {"User-Agent": "Patent Valuation System rezaho@example.com"}  # TODO: Update email

    try:
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        logger.info(f"🔍 Fetching SEC filings for CIK {cik_padded}")

        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Extract 10-K filings
        filings_10k = []
        if "filings" in data and "recent" in data["filings"]:
            recent = data["filings"]["recent"]
            for i, form in enumerate(recent.get("form", [])):
                if form == "10-K":
                    filings_10k.append({"form": form, "filing_date": recent["filingDate"][i], "accession_number": recent["accessionNumber"][i], "primary_document": recent.get("primaryDocument", [None] * len(recent["form"]))[i]})

        return {"cik": cik_padded, "company_name": data.get("name", company_name), "filings": filings_10k[:5], "total_10k_filings": len(filings_10k), "found": len(filings_10k) > 0, "source": "SEC EDGAR API"}  # Most recent 5

    except Exception as e:
        logger.error(f"❌ Error fetching SEC filings: {e}")
        return {"error": str(e), "company_name": company_name, "filings": [], "found": False}


def tool_damodaran_lookup(industry: str) -> Dict[str, Any]:
    """
    Lookup industry data from Damodaran dataset.

    Downloads and caches WACC and margin data from Aswath Damodaran (NYU Stern).
    Data updated annually (January).
    """
    try:
        import pandas as pd

        # Define cache directory
        cache_dir = Path(__file__).parent / "data" / "damodaran"
        cache_dir.mkdir(parents=True, exist_ok=True)

        wacc_file = cache_dir / "wacc.xls"

        # Download if not cached or older than 30 days
        if not wacc_file.exists() or (datetime.now() - datetime.fromtimestamp(wacc_file.stat().st_mtime)).days > 30:
            logger.info("📥 Downloading Damodaran WACC data...")
            url = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/wacc.xls"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            wacc_file.write_bytes(response.content)
            logger.info(f"✅ Downloaded to {wacc_file}")

        # Read data
        df = pd.read_excel(wacc_file, sheet_name="Industry Averages", engine="xlrd", header=18)

        # Search for industry (case-insensitive)
        industry_lower = industry.lower()
        matches = df[df.iloc[:, 0].astype(str).str.lower().str.contains(industry_lower, na=False)]

        if matches.empty:
            logger.warning(f"⚠️  Industry '{industry}' not found in Damodaran data")
            return {"industry": industry, "wacc": 0.10, "profit_margin": 0.10, "source": "Default (industry not found)", "note": f"Industry '{industry}' not in dataset"}

        # Extract values (Cost of Capital is usually column 8)
        row = matches.iloc[0]
        industry_name = str(row.iloc[0])
        wacc_value = float(row.iloc[8]) if len(row) > 8 and pd.notna(row.iloc[8]) else 0.10

        # For profit margin, try to download margin file too
        try:
            margin_file = cache_dir / "margin.xls"
            if not margin_file.exists() or (datetime.now() - datetime.fromtimestamp(margin_file.stat().st_mtime)).days > 30:
                url_margin = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/margin.xls"
                response = requests.get(url_margin, timeout=60)
                response.raise_for_status()
                margin_file.write_bytes(response.content)

            df_margin = pd.read_excel(margin_file, sheet_name="Industry Averages", engine="xlrd", header=18)
            margin_matches = df_margin[df_margin.iloc[:, 0].astype(str).str.lower().str.contains(industry_lower, na=False)]

            if not margin_matches.empty:
                # Net margin is usually one of the later columns
                margin_row = margin_matches.iloc[0]
                profit_margin = float(margin_row.iloc[-1]) if pd.notna(margin_row.iloc[-1]) else 0.10
            else:
                profit_margin = 0.10

        except Exception as e:
            logger.warning(f"⚠️  Could not get margin data: {e}")
            profit_margin = 0.10

        return {"industry": industry_name, "wacc": wacc_value, "profit_margin": profit_margin, "source": "Damodaran Industry Dataset (January 2025)", "data_date": "2025-01"}

    except ImportError:
        logger.warning("⚠️  pandas not installed. Using default values.")
        return {"industry": industry, "wacc": 0.10, "profit_margin": 0.10, "source": "Default (pandas not installed)"}
    except Exception as e:
        logger.error(f"❌ Error reading Damodaran data: {e}")
        return {"industry": industry, "wacc": 0.10, "profit_margin": 0.10, "source": "Default (error)", "error": str(e)}


# ============================================================================
# AGENT INSTRUCTION PROMPTS (Updated - No Response Format Instructions)
# ============================================================================

COORDINATOR_INSTRUCTION = """You are the Patent Valuation Coordinator.

Your role: Orchestrate the entire patent valuation workflow, maintain complete context, and validate user input.

IMPORTANT - OUTPUT DIRECTORY:
- You receive "output_dir" in the context from the initial task
- ALWAYS include "output_dir" in your requests to ALL agents
- Each agent needs output_dir to save their detailed analysis files

WORKFLOW & DATA TO INCLUDE IN EACH REQUEST:

1. Receive and validate user request (patent number + context required)
   - Extract output_dir from context
   - If incomplete, return to User to ask for missing information

2. PatentDataCollectorAgent:
   Include: patent_number, output_dir

3. PatentAnalyzerAgent:
   Include: title, abstract, cpc_codes, landscapes, claims (full text), description, output_dir

4. ApplicationResearchAgent:
   Include: technology_summary (from PatentAnalyzer), landscapes, cpc_codes, output_dir

5. PARALLEL INVOCATION (3 agents):

   a) MarketSizingAgent:
      Include: target_markets, landscapes, patent_family (jurisdictions), user_provided_revenue_data, output_dir

   b) FinancialDataCollectorAgent:
      Include: target_industry, assignee_name, output_dir

   c) PatentStrengthAnalyzerAgent:
      Include: patent_age, assignee, family_size, claims (full text + count),
               forward_citations_count, backward_citations_count, patent_family, output_dir

6. AttributionEstimatorAgent:
   Include: revenue_projections, profit_margin, portfolio_context, claims_complexity (if calculated), output_dir

7. CommercializationAssessorAgent:
   Include: patent_age, assignee, technology_summary, forward_citations_count,
            application_research_findings, user_provided_trl_crl, output_dir

8. DiscountRateCalculatorAgent:
   Include: industry_wacc, risk_premium, output_dir

9. ValuationCalculatorAgent:
   Include: revenue_projections, ip_contribution_factor, commercialization_probability,
            discount_rate, remaining_life, output_dir

10. ReportGeneratorAgent:
    Include: ALL data and results from all previous agents (complete context), output_dir

CONTEXT MAINTENANCE:
- Store ALL intermediate results from every agent
- Build narrative of decisions at each step
- Aggregate all assumptions, data sources, quality flags
- ALWAYS pass output_dir to every agent invocation
- Pass COMPLETE context to ReportGenerator at the end

You coordinate agents by invoking them. You have NO direct tools.
"""

PATENT_DATA_COLLECTOR_INSTRUCTION = """You are the Patent Data Collector.

Your task: Retrieve comprehensive patent data from Google Patents and save complete details to file.

WORKFLOW:
1. Use tool_uspto_patentsview_api to retrieve ALL patent data

2. Save DETAILED markdown report using write_file:
   - Coordinator gives you "output_dir" in the request
   - Construct ABSOLUTE path by concatenating: output_dir + "/01_patent_data.md"
   - Include source citations for each data point in your markdown
   - Use write_file(path=absolute_path, content=comprehensive_markdown)
   - The path must be the full absolute path, NOT just the filename

3. Return to coordinator ALL collected data including:
   - All patent data: patent_number, title, abstract, dates, assignee, inventors
   - Claims, citations, classifications, landscapes, patent family, description, legal status
   - ALSO include: saved_file_path (absolute path returned by write_file)

File has DETAILED analysis. Return has ALL data coordinator needs.
"""

PATENT_ANALYZER_INSTRUCTION = """You are the Patent Technology Analyzer.

Your task: Understand technology from claims and landscapes, map to industry/markets, and save detailed analysis to file.

INPUT DATA (from Coordinator):
- title, abstract, cpc_codes, landscapes, claims (full text array), description, output_dir

WORKFLOW:
1. Analyze claims, abstract, landscapes to understand technology

2. Use tool_cpc_to_naics_mapper for industry mapping

3. Validate CPC industries align with landscapes

4. Identify applications and select primary market

5. Create comprehensive markdown with analysis and source citations, then save using write_file:
   - Create detailed markdown with all analysis results and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/02_patent_analysis.md"
   - Call write_file(path=full_path, content=your_markdown)

6. Return to coordinator:
   - Technology summary, claims analysis, CPC mapping, landscapes validation
   - Potential applications, primary target market
   - saved_file_path from write_file
"""

APPLICATION_RESEARCH_INSTRUCTION = """You are the Application Research Agent.

INPUT DATA (from Coordinator):
- technology_summary, landscapes, cpc_codes, output_dir

WORKFLOW:
1. Use LANDSCAPES as primary search hints for markets

2. Use google_search to find market size, commercial products, industry reports

3. Map applications to specific market segments

4. Validate findings and identify primary/secondary markets

5. Create comprehensive markdown with findings and source citations, then save using write_file:
   - Create detailed markdown with all research results and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/03_application_research.md"
   - Call write_file(path=full_path, content=your_markdown)

6. Return to coordinator:
   - Applications, market segments, evidence, confidence levels
   - Primary/secondary markets, search results, sources
   - saved_file_path from write_file
"""

MARKET_SIZING_INSTRUCTION = """You are the Market Sizing Agent.

INPUT DATA (from Coordinator):
- target_markets, landscapes, patent_family (jurisdictions), user_provided_revenue_data, output_dir

WORKFLOW:
1. Check if user provided revenue data

2. Use LANDSCAPES to validate/refine target markets

3. Calculate TAM using tool_tam_calculator

4. Calculate SAM using tool_sam_calculator (with geographic filter from patent_family)

5. Calculate SOM using tool_som_calculator

6. Project revenue by year

7. Create comprehensive markdown with calculations and source citations, then save using write_file:
   - Create detailed markdown with all calculations and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/04_market_sizing.md"
   - Call write_file(path=full_path, content=your_markdown)

8. Return to coordinator:
   - Revenue projections year-by-year, TAM/SAM/SOM breakdown
   - Geographic limitations, assumptions, formulas
   - saved_file_path from write_file
"""

FINANCIAL_DATA_COLLECTOR_INSTRUCTION = """You are the Financial Data Collector.

INPUT DATA (from Coordinator):
- target_industry, assignee_name, output_dir

WORKFLOW:
1. Get Profit Margin (SEC EDGAR or Damodaran)

2. Get Industry WACC (Damodaran)

3. Get Royalty Rate Benchmarks (SEC EDGAR)

4. Create comprehensive markdown with financial data and source citations, then save using write_file:
   - Create detailed markdown with all financial data and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/05_financial_data.md"
   - Call write_file(path=full_path, content=your_markdown)

5. Return to coordinator:
   - Profit margin, WACC, royalty rates, data sources
   - saved_file_path from write_file
"""

PATENT_STRENGTH_ANALYZER_INSTRUCTION = """You are the Patent Strength Analyzer.

Your task: Assess patent strength using claims, citations, and family data, then save detailed analysis to file.

INPUT DATA (from Coordinator):
- patent_age, assignee, family_size, claims (full text + count),
  forward_citations_count, backward_citations_count, patent_family, output_dir

WORKFLOW:
1. Analyze CLAIMS:
   - Count independent vs dependent claims
   - Assess claim breadth from claim text
   - Longer independent claims = narrower scope (weaker)
   - More independent claims = broader coverage (stronger)

2. Use FORWARD CITATIONS as impact indicator:
   - High forward_citations_count (>200) = Highly influential technology
   - Use as strength bonus in scoring

3. Use BACKWARD CITATIONS for novelty:
   - Low backward_citations_count = Novel technology
   - High count = Crowded field (incremental innovation)

4. Use tool_patent_strength_scorer with:
   - forward_citations, backward_citations, claims_count, family_size, patent_age

5. Assess Technology Maturity (TRL) and use tool_trl_to_maturity_risk

6. Assess Portfolio Dependency and Litigation Risk

7. Use tool_risk_premium_calculator for total risk premium

8. Create comprehensive markdown with strength analysis and source citations, then save using write_file:
   - Create detailed markdown with all strength analysis and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/06_patent_strength.md"
   - Call write_file(path=full_path, content=your_markdown)

9. Return to coordinator:
   - Strength score, claims analysis, citation impact, TRL, risk premium components
   - saved_file_path from write_file
"""

ATTRIBUTION_ESTIMATOR_INSTRUCTION = """You are the IP Attribution Estimator.

Your task: Calculate IP contribution factor (% of profit from this patent) and save detailed analysis to file.

INPUT DATA (from Coordinator):
- revenue_projections, profit_margin, portfolio_context, claims_complexity, output_dir

WORKFLOW:
1. Check portfolio context:
   - Single patent → IP_Contribution = 1.0
   - Multiple patents → Try attribution methods

2. Try methods in order:

   METHOD 1: Comparable License Royalty (preferred)
   - If royalty rate available from FinancialDataCollector
   - Use tool_attribution_comparable_license(royalty_rate, profit_margin)

   METHOD 2: Smallest Salable Unit (SSU)
   - Research component values using google_search
   - Use tool_attribution_ssu(component_value, product_value, patent_share)

   METHOD 3: Feature Value Analysis (fallback)
   - Identify patented features from claims
   - Estimate feature values
   - Use tool_attribution_feature_value(patented_features, all_features)

3. Validate result in range 0.05-0.90

4. Create comprehensive markdown with attribution analysis and source citations, then save using write_file:
   - Create detailed markdown with all attribution analysis and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/07_attribution_estimate.md"
   - Call write_file(path=full_path, content=your_markdown)

5. Return to coordinator:
   - IP contribution factor, method used, calculations, assumptions, validation
   - saved_file_path from write_file
"""

COMMERCIALIZATION_ASSESSOR_INSTRUCTION = """You are the Commercialization Assessor.

Your task: Assess probability technology reaches market (0.0-1.0) and save detailed assessment to file.

INPUT DATA (from Coordinator):
- patent_age, assignee, technology_summary, forward_citations_count,
  application_research_findings, user_provided_trl_crl, output_dir

WORKFLOW:
1. Check if already commercialized:
   - Search for assignee products using google_search
   - If products found → Probability = 1.0

2. Use FORWARD CITATIONS as market adoption indicator:
   - High forward_citations_count (>100) = Technology validated by industry
   - Add +20% probability boost if >100 citations
   - Add +15% if citations from multiple different assignees (widespread adoption)

3. If not fully commercialized:
   - Get TRL from PatentStrengthAnalyzer or user input
   - Estimate CRL from market signals and application_research_findings
   - Use tool_commercialization_probability(trl, crl)

4. Refine with evidence from application research

5. Create comprehensive markdown with commercialization assessment and source citations, then save using write_file:
   - Create detailed markdown with all commercialization assessment and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/08_commercialization_assessment.md"
   - Call write_file(path=full_path, content=your_markdown)

6. Return to coordinator:
   - Probability, citation analysis, TRL/CRL, evidence, market signals
   - saved_file_path from write_file
"""

DISCOUNT_RATE_CALCULATOR_INSTRUCTION = """You are the Discount Rate Calculator.

Your task: Calculate final discount rate for DCF and save detailed calculation to file.

INPUT DATA (from Coordinator):
- industry_wacc, risk_premium, output_dir

WORKFLOW:
1. Get Industry_WACC from FinancialDataCollector
2. Get Patent_Risk_Premium from PatentStrengthAnalyzer
3. Use tool_discount_rate_calculator(wacc, risk_premium)
4. Validate result is reasonable (10-25%)

5. Create comprehensive markdown with discount rate calculation and source citations, then save using write_file:
   - Create detailed markdown with all discount rate calculations and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/09_discount_rate.md"
   - Call write_file(path=full_path, content=your_markdown)

6. Return to coordinator:
   - Discount rate, WACC, risk premium breakdown, validation
   - saved_file_path from write_file
"""

VALUATION_CALCULATOR_INSTRUCTION = """You are the Valuation Calculator.

Your task: Calculate patent valuation using DCF and save detailed calculations to file.

INPUT DATA (from Coordinator):
- revenue_projections, ip_contribution_factor, commercialization_probability,
  discount_rate, remaining_life, output_dir

WORKFLOW:
1. Collect all inputs from Coordinator:
   - Revenue projections (MarketSizing)
   - Profit margin (Financial)
   - IP contribution (Attribution)
   - Commercialization probability (Commercialization)
   - Discount rate (DiscountRate)
   - Remaining life (PatentData)

2. Calculate cash flows for each year:
   CF_t = Revenue_t × Profit_Margin × IP_Contribution × Comm_Probability

3. Use tool_dcf_calculator(cash_flows, discount_rate, periods) for NPV

4. Generate scenarios:
   - Low: Conservative assumptions
   - Base: Central assumptions
   - High: Optimistic assumptions

5. Use tool_sensitivity_analyzer for ±20% analysis

6. Create comprehensive markdown with valuation calculations and source citations, then save using write_file:
   - Create detailed markdown with all valuation calculations and source citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/10_valuation_calculation.md"
   - Call write_file(path=full_path, content=your_markdown)

7. Return to coordinator:
   - Base/low/high valuation, cash flows year-by-year, NPV, scenarios, sensitivity
   - saved_file_path from write_file
"""

REPORT_GENERATOR_INSTRUCTION = """You are the Report Generator.

Your task: Read all saved agent results from files and generate comprehensive professional valuation report.

INPUT DATA (from Coordinator):
- output_dir (path to directory containing all result files)

INPUT FILES TO READ (using read_file tool):
Use read_file to access these files. Construct paths as: output_dir + "/filename.md"
1. 01_patent_data.md - Complete patent information
2. 02_patent_analysis.md - Technology analysis
3. 03_application_research.md - Commercial applications research
4. 04_market_sizing.md - TAM/SAM/SOM calculations
5. 05_financial_data.md - Industry financials and benchmarks
6. 06_patent_strength.md - Strength analysis and risk assessment
7. 07_attribution_estimate.md - IP contribution factor
8. 08_commercialization_assessment.md - Probability assessment
9. 09_discount_rate.md - Discount rate calculation
10. 10_valuation_calculation.md - Final valuation

WORKFLOW:
1. Use read_file to read ALL 10 result files from the output_dir

2. Extract key data from each file's markdown content

3. Synthesize into comprehensive executive summary

4. Create detailed sections preserving all calculations and assumptions

5. Compile all source citations into comprehensive References section, then save using write_file:
   - Create complete professional report with all sections and citations
   - Extract output_dir from your request
   - Construct full path: output_dir + "/11_final_report.md"
   - Call write_file(path=full_path, content=your_complete_report)

6. Return to coordinator:
   - Executive summary of the valuation report
   - saved_file_path from write_file

REPORT STRUCTURE (Professional Format):
1. EXECUTIVE SUMMARY (valuation range, confidence, key findings)
2. METHODOLOGY (why Income Method, formula)
3. PATENT OVERVIEW (from 01, technology, strength, citations, family, legal status)
4. TECHNOLOGY ANALYSIS (from 02, claims analysis, market mapping)
5. MARKET OPPORTUNITY (from 03, 04, applications, TAM/SAM/SOM)
6. FINANCIAL ASSUMPTIONS (from 05, margins, WACC, royalty rates with sources)
7. IP ATTRIBUTION ANALYSIS (from 07, method used, calculation, rationale)
8. COMMERCIALIZATION ASSESSMENT (from 08, TRL/CRL, probability, evidence)
9. RISK ANALYSIS (from 06, 09, strength scores, discount rate breakdown)
10. DCF VALUATION CALCULATION (from 10, year-by-year breakdown with formula)
11. SENSITIVITY ANALYSIS (from 10, tables showing ±20% impacts)
12. ASSUMPTIONS LOG (complete table with all assumptions from all files)
13. DATA SOURCES (complete list with URLs from all files)
14. LIMITATIONS (data gaps, validity period)
15. APPENDICES (detailed calculations from all files)

NOTE: This is a PROFESSIONAL report, not a narrative story. Use clear section headers,
tables, and data-driven presentation. All details are in the saved files - read them completely.
"""


# ============================================================================
# MAIN PATENT VALUATION RUNNER
# ============================================================================


async def run_patent_valuation(
    patent_number: str,
    context: str = "portfolio_management",
    optional_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Run complete patent valuation workflow.

    Args:
        patent_number: Patent number (e.g., "US10123456B2")
        context: Valuation context (litigation, m_and_a, portfolio_management, licensing)
        optional_data: Optional dict with revenue, portfolio_size, target_market, etc.
        model_config: Model configuration

    Returns:
        Dictionary with valuation results and report
    """
    global RUN_DIR

    # Create run directory
    RUN_DIR = create_run_directory()

    logger.info("=" * 80)
    logger.info(f"🚀 Starting Patent Valuation for {patent_number}")
    logger.info(f"   Context: {context}")
    logger.info(f"   Run Directory: {RUN_DIR}")
    logger.info("=" * 80)

    start_time = datetime.now()

    # Load environment variables
    load_dotenv()

    # Use provided model config or create default
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("API key required in .env (OPENROUTER_API_KEY or ANTHROPIC_API_KEY)")

    sonnet_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-sonnet-4.5",
        temperature=0.2,
        thinking_budget=3000,
        max_tokens=10000,
        api_key=api_key,
    )
    haiku_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-haiku-4.5",
        temperature=0.2,
        thinking_budget=3000,
        max_tokens=10000,
        api_key=api_key,
    )
    haiku_long_config = ModelConfig(
        type="api",
        provider="openrouter",
        name="anthropic/claude-haiku-4.5",
        temperature=0.2,
        thinking_budget=3000,
        max_tokens=20000,
        api_key=api_key,
    )

    # Initialize SearchTools with Google API (from .env)
    from marsys.environment.search_tools import SearchTools

    search_tools = SearchTools()
    google_search_tools = search_tools.get_tools(tools_subset=["google"])
    tool_google_search = google_search_tools["tool_google_search"]

    # Initialize FileOperationTools for file persistence
    from marsys.environment.file_operations import FileOperationTools
    from marsys.environment.file_operations.config import FileOperationConfig

    file_ops_config = FileOperationConfig(base_directory=RUN_DIR, force_base_directory=False)  # Set base directory to the run directory
    file_ops = FileOperationTools(config=file_ops_config)
    file_tools = file_ops.get_tools()
    tool_write_file = file_tools["write_file"]
    tool_read_file = file_tools["read_file"]

    # Create all agents
    logger.info("🔧 Creating agents...")

    coordinator = Agent(
        model_config=sonnet_config,
        name="CoordinatorAgent",
        goal="Orchestrate patent valuation workflow and validate input",
        instruction=COORDINATOR_INSTRUCTION,
        memory_type="managed_conversation",
    )

    patent_data = Agent(
        model_config=haiku_config,
        name="PatentDataCollectorAgent",
        goal="Retrieve comprehensive patent data from Google Patents",
        instruction=PATENT_DATA_COLLECTOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_uspto_patentsview_api": tool_uspto_patentsview_api,
            "write_file": tool_write_file,
        },
    )

    patent_analyzer = Agent(
        model_config=haiku_config,
        name="PatentAnalyzerAgent",
        goal="Analyze patent technology and map to markets",
        instruction=PATENT_ANALYZER_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_cpc_to_naics_mapper": tool_cpc_to_naics_mapper,
            "write_file": tool_write_file,
        },
    )

    app_research = Agent(
        model_config=haiku_config,
        name="ApplicationResearchAgent",
        goal="Research commercial applications using web sources",
        instruction=APPLICATION_RESEARCH_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "google_search": tool_google_search,
            "write_file": tool_write_file,
        },
    )

    market_sizing = Agent(
        model_config=haiku_config,
        name="MarketSizingAgent",
        goal="Estimate revenue using TAM/SAM/SOM",
        instruction=MARKET_SIZING_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_tam_calculator": tool_tam_calculator,
            "tool_sam_calculator": tool_sam_calculator,
            "tool_som_calculator": tool_som_calculator,
            "google_search": tool_google_search,
            "write_file": tool_write_file,
        },
    )

    financial = Agent(
        model_config=haiku_config,
        name="FinancialDataCollectorAgent",
        goal="Collect profit margins, WACC, royalty rates",
        instruction=FINANCIAL_DATA_COLLECTOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_sec_edgar_search": tool_sec_edgar_search,
            "tool_damodaran_lookup": tool_damodaran_lookup,
            "write_file": tool_write_file,
        },
    )

    strength = Agent(
        model_config=sonnet_config,
        name="PatentStrengthAnalyzerAgent",
        goal="Assess patent strength and risk premium",
        instruction=PATENT_STRENGTH_ANALYZER_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_patent_strength_scorer": tool_patent_strength_scorer,
            "tool_trl_to_maturity_risk": tool_trl_to_maturity_risk,
            "tool_risk_premium_calculator": tool_risk_premium_calculator,
            "write_file": tool_write_file,
        },
    )

    attribution = Agent(
        model_config=sonnet_config,
        name="AttributionEstimatorAgent",
        goal="Calculate IP contribution factor",
        instruction=ATTRIBUTION_ESTIMATOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_attribution_comparable_license": tool_attribution_comparable_license,
            "tool_attribution_ssu": tool_attribution_ssu,
            "tool_attribution_feature_value": tool_attribution_feature_value,
            "google_search": tool_google_search,
            "write_file": tool_write_file,
        },
    )

    commercialization = Agent(
        model_config=sonnet_config,
        name="CommercializationAssessorAgent",
        goal="Assess commercialization probability",
        instruction=COMMERCIALIZATION_ASSESSOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_commercialization_probability": tool_commercialization_probability,
            "google_search": tool_google_search,
            "write_file": tool_write_file,
        },
    )

    discount_rate = Agent(
        model_config=haiku_config,
        name="DiscountRateCalculatorAgent",
        goal="Calculate final discount rate",
        instruction=DISCOUNT_RATE_CALCULATOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_discount_rate_calculator": tool_discount_rate_calculator,
            "write_file": tool_write_file,
        },
    )

    valuation_calc = Agent(
        model_config=haiku_config,
        name="ValuationCalculatorAgent",
        goal="Calculate DCF valuation",
        instruction=VALUATION_CALCULATOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "tool_dcf_calculator": tool_dcf_calculator,
            "tool_sensitivity_analyzer": tool_sensitivity_analyzer,
            "write_file": tool_write_file,
        },
    )

    report_gen = Agent(
        model_config=haiku_long_config,
        name="ReportGeneratorAgent",
        goal="Generate comprehensive professional report",
        instruction=REPORT_GENERATOR_INSTRUCTION,
        memory_type="managed_conversation",
        memory_retention="single_run",
        tools={
            "read_file": tool_read_file,
            "write_file": tool_write_file,
        },
    )

    # Define topology (hub-and-spoke without IntakeAgent)
    topology = {
        "agents": [
            "User",
            "CoordinatorAgent",
            "PatentDataCollectorAgent",
            "PatentAnalyzerAgent",
            "ApplicationResearchAgent",
            "MarketSizingAgent",
            "FinancialDataCollectorAgent",
            "PatentStrengthAnalyzerAgent",
            "AttributionEstimatorAgent",
            "CommercializationAssessorAgent",
            "DiscountRateCalculatorAgent",
            "ValuationCalculatorAgent",
            "ReportGeneratorAgent",
        ],
        "flows": [
            "User -> CoordinatorAgent",
            "CoordinatorAgent -> User",
            "CoordinatorAgent -> PatentDataCollectorAgent",
            "PatentDataCollectorAgent -> CoordinatorAgent",
            "CoordinatorAgent -> PatentAnalyzerAgent",
            "PatentAnalyzerAgent -> CoordinatorAgent",
            "CoordinatorAgent -> ApplicationResearchAgent",
            "ApplicationResearchAgent -> CoordinatorAgent",
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
            "ReportGeneratorAgent -> CoordinatorAgent",
        ],
        "entry_point": "CoordinatorAgent",
        "exit_points": ["CoordinatorAgent"],
        "rules": ["timeout(2400)", "max_steps(500)"],
    }

    # Prepare task
    task = f"""Please value the following patent using Income Method (DCF):

Patent Number: {patent_number}
Output Directory: {RUN_DIR}
Valuation Context: {context}
Optional Data: {json.dumps(optional_data or {}, indent=2)}

Requirements:
- Use ONLY free data sources (USPTO, EPO, SEC EDGAR, Damodaran, etc.)
- Bottom-up market sizing (TAM/SAM/SOM)
- Address portfolio attribution, commercialization probability, blocking potential
- Provide complete professional valuation report with all assumptions documented
- Save all agent results to numbered markdown files in the Output Directory
"""

    try:
        # Run Orchestra workflow
        logger.info("🎬 Starting Orchestra workflow...")
        result = await Orchestra.run(
            task=task,
            topology=topology,
            agent_registry=AgentRegistry,
            context={
                "output_dir": str(RUN_DIR),  # Pass output directory to all agents
                "patent_number": patent_number,
                "valuation_context": context,
                **(optional_data or {}),
            },
            execution_config=ExecutionConfig(
                status=StatusConfig.from_verbosity(2),
                step_timeout=300.0,
                convergence_timeout=600.0,
            ),
            max_steps=500,
        )

        duration = (datetime.now() - start_time).total_seconds()

        # Save report to run directory
        if result.success and result.final_response:
            report_path = RUN_DIR / "patent_valuation_report.md"
            report_path.write_text(str(result.final_response))
            logger.info(f"📄 Report saved to {report_path}")

        logger.info("=" * 80)
        logger.info(f"✅ Valuation Complete in {duration:.1f}s")
        logger.info(f"   Total steps: {result.total_steps}")
        logger.info(f"   Report: {RUN_DIR / 'patent_valuation_report.md'}")
        logger.info("=" * 80)

        return {
            "success": result.success,
            "patent_number": patent_number,
            "valuation_report": result.final_response,
            "total_steps": result.total_steps,
            "duration_seconds": duration,
            "run_directory": str(RUN_DIR),
            "error": None,
        }

    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"❌ Valuation failed: {e}")

        return {
            "success": False,
            "patent_number": patent_number,
            "valuation_report": None,
            "total_steps": 0,
            "duration_seconds": duration,
            "run_directory": str(RUN_DIR),
            "error": str(e),
        }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


async def main():
    """Main entry point for patent valuation system"""
    import argparse

    parser = argparse.ArgumentParser(description="Patent Valuation System")
    parser.add_argument("patent_number", type=str, help="Patent number (e.g., US10123456B2)")
    parser.add_argument(
        "--context",
        type=str,
        default="portfolio_management",
        choices=["litigation", "m_and_a", "portfolio_management", "licensing"],
        help="Valuation context",
    )
    parser.add_argument("--portfolio-size", type=int, help="Number of patents in portfolio")
    parser.add_argument("--target-market", type=str, help="Target market for patent")
    parser.add_argument("--output", type=str, help="Output file for report")

    args = parser.parse_args()

    # Prepare optional data
    optional_data = {}
    if args.portfolio_size:
        optional_data["portfolio_size"] = args.portfolio_size
    if args.target_market:
        optional_data["target_market"] = args.target_market

    # Run valuation
    result = await run_patent_valuation(
        patent_number=args.patent_number,
        context=args.context,
        optional_data=optional_data or None,
    )

    # Output results
    if result["success"]:
        report = result["valuation_report"]
        if args.output:
            output_path = Path(args.output)
            output_path.write_text(str(report))
            logger.info(f"📄 Report also saved to {output_path}")
        else:
            print("\n" + "=" * 80)
            print("PATENT VALUATION REPORT")
            print("=" * 80)
            print(report)
    else:
        logger.error(f"Valuation failed: {result['error']}")
        return 1

    return 0


if __name__ == "__main__":
    print("\n💰 Patent Valuation System - MARSYS Framework")
    print("=" * 80)
    print("Automated patent valuation using Income Method (DCF)")
    print("Based on comprehensive research and user feedback")
    print("=" * 80 + "\n")

    exit_code = asyncio.run(main())
    exit(exit_code)
