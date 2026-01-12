"""
University Contact Finder
Finds institutional research office contacts for universities using LLMs and web search.

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic Claude
- Perplexity (with built-in search)
- Local Ollama models

Requirements:
    pip install pandas openpyxl requests openai anthropic python-dotenv beautifulsoup4 pydantic
"""

import pandas as pd
import json
import os
import time
from typing import List, Dict, Optional, Literal
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
import re

# Optional imports with graceful fallbacks
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class ContactInfo:
    """Structure for contact information"""
    name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    contact_type: Optional[str] = None  # 'general_counsel' or 'oir'
    source_url: Optional[str] = None
    # Legacy fields for backwards compatibility
    fax: Optional[str] = None
    office: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    mailing_address: Optional[str] = None
    last_updated: Optional[str] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}


class UniversityContactFinder:
    """Find institutional research contacts for universities"""

    def __init__(
        self,
        provider: Literal["openai", "anthropic", "perplexity", "ollama"] = "openai",
        model: Optional[str] = None,
        search_api: Literal["perplexity", "tavily", "brave", "serp"] = "perplexity",
        rate_limit_delay: float = 1.0,
        max_retries: int = 3
    ):
        """
        Initialize the contact finder

        Args:
            provider: LLM provider to use
            model: Specific model to use (None for defaults)
            search_api: Web search API to use (if not using Perplexity)
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.provider = provider
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.search_api = search_api

        # Set default models
        if model is None:
            self.model = {
                "openai": "gpt-4o-mini",  # Cost-effective
                "anthropic": "claude-3-5-sonnet-20241022",
                "perplexity": "sonar",  # Current Perplexity model (2025) - has web search built-in
                "ollama": "llama3.1:8b"
            }[provider]
        else:
            self.model = model

        # Initialize LLM client
        self._init_llm_client()

        # Initialize search API if needed
        if provider != "perplexity":
            self._init_search_api()

    def _init_llm_client(self):
        """Initialize the LLM client based on provider"""
        if self.provider == "openai":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package not installed. Run: pip install openai")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = OpenAI(api_key=api_key)

        elif self.provider == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic package not installed. Run: pip install anthropic")
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = Anthropic(api_key=api_key)

        elif self.provider == "perplexity":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package needed for Perplexity. Run: pip install openai")
            api_key = os.getenv("PERPLEXITY_API_KEY")
            if not api_key:
                raise ValueError("PERPLEXITY_API_KEY not found in environment")
            self.client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

        elif self.provider == "ollama":
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package needed for Ollama. Run: pip install openai")
            # Ollama runs locally, no API key needed
            self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def _init_search_api(self):
        """Initialize web search API if not using Perplexity"""
        if not REQUESTS_AVAILABLE:
            raise ImportError("Requests package not installed. Run: pip install requests")

        if self.search_api == "tavily":
            self.search_api_key = os.getenv("TAVILY_API_KEY")
            if not self.search_api_key:
                raise ValueError("TAVILY_API_KEY not found in environment")

        elif self.search_api == "brave":
            self.search_api_key = os.getenv("BRAVE_API_KEY")
            if not self.search_api_key:
                raise ValueError("BRAVE_API_KEY not found in environment")

        elif self.search_api == "serp":
            self.search_api_key = os.getenv("SERPAPI_API_KEY")
            if not self.search_api_key:
                raise ValueError("SERPAPI_API_KEY not found in environment")

    def _web_search(self, query: str, university_name: str) -> str:
        """Perform web search using configured API"""
        if self.search_api == "tavily":
            return self._tavily_search(query)
        elif self.search_api == "brave":
            return self._brave_search(query)
        elif self.search_api == "serp":
            return self._serp_search(query)
        else:
            # Fallback to direct prompt for Perplexity
            return ""

    def _tavily_search(self, query: str) -> str:
        """Search using Tavily API"""
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.search_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 5
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        results = response.json()

        # Format results as text
        text = ""
        for result in results.get("results", []):
            text += f"\n\n**{result['title']}**\n{result['url']}\n{result['content']}\n"
        return text

    def _brave_search(self, query: str) -> str:
        """Search using Brave Search API"""
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.search_api_key
        }
        params = {"q": query, "count": 5}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        results = response.json()

        text = ""
        for result in results.get("web", {}).get("results", []):
            text += f"\n\n**{result['title']}**\n{result['url']}\n{result.get('description', '')}\n"
        return text

    def _serp_search(self, query: str) -> str:
        """Search using SerpAPI"""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": self.search_api_key,
            "num": 5
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()

        text = ""
        for result in results.get("organic_results", []):
            text += f"\n\n**{result['title']}**\n{result['link']}\n{result.get('snippet', '')}\n"
        return text

    def _create_prompt(self, university_name: str, search_context: Optional[str] = None) -> str:
        """Create the prompt for finding contact information"""
        base_prompt = f"""Find contact information for {university_name}. Search in this PRIORITY ORDER:

