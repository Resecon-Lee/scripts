# Database-Based AI Usage Analyzer

## Overview

`db_usage_analyzer.py` is a **faster, offline alternative** to `ai_usage_analyzer.py` that works directly with exported SQLite databases instead of making API calls to OpenWebUI instances.

## Performance Comparison

| Metric | API-Based (`ai_usage_analyzer.py`) | DB-Based (`db_usage_analyzer.py`) |
|--------|-------------------------------------|-----------------------------------|
| **Speed** | ~2-5 minutes (560 chats) | **~3-5 seconds** (560 chats) |
| **Network Required** | ✅ Yes (multiple HTTP requests) | ❌ No (local queries only)* |
| **Rate Limits** | ✅ Subject to API limits | ❌ No limits |
| **Data Freshness** | ✅ Real-time | ⚠️ Snapshot at export time |
| **Azure Costs** | ✅ Fetches live data | ✅ Fetches live data* |
| **Offline Mode** | ❌ Not possible | ✅ Fully offline with `--skip-azure` |

\* Azure cost data still requires API access unless `--skip-azure` is used

## Usage

### Basic Usage (with Azure costs)
```bash
python db_usage_analyzer.py ./data/berkshiregpt.db
```

### Offline Mode (skip Azure costs)
```bash
python db_usage_analyzer.py ./data/berkshiregpt.db --skip-azure
```

### Multiple Databases
```bash
# Analyze different instances
python db_usage_analyzer.py ./data/resgpt.db
python db_usage_analyzer.py ./data/fasgpt.db
python db_usage_analyzer.py ./data/berkshiregpt.db
```

## Exporting Databases from OpenWebUI

To export a database from your OpenWebUI instance:

### Method 1: Direct Database Copy (if you have server access)
```bash
# SSH into your OpenWebUI server
ssh user@berkshiregpt.resecon.ai

# Copy the database (default location)
cp /app/backend/data/webui.db /tmp/berkshiregpt.db

# Download to your local machine
scp user@berkshiregpt.resecon.ai:/tmp/berkshiregpt.db ./data/
```

### Method 2: Docker Export
```bash
# If running in Docker
docker cp openwebui-container:/app/backend/data/webui.db ./data/berkshiregpt.db
```

### Method 3: Database Backup via OpenWebUI Admin
1. Log into OpenWebUI as admin
2. Navigate to Admin Panel → Settings → Database
3. Click "Export Database" or "Backup Database"
4. Download the exported `.db` file

## What Data is Extracted

The database analyzer extracts the following data:

### ✅ Available from Database:
- **Users**: Full profiles, roles, activity timestamps
- **Chats**: Complete chat history with metadata
- **Messages**: All user and assistant messages (stored in chat JSON)
- **Models**: Available models and usage statistics
- **Knowledge Bases**: Document collections and metadata
- **Files**: Uploaded file references
- **Tags**: Chat categorization
- **Usage Trends**: Daily, weekly, monthly activity patterns
- **Message Statistics**: Counts, lengths, ratios

### ⚠️ Requires API Call:
- **Azure Costs**: Must fetch from Azure Cost Management API (unless `--skip-azure` is used)

### ❌ Not Available:
- **Real-time Data**: Database is a snapshot from export time
- **Live User Sessions**: Active connections not stored in DB

## Generated Reports

The script generates the same HTML reports as the API-based version:

- **Location**: `output/ai_usage/{instance_name}_Report.html`
- **Contains**:
  - User activity and engagement metrics
  - Model usage distribution (charts)
  - Chat and message analysis
  - Knowledge base utilization
  - Azure cost breakdown (if not skipped)
  - Usage trends over time (line charts)
  - Top users by activity

## Database Schema Reference

Key tables used by the analyzer:

### `user` table
- `id`, `name`, `email`, `role`
- `created_at`, `last_active_at`
- `settings`, `info`

