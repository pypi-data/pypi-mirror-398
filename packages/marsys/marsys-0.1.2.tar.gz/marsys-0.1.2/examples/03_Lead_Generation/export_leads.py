#!/usr/bin/env python3
"""
Export Lead Generation Results to CSV and Markdown

Converts the output from the lead generation multi-agent system into:
1. A CSV file with all contacts and company information
2. A structured Markdown report with table of contents

Usage:
    python export_leads.py                                    # Use default output dir
    python export_leads.py --input output/lead_gen_marsys     # Custom input dir
    python export_leads.py --output-dir ./exports             # Custom output location
"""

import argparse
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSONL file and return list of records."""
    records = []
    if not file_path.exists():
        return records

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"Warning: Could not parse line in {file_path}: {e}")
    return records


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load a JSON file and return the data."""
    if not file_path.exists():
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse {file_path}: {e}")
            return None


def load_all_data(input_dir: Path) -> Dict[str, Any]:
    """Load all lead generation data from the output directory."""
    data = {
        'companies': {},
        'contacts': [],
        'qualified_companies': []
    }

    # Load qualified companies
    qualified_path = input_dir / 'qualified_companies.jsonl'
    if qualified_path.exists():
        data['qualified_companies'] = load_jsonl(qualified_path)

    # Load qualification details for each company
    qualification_dir = input_dir / 'qualification'
    if qualification_dir.exists():
        for qual_file in qualification_dir.glob('*_qualification.json'):
            company_id = qual_file.stem.replace('_qualification', '')
            qual_data = load_json(qual_file)
            if qual_data:
                data['companies'][company_id] = {
                    'qualification': qual_data,
                    'contacts': []
                }

    # Load company reports
    reports_dir = input_dir / 'company_reports'
    if reports_dir.exists():
        for report_file in reports_dir.glob('*.md'):
            company_id = report_file.stem
            if company_id not in data['companies']:
                data['companies'][company_id] = {'contacts': []}
            with open(report_file, 'r', encoding='utf-8') as f:
                data['companies'][company_id]['report'] = f.read()

    # Load contacts for each company
    contacts_dir = input_dir / 'contacts'
    if contacts_dir.exists():
        for contact_file in contacts_dir.glob('*_employees.jsonl'):
            company_id = contact_file.stem.replace('_employees', '')
            contacts = load_jsonl(contact_file)

            if company_id not in data['companies']:
                data['companies'][company_id] = {'contacts': []}

            data['companies'][company_id]['contacts'] = contacts
            data['contacts'].extend(contacts)

    return data


def export_to_csv(data: Dict[str, Any], output_path: Path) -> None:
    """Export all contacts to a CSV file with company information."""

    # Define CSV columns
    fieldnames = [
        'company_id',
        'company_name',
        'company_website',
        'company_industry',
        'company_country',
        'company_qualification_status',
        'company_fit_score',
        'company_priority',
        'person_name',
        'job_title',
        'linkedin_url',
        'email',
        'location',
        'skills',
        'profile_summary',
        'outreach_hooks'
    ]

    rows = []

    for company_id, company_data in data['companies'].items():
        qual = company_data.get('qualification', {})
        contacts = company_data.get('contacts', [])

        # Get company info from qualification data
        company_name = qual.get('company_name', company_id)
        company_website = qual.get('company_website', '')
        company_industry = qual.get('industry', '')
        company_country = qual.get('country', '')
        qualification_status = qual.get('qualification_status', '')
        fit_score = qual.get('fit_score', '')
        priority = qual.get('priority', '')

        if contacts:
            for contact in contacts:
                rows.append({
                    'company_id': company_id,
                    'company_name': contact.get('company_name', company_name),
                    'company_website': company_website,
                    'company_industry': company_industry,
                    'company_country': company_country,
                    'company_qualification_status': qualification_status,
                    'company_fit_score': fit_score,
                    'company_priority': priority,
                    'person_name': contact.get('person_name', ''),
                    'job_title': contact.get('job_title', ''),
                    'linkedin_url': contact.get('linkedin_url', ''),
                    'email': contact.get('email', ''),
                    'location': contact.get('location', ''),
                    'skills': ', '.join(contact.get('skills', [])) if isinstance(contact.get('skills'), list) else contact.get('skills', ''),
                    'profile_summary': contact.get('profile_summary', ''),
                    'outreach_hooks': ' | '.join(contact.get('outreach_hooks', [])) if isinstance(contact.get('outreach_hooks'), list) else contact.get('outreach_hooks', '')
                })
        else:
            # Add company even without contacts
            rows.append({
                'company_id': company_id,
                'company_name': company_name,
                'company_website': company_website,
                'company_industry': company_industry,
                'company_country': company_country,
                'company_qualification_status': qualification_status,
                'company_fit_score': fit_score,
                'company_priority': priority,
                'person_name': '',
                'job_title': '',
                'linkedin_url': '',
                'email': '',
                'location': '',
                'skills': '',
                'profile_summary': '',
                'outreach_hooks': ''
            })

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV exported to: {output_path}")
    print(f"  - Total rows: {len(rows)}")


