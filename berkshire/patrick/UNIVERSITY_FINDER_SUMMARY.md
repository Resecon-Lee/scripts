# University Contact Finder - Complete Summary

## What You Have

A complete, production-ready Python system for automatically finding university Institutional Research office contacts using AI and web search.

## Files Created

### Core Scripts
1. **`university_contact_finder.py`** (20KB)
   - Main script with full functionality
   - Supports 4 LLM providers (OpenAI, Claude, Perplexity, Ollama)
   - Supports 4 search APIs (Perplexity, Tavily, Brave, SerpAPI)
   - Excel processing with progress saving
   - Command-line interface

2. **`quickstart_university_finder.py`** (8KB)
   - Interactive setup wizard
   - Dependency checker
   - API key configuration
   - Sample file creation
   - Test runner

### Documentation
3. **`QUICKSTART.md`** - 5-minute getting started guide
4. **`UNIVERSITY_FINDER_README.md`** - Complete documentation (10KB)
5. **`PROVIDER_COMPARISON.md`** - Detailed provider comparison (8KB)
6. **`PROVIDER_COMPARISON.md`** - Choose the right LLM/search combo

### Configuration
7. **`requirements_university_finder.txt`** - Python dependencies
8. **`.env.example`** - API key template

### Examples
9. **`example_universities.xlsx`** - Sample input file

---

## Quick Start (3 Steps)

### 1. Install
```powershell
pip install -r requirements_university_finder.txt
```

### 2. Setup
```powershell
python quickstart_university_finder.py
```
This guides you through API key setup and runs a test.

### 3. Run
```powershell
python university_contact_finder.py your_universities.xlsx results.xlsx
```

---

## Features

### What It Does
✅ Finds Institutional Research office contacts
✅ Searches related departments (Admissions, Provost, Financial Aid)
✅ Extracts: names, titles, emails, phones, websites, social media
✅ Processes Excel files automatically
✅ Saves progress after each university
✅ Resumes from interruptions
✅ Handles errors gracefully

### What You Get
- Up to 3 contacts per university
- Full contact details (email, phone, title, department, office location)
- Source URLs for verification
- Timestamps and status tracking

---

## Provider Options

### Recommended: Perplexity
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity
```
- **Why**: Built-in search, most accurate, cost-effective
- **Cost**: $0.50-$2 per 100 universities
- **Setup**: One API key from https://www.perplexity.ai/settings/api

### Alternative: OpenAI + Tavily
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider openai --search-api tavily
```
- **Why**: Established service, good quality
- **Cost**: $1-$3 per 100 universities
- **Setup**: OpenAI + Tavily API keys

### Budget: Ollama (Local + Free)
```powershell
python university_contact_finder.py input.xlsx output.xlsx --provider ollama --search-api tavily
```
- **Why**: Free LLM, good for large batches
- **Cost**: Only search API costs
- **Setup**: Install Ollama + search API key

See `PROVIDER_COMPARISON.md` for detailed comparison.

---

## Common Use Cases

### Test with a Few Universities
```powershell
python university_contact_finder.py input.xlsx test.xlsx --max 5
```

### Process Large Batch
```powershell
# Use Perplexity for best results
python university_contact_finder.py universities.xlsx results.xlsx --provider perplexity --delay 1.5
```

### Resume After Interruption
```powershell
# If stopped at row 49, resume from row 50
python university_contact_finder.py input.xlsx output.xlsx --start-row 50
```

### Different Column Name
```powershell
# If your Excel uses "Institution" instead of "University"
python university_contact_finder.py input.xlsx output.xlsx --column Institution
```

---

## Output Format

Your Excel will have these columns added:

**Primary Contact:**
- contact_1_name
- contact_1_title
- contact_1_department
- contact_1_email
- contact_1_phone
- contact_1_office
- contact_1_website

**Additional Contacts:** (contact_2_*, contact_3_*)

**Metadata:**
- search_status
- contacts_found
- last_updated
- source_urls

---

## Cost Examples

| Universities | Provider | Estimated Cost |
|--------------|----------|---------------|
| 10 | Perplexity | $0.05 - $0.20 |
| 50 | Perplexity | $0.25 - $1.00 |
| 100 | Perplexity | $0.50 - $2.00 |
| 500 | Perplexity | $2.50 - $10.00 |
| 100 | OpenAI (mini) | $1.00 - $3.00 |
| 100 | Claude | $3.00 - $8.00 |
| 1000 | Ollama + Tavily | $5.00 - $20.00 |

