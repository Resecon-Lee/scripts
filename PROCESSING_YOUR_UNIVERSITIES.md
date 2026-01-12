# Processing Your Universities File

Your file: `data/universities.csv.xlsx`
- **Total universities**: 6,050
- **Column name**: "Institution Name"
- **File type**: Excel (despite .csv in filename)

## ✅ Script is Ready!

**Good news**: The script I created will work with your file without any modifications! I've also added CSV support and created a specialized runner script.

## Important Notes About Your Data

### Not All Universities Will Have IR Contacts

Your file includes ALL types of institutions:
- ✅ Major universities (Harvard, Stanford, MIT) - **will likely have IR offices**
- ⚠️ Small colleges - **may or may not have IR offices**
- ⚠️ Beauty schools, trade schools - **probably won't have IR offices**
- ⚠️ Specialized academies - **unlikely to have IR offices**

**Expected success rate**: 20-40% of institutions will have findable IR contacts
- Large universities (R1/R2): ~80-90% success
- Medium colleges: ~40-60% success
- Small/specialized schools: ~5-20% success

The script will handle this gracefully:
- `contacts_found = 0` when no contacts found (normal!)
- `search_status = "completed"` even if 0 contacts
- Still searches admissions/provost/financial aid as fallback

## Quick Start

### 1. Install Dependencies (if not done)
```powershell
pip install pandas openpyxl requests python-dotenv openai anthropic
```

### 2. Set Up API Key
Copy `.env.example` to `.env` and add your Perplexity API key:
```
PERPLEXITY_API_KEY=pplx-your-key-here
```

### 3. Test with 10 Universities
```powershell
python process_universities.py --test
```

This will:
- Process first 10 universities
- Cost: ~$0.15
- Time: ~30 seconds
- Output: `data/universities_with_contacts.xlsx`

### 4. Review Test Results
Open `data/universities_with_contacts.xlsx` and check:
- How many contacts were found (`contacts_found` column)
- Quality of extracted information
- If format looks good

### 5. Process More (Gradually)
```powershell
# Process first 100
python process_universities.py --max 100
# Cost: ~$1.50, Time: ~5 minutes

# Process first 500
python process_universities.py --max 500
# Cost: ~$7.50, Time: ~25 minutes

# Process all 6,050 (if needed)
python process_universities.py --all
# Cost: ~$90, Time: ~5 hours
```

## Recommended Approach

### Option A: Process All (If Budget Allows)
```powershell
# Use Perplexity for all 6,050 universities
# Estimated cost: $90, Time: ~5 hours
python process_universities.py --all --provider perplexity
```

### Option B: Process Major Universities Only
Manually filter your Excel first to include only:
- R1/R2 research universities
- State universities
- Institutions with 1000+ students

Then process that subset.

### Option C: Batch Processing
```powershell
# Process in batches of 500
python process_universities.py --max 500
python process_universities.py --start 500 --max 500
python process_universities.py --start 1000 --max 500
# ... and so on
```

### Option D: Use Free Ollama for Large Batches
```powershell
# Install Ollama first: https://ollama.ai/
ollama pull llama3.1:8b

# Process all 6,050 with free local LLM
# Cost: ~$30 (just search API), Time: ~13 hours
python process_universities.py --all --provider ollama --search-api tavily
```

## Commands Reference

### Testing
```powershell
# Test with 10 universities (recommended first step)
python process_universities.py --test

# Test with specific provider
python process_universities.py --test --provider openai
```

### Processing
```powershell
# Process first N universities
python process_universities.py --max 100

# Process all universities
python process_universities.py --all

# Resume from specific row
python process_universities.py --start 1000 --max 500

# Use different output file
python process_universities.py --max 100 --output my_results.xlsx
```

### Provider Options
```powershell
# Use Perplexity (recommended)
python process_universities.py --max 100 --provider perplexity

# Use OpenAI (needs Tavily)
python process_universities.py --max 100 --provider openai --search-api tavily

# Use Claude (highest quality)
python process_universities.py --max 100 --provider anthropic --search-api tavily

# Use Ollama (free, local)
python process_universities.py --max 100 --provider ollama --search-api tavily
```

### Advanced
```powershell
# Slower rate (if hitting rate limits)
python process_universities.py --max 100 --delay 2.0

# Skip confirmation prompt (for automation)
python process_universities.py --max 100 --no-confirm
```

## Expected Output

Your output file will have these NEW columns added:

**Contact 1:**
- contact_1_name
- contact_1_title
- contact_1_department
- contact_1_email ⭐
- contact_1_phone ⭐
- contact_1_office
- contact_1_website

**Contact 2 & 3:** (same fields)