### `chat` table
- `id`, `user_id`, `title`
- `created_at`, `updated_at`
- `chat` (JSON field containing):
  - `models[]` - Models used in chat
  - `messages[]` - Full message history
  - `files[]` - Attached files
  - `tags[]` - Chat tags

### `model` table
- `id`, `name`, `base_model_id`
- `is_active`, `params`, `meta`

### `knowledge` table
- `id`, `name`, `description`

## Troubleshooting

### Database File Not Found
```bash
# Make sure path is correct and file exists
ls -la ./data/berkshiregpt.db

# Use absolute path if relative doesn't work
python db_usage_analyzer.py "C:\Users\lfelican\Dev\Scripts\data\berkshiregpt.db"
```

### Azure Cost Fetching Fails
```bash
# Run in offline mode instead
python db_usage_analyzer.py ./data/berkshiregpt.db --skip-azure
```

### Database Locked Error
```bash
# Stop OpenWebUI if it's running and using the database
# Or make a copy of the database first
cp ./data/berkshiregpt.db ./data/berkshiregpt-copy.db
python db_usage_analyzer.py ./data/berkshiregpt-copy.db
```

## When to Use Each Analyzer

### Use `db_usage_analyzer.py` (Database-Based) when:
- ✅ You want **fast analysis** (10-100x faster)
- ✅ You have **exported database files**
- ✅ You need **offline analysis**
- ✅ You're doing **historical analysis** on snapshots
- ✅ You want to **avoid API rate limits**
- ✅ You're **analyzing multiple instances** in bulk

### Use `ai_usage_analyzer.py` (API-Based) when:
- ✅ You need **real-time data**
- ✅ You don't have **database access**
- ✅ You want to **avoid exporting databases**
- ✅ You need the **absolute latest** information
- ✅ Database export process is **not feasible**

## Recommended Workflow

1. **Weekly Snapshots**: Export databases weekly for historical analysis
   ```bash
   # Automated export script
   ./export_databases.sh
   ```

2. **Fast Analysis**: Use database analyzer for routine reports
   ```bash
   python db_usage_analyzer.py ./data/berkshiregpt.db
   ```

3. **Real-time Checks**: Use API analyzer when you need current data
   ```bash
   python ai_usage_analyzer.py berkshiregpt
   ```

## Example: Analyzing All Three Instances

```bash
# Export all databases (on server)
scp user@resgpt.resecon.ai:/app/backend/data/webui.db ./data/resgpt.db
scp user@fasgpt.resecon.ai:/app/backend/data/webui.db ./data/fasgpt.db
scp user@berkshiregpt.resecon.ai:/app/backend/data/webui.db ./data/berkshiregpt.db

# Analyze all (takes ~10 seconds total instead of ~10 minutes)
python db_usage_analyzer.py ./data/resgpt.db --skip-azure
python db_usage_analyzer.py ./data/fasgpt.db --skip-azure
python db_usage_analyzer.py ./data/berkshiregpt.db --skip-azure

# Fetch Azure costs once (shared across all instances)
python db_usage_analyzer.py ./data/berkshiregpt.db
```

## Output

After running the analyzer, you'll find:
- HTML report at `output/ai_usage/{instance_name}_Report.html`
- Console output showing analysis progress
- Same visualizations and metrics as API-based version

## Performance Tips

1. **Skip Azure Costs for Speed**: Use `--skip-azure` when you don't need cost data
2. **Analyze Multiple DBs in Parallel**: Run multiple analyzers simultaneously
3. **Use Local SSD**: Store database files on fast storage
4. **Regular Exports**: Schedule weekly exports for consistent snapshots

## Migration from API-Based Analyzer

The database analyzer produces **identical output** to the API-based version, so you can:
- Use the same HTML report viewing process
- Compare reports between versions
- Gradually migrate from API to database approach
- Use both analyzers interchangeably

No changes needed to your reporting workflow!
