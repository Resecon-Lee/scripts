# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal scripts repository containing development utilities and tools for Windows environments. The repository is not a git repository and contains standalone scripts and tools.

## Repository Structure

```
scripts/
├── openwebUI/              # Open WebUI tools and extensions
│   └── dide-combined.py   # DocuInsight Data Engine (DIDE) complete suite
└── setup-dev-env.ps1      # Windows development environment setup script
```

## Key Components

### 1. DIDE (DocuInsight Data Engine) - openwebUI/dide-combined.py

A comprehensive data analysis tool designed as an Open WebUI plugin for file processing and analysis.

**Purpose**: Unified tool for file handling, data analysis, advanced statistics, and intelligence reporting.

**Architecture**:
- **Global State Management**: Uses global dictionaries (`_GLOBAL_DATAFRAMES`, `_GLOBAL_METADATA`, `_GLOBAL_LOGS`, `_GLOBAL_RAW_FILES`, `_GLOBAL_ANALYSIS_HISTORY`) to persist data across function calls in the Open WebUI environment
- **Two-Phase Processing**: Separates file extraction (`extract_and_store_file`) from processing (`process_stored_file`) to enable reprocessing without re-uploading
- **Format Detection**: Auto-detects CSV, Excel (.xlsx, .xls), and key-value formats
- **Robust Error Handling**: Includes malformed row tracking, auto-fixing, and detailed parsing logs

**Core Capabilities** (organized by category):

*File Operations*:
- `extract_and_store_file()` - Extract and store raw file content
- `process_stored_file()` - Process stored file with format detection
- `list_stored_files()` - View all stored files
- `analyze_uploaded_file()` - One-step upload and process
- `load_from_text()` - Create dataframes from text/clipboard data
- `export_corrected_csv()` - Export cleaned data
- `show_parsing_log()` - View parsing issues and warnings

*Data Inspection*:
- `verify_data_loaded()` - Check loaded data and preview
- `show_columns()` - Display column names and types
- `get_row_count()` - Get record counts
- `query_data()` - SQL-like data queries

*Analysis & Statistics*:
- `get_statistics()` - Basic statistical measures
- `count_by_column()` - Frequency distributions
- `filter_data()` - Filter and subset data
- `group_and_aggregate()` - Group by and aggregation operations
- `statistical_trend_analysis()` - Time series and trend analysis
- `comparative_analysis()` - Compare multiple datasets
- `identify_data_gaps()` - Find missing or incomplete data

*Intelligence & Reporting*:
- `extract_key_information()` - Extract insights and patterns
- `generate_executive_summary()` - Create executive summaries
- `risk_compliance_assessment()` - Risk and compliance analysis
- `export_summary()` - Generate comprehensive reports
- `get_analysis_history()` - View analysis audit trail

**File Format Support**:
- CSV files with robust error handling (handles malformed rows, varying column counts)
- Excel files (.xlsx, .xls) with multi-sheet support
- Key-value text files (converts to structured format)

**Configuration** (via Valves class):
- `MAX_FILE_SIZE_MB` - Maximum file size (default: 50 MB)
- `MAX_ROWS_DISPLAY` - Display limit (default: 100 rows)
- `AUTO_FIX_ERRORS` - Auto-fix malformed files (default: true)
- `SKIP_BAD_ROWS` - Skip malformed rows (default: true)
- `MAX_ERROR_ROWS` - Error reporting limit (default: 1000)

**Dependencies**: pandas, openpyxl, xlrd

**Usage Pattern**:
```python
# Method 1: Two-phase (recommended for reprocessing)
await extract_and_store_file(__files__=files, file_id="mydata")
await process_stored_file(file_id="mydata")

# Method 2: Direct processing
await analyze_uploaded_file(__files__=files, file_id="mydata")

# Analysis workflow
await verify_data_loaded(file_id="mydata")  # Preview data
await get_statistics(columns=["Age", "Salary"], file_id="mydata")
await generate_executive_summary(focus_areas=["demographics"], file_id="mydata")
```

### 2. Development Environment Setup - setup-dev-env.ps1

**Purpose**: Comprehensive PowerShell script for bootstrapping a Windows development environment.

**Requirements**: Must run as Administrator

**What It Installs**:
- Package managers: Chocolatey, Scoop
- Runtimes: Node.js, Python
- Databases: MongoDB, PostgreSQL, Redis, MySQL
- Version control: Git, GitHub CLI, GitExtensions, SourceTree
- API tools: Postman, Insomnia
- CLI utilities: fzf, ripgrep, bat, exa, zoxide, delta, etc.
- Global npm packages: React/Vue/Angular CLIs, Vite, TypeScript, testing frameworks
- Global Python packages: Flask, Django, FastAPI, pytest, Jupyter
- WSL2 setup and configuration

**Post-Installation**:
- Creates `$PROFILE` with PowerShell configuration
- Sets up development directory structure in `$env:USERPROFILE\Dev`
- Configures Git with user input
- Adds helpful aliases and functions

**Key Features**:
- Idempotent (checks before installing)
- Interactive prompts for Git config and WSL
- Automatic PowerShell profile creation with aliases
- Terminal enhancement with Oh My Posh/Starship

## Development Workflow

Since this is a scripts repository without version control:

1. **For DIDE development**: Edit `openwebUI/dide-combined.py` directly. Test within Open WebUI environment.
2. **For setup script**: Test in isolated VM or use `-WhatIf` where supported.
3. **Dependencies**: Install Python dependencies manually: `pip install pandas openpyxl xlrd`

## Common Tasks

### Working with DIDE

**Testing DIDE locally** (outside Open WebUI):
```powershell
cd openwebUI
python -m pytest  # If tests exist
python -c "from dide_combined import Tools; t = Tools(); print('Import successful')"
```

**Installing DIDE in Open WebUI**:
- Copy `dide-combined.py` to Open WebUI's tools directory
- DIDE appears as available tool functions in Open WebUI interface

### Running the Setup Script

```powershell
# Review what would be installed
Get-Content setup-dev-env.ps1 | Select-String "choco install|scoop install|npm install -g|pip install"

# Run the full setup (as Administrator)
.\setup-dev-env.ps1
```

## Important Notes

- **DIDE Global State**: The tool uses module-level globals to persist state across function calls in Open WebUI's execution environment. This is intentional for the plugin architecture.
- **No Git**: This repository is not version controlled. Changes are direct edits to scripts.
- **Windows-Specific**: Both scripts are designed for Windows (PowerShell, Windows package managers).
- **File Size**: DIDE file is large (~2400 lines) due to comprehensive functionality. Functions are async for Open WebUI compatibility.