**Metadata:**
- search_status (`completed` or `error: ...`)
- contacts_found (`0`, `1`, `2`, or `3`)
- last_updated (timestamp)
- source_urls (where info was found)

### Sample Output Row

| Institution Name | contacts_found | contact_1_name | contact_1_email | contact_1_phone | contact_1_title |
|------------------|----------------|----------------|-----------------|-----------------|-----------------|
| Harvard University | 2 | Dr. Jane Smith | jane@harvard.edu | (617) 555-1234 | Director of IR |
| ABC Beauty Academy | 0 | | | | |

## Cost & Time Estimates

### By Batch Size (using Perplexity)

| Universities | Cost | Time |
|--------------|------|------|
| 10 (test) | $0.15 | 30 sec |
| 50 | $0.75 | 2.5 min |
| 100 | $1.50 | 5 min |
| 500 | $7.50 | 25 min |
| 1,000 | $15 | 50 min |
| 6,050 (all) | $90 | 5 hours |

### By Provider (for all 6,050)

| Provider | Cost | Time |
|----------|------|------|
| Perplexity | $90 | 5 hrs |
| OpenAI (mini) + Tavily | $150 | 6.5 hrs |
| Claude + Tavily | $330 | 8 hrs |
| Ollama + Tavily | $30 | 13 hrs |

## Troubleshooting

### "Institution Name" column not found
The script is configured for your specific file. If error occurs:
```powershell
# Check what columns are in your file
python -c "import pandas as pd; print(pd.read_excel('data/universities.csv.xlsx').columns.tolist())"
```

### Process interrupted
No problem! Progress is saved after each university:
```powershell
# Check last row processed
# Open data/universities_with_contacts.xlsx
# Find last row with data in 'last_updated' column
# Resume from next row

python process_universities.py --start 150 --max 500
```

### Many universities have 0 contacts
This is normal! Expected results:
- 20-40% of institutions will have IR contacts
- Large universities: higher success rate
- Small/specialized schools: lower success rate

### Running out of API credits
```powershell
# Switch to Ollama (free LLM)
python process_universities.py --provider ollama --start 100 --max 500

# Or use free Tavily tier (1,000 searches/month)
# Process 1,000 per month: python process_universities.py --max 1000
```

## Monitoring Progress

The script shows real-time progress:
```
[1/100] Processing: Harvard University
  🔍 Searching for contacts...
  ✅ Found 2 contact(s)
  💾 Progress saved to data/universities_with_contacts.xlsx

[2/100] Processing: ABC Beauty Academy
  🔍 Searching for contacts...
  ✅ Found 0 contact(s)
  💾 Progress saved to data/universities_with_contacts.xlsx
```

You can also:
1. Open the output Excel file during processing
2. Check the `contacts_found` column for summary
3. Monitor the `last_updated` timestamps

## After Processing

### Analyze Results
```powershell
python -c "
import pandas as pd
df = pd.read_excel('data/universities_with_contacts.xlsx')

total = len(df)
completed = len(df[df['search_status'] == 'completed'])
with_contacts = len(df[df['contacts_found'] > 0])

print(f'Total processed: {total}')
print(f'Successful: {completed}')
print(f'With contacts: {with_contacts} ({with_contacts/total*100:.1f}%)')
print(f'Total contacts: {df[\"contacts_found\"].sum():.0f}')
"
```

### Filter to Only Universities with Contacts
```powershell
python -c "
import pandas as pd
df = pd.read_excel('data/universities_with_contacts.xlsx')
df_with_contacts = df[df['contacts_found'] > 0]
df_with_contacts.to_excel('data/universities_with_contacts_only.xlsx', index=False)
print(f'Saved {len(df_with_contacts)} universities with contacts')
"
```

## Best Practices

1. **Start Small**: Always run `--test` first
2. **Check Quality**: Review first 10 results before processing all
3. **Save Money**: Use `--max` to process in batches
4. **Be Prepared**: Not all institutions will have IR offices (this is normal!)
5. **Resume Capability**: If interrupted, use `--start` to continue
6. **Monitor Progress**: Output file updates after each university
7. **Verify Results**: Spot-check contact info for accuracy

## Next Steps

```powershell
# 1. Test with 10 universities
python process_universities.py --test

# 2. Review results in data/universities_with_contacts.xlsx

# 3. If satisfied, process more
python process_universities.py --max 100

# 4. Continue until done!
```

## Questions?

- See `UNIVERSITY_FINDER_README.md` for full documentation
- See `PROVIDER_COMPARISON.md` for provider details
- See `QUICKSTART.md` for general getting started

---

**Ready to start?**
```powershell
python process_universities.py --test
```
