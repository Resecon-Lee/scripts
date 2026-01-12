# Scripts Repository

A collection of development utilities, automation tools, and data analysis scripts for Windows environments.

## Table of Contents

- [University IR Contact Finder](#university-ir-contact-finder)
- [AI Usage Analytics](#ai-usage-analytics)
- [OpenWebUI Sync Tools](#openwebui-sync-tools)
- [DIDE - DocuInsight Data Engine](#dide---docuinsight-data-engine)
- [Development Environment Setup](#development-environment-setup)
- [Utility Scripts](#utility-scripts)

---

## University IR Contact Finder

Scripts for scraping university websites to find Office of Institutional Research (OIR) contact information using LLMs and web search.

| Script | Description |
|--------|-------------|
| `university_contact_finder.py` | Main contact finder using LLMs (OpenAI, Anthropic, Perplexity, Ollama) with web search to locate IR office contacts |
| `process_universities.py` | Batch processor for 6,050+ universities from IPEDS data with resume capability |
| `quickstart_university_finder.py` | Interactive setup wizard for API keys and configuration |
| `merge_ir_contacts.py` | Merges existing IR contacts database with universities list |
| `merge_comprehensive_contacts.py` | Merges comprehensive database (4,786 universities) with main list |
| `remove_duplicates.py` | Removes duplicate universities based on IPEDS ID (UnitID) |

**Related Files:**
- `requirements_university_finder.txt` - Python dependencies
- `example_universities.xlsx` - Sample input file
- `berkshire/patrick/` - Copy of scripts for sharing

**Documentation:**
- `UNIVERSITY_FINDER_README.md` - Main documentation
- `UNIVERSITY_FINDER_SUMMARY.md` - Project summary
- `QUICKSTART.md` - Quick start guide
- `PROVIDER_COMPARISON.md` - LLM provider comparison
- `PROCESSING_YOUR_UNIVERSITIES.md` - Processing guide
- `README_YOUR_FILE.md` - File format documentation
- `FINAL_DATABASE_SUMMARY.md` - Database summary

**Azure Deployment:**
- `deploy_to_azure.sh` - Bash deployment script for Azure Linux VM
- `Deploy-ToAzure.ps1` - PowerShell deployment script
- `run_background.sh` - Run contact finder in background on server
- `monitor_progress.sh` - Monitor processing progress
- `check_status.sh` - Check processing status
- `AZURE_DEPLOYMENT_GUIDE.md` - Deployment documentation
- `QUICKSTART_AZURE.md` - Azure quick start guide

---

## AI Usage Analytics

Tools for analyzing usage across multiple OpenWebUI instances and generating comprehensive reports.

| Script | Description |
|--------|-------------|
| `ai_usage_analyzer.py` | Comprehensive analyzer for OpenWebUI instances (FASGpt, RESGpt, BerkshireGPT) with HTML report generation |
| `db_usage_analyzer.py` | Fast offline analyzer using exported SQLite databases (10-100x faster than API) |
| `multi_instance_analysis.py` | Analyze multiple OpenWebUI instances in a single run |
| `enhanced_analysis.py` | Enhanced reporting with additional visualizations |
| `comprehensive_fasgpt_analysis.py` | Deep-dive analysis specifically for FASGPT instance |
| `analyze_fasgpt_topics.py` | Topic analysis and categorization for FASGPT chats |
| `generate_report.py` | Generate formatted reports from analysis data |
| `check_report.py` | Validate generated reports |

**Features:**
- User activity and engagement metrics
- Model usage distribution and trends
- Chat and message content analysis
- Knowledge base utilization
- Azure cost tracking and forecasts
- Beautiful HTML visualizations with Chart.js

**Related Files:**
- `output/ai_usage/` - Generated reports (HTML, PDF, MD)
- `DB_ANALYZER_README.md` - Database analyzer documentation

---

## OpenWebUI Sync Tools

Tools for synchronizing and managing data across OpenWebUI instances.

| Script | Description |
|--------|-------------|
| `sync_cli.py` | Command-line interface for sync operations |
| `openwebui_sync/config.py` | Configuration settings for instances and Azure |
| `openwebui_sync/database.py` | Database operations and schema |
| `openwebui_sync/sync_engine.py` | Core synchronization logic |
| `openwebui_sync/report_generator.py` | Generate sync reports |
| `openwebui_sync/scheduler.py` | Scheduled sync tasks |

**Test Scripts:**
- `test_all_endpoint.py` - Test all API endpoints
- `test_api_keys.py` - Validate API keys
- `test_chat_access.py` - Test chat access permissions
- `test_chat_list.py` - Test chat listing
- `test_me_endpoint.py` - Test user endpoint
- `test_own_chats.py` - Test own chats retrieval
- `check_db.py` - Check database status
- `examine_db.py` - Examine database contents

**Related Files:**
- `README_SYNC.md` - Sync tools documentation
- `requirements.txt` - Python dependencies

---

## DIDE - DocuInsight Data Engine

An Open WebUI plugin for comprehensive file processing and data analysis.

| Script | Description |
|--------|-------------|
| `openwebUI/dide-combined.py` | Complete DIDE suite (~2400 lines) with file handling, data analysis, statistics, and reporting |

**Capabilities:**
- **File Operations:** Upload, extract, process CSV/Excel/key-value files
- **Data Inspection:** Preview data, show columns, get row counts, SQL-like queries
- **Analysis:** Statistics, frequency distributions, filtering, grouping, trend analysis
- **Reporting:** Executive summaries, risk assessments, comprehensive exports

**Supported Formats:**
- CSV (with robust error handling for malformed rows)
- Excel (.xlsx, .xls) with multi-sheet support
- Key-value text files

---

## Development Environment Setup

| Script | Description |
|--------|-------------|
| `setup-dev-env.ps1` | Comprehensive Windows dev environment bootstrap script |

**What It Installs:**
- Package managers: Chocolatey, Scoop
- Runtimes: Node.js, Python
- Databases: MongoDB, PostgreSQL, Redis, MySQL
- Version control: Git, GitHub CLI, GitExtensions, SourceTree
- API tools: Postman, Insomnia
- CLI utilities: fzf, ripgrep, bat, exa, zoxide, delta
- Global npm/Python packages
- WSL2 setup

**Requirements:** Must run as Administrator

---

## Utility Scripts

| Script | Description |
|--------|-------------|
| `convert_to_pdf.py` | Convert markdown files to PDF |
| `simple_md_to_pdf.py` | Simplified markdown to PDF converter |
| `generate_tokens.py` | Generate test token files |

---

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# LLM API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
PERPLEXITY_API_KEY=pplx-your-key-here

# Search APIs
TAVILY_API_KEY=tvly-your-key-here

# Azure Cost Management
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_SUBSCRIPTION_ID=your-azure-subscription-id
```

### Dependencies

```bash
# University Contact Finder
pip install -r requirements_university_finder.txt

# General tools
pip install -r requirements.txt
```

---

## Output Directories

- `output/` - General output files
- `output/ai_usage/` - AI analytics reports
- `data/` - Data files (excluded from git)

---

## License

Private repository - internal use only.
