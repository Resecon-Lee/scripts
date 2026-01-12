# Quick Guide: Processing Your Universities File

## Your File
- **Location**: `data/universities.csv.xlsx`
- **Total Universities**: 6,050
- **Column Name**: "Institution Name"

## ✅ No Modifications Needed!

The script works with your file as-is. I've updated it to:
- ✅ Support both CSV and Excel files automatically
- ✅ Handle the "Institution Name" column
- ✅ Gracefully handle when contacts aren't found (expected for many institutions!)

## 🚀 Get Started (3 Commands)

### 1. Install
```powershell
pip install pandas openpyxl requests python-dotenv openai anthropic
```

### 2. Setup API Key
Get a Perplexity API key (free trial available):
- Go to: https://www.perplexity.ai/settings/api
- Create `.env` file and add: `PERPLEXITY_API_KEY=pplx-your-key-here`

### 3. Test
```powershell
python process_universities.py --test
```

This processes the first 10 universities (~$0.15, 30 seconds).

## 📋 What to Expect

### Success Rate
Not all 6,050 institutions will have IR office contacts:
- **Large universities** (Harvard, MIT, etc.): 80-90% will have contacts
- **Medium colleges**: 40-60% will have contacts
- **Small/specialized schools** (beauty academies, trade schools): 5-20% will have contacts

**Overall expected**: 20-40% of institutions will have findable contacts (1,200-2,400 out of 6,050)

This is **completely normal**! Many small institutions don't have dedicated IR offices.

### Output
Your file will have these columns added:
- `contact_1_name`, `contact_1_email`, `contact_1_phone`, etc.
- `contact_2_*`, `contact_3_*` (additional contacts)
- `contacts_found` (0, 1, 2, or 3)
- `search_status` (completed or error)
- `source_urls` (where info was found)

## 💰 Cost Options

### Option 1: Perplexity (Recommended)
```powershell
python process_universities.py --all
```
- **Cost**: ~$90 for all 6,050 universities
- **Time**: ~5 hours
- **Quality**: Best accuracy for web search

### Option 2: Batch Processing (Save Money)
```powershell
# Process 100 at a time
python process_universities.py --max 100  # Cost: $1.50, 5 min
python process_universities.py --start 100 --max 100
python process_universities.py --start 200 --max 100
# etc...
```

### Option 3: Free LLM (Ollama)
```powershell
# Install Ollama first: https://ollama.ai/
ollama pull llama3.1:8b

# Process all with free LLM
python process_universities.py --all --provider ollama
```
- **Cost**: ~$30 (just search API)
- **Time**: ~13 hours
- **Quality**: Good, slightly lower accuracy

## 📊 Processing Commands

```powershell
# Test with 10 universities (RECOMMENDED FIRST STEP)
python process_universities.py --test

# Process first 100
python process_universities.py --max 100

# Process all 6,050
python process_universities.py --all

# Resume from row 500
python process_universities.py --start 500 --max 500

# Use different provider
python process_universities.py --provider openai --max 100
```

## ⚠️ Important Notes

1. **Not all institutions will have contacts** - This is expected! See success rates above.

2. **Progress is saved** - File updates after each university. Safe to interrupt and resume.

3. **Resume if interrupted**:
   ```powershell
   # If stopped at row 249, resume from 250
   python process_universities.py --start 250
   ```

4. **Check results periodically** - Open `data/universities_with_contacts.xlsx` during processing to monitor.

## 🎯 Recommended Workflow

### Day 1: Test
```powershell
python process_universities.py --test
```
Review results, verify quality.

### Day 2: Small Batch
```powershell
python process_universities.py --max 100
```
Cost: $1.50, Time: 5 minutes

### Day 3+: Full Processing
```powershell
# Option A: Process all at once (run overnight)
python process_universities.py --all

# Option B: Process in batches
python process_universities.py --max 500  # ~$7.50, 25 min
python process_universities.py --start 500 --max 500
# Continue as needed...
```

## 📈 Monitor Progress

The script shows real-time updates:
```
[1/6050] Processing: Harvard University
  🔍 Searching for contacts...
  ✅ Found 2 contact(s)
  💾 Progress saved

[2/6050] Processing: ABC Beauty Academy
  ✅ Found 0 contact(s)
  💾 Progress saved
```

## 🔍 After Processing

### Get Statistics
```powershell
python -c "
import pandas as pd
df = pd.read_excel('data/universities_with_contacts.xlsx')
print(f'Total: {len(df)}')
print(f'With contacts: {len(df[df[\"contacts_found\"] > 0])}')
print(f'Success rate: {len(df[df[\"contacts_found\"] > 0])/len(df)*100:.1f}%')
"
```

### Extract Only Universities with Contacts
```powershell
python -c "
import pandas as pd
df = pd.read_excel('data/universities_with_contacts.xlsx')
df[df['contacts_found'] > 0].to_excel('universities_contacts_only.xlsx', index=False)
"
```

## 📚 Documentation

- **PROCESSING_YOUR_UNIVERSITIES.md** - Detailed guide for your file
- **UNIVERSITY_FINDER_README.md** - Complete script documentation
- **PROVIDER_COMPARISON.md** - Compare LLM options
- **QUICKSTART.md** - General getting started

## 🆘 Help

### Issue: "Institution Name column not found"
Your file is correctly configured. If this happens, check:
```powershell
python -c "import pandas as pd; print(pd.read_excel('data/universities.csv.xlsx').columns.tolist())"
```

### Issue: "Many universities have 0 contacts"
This is **normal**! Expected: 60-80% will have 0 contacts (small schools, trade schools, etc.)

### Issue: "Process stopped"
Resume from where it stopped:
```powershell
python process_universities.py --start <last_row> --max 500
```

## ✨ Ready to Start?

```powershell
# Run this now:
python process_universities.py --test
```

Then review the results in `data/universities_with_contacts.xlsx`!

---

**Questions?** See `PROCESSING_YOUR_UNIVERSITIES.md` for full details.
