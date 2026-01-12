# Azure Deployment Guide

Complete guide for deploying and running the University Contact Finder on Azure Linux server.

## 📦 What Gets Deployed

### Files Copied to Server:
- **Python Scripts**:
  - `university_contact_finder.py` - Core contact finding library
  - `process_universities.py` - Main processing script
  - `merge_comprehensive_contacts.py` - Database merging
  - `remove_duplicates.py` - Deduplication tool

- **Data**:
  - `universities_master_with_contacts.xlsx` - Master database (10,651 universities)

- **Configuration**:
  - `requirements_university_finder.txt` - Python dependencies
  - `.env` - API key (Perplexity)

- **Shell Scripts**:
  - `run_background.sh` - Start processing in background
  - `monitor_progress.sh` - Live progress monitoring
  - `check_status.sh` - Quick status check

---

## 🚀 Quick Start

### Step 1: Deploy to Azure

From your Windows machine:

```powershell
# Replace with your Azure server IP/hostname
.\Deploy-ToAzure.ps1 -ServerHost "your-server-ip-or-hostname"
```

This will:
- ✅ Copy all files to server
- ✅ Install Python 3 and dependencies
- ✅ Create virtual environment
- ✅ Set up directory structure
- ✅ Make scripts executable

### Step 2: SSH to Server

```powershell
ssh -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" azureuser@your-server
```

### Step 3: Navigate to Deployment

```bash
cd /home/azureuser/university_contact_finder
```

### Step 4: Start Processing

```bash
./run_background.sh
```

You'll get options:
1. Test (10 universities)
2. Small batch (100)
3. Medium batch (500)
4. Large batch (1000)
5. All remaining (~5,877)
6. Custom number

### Step 5: Disconnect!

**You can now close SSH** - the process continues running in background!

---

## 📊 Monitoring Progress

### Option 1: Live Monitor (from server)

```bash
ssh -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" azureuser@your-server
cd /home/azureuser/university_contact_finder
./monitor_progress.sh
```

Shows:
- Live log updates (refreshes every 2 seconds)
- Progress counter (e.g., [145/500])
- Universities processed
- Errors encountered

Press `Ctrl+C` to stop monitoring (process continues!)

### Option 2: Quick Status Check

```bash
./check_status.sh
```

Shows:
- Running status (PID, CPU, Memory)
- Current progress
- Last 5 log entries
- Commands to monitor/stop

### Option 3: View Logs Directly

```bash
# List all logs
ls -lth logs/

# View latest log
tail -f logs/process_*.log

# Search for errors
grep ERROR logs/process_*.log

# Count completed
grep FOUND logs/process_*.log | wc -l
```

---

## 📁 Server Directory Structure

```
/home/azureuser/university_contact_finder/
├── venv/                          # Python virtual environment
├── data/
│   ├── universities_master_with_contacts.xlsx (input)
│   └── universities_master_with_contacts_with_contacts.xlsx (output)
├── logs/
│   ├── process_test_20250123_140530.log
│   ├── process_small_20250123_150200.log
│   └── process.pid                # Current process PID
├── scripts/
│   ├── university_contact_finder.py
│   ├── process_universities.py
│   └── ... (other Python scripts)
├── run_background.sh              # Start processing
├── monitor_progress.sh            # Monitor progress
├── check_status.sh                # Check status
├── requirements_university_finder.txt
└── .env                           # API key
```

---

## 🎯 Usage Examples

### Example 1: Test with 10 Universities

```bash
./run_background.sh
# Select option 1 (Test)
# Closes SSH - process runs
```

Later:
```bash
./check_status.sh
# Shows: "[STATUS] RUNNING - Progress: [7/10]"
```

### Example 2: Process All Remaining

```bash
./run_background.sh
# Select option 5 (All remaining)
# Estimated: ~5,877 universities, ~5 hours, ~$88

# Disconnect - grab coffee - come back later
```

Check from Windows:
```powershell
ssh -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" azureuser@your-server "./check_status.sh"
```

### Example 3: Process in Batches

Day 1:
```bash
./run_background.sh
# Option 3 (500 universities)
# Wait ~25 minutes or disconnect
```

Day 2:
```bash
./run_background.sh
# Option 3 again (next 500)
# Script automatically continues from where it left off
```

