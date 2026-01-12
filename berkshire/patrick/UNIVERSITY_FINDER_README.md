# University Contact Finder

Automatically find and extract contact information for university Institutional Research offices and related departments using AI/LLMs and web search.

## Features

- ✅ Multiple LLM providers (OpenAI, Claude, Perplexity, Ollama)
- ✅ Multiple search APIs (Perplexity, Tavily, Brave, SerpAPI)
- ✅ Automated Excel processing with progress saving
- ✅ Extracts: names, titles, emails, phones, websites, social media
- ✅ Searches multiple departments (IR, Admissions, Provost, Financial Aid, etc.)
- ✅ Retry logic and error handling
- ✅ Resume capability (start from specific row)

## Quick Start

### 1. Install Dependencies

```powershell
pip install -r requirements_university_finder.txt
```

### 2. Set Up API Keys

Copy `.env.example` to `.env` and add your API keys:

```powershell
cp .env.example .env
# Edit .env with your favorite editor
```

**Recommended Option: Perplexity** (has built-in web search, most accurate)
- Sign up at https://www.perplexity.ai/settings/api
- Get API key (free tier available)
- Add to `.env`: `PERPLEXITY_API_KEY=pplx-...`

**Alternative Options:**
- **OpenAI** (gpt-4o-mini): https://platform.openai.com/api-keys
- **Anthropic Claude**: https://console.anthropic.com/
- **Ollama** (free, local): https://ollama.ai/ (no API key needed)

### 3. Prepare Your Excel File

Create an Excel file with a column named "University" (or any name you specify):

```
| University                      |
|---------------------------------|
| Harvard University              |
| Stanford University             |
| University of California LA     |
```

### 4. Run the Script

**Using Perplexity (Recommended):**
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity
```

**Using OpenAI with Tavily Search:**
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider openai --search-api tavily
```

**Using Claude:**
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider anthropic --search-api tavily
```

**Using Ollama (Free, Local):**
```powershell
# First, start Ollama and pull a model:
ollama pull llama3.1:8b

# Then run:
python university_contact_finder.py input.xlsx output.xlsx --provider ollama --search-api tavily
```

## Command Line Options

```
usage: university_contact_finder.py [-h] [--provider {openai,anthropic,perplexity,ollama}]
                                     [--model MODEL] [--search-api {perplexity,tavily,brave,serp}]
                                     [--column COLUMN] [--sheet SHEET] [--start-row START_ROW]
                                     [--max MAX] [--delay DELAY]
                                     input_file output_file

Arguments:
  input_file                 Input Excel file with university names
  output_file                Output Excel file for results

Options:
  --provider                 LLM provider: openai, anthropic, perplexity, ollama (default: perplexity)
  --model                    Specific model to use (optional)
  --search-api               Search API: perplexity, tavily, brave, serp (default: perplexity)
  --column                   Column name with universities (default: "University")
  --sheet                    Sheet name to process (default: "Sheet1")
  --start-row                Row to start from for resuming (default: 0)
  --max                      Maximum universities to process (optional)
  --delay                    Delay between requests in seconds (default: 1.0)
