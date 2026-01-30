# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

University Contact Finder - A toolset for automatically discovering and extracting contact information for university **General Counsel** and **Institutional Research (OIR)** offices using AI/LLMs and web search APIs. Designed to process large datasets with resume capability, progress saving, and multiple LLM provider support.

**Contact Priority:**
1. General Counsel (legal department) - PRIMARY
2. OIR Director/Manager (Institutional Research) - SECONDARY

## Data Sources

### IPEDS Database (US Department of Education)
**Location:** `C:\Users\lfelican\dev\Scripts\data\universities.csv.xlsx`
- **6,050 universities** from IPEDS (Integrated Postsecondary Education Data System)
- Source: https://nces.ed.gov/ipeds/datacenter/
- Contains: UnitID, Institution Name, Address, City, State, ZIP, Chief Administrator, Phone, Website URLs
- Data suffix `(HD2024)` indicates 2024 survey data

### Other Data Files in `C:\Users\lfelican\dev\Scripts\data\`
- `Comprehensive_US_Universities_IR_Contacts_Database.csv` - Pre-existing IR contacts
- `US_Universities_IR_Contacts_Database.xlsx` - IR contacts reference
- `universities_master_with_contacts.xlsx` - Merged master file

### Project Input File
- `b_schools_list.xlsx` - 376 universities (exported from HubSpot CRM)
- Columns: `Record ID - Company`, `university`

## Architecture

### Core Pipeline

```
Input Excel/CSV → UniversityContactFinder → LLM + Web Search → One Row Per Contact → Output Excel/CSV
```

**Main Components:**

1. **university_contact_finder.py** - Core engine
   - Prioritizes General Counsel contacts first, then OIR
   - Outputs **one row per contact** (normalized format for easy sorting/filtering)
   - Supports 4 LLM providers: OpenAI, Anthropic Claude, Perplexity (recommended), Ollama
   - Progress saved after each university (resume-capable)

2. **process_universities.py** - Batch processor for IPEDS dataset
   - Cost/time estimation before processing
   - `--skip-existing` flag to process only universities without contacts
   - `--exclude-from` flag to skip universities already in other files (with fuzzy matching)
   - `--fuzzy-threshold` to control matching sensitivity (default: 0.85)
   - Auto-detects Excel sheet names (no longer requires 'Sheet1')

3. **merge_ir_contacts.py** / **merge_comprehensive_contacts.py** - Database merging utilities

4. **remove_duplicates.py** - Deduplication based on IPEDS UnitID

## Output Schema (One Row Per Contact)

Each row represents ONE contact with these columns:
- Original columns from input file (e.g., `Record ID - Company`, `university`)
- `contact_type` - "general_counsel", "oir", etc.
- `contact_name` - Full name
- `contact_title` - Job title
- `contact_department` - Department name
- `contact_email` - Email address
- `contact_phone` - Phone number
- `contact_website` - Department/contact page URL
- `contact_address` - Physical address (building, room, street, city, state, zip)
- `contact_source_url` - URL where contact info was found
- `search_status` - "completed", "no_contacts_found", or error message
- `last_updated` - Timestamp

**Example Output:**
```
| university | contact_type    | contact_name  | contact_email    |
|------------|-----------------|---------------|------------------|
| Harvard    | general_counsel | John Smith    | john@harvard.edu |
| Harvard    | oir             | Jane Doe      | jane@harvard.edu |
| Stanford   | general_counsel | Bob Wilson    | bob@stanford.edu |
```

## Commands

### Setup
```powershell
pip install -r requirements_university_finder.txt
cp .env.example .env  # Add your API keys
```

### Processing Universities
```powershell
# Test with 3 universities
python university_contact_finder.py b_schools_list.xlsx test_output.xlsx --max 3 --provider perplexity --column university

# Process all universities in a file
python university_contact_finder.py b_schools_list.xlsx output.xlsx --provider perplexity --column university

# Resume from row 50
python university_contact_finder.py input.xlsx output.xlsx --start-row 50

# Process IPEDS dataset
python process_universities.py --input "C:\Users\lfelican\dev\Scripts\data\universities.csv.xlsx" --max 100
```

### Key Command Options
- `--provider` - LLM provider: perplexity (recommended), openai, anthropic, ollama
- `--column` - Column name containing university names (default: "University")
- `--max` - Limit number of universities to process
- `--start-row` - Resume from specific row
- `--delay` - Seconds between requests (default: 1.0)
- `--exclude-from` - Skip universities found in these file(s) (supports multiple files)
- `--fuzzy-threshold` - Similarity threshold for fuzzy matching (0-1, default: 0.85)

### Excluding Already-Processed Universities
```powershell
# Exclude universities from one file
python process_universities.py --input data/universities.csv.xlsx --exclude-from b_schools_contacts_full.xlsx --all

# Exclude from multiple files
python process_universities.py --input data/universities.csv.xlsx --exclude-from file1.xlsx file2.xlsx --all

# Adjust fuzzy matching (stricter = 0.9, looser = 0.75)
python process_universities.py --exclude-from existing.xlsx --fuzzy-threshold 0.9 --all
```

The exclusion feature uses fuzzy matching to handle name variations like:
- "University of California, Berkeley" vs "UC Berkeley"
- "Saint Mary's College" vs "St. Mary's College"

## Key Configuration

### Environment Variables (.env)
```
PERPLEXITY_API_KEY=pplx-...    # Recommended (has built-in search)
OPENAI_API_KEY=sk-...          # Alternative
ANTHROPIC_API_KEY=sk-ant-...   # Alternative
TAVILY_API_KEY=tvly-...        # Required if not using Perplexity
```

### Default Models
- Perplexity: `sonar`
- OpenAI: `gpt-4o-mini`
- Anthropic: `claude-3-5-sonnet-20241022`
- Ollama: `llama3.1:8b`

## Cost Estimates

Per 100 universities:
- Perplexity: ~$1.50
- OpenAI GPT-4o-mini + Tavily: ~$2.50
- Anthropic Claude + Tavily: ~$5.50

## Recent Processing Results

### HubSpot B-Schools (b_schools_list.xlsx)
- **Input:** 376 universities
- **Output:** 601 rows (one per contact)
- **Contacts found:** 555
  - General Counsel: 437 (87.5% of universities)
  - OIR: 117 (30.9% of universities)
- **No contacts found:** 45 universities (12%)
- **Output file:** `b_schools_contacts_full.xlsx`

### Full IPEDS Database Run (January 2026)
- **Input:** 6,050 universities from IPEDS
- **Excluded:** 368 (already in b_schools_contacts_full.xlsx via fuzzy matching)
- **Processed:** 5,682 universities
- **Contacts found:** 2,654 (~47% success rate)
- **Output rows:** 6,546
- **Output file:** `C:\Users\lfelican\dev\Scripts\data\universities.csv_with_contacts.xlsx`
- **Provider:** Perplexity (sonar model)
- **Note:** Many smaller/vocational schools (beauty academies, trade schools) don't have General Counsel or OIR offices

## Important Notes

- Progress auto-saves after each university - safe to interrupt with Ctrl+C
- Use `--start-row` to resume processing
- Perplexity provider is recommended (built-in web search, most accurate)
- Output format is one row per contact for easy sorting/filtering in Excel
- Universities with no contacts still get a row with `search_status = 'no_contacts_found'`
- Excel sheet names are auto-detected (no need to specify 'Sheet1')
- Use `--exclude-from` to avoid reprocessing universities from previous runs