**PRIORITY 1 - General Counsel (MOST IMPORTANT):**
- Office of General Counsel
- University Legal Counsel
- Chief Legal Officer
- University Attorney
- Legal Affairs Office

**PRIORITY 2 - Office of Institutional Research (OIR):**
- Director of Institutional Research
- Head of Institutional Research
- Manager of Institutional Research
- Office of Institutional Effectiveness
- Analytics and Planning Director

Return contacts in priority order: General Counsel contact FIRST, then OIR Director/Manager SECOND.

For each contact found, extract these fields:
- name (full name)
- title (job title/position)
- department (department name)
- email (email address)
- phone (phone number with area code)
- website (department or contact page URL)
- address (physical/mailing address including building, room, street, city, state, zip)
- source_url (URL where information was found)

Return the results as a JSON array of contact objects. If no contacts are found, return an empty array.

Example format:
[
  {{
    "name": "John Smith",
    "title": "General Counsel",
    "department": "Office of General Counsel",
    "email": "john.smith@university.edu",
    "phone": "(555) 123-4567",
    "website": "https://university.edu/legal",
    "address": "Legal Building, Suite 100, 123 University Ave, City, ST 12345",
    "source_url": "https://university.edu/legal/contact",
    "contact_type": "general_counsel"
  }},
  {{
    "name": "Dr. Jane Doe",
    "title": "Director of Institutional Research",
    "department": "Office of Institutional Research",
    "email": "jane.doe@university.edu",
    "phone": "(555) 987-6543",
    "website": "https://university.edu/ir",
    "address": "Admin Building, Room 202, 456 Campus Dr, City, ST 12345",
    "source_url": "https://university.edu/ir/contact",
    "contact_type": "oir"
  }}
]