def export_to_markdown(data: Dict[str, Any], output_path: Path) -> None:
    """Export all data to a structured Markdown report."""

    lines = []

    # Header
    lines.append("# Lead Generation Report")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # Summary statistics
    total_companies = len(data['companies'])
    total_contacts = len(data['contacts'])
    companies_with_contacts = sum(1 for c in data['companies'].values() if c.get('contacts'))

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total Companies:** {total_companies}")
    lines.append(f"- **Companies with Contacts:** {companies_with_contacts}")
    lines.append(f"- **Total Contacts:** {total_contacts}")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")

    for idx, (company_id, company_data) in enumerate(data['companies'].items(), 1):
        qual = company_data.get('qualification', {})
        company_name = qual.get('company_name', company_id)
        contact_count = len(company_data.get('contacts', []))
        # Create anchor-friendly ID
        anchor = company_id.lower().replace(' ', '-').replace('.', '').replace('_', '-')
        lines.append(f"{idx}. [{company_name}](#{anchor}) ({contact_count} contacts)")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Company sections
    lines.append("## Companies")
    lines.append("")

    for company_id, company_data in data['companies'].items():
        qual = company_data.get('qualification', {})
        contacts = company_data.get('contacts', [])
        report = company_data.get('report', '')

        company_name = qual.get('company_name', company_id)

        # Company header
        lines.append(f"### {company_name}")
        lines.append("")

        # Company info table
        lines.append("#### Company Information")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **ID** | {company_id} |")

        if qual:
            if qual.get('company_website'):
                lines.append(f"| **Website** | {qual.get('company_website')} |")
            if qual.get('industry'):
                lines.append(f"| **Industry** | {qual.get('industry')} |")
            if qual.get('country'):
                lines.append(f"| **Country** | {qual.get('country')} |")
            if qual.get('employee_count'):
                lines.append(f"| **Employee Count** | {qual.get('employee_count')} |")
            if qual.get('qualification_status'):
                lines.append(f"| **Qualification** | {qual.get('qualification_status')} |")
            if qual.get('fit_score'):
                lines.append(f"| **Fit Score** | {qual.get('fit_score')} |")
            if qual.get('priority'):
                lines.append(f"| **Priority** | {qual.get('priority')} |")

        lines.append("")

        # Qualification reasoning
        if qual.get('reasoning'):
            lines.append("#### Qualification Reasoning")
            lines.append("")
            reasoning = qual.get('reasoning')
            if isinstance(reasoning, dict):
                for key, value in reasoning.items():
                    lines.append(f"**{key.replace('_', ' ').title()}:**")
                    if isinstance(value, list):
                        for item in value:
                            lines.append(f"- {item}")
                    else:
                        lines.append(str(value))
                    lines.append("")
            else:
                lines.append(str(reasoning))
                lines.append("")

        # Recommended approach
        if qual.get('recommended_approach'):
            lines.append("#### Recommended Approach")
            lines.append("")
            approach = qual.get('recommended_approach')
            if isinstance(approach, dict):
                for key, value in approach.items():
                    lines.append(f"**{key}:** {value}")
            else:
                lines.append(str(approach))
            lines.append("")

        # Use case fit
        if qual.get('use_case_fit'):
            lines.append("#### Use Case Fit")
            lines.append("")
            use_cases = qual.get('use_case_fit')
            if isinstance(use_cases, list):
                for uc in use_cases:
                    lines.append(f"- {uc}")
            elif isinstance(use_cases, dict):
                for key, value in use_cases.items():
                    lines.append(f"- **{key}**: {value}")
            else:
                lines.append(str(use_cases))
            lines.append("")

        # Contacts section
        if contacts:
            lines.append(f"#### Contacts ({len(contacts)})")
            lines.append("")

            for contact in contacts:
                person_name = contact.get('person_name', 'Unknown')
                job_title = contact.get('job_title', 'Unknown Title')

                lines.append(f"##### {person_name}")
                lines.append("")
                lines.append(f"**{job_title}**")
                lines.append("")

                # Contact details table
                lines.append("| Field | Value |")
                lines.append("|-------|-------|")

                if contact.get('linkedin_url'):
                    lines.append(f"| LinkedIn | [{contact.get('linkedin_url')}]({contact.get('linkedin_url')}) |")
                if contact.get('email'):
                    lines.append(f"| Email | {contact.get('email')} |")
                if contact.get('location'):
                    lines.append(f"| Location | {contact.get('location')} |")

                lines.append("")

                # Skills
                skills = contact.get('skills', [])
                if skills:
                    lines.append("**Skills:**")
                    if isinstance(skills, list):
                        lines.append(", ".join(skills))
                    else:
                        lines.append(str(skills))
                    lines.append("")

                # Profile summary
                if contact.get('profile_summary'):
                    lines.append("**Summary:**")
                    lines.append(contact.get('profile_summary'))
                    lines.append("")

                # Outreach hooks
                hooks = contact.get('outreach_hooks', [])
                if hooks:
                    lines.append("**Outreach Hooks:**")
                    if isinstance(hooks, list):
                        for hook in hooks:
                            lines.append(f"- {hook}")
                    else:
                        lines.append(f"- {hooks}")
                    lines.append("")
        else:
            lines.append("#### Contacts")
            lines.append("")
            lines.append("*No contacts found for this company.*")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Write the file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Markdown exported to: {output_path}")
    print(f"  - Total companies: {total_companies}")
    print(f"  - Total contacts: {total_contacts}")


def main():
    parser = argparse.ArgumentParser(
        description="Export lead generation results to CSV and Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='examples/03_Lead_Generation/output/lead_gen_marsys',
        help='Input directory containing lead generation output'
    )
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default=None,
        help='Output directory for exported files (default: same as input)'
    )
    parser.add_argument(
        '--csv-name',
        type=str,
        default='leads_export.csv',
        help='Name for the CSV output file'
    )
    parser.add_argument(
        '--md-name',
        type=str,
        default='leads_report.md',
        help='Name for the Markdown output file'
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"Error: Input directory does not exist: {input_dir}")
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from: {input_dir}")
    print("")

    # Load all data
    data = load_all_data(input_dir)

    if not data['companies']:
        print("Warning: No company data found")
        return 1

    # Export to CSV
    csv_path = output_dir / args.csv_name
    export_to_csv(data, csv_path)
    print("")

    # Export to Markdown
    md_path = output_dir / args.md_name
    export_to_markdown(data, md_path)

    print("")
    print("Export complete!")

    return 0


if __name__ == "__main__":
    exit(main())