---

## 🛑 Stopping the Process

### Stop Running Process

```bash
# Check PID
./check_status.sh

# Stop it
kill $(cat logs/process.pid)

# Or force stop
kill -9 $(cat logs/process.pid)
```

### Resume Later

The script uses `--skip-existing` so you can always resume:

```bash
# Start again - it continues from where it stopped
./run_background.sh
```

---

## 📥 Download Results

### From Server to Windows

```powershell
# Download output file
scp -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" `
    azureuser@your-server:/home/azureuser/university_contact_finder/data/universities_master_with_contacts_with_contacts.xlsx `
    C:\Users\lfelican\Downloads\

# Download logs
scp -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" `
    azureuser@your-server:/home/azureuser/university_contact_finder/logs/process_*.log `
    C:\Users\lfelican\Downloads\logs\
```

---

## ⚙️ Advanced Options

### Manual Python Execution

```bash
cd /home/azureuser/university_contact_finder
source venv/bin/activate

# Run manually
python scripts/process_universities.py \
    --input data/universities_master_with_contacts.xlsx \
    --skip-existing \
    --max 100 \
    --no-confirm
```

### Check API Credits

```bash
# Monitor API calls in log
grep "FOUND" logs/process_*.log | wc -l
# Each = 1 API call

# Estimate remaining cost
# Remaining universities × $0.015
```

### Resume from Specific Row

```bash
python scripts/process_universities.py \
    --input data/universities_master_with_contacts.xlsx \
    --start 1000 \
    --max 500 \
    --no-confirm
```

---

## 🐛 Troubleshooting

### "Process not running but PID file exists"

```bash
# Clean up
rm logs/process.pid

# Restart
./run_background.sh
```

### "Permission denied" on scripts

```bash
chmod +x *.sh
```

### "Virtual environment not found"

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_university_finder.txt
```

### Check if Python packages installed

```bash
source venv/bin/activate
pip list | grep -E "pandas|openpyxl|openai"
```

### API Key Issues

```bash
# Check .env file exists
cat .env

# Should show:
# PERPLEXITY_API_KEY=pplx-...
```

---

## 💰 Cost Tracking

### Monitor Spending

```bash
# Universities processed so far
grep -c "FOUND" logs/process_*.log

# Estimated cost
echo "scale=2; $(grep -c "FOUND" logs/process_*.log) * 0.015" | bc
```

### Remaining Budget

```bash
# Check output file
python3 << EOF
import pandas as pd
df = pd.read_excel('data/universities_master_with_contacts_with_contacts.xlsx')
completed = df['search_status'].notna().sum()
total = len(df[~df['has_ir_contact']])
remaining = total - completed
cost_remaining = remaining * 0.015
print(f"Completed: {completed}")
print(f"Remaining: {remaining}")
print(f"Estimated cost to complete: \${cost_remaining:.2f}")
EOF
```

---

## 📋 Quick Reference

### SSH to Server
```powershell
ssh -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" azureuser@your-server
```

### Deploy/Update
```powershell
.\Deploy-ToAzure.ps1 -ServerHost "your-server"
```

### Start Processing
```bash
./run_background.sh
```

### Monitor
```bash
./monitor_progress.sh    # Live updates
./check_status.sh        # Quick check
tail -f logs/process_*.log  # Raw log
```

### Download Results
```powershell
scp -i "C:\...\azure-vm-key.pem" azureuser@server:/home/azureuser/university_contact_finder/data/*.xlsx C:\Downloads\
```

---

## ✨ Benefits of Azure Deployment

✅ **No terminal required** - Process runs independently
✅ **Fast server** - Azure VM faster than local machine
✅ **Resume anytime** - Check progress from anywhere
✅ **Reliable** - Won't stop if local PC sleeps/restarts
✅ **Cost effective** - Azure VM + API costs still cheaper than manual
✅ **Scalable** - Can upgrade VM if needed

---

## 🎉 You're Ready!

1. Deploy: `.\Deploy-ToAzure.ps1 -ServerHost "your-server"`
2. SSH: `ssh -i "...azure-vm-key.pem" azureuser@your-server`
3. Start: `./run_background.sh`
4. Disconnect and let it run!
5. Check anytime: `./check_status.sh`

**The process runs independently on Azure!** ☁️