Important:
- PRIORITIZE General Counsel - return this contact FIRST if found
- Return OIR Director/Manager as second contact
- Only include verified, current information from official university websites
- Include physical address with building, room number, street, city, state, zip when available
- If information is uncertain, omit that field
- Return valid JSON only, no additional text"""

        if search_context:
            return f"{base_prompt}\n\nSearch results:\n{search_context}"

        return base_prompt

    def _call_llm(self, prompt: str) -> str:
        """Call the configured LLM with the prompt"""
        for attempt in range(self.max_retries):
            try:
                if self.provider == "openai" or self.provider == "perplexity" or self.provider == "ollama":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a research assistant that finds accurate contact information for university departments. Always return valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,  # Low temperature for factual responses
                        max_tokens=2000
                    )
                    return response.choices[0].message.content

                elif self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=2000,
                        temperature=0.1,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    return response.content[0].text

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"  [WARNING] Error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                    print(f"  [RETRY] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        return "[]"  # Return empty array if all retries fail

    def _extract_json_from_response(self, response: str) -> List[Dict]:
        """Extract JSON array from LLM response"""
        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Try to parse entire response as JSON
        try:
            result = json.loads(response)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return [result]
        except json.JSONDecodeError:
            pass

        return []

    def find_contacts(self, university_name: str) -> List[ContactInfo]:
        """
        Find contacts for a single university

        Args:
            university_name: Name of the university

        Returns:
            List of ContactInfo objects
        """
        print(f"\n[SEARCH] Searching for contacts at {university_name}...")

        try:
            # For Perplexity, it has built-in search, so we just send the prompt
            if self.provider == "perplexity":
                prompt = self._create_prompt(university_name)
                response = self._call_llm(prompt)
            else:
                # For other providers, do web search first
                search_query = f"{university_name} institutional research contact information email phone"
                print(f"  [WEB] Performing web search...")
                search_results = self._web_search(search_query, university_name)
                prompt = self._create_prompt(university_name, search_results)
                response = self._call_llm(prompt)

            # Extract JSON from response
            contacts_data = self._extract_json_from_response(response)

            # Convert to ContactInfo objects
            contacts = []
            for data in contacts_data:
                contact = ContactInfo(**data)
                contacts.append(contact)

            print(f"  [FOUND] {len(contacts)} contact(s)")
            return contacts

        except Exception as e:
            print(f"  [ERROR] Error finding contacts: {str(e)}")
            return []

        finally:
            # Rate limiting
            time.sleep(self.rate_limit_delay)

    def process_excel(
        self,
        input_file: str,
        output_file: str,
        university_column: str = "University",
        sheet_name: str = "Sheet1",
        start_row: int = 0,
        max_universities: Optional[int] = None,
        skip_existing: bool = False
    ) -> pd.DataFrame:
        """
        Process Excel or CSV file with university names and add contact information.
        Creates one row per contact found (normalized format for easy sorting/filtering).

        Args:
            input_file: Path to input Excel/CSV file
            output_file: Path to output Excel/CSV file
            university_column: Name of column containing university names
            sheet_name: Sheet name to read from (Excel only)
            start_row: Row to start from (for resuming)
            max_universities: Maximum number of universities to process (None for all)
            skip_existing: Skip universities that already have contacts (default: False)

        Returns:
            DataFrame with results (one row per contact)
        """
        print(f"\n{'='*60}")
        print(f"University Contact Finder")
        print(f"Provider: {self.provider} | Model: {self.model}")
        print(f"Output Format: One row per contact")
        print(f"{'='*60}")

        # Read input file (supports both CSV and Excel)
        print(f"\n[READING] {input_file}...")
        if input_file.lower().endswith('.csv'):
            df_input = pd.read_csv(input_file)
            file_type = 'csv'
        else:
            df_input = pd.read_excel(input_file, sheet_name=sheet_name)
            file_type = 'excel'

        if university_column not in df_input.columns:
            raise ValueError(f"Column '{university_column}' not found. Available columns: {list(df_input.columns)}")

        print(f"  Found {len(df_input)} universities")

        # Apply filters
        if start_row > 0:
            df_input = df_input.iloc[start_row:]
            print(f"  Starting from row {start_row}")

        # Check for existing contacts and skip if requested
        if skip_existing and 'has_existing_contact' in df_input.columns:
            df_to_process = df_input[~df_input['has_existing_contact']]
            skipped_count = len(df_input) - len(df_to_process)
            print(f"  Skipping {skipped_count} universities with existing contacts")
            print(f"  {len(df_to_process)} universities need contact info")
            df_input = df_to_process

        if max_universities:
            df_input = df_input.head(max_universities)
            print(f"  Processing first {max_universities} universities")

        # Get original columns from input file
        original_columns = list(df_input.columns)

        # Contact-specific columns to add
        contact_columns = [
            'contact_type', 'contact_name', 'contact_title', 'contact_department',
            'contact_email', 'contact_phone', 'contact_website', 'contact_address',
            'contact_source_url', 'search_status', 'last_updated'
        ]

        # Initialize output list to collect all rows
        output_rows = []

        # Process each university
        total = len(df_input)
        total_contacts = 0

        for idx, row in df_input.iterrows():
            university = row[university_column]
            print(f"\n[{idx - df_input.index[0] + 1}/{total}] Processing: {university}")

            try:
                contacts = self.find_contacts(university)

                if contacts:
                    # Create one row per contact, preserving original university data
                    for contact in contacts:
                        new_row = row.to_dict()  # Copy original row data
                        new_row['contact_type'] = contact.contact_type or contact.department or 'unknown'
                        new_row['contact_name'] = contact.name
                        new_row['contact_title'] = contact.title
                        new_row['contact_department'] = contact.department
                        new_row['contact_email'] = contact.email
                        new_row['contact_phone'] = contact.phone
                        new_row['contact_website'] = contact.website
                        new_row['contact_address'] = contact.address or contact.mailing_address or contact.office
                        new_row['contact_source_url'] = contact.source_url
                        new_row['search_status'] = 'completed'
                        new_row['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        output_rows.append(new_row)
                        total_contacts += 1

                    print(f"  [FOUND] {len(contacts)} contact(s)")
                else:
                    # No contacts found - still add a row to track this university
                    new_row = row.to_dict()
                    for col in contact_columns:
                        new_row[col] = None
                    new_row['search_status'] = 'no_contacts_found'
                    new_row['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    output_rows.append(new_row)
                    print(f"  [FOUND] 0 contact(s)")

                # Save progress after each university
                df_output = pd.DataFrame(output_rows)
                if file_type == 'csv' or output_file.lower().endswith('.csv'):
                    df_output.to_csv(output_file, index=False)
                else:
                    df_output.to_excel(output_file, index=False, sheet_name=sheet_name)
                print(f"  [SAVED] Progress saved to {output_file}")

            except Exception as e:
                print(f"  [ERROR] Error: {str(e)}")
                # Add error row
                new_row = row.to_dict()
                for col in contact_columns:
                    new_row[col] = None
                new_row['search_status'] = f'error: {str(e)}'
                new_row['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                output_rows.append(new_row)

                # Save progress
                df_output = pd.DataFrame(output_rows)
                if file_type == 'csv' or output_file.lower().endswith('.csv'):
                    df_output.to_csv(output_file, index=False)
                else:
                    df_output.to_excel(output_file, index=False, sheet_name=sheet_name)

        # Final output
        df_output = pd.DataFrame(output_rows)

        print(f"\n{'='*60}")
        print(f"[COMPLETE] Processing complete!")
        print(f"  Universities processed: {total}")
        print(f"  Total contacts found: {total_contacts}")
        print(f"  Output rows: {len(df_output)}")
        print(f"[SAVED] Results saved to: {output_file}")
        print(f"{'='*60}\n")

        return df_output


def main():
    """Example usage"""
    import argparse

    parser = argparse.ArgumentParser(description="Find university institutional research contacts")
    parser.add_argument("input_file", help="Input Excel file with university names")
    parser.add_argument("output_file", help="Output Excel file for results")
    parser.add_argument("--provider", choices=["openai", "anthropic", "perplexity", "ollama"],
                       default="perplexity", help="LLM provider to use")
    parser.add_argument("--model", help="Specific model to use")
    parser.add_argument("--search-api", choices=["perplexity", "tavily", "brave", "serp"],
                       default="perplexity", help="Search API to use")
    parser.add_argument("--column", default="University", help="Column name with university names")
    parser.add_argument("--sheet", default="Sheet1", help="Sheet name to process")
    parser.add_argument("--start-row", type=int, default=0, help="Row to start from")
    parser.add_argument("--max", type=int, help="Maximum universities to process")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")

    args = parser.parse_args()

    # Create finder
    finder = UniversityContactFinder(
        provider=args.provider,
        model=args.model,
        search_api=args.search_api,
        rate_limit_delay=args.delay
    )

    # Process Excel file
    finder.process_excel(
        input_file=args.input_file,
        output_file=args.output_file,
        university_column=args.column,
        sheet_name=args.sheet,
        start_row=args.start_row,
        max_universities=args.max
    )


if __name__ == "__main__":
    main()