```

## Examples

### Test with a Few Universities First

```powershell
# Process only first 5 universities
python university_contact_finder.py universities.xlsx test_output.xlsx --max 5
```

### Resume After Interruption

```powershell
# Start from row 50 (if previous run stopped at row 49)
python university_contact_finder.py universities.xlsx output.xlsx --start-row 50
```

### Custom Column Name

```powershell
# If your Excel has a column named "Institution"
python university_contact_finder.py input.xlsx output.xlsx --column Institution
```

### Use Specific Model

```powershell
# Use GPT-4 instead of default gpt-4o-mini
python university_contact_finder.py input.xlsx output.xlsx --provider openai --model gpt-4
```

## Output Format

The script adds these columns to your Excel file:

**Contact 1 (Primary):**
- `contact_1_name` - Full name
- `contact_1_title` - Job title/position
- `contact_1_department` - Department name
- `contact_1_email` - Email address
- `contact_1_phone` - Phone number
- `contact_1_office` - Office location
- `contact_1_website` - Department/personal website

**Contact 2 & 3:** (Same fields, different contacts)

**Metadata:**
- `search_status` - "completed" or error message
- `contacts_found` - Number of contacts found
- `last_updated` - Timestamp of search
- `source_urls` - URLs where information was found

## Cost Estimates

**Per University (approximate):**
- **Perplexity** (Recommended): $0.005 - $0.02 (most accurate, has search built-in)
- **OpenAI GPT-4o-mini + Tavily**: $0.01 - $0.03
- **OpenAI GPT-4 + Tavily**: $0.05 - $0.15
- **Claude Sonnet + Tavily**: $0.03 - $0.08
- **Ollama (Local)**: Free for LLM, paid for search API or free with rate limits

**For 100 universities:**
- Budget $0.50 - $2.00 with Perplexity (recommended)
- Budget $1.00 - $3.00 with GPT-4o-mini
- Budget $20 - $50 with Claude/GPT-4 (higher quality)

## Getting API Keys

### Perplexity (Recommended - Built-in Search)
1. Go to https://www.perplexity.ai/settings/api
2. Create account and get API key
3. Free tier: $5 credit
4. Paid: Pay as you go

### Tavily Search API (If not using Perplexity)
1. Go to https://tavily.com
2. Sign up for free tier (1,000 searches/month)
3. Get API key from dashboard

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create account and add payment method
3. Generate API key
4. Recommended model: `gpt-4o-mini` (cost-effective)

### Anthropic Claude
1. Go to https://console.anthropic.com/
2. Create account and add payment method
3. Generate API key

### Ollama (Free, Local)
1. Download from https://ollama.ai/
2. Install and run: `ollama pull llama3.1:8b`
3. No API key needed!

### Brave Search API (Alternative)
1. Go to https://brave.com/search/api/
2. Free tier: 2,000 queries/month
3. Get API key

### SerpAPI (Google Search Alternative)
1. Go to https://serpapi.com/
2. Free tier: 100 searches/month
3. Get API key

## Troubleshooting

### "No API key found"
- Make sure you created `.env` file (copy from `.env.example`)
- Check that API key is properly set in `.env`
- API key format: `PERPLEXITY_API_KEY=pplx-...` (no quotes, no spaces)

### "Rate limit exceeded"
- Increase delay: `--delay 2.0` (2 seconds between requests)
- Use free tier limits responsibly
- Consider upgrading to paid tier

### "No contacts found"
- Some universities may not have public contact info
- Try different search terms manually to verify
- Check `source_urls` column to see what was searched

### Script crashes/stops
- Progress is saved after each university
- Resume with `--start-row` from where it stopped
- Check output Excel file to see last completed row

### Ollama connection error
- Make sure Ollama is running: `ollama serve`
- Check model is pulled: `ollama list`
- Default port should be 11434

## Tips for Best Results

1. **Start Small**: Test with `--max 5` first to verify it works
2. **Use Perplexity**: Built-in search gives best results
3. **Check Progress**: Output file saves after each university
4. **Be Patient**: Web search + LLM takes 2-5 seconds per university
5. **Verify Results**: Manually spot-check a few contacts for accuracy
6. **Rate Limits**: Respect API rate limits with `--delay`

## Advanced Usage

### Programmatic Use

```python
from university_contact_finder import UniversityContactFinder

# Initialize finder
finder = UniversityContactFinder(
    provider="perplexity",
    model="llama-3.1-sonar-large-128k-online",
    rate_limit_delay=1.0
)

# Find contacts for single university
contacts = finder.find_contacts("Harvard University")
for contact in contacts:
    print(f"{contact.name} - {contact.email}")

# Process entire Excel file
df = finder.process_excel(
    input_file="universities.xlsx",
    output_file="results.xlsx",
    university_column="University",
    max_universities=10  # Process first 10
)
```

### Custom Search

```python
# Use different search API
finder = UniversityContactFinder(
    provider="openai",
    model="gpt-4o-mini",
    search_api="tavily"
)

# Find contacts
contacts = finder.find_contacts("MIT")
```

## What Information Gets Extracted?

The script searches for and extracts:

### Departments Searched:
- Office of Institutional Research
- Institutional Effectiveness
- Analytics and Planning
- Assessment Office
- Office of Admissions
- Office of the Provost
- Academic Affairs
- Financial Aid
- Enrollment Management

### Information Extracted:
- Full name
- Job title/position
- Department name
- Email address
- Phone number (including extensions)
- Fax number
- Office location/building/room
- Department website
- LinkedIn profile
- Twitter/X handle
- Mailing address
- Source URL

## Privacy & Ethics

- ✅ Only extracts publicly available information
- ✅ Information is sourced from official university websites
- ✅ Respects rate limits and robots.txt
- ⚠️ Verify data accuracy before use
- ⚠️ Use responsibly and ethically
- ⚠️ Comply with data protection regulations (GDPR, CCPA, etc.)

## License

MIT License - Feel free to modify and use for your needs.

## Support

For issues or questions:
1. Check this README
2. Review error messages in console output
3. Check the `search_status` column in output Excel for specific errors
4. Verify API keys are correctly set in `.env`

## Changelog

**v1.0.0** - Initial release
- Multi-provider support (OpenAI, Claude, Perplexity, Ollama)
- Multi-search API support (Perplexity, Tavily, Brave, SerpAPI)
- Excel processing with progress saving
- Resume capability
- Comprehensive error handling
