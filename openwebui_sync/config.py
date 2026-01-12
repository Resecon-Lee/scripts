"""
Configuration module for OpenWebUI Sync

Contains all configuration settings including:
- Database path
- OpenWebUI instance configurations
- Azure credentials
- Sync settings
"""

import os
from pathlib import Path

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Database file path
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "openwebui_sync.db"

# Ensure data directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
# OPENWEBUI INSTANCES
# ============================================================================

INSTANCES = {
    "resgpt": {
        "url": "http://resgpt.resecon.ai",
        "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjA2MDMyOTk4LWY5YjktNDY0ZS1iMmI2LTc1Zjg2MTRlMjBmMCJ9.sVAkpP6TZsg0VdXZ7GAKLxNTgPNAYvPBXDlr3tkH0wE",
        "is_active": True
    },
    "fasgpt": {
        "url": "http://fasgpt.resecon.ai",
        "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImY3Njg4YzQ1LWIxNDctNDlmNy1hMDZjLTVhYzhiZjUyYjFiOSJ9.8YQcL-BIBA7w2Y0v3lxOcNwh2MMWaS5adOs22ruK9H4",
        "is_active": True
    },
    "berkshiregpt": {
        "url": "http://berkshiregpt.resecon.ai",
        "api_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8",
        "is_active": True
    }
}

# ============================================================================
# AZURE COST MANAGEMENT
# ============================================================================
# Set these in your .env file or environment variables
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")

# ============================================================================
# SYNC SETTINGS
# ============================================================================

# API request timeout in seconds
API_TIMEOUT = 30

# Delay between API requests to avoid rate limiting (seconds)
API_DELAY = 0.05

# Maximum retries for failed API requests
MAX_RETRIES = 3

# Batch size for database inserts
DB_BATCH_SIZE = 100

# ============================================================================
# REPORT SETTINGS
# ============================================================================

# Output directory for generated reports
REPORTS_DIR = BASE_DIR / "output" / "ai_usage"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Number of top users to display in reports
TOP_USERS_LIMIT = 10

# Number of days of trend data to include
TREND_DAYS = 30

# ============================================================================
# LOGGING
# ============================================================================

# Log file path
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS_DIR / "openwebui_sync.log"

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"
