# Workflow: Using Existing IR Contacts Database

You have two files:
1. **`data/universities.csv.xlsx`** - 6,050 universities (need contacts)
2. **`data/US_Universities_IR_Contacts_Database.xlsx`** - 106 universities with IR contacts

## ✅ Step 1: Merge Files (COMPLETED!)

I ran the merge script for you:

```powershell
python merge_ir_contacts.py
```

### Results:
- **110 universities matched** (1.8%) - now have existing contacts!
  - 94 matched by IPEDS ID (most accurate)
  - 16 matched by name
- **5,940 universities** (98.2%) still need web searches
- **Output file**: `data/universities_with_existing_contacts.xlsx`

### What the merged file has:
- All 6,050 universities from your original list
- Columns added from existing database (for 110 universities):
  - `existing_ir_office_name`
  - `existing_ir_office_email`
  - `existing_ir_office_phone`
  - `existing_ir_director_name`
  - `existing_ir_director_email`
  - `existing_main_phone`
  - `existing_website`
  - `has_existing_contact` (TRUE for 110 universities)
  - `match_method` (IPEDS ID or Name)

---

## Step 2: Search Web for Remaining Universities

Now you'll search for the **5,940 universities** that don't have contacts yet.

### Option A: Search Only Universities Without Contacts

```powershell
# Test with 10 universities (that don't have existing contacts)
python process_universities.py --input data/universities_with_existing_contacts.xlsx --skip-existing --test --no-confirm

# Process first 100 without contacts
python process_universities.py --input data/universities_with_existing_contacts.xlsx --skip-existing --max 100

# Process all 5,940 remaining universities
python process_universities.py --input data/universities_with_existing_contacts.xlsx --skip-existing --all
```

The `--skip-existing` flag tells the script to skip the 110 universities that already have contacts!

### Option B: Process All (Including Re-searching Existing)

If you want to search for ALL universities (including the 110 with existing data) to potentially find more contacts:

```powershell
python process_universities.py --input data/universities_with_existing_contacts.xlsx --max 100
```

---

## Cost Savings

By using existing contacts, you save money!

### Without existing database:
- 6,050 universities × $0.015 = **$90.75**

### With existing database (skip 110):
- 5,940 universities × $0.015 = **$89.10**

**Savings**: ~$1.65 (and time!)

Plus you already have accurate, verified contacts for 110 universities.

---

## Commands Summary

### 1. Merge Files (Already Done!)
```powershell
python merge_ir_contacts.py
```
✅ Output: `data/universities_with_existing_contacts.xlsx`

### 2. Test with 10 Universities (Without Existing Contacts)
```powershell
python process_universities.py \
  --input data/universities_with_existing_contacts.xlsx \
  --skip-existing \
  --test \
  --no-confirm
```

### 3. Process Remaining Universities

```powershell
# Small batch (100)
python process_universities.py \
  --input data/universities_with_existing_contacts.xlsx \
  --skip-existing \
  --max 100

# All remaining (5,940)
python process_universities.py \
  --input data/universities_with_existing_contacts.xlsx \
  --skip-existing \
  --all
```

---

## What You'll Get

The final file will have BOTH:
1. **Existing contacts** (from database) - 110 universities
   - In `existing_ir_*` columns
2. **New contacts** (from web search) - for remaining universities
   - In `contact_1_*`, `contact_2_*`, `contact_3_*` columns

### Example Row (University with Existing Contact):
| Institution Name | has_existing_contact | existing_ir_director_name | existing_ir_director_email | contact_1_name | contact_1_email |
|------------------|----------------------|---------------------------|----------------------------|----------------|-----------------|
| Auburn University | TRUE | Matthew Campbell | campbmw@auburn.edu | (empty) | (empty) |

### Example Row (University from Web Search):
| Institution Name | has_existing_contact | existing_ir_director_name | existing_ir_director_email | contact_1_name | contact_1_email |
|------------------|----------------------|---------------------------|----------------------------|----------------|-----------------|
| Harvard University | FALSE | (empty) | (empty) | Dr. Jane Smith | jane@harvard.edu |

---

## Verification: Check the Merged File

```powershell
python -c "
import pandas as pd
df = pd.read_excel('data/universities_with_existing_contacts.xlsx')

print(f'Total universities: {len(df):,}')
print(f'With existing contacts: {df[\"has_existing_contact\"].sum()}')
print(f'Without contacts (need web search): {(~df[\"has_existing_contact\"]).sum()}')
print()
print('Sample universities with existing contacts:')
print(df[df['has_existing_contact']][['Institution Name', 'existing_ir_director_name', 'existing_ir_director_email']].head(5))
"
```

---

## Next Steps

### Ready to search? Run:

```powershell
# Test first (always!)
python process_universities.py \
  --input data/universities_with_existing_contacts.xlsx \
  --skip-existing \
  --test \
  --no-confirm
```

### Need API Key?
1. Get Perplexity API key: https://www.perplexity.ai/settings/api
2. Create `.env` file:
   ```
   PERPLEXITY_API_KEY=pplx-your-key-here
   ```

---

## Summary

✅ **Merged files** - 110 universities have existing contacts
✅ **Ready to search** - 5,940 universities need web searches
✅ **Scripts updated** - `--skip-existing` flag added
✅ **Cost optimized** - Only search what you need

**Total universities with contacts after completion**: 110 (existing) + ~1,200-2,400 (from web) = ~1,400-2,500 universities
