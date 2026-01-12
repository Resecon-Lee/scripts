# Azure Deployment - Quick Start

## 🚀 Deploy in 3 Commands

### 1. Deploy from Windows
```powershell
cd C:\Users\lfelican\Dev\scripts
.\Deploy-ToAzure.ps1 -ServerHost "YOUR-AZURE-SERVER-IP"
```

### 2. SSH to Server
```powershell
ssh -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" azureuser@YOUR-SERVER
```

### 3. Start Processing
```bash
cd /home/azureuser/university_contact_finder
./run_background.sh
```

Select option 1-5, then **disconnect** - it keeps running!

---

## ✅ What This Does

- ✅ Processes **5,877 remaining universities**
- ✅ Runs in **background** (survives SSH disconnect)
- ✅ Saves **progress after each university**
- ✅ Creates **detailed logs**
- ✅ Can **monitor anytime** without stopping
- ✅ **Cost**: ~$88 for all remaining

---

## 📊 Monitor Progress

### Quick Check (from anywhere)
```bash
ssh -i "...\azure-vm-key.pem" azureuser@server "cd /home/azureuser/university_contact_finder && ./check_status.sh"
```

### Live Monitor
```bash
ssh -i "...\azure-vm-key.pem" azureuser@server
cd /home/azureuser/university_contact_finder
./monitor_progress.sh
```

---

## 📥 Download Results

```powershell
scp -i "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem" `
    azureuser@YOUR-SERVER:/home/azureuser/university_contact_finder/data/universities_master_with_contacts_with_contacts.xlsx `
    C:\Downloads\
```

---

## 🎯 Processing Options

When you run `./run_background.sh`, you get:

1. **Test** (10 universities) - ~$0.15, 30 seconds
2. **Small** (100 universities) - ~$1.50, 5 minutes
3. **Medium** (500 universities) - ~$7.50, 25 minutes
4. **Large** (1,000 universities) - ~$15, 50 minutes
5. **All** (5,877 universities) - ~$88, 5 hours

---

## 💡 Pro Tips

✅ **Start with option 1** (Test) to verify everything works
✅ **Then run option 5** (All) and disconnect
✅ **Check progress** periodically with `./check_status.sh`
✅ **Download results** when complete
✅ **Process continues** even if you close terminal!

---

**Ready?** Run this now:
```powershell
.\Deploy-ToAzure.ps1 -ServerHost "YOUR-AZURE-SERVER-IP"
```
