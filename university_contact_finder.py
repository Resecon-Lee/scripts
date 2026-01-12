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
    fax: Optional[str] = None
    office: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    mailing_address: Optional[str] = None
    source_url: Optional[str] = None
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
        base_prompt = f"""Find contact information for the Office of Institutional Research (or similar departments like Institutional Effectiveness, Analytics, Planning and Assessment) at {university_name}.

Also check related departments if IR office is not found:
- Office of Admissions
- Office of the Provost
- Academic Affairs
- Financial Aid
- Enrollment Management

For each contact found, extract:
- Name
- Title/Position
- Department
- Email address
- Phone number
- Fax number (if available)
- Office location
- Website URL
- LinkedIn profile (if available)
- Twitter/X handle (if available)
- Mailing address
- Source URL where information was found

Return the results as a JSON array of contact objects. If no contacts are found, return an empty array.

Example format:
[
  {{
    "name": "Dr. Jane Smith",
    "title": "Director of Institutional Research",
    "department": "Office of Institutional Research",
    "email": "jane.smith@university.edu",
    "phone": "(555) 123-4567",
    "office": "Admin Building, Room 202",
    "website": "https://university.edu/ir",
    "source_url": "https://university.edu/ir/contact",
    "last_updated": "{datetime.now().strftime('%Y-%m-%d')}"
  }}
]

Important:
- Only include verified, current information
- Prefer official university websites
- Include multiple contacts if available
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
        Process Excel or CSV file with university names and add contact information

        Args:
            input_file: Path to input Excel/CSV file
            output_file: Path to output Excel/CSV file
            university_column: Name of column containing university names
            sheet_name: Sheet name to read from (Excel only)
            start_row: Row to start from (for resuming)
            max_universities: Maximum number of universities to process (None for all)
            skip_existing: Skip universities that already have contacts (default: False)

        Returns:
            DataFrame with results
        """
        print(f"\n{'='*60}")
        print(f"University Contact Finder")
        print(f"Provider: {self.provider} | Model: {self.model}")
        print(f"{'='*60}")

        # Read input file (supports both CSV and Excel)
        print(f"\n[READING] {input_file}...")
        if input_file.lower().endswith('.csv'):
            df = pd.read_csv(input_file)
            file_type = 'csv'
        else:
            df = pd.read_excel(input_file, sheet_name=sheet_name)
            file_type = 'excel'

        if university_column not in df.columns:
            raise ValueError(f"Column '{university_column}' not found. Available columns: {list(df.columns)}")

        print(f"  Found {len(df)} universities")

        # Apply filters
        if start_row > 0:
            df = df.iloc[start_row:]
            print(f"  Starting from row {start_row}")

        # Check for existing contacts and skip if requested
        if skip_existing and 'has_existing_contact' in df.columns:
            df_to_process = df[~df['has_existing_contact']]
            skipped_count = len(df) - len(df_to_process)
            print(f"  Skipping {skipped_count} universities with existing contacts")
            print(f"  {len(df_to_process)} universities need contact info")
            df = df_to_process

        if max_universities:
            df = df.head(max_universities)
            print(f"  Processing first {max_universities} universities")

        # Add columns for contact information
        contact_columns = [
            'contact_1_name', 'contact_1_title', 'contact_1_department', 'contact_1_email',
            'contact_1_phone', 'contact_1_office', 'contact_1_website',
            'contact_2_name', 'contact_2_title', 'contact_2_department', 'contact_2_email',
            'contact_2_phone', 'contact_2_office', 'contact_2_website',
            'contact_3_name', 'contact_3_title', 'contact_3_department', 'contact_3_email',
            'contact_3_phone', 'contact_3_office', 'contact_3_website',
            'search_status', 'contacts_found', 'last_updated', 'source_urls'
        ]

        for col in contact_columns:
            if col not in df.columns:
                df[col] = None

        # Process each university
        total = len(df)
        for idx, row in df.iterrows():
            university = row[university_column]
            print(f"\n[{idx - df.index[0] + 1}/{total}] Processing: {university}")

            try:
                contacts = self.find_contacts(university)

                # Store up to 3 contacts
                for i, contact in enumerate(contacts[:3]):
                    prefix = f'contact_{i+1}_'
                    df.at[idx, f'{prefix}name'] = contact.name
                    df.at[idx, f'{prefix}title'] = contact.title
                    df.at[idx, f'{prefix}department'] = contact.department
                    df.at[idx, f'{prefix}email'] = contact.email
                    df.at[idx, f'{prefix}phone'] = contact.phone
                    df.at[idx, f'{prefix}office'] = contact.office
                    df.at[idx, f'{prefix}website'] = contact.website

                # Store metadata
                df.at[idx, 'search_status'] = 'completed'
                df.at[idx, 'contacts_found'] = len(contacts)
                df.at[idx, 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                source_urls = [c.source_url for c in contacts if c.source_url]
                if source_urls:
                    df.at[idx, 'source_urls'] = '; '.join(source_urls)

                # Save progress after each university
                if file_type == 'csv' or output_file.lower().endswith('.csv'):
                    df.to_csv(output_file, index=False)
                else:
                    df.to_excel(output_file, index=False, sheet_name=sheet_name)
                print(f"  [SAVED] Progress saved to {output_file}")

            except Exception as e:
                print(f"  [ERROR] Error: {str(e)}")
                df.at[idx, 'search_status'] = f'error: {str(e)}'
                df.at[idx, 'last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if file_type == 'csv' or output_file.lower().endswith('.csv'):
                    df.to_csv(output_file, index=False)
                else:
                    df.to_excel(output_file, index=False, sheet_name=sheet_name)

        print(f"\n{'='*60}")
        print(f"[COMPLETE] Processing complete!")
        print(f"[SAVED] Results saved to: {output_file}")
        print(f"{'='*60}\n")

        return df


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
