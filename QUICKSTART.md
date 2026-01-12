# University Contact Finder - Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Install Dependencies

```powershell
pip install pandas openpyxl requests python-dotenv openai anthropic
```

Or use the requirements file:
```powershell
pip install -r requirements_university_finder.txt
```

## Step 2: Get an API Key

**Option A: Perplexity (Recommended - Easiest)**
- Go to https://www.perplexity.ai/settings/api
- Sign up and get API key
- Free tier: $5 credit
- Has built-in web search (no separate search API needed!)

**Option B: OpenAI + Tavily**
- OpenAI: https://platform.openai.com/api-keys
- Tavily: https://tavily.com (1,000 free searches/month)

**Option C: Ollama (Free, Local)**
- Download: https://ollama.ai/
- Install and run: `ollama pull llama3.1:8b`
- Still need search API (Tavily recommended)

## Step 3: Interactive Setup

Run the quick start script:
```powershell
python quickstart_university_finder.py
```

This will:
1. ✅ Check your dependencies
2. ✅ Help you set up your API keys
3. ✅ Create a sample Excel file
4. ✅ Run a test with 3 universities
5. ✅ Show you the results!

## Step 4: Use Your Own Data

Create an Excel file with a "University" column:

```
| University                      |
|---------------------------------|
| Harvard University              |
| Stanford University             |
| Your University Here            |
```

Then run:
```powershell
python university_contact_finder.py your_universities.xlsx results.xlsx
```

## That's It!

The script will:
- 🔍 Search for Institutional Research offices
- 📧 Extract emails, phones, names, titles
- 💾 Save progress after each university
- ✅ Create an Excel file with all contacts

## Example Output

Your output Excel will have:

| University | contact_1_name | contact_1_email | contact_1_phone | contact_1_title | ... |
|------------|----------------|-----------------|-----------------|-----------------|-----|
| Harvard    | Dr. Jane Smith | jane@harvard.edu| (617) 555-1234 | Director of IR  | ... |
| Stanford   | John Doe       | jdoe@stanford.edu| (650) 555-5678| Associate Director | ... |

## Cost Estimate

- **Perplexity**: ~$0.50-$2.00 per 100 universities
- **GPT-4o-mini**: ~$1.00-$3.00 per 100 universities
- **Ollama**: Free LLM + search API costs

## Need Help?

See `UNIVERSITY_FINDER_README.md` for:
- Detailed documentation
- All command-line options
- Troubleshooting guide
- Advanced usage examples

## Common Commands

```powershell
# Test with just 5 universities first
python university_contact_finder.py input.xlsx output.xlsx --max 5

# Resume from row 50 (if script was interrupted)
python university_contact_finder.py input.xlsx output.xlsx --start-row 50

# Use different provider
python university_contact_finder.py input.xlsx output.xlsx --provider openai

# Get help
python university_contact_finder.py --help
```

## Tips

1. **Start small**: Test with `--max 5` first
2. **Check results**: Open output Excel after a few universities
3. **Be patient**: Each university takes 2-5 seconds
4. **Save progress**: Script auto-saves after each university
5. **Resume if interrupted**: Use `--start-row` to continue

---

**Ready to go? Run:**
```powershell
python quickstart_university_finder.py
```