---

## Documentation Quick Reference

- **New user?** Start with `QUICKSTART.md`
- **Need details?** Read `UNIVERSITY_FINDER_README.md`
- **Choose provider?** See `PROVIDER_COMPARISON.md`
- **API keys?** Copy `.env.example` to `.env`
- **Troubleshooting?** Check README troubleshooting section

---

## Example Workflow

### First Time User
1. Read `QUICKSTART.md`
2. Run `python quickstart_university_finder.py`
3. Get Perplexity API key
4. Test with sample file
5. Process your universities

### Experienced User
1. Create Excel with "University" column
2. Copy `.env.example` to `.env`, add API key
3. Run: `python university_contact_finder.py input.xlsx output.xlsx`
4. Open output.xlsx to see results

---

## Best Practices

1. **Start Small**: Always test with `--max 5` first
2. **Check Results**: Review first few contacts for accuracy
3. **Save Progress**: Script auto-saves, but keep backups
4. **Verify Data**: Spot-check contact information
5. **Respect Rate Limits**: Use `--delay` if needed
6. **Use Perplexity**: Best accuracy-to-cost ratio

---

## Support & Help

### Command Line Help
```powershell
python university_contact_finder.py --help
```

### Common Issues

**"No API key found"**
- Create `.env` file (copy from `.env.example`)
- Add your API key without quotes

**"Module not found"**
```powershell
pip install -r requirements_university_finder.txt
```

**"No contacts found"**
- Check university name is correct
- Some universities may not have public IR contacts
- Try manually searching to verify

**Script stops/crashes**
- Check `output.xlsx` for last completed row
- Resume with `--start-row` from next row

---

## Advanced Features

### Programmatic Use
```python
from university_contact_finder import UniversityContactFinder

finder = UniversityContactFinder(provider="perplexity")
contacts = finder.find_contacts("Harvard University")

for contact in contacts:
    print(f"{contact.name}: {contact.email}")
```

### Custom Configuration
```python
finder = UniversityContactFinder(
    provider="openai",
    model="gpt-4o",  # Use GPT-4 instead of mini
    search_api="tavily",
    rate_limit_delay=2.0,  # 2 second delay
    max_retries=5  # More retries
)
```

---

## Next Steps

### Ready to Start?
```powershell
# Interactive setup
python quickstart_university_finder.py

# Or direct run
python university_contact_finder.py your_file.xlsx results.xlsx
```

### Need More Info?
- `QUICKSTART.md` - Getting started
- `UNIVERSITY_FINDER_README.md` - Full documentation
- `PROVIDER_COMPARISON.md` - Choose best provider

---

## File Checklist

Before running, ensure you have:
- ✅ Installed dependencies (`requirements_university_finder.txt`)
- ✅ Created `.env` file with API key
- ✅ Prepared Excel file with "University" column
- ✅ Tested with `--max 5` first

---

## Success Tips

1. **Perplexity first**: Best all-around choice
2. **Test small**: Use `--max 5` to verify before big batches
3. **Monitor progress**: Check output Excel periodically
4. **Verify accuracy**: Spot-check first 5-10 results
5. **Be patient**: Each university takes 2-5 seconds
6. **Save API costs**: Test with small batch first

---

## Contact Information Extracted

The script searches for and extracts:

### Departments:
- Office of Institutional Research ⭐ (primary target)
- Institutional Effectiveness
- Analytics & Planning
- Assessment Office
- Office of Admissions
- Office of the Provost
- Academic Affairs
- Financial Aid
- Enrollment Management

### Information:
- Name
- Job Title
- Department
- Email ⭐
- Phone ⭐
- Fax
- Office Location
- Website
- LinkedIn
- Twitter/X
- Mailing Address
- Source URL (for verification)

---

## License & Ethics

- ✅ Open source (MIT License)
- ✅ Only public information
- ✅ Ethical web scraping
- ⚠️ Verify accuracy before use
- ⚠️ Comply with data protection laws

---

**Questions?** Check `UNIVERSITY_FINDER_README.md` for comprehensive documentation.

**Ready to go?** Run: `python quickstart_university_finder.py`
