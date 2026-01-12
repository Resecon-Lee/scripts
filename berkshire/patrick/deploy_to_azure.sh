#!/bin/bash
#
# Deploy University Contact Finder to Azure Linux Server
# This script sets up everything needed to run the contact finder on the server
#

set -e  # Exit on error

echo "============================================================"
echo "University Contact Finder - Azure Deployment"
echo "============================================================"

# Configuration
SERVER_USER="azureuser"
SERVER_HOST="your-server-ip-or-hostname"
DEPLOY_DIR="/home/azureuser/university_contact_finder"
SSH_KEY="C:/Users/lfelican/Dev/poc/claude/azure-deep-research/azure-vm-key.pem"

echo ""
echo "[INFO] Deploying to: ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}"
echo ""

# Create deployment directory on server
echo "[STEP 1] Creating directory on server..."
ssh -i "$SSH_KEY" ${SERVER_USER}@${SERVER_HOST} "mkdir -p ${DEPLOY_DIR}/{data,logs,scripts}"

# Copy Python scripts
echo "[STEP 2] Copying Python scripts..."
scp -i "$SSH_KEY" \
    university_contact_finder.py \
    process_universities.py \
    merge_comprehensive_contacts.py \
    remove_duplicates.py \
    ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/scripts/

# Copy requirements
echo "[STEP 3] Copying requirements..."
scp -i "$SSH_KEY" \
    requirements_university_finder.txt \
    ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/

# Copy .env file (with API key)
echo "[STEP 4] Copying .env file..."
scp -i "$SSH_KEY" \
    .env \
    ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/

# Copy data files
echo "[STEP 5] Copying data files..."
scp -i "$SSH_KEY" \
    data/universities_master_with_contacts.xlsx \
    ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/data/

# Copy deployment scripts
echo "[STEP 6] Copying deployment scripts..."
scp -i "$SSH_KEY" \
    run_background.sh \
    monitor_progress.sh \
    check_status.sh \
    ${SERVER_USER}@${SERVER_HOST}:${DEPLOY_DIR}/

# Make scripts executable
echo "[STEP 7] Making scripts executable..."
ssh -i "$SSH_KEY" ${SERVER_USER}@${SERVER_HOST} "chmod +x ${DEPLOY_DIR}/*.sh"

# Install dependencies on server
echo "[STEP 8] Installing Python dependencies on server..."
ssh -i "$SSH_KEY" ${SERVER_USER}@${SERVER_HOST} << 'ENDSSH'
cd /home/azureuser/university_contact_finder

# Update system
sudo apt-get update

# Install Python and pip if not present
sudo apt-get install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv

# Activate and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_university_finder.txt

echo "Dependencies installed successfully!"
ENDSSH

echo ""
echo "============================================================"
echo "Deployment Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. SSH into server: ssh -i \"$SSH_KEY\" ${SERVER_USER}@${SERVER_HOST}"
echo "2. Navigate to: cd ${DEPLOY_DIR}"
echo "3. Start processing: ./run_background.sh"
echo "4. Monitor progress: ./monitor_progress.sh"
echo ""
