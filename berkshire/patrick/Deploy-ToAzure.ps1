# Deploy University Contact Finder to Azure Linux Server
# Run from Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerHost,

    [string]$ServerUser = "azureuser",
    [string]$SSHKey = "C:\Users\lfelican\Dev\poc\claude\azure-deep-research\azure-vm-key.pem"
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "University Contact Finder - Azure Deployment" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Deploying to: $ServerUser@$ServerHost" -ForegroundColor Yellow
Write-Host "SSH Key: $SSHKey" -ForegroundColor Yellow
Write-Host ""

$DeployDir = "/home/$ServerUser/university_contact_finder"

# Step 1: Create directories on server
Write-Host "[STEP 1] Creating directories on server..." -ForegroundColor Green
ssh -i $SSHKey "$ServerUser@$ServerHost" "mkdir -p $DeployDir/{data,logs,scripts}"

# Step 2: Copy Python scripts
Write-Host "[STEP 2] Copying Python scripts..." -ForegroundColor Green
scp -i $SSHKey `
    university_contact_finder.py `
    process_universities.py `
    merge_comprehensive_contacts.py `
    remove_duplicates.py `
    "$ServerUser@${ServerHost}:${DeployDir}/scripts/"

# Step 3: Copy requirements
Write-Host "[STEP 3] Copying requirements..." -ForegroundColor Green
scp -i $SSHKey `
    requirements_university_finder.txt `
    "$ServerUser@${ServerHost}:${DeployDir}/"

# Step 4: Copy .env file
Write-Host "[STEP 4] Copying .env file (with API key)..." -ForegroundColor Green
scp -i $SSHKey .env "$ServerUser@${ServerHost}:${DeployDir}/"

# Step 5: Copy data files
Write-Host "[STEP 5] Copying data files..." -ForegroundColor Green
scp -i $SSHKey `
    data/universities_master_with_contacts.xlsx `
    "$ServerUser@${ServerHost}:${DeployDir}/data/"

# Step 6: Copy shell scripts
Write-Host "[STEP 6] Copying deployment scripts..." -ForegroundColor Green
scp -i $SSHKey `
    run_background.sh `
    monitor_progress.sh `
    check_status.sh `
    "$ServerUser@${ServerHost}:${DeployDir}/"

# Step 7: Make scripts executable and install dependencies
Write-Host "[STEP 7] Setting up Python environment on server..." -ForegroundColor Green
ssh -i $SSHKey "$ServerUser@$ServerHost" @"
cd $DeployDir

# Make scripts executable
chmod +x *.sh

# Update system
sudo apt-get update -qq

# Install Python and dependencies
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Install Python packages
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements_university_finder.txt --quiet

echo 'Setup complete!'
"@

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. SSH into server:" -ForegroundColor White
Write-Host "   ssh -i `"$SSHKey`" $ServerUser@$ServerHost" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Navigate to deployment:" -ForegroundColor White
Write-Host "   cd $DeployDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Start processing (background):" -ForegroundColor White
Write-Host "   ./run_background.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Monitor progress:" -ForegroundColor White
Write-Host "   ./monitor_progress.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Check status anytime:" -ForegroundColor White
Write-Host "   ./check_status.sh" -ForegroundColor Cyan
Write-Host ""
Write-Host "6. Disconnect and process continues!" -ForegroundColor White
Write-Host ""
