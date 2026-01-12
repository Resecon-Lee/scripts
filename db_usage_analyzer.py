"""
DB-Based AI Usage Analyzer - Fast Offline OpenWebUI Analytics

This script analyzes usage from exported SQLite databases instead of API calls.
Benefits:
- 10-100x faster than API approach
- No network required (except for Azure costs)
- No rate limits
- Works offline

Usage:
    python db_usage_analyzer.py <db_path> [--skip-azure]

    db_path: Path to exported SQLite database (e.g., ./data/berkshiregpt.db)
    --skip-azure: Skip Azure cost fetching (for offline mode)

Example:
    python db_usage_analyzer.py ./data/berkshiregpt.db
    python db_usage_analyzer.py ./data/berkshiregpt.db --skip-azure

Author: AI Usage Analytics Team
Date: November 2025
"""

import sqlite3
import json
import sys
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time
import requests

# ============================================================================
# AZURE CONFIGURATION
# ============================================================================
# Set these in your .env file or environment variables
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")

# Output directory for generated reports
OUTPUT_DIR = "output/ai_usage"

# Azure token cache
_azure_token_cache = {
    'token': None,
    'expires_at': None
}

def ensure_output_dir():
    """Ensure output directory exists for saving reports."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_azure_access_token():
    """Get Azure access token using OAuth2 with caching"""
    global _azure_token_cache

    # Check if token is cached and still valid
    if _azure_token_cache['token'] and _azure_token_cache['expires_at']:
        # Refresh if token expires in less than 5 minutes
        if datetime.now() < _azure_token_cache['expires_at'] - timedelta(minutes=5):
            return _azure_token_cache['token']

    # Get new token
    token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"

    data = {
        'client_id': AZURE_CLIENT_ID,
        'client_secret': AZURE_CLIENT_SECRET,
        'scope': 'https://management.azure.com/.default',
        'grant_type': 'client_credentials'
    }

    try:
        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)

        # Cache token
        _azure_token_cache['token'] = access_token
        _azure_token_cache['expires_at'] = datetime.now() + timedelta(seconds=expires_in)

        return access_token

    except Exception as e:
        print(f"    Error getting Azure access token: {e}")
        return None

def get_azure_costs():
    """Fetch actual costs from Azure Cost Management API using REST"""
    print("\nFetching Azure cost data...")

    try:
        # Get access token
        access_token = get_azure_access_token()
        if not access_token:
            raise Exception("Failed to obtain Azure access token")

        # Get current month dates
        today = datetime.now()
        start_date = today.replace(day=1).strftime('%Y-%m-%dT00:00:00Z')
        end_date = today.strftime('%Y-%m-%dT23:59:59Z')

        # Cost Management API endpoint
        api_url = f"https://management.azure.com/subscriptions/{AZURE_SUBSCRIPTION_ID}/providers/Microsoft.CostManagement/query?api-version=2023-11-01"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Query for actual costs
        query_body = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_date,
                "to": end_date
            },
            "dataset": {
                "granularity": "Daily",
                "aggregation": {
                    "totalCost": {
                        "name": "PreTaxCost",
                        "function": "Sum"
                    }
                },
                "grouping": [
                    {
                        "type": "Dimension",
                        "name": "ServiceName"
                    },
                    {
                        "type": "Dimension",
                        "name": "ResourceId"
                    },
                    {
                        "type": "Dimension",
                        "name": "ResourceLocation"
                    }
                ]
            }
        }

        # Execute query with retry logic
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = requests.post(api_url, headers=headers, json=query_body, timeout=60)

                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"    Rate limited, waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    retry_count += 1
                    continue

                response.raise_for_status()
                break

            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                wait_time = 2 ** retry_count
                print(f"    Retry {retry_count}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)

        result = response.json()

        # Process results
        cost_data = {
            'total_cost': 0,
            'by_resource_group': defaultdict(float),
            'by_service': defaultdict(float),
            'by_location': defaultdict(float),
            'by_resource': defaultdict(float),
            'daily_costs': {},
            'currency': 'USD'
        }

        # Parse response
        if 'properties' in result:
            props = result['properties']

            # Get columns and rows
            columns = props.get('columns', [])
            rows = props.get('rows', [])

            # Find column indices
            col_indices = {}
            for i, col in enumerate(columns):
                col_name = col.get('name', '')
                col_indices[col_name] = i

            # Process each row
            for row in rows:
                cost = float(row[col_indices.get('PreTaxCost', 0)]) if 'PreTaxCost' in col_indices else 0
                date_val = row[col_indices.get('UsageDate', 1)] if 'UsageDate' in col_indices else None
                service = row[col_indices.get('ServiceName', 2)] if 'ServiceName' in col_indices else 'Unknown'
                resource_id = row[col_indices.get('ResourceId', 3)] if 'ResourceId' in col_indices else 'Unknown'
                location = row[col_indices.get('ResourceLocation', 4)] if 'ResourceLocation' in col_indices else 'Unknown'

                cost_data['total_cost'] += cost
                cost_data['by_service'][service] += cost
                cost_data['by_location'][location] += cost
                cost_data['by_resource'][resource_id] += cost

                # Extract resource group from resource ID
                if resource_id and '/resourceGroups/' in resource_id:
                    try:
                        rg = resource_id.split('/resourceGroups/')[1].split('/')[0]
                        cost_data['by_resource_group'][rg] += cost
                    except:
                        pass

                # Track daily costs
                if date_val:
                    date_str = str(date_val)[:10]  # YYYY-MM-DD
                    cost_data['daily_costs'][date_str] = cost_data['daily_costs'].get(date_str, 0) + cost

        # Calculate forecast based on average daily spend
        if cost_data['daily_costs']:
            days_elapsed = len(cost_data['daily_costs'])
            avg_daily_cost = cost_data['total_cost'] / max(days_elapsed, 1)
            days_remaining_in_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - today
            days_remaining = days_remaining_in_month.days

            # Forecast = current spend + (avg daily * remaining days)
            cost_data['forecast_mtd'] = cost_data['total_cost'] + (avg_daily_cost * days_remaining)

            # 30-day forecast
            cost_data['forecast_30d'] = avg_daily_cost * 30
        else:
            cost_data['forecast_mtd'] = cost_data['total_cost']
            cost_data['forecast_30d'] = 0

        print(f"  [SUCCESS] Total Azure cost (MTD): ${cost_data['total_cost']:.2f}")
        print(f"  [SUCCESS] Forecast (30-day): ${cost_data['forecast_30d']:.2f}")
        print(f"  [SUCCESS] Services tracked: {len(cost_data['by_service'])}")
        print(f"  [SUCCESS] Locations tracked: {len(cost_data['by_location'])}")

        return cost_data

    except Exception as e:
        print(f"  [ERROR] Error fetching Azure costs: {e}")
        return {
            'total_cost': 0,
            'by_resource_group': {},
            'by_service': {},
            'by_location': {},
            'by_resource': {},
            'daily_costs': {},
            'forecast_30d': 0,
            'forecast_mtd': 0,
            'currency': 'USD',
            'error': str(e)
        }

def analyze_message_content_from_json(chat_json):
    """
    Extract and analyze message content from chat JSON.

    Args:
        chat_json (dict): Parsed chat JSON object

    Returns:
        dict: Message statistics
    """
    messages = chat_json.get('messages', [])

    if not messages:
        return {
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0,
            'avg_user_length': 0,
            'avg_assistant_length': 0,
            'user_assistant_ratio': 0,
            'sample_messages': [],
            'total_chars': 0
        }

    user_messages = [m for m in messages if m.get('role') == 'user']
    assistant_messages = [m for m in messages if m.get('role') == 'assistant']

    # Calculate average message lengths
    user_lengths = [len(m.get('content', '')) for m in user_messages]
    assistant_lengths = [len(m.get('content', '')) for m in assistant_messages]

    avg_user_length = sum(user_lengths) / len(user_lengths) if user_lengths else 0
    avg_assistant_length = sum(assistant_lengths) / len(assistant_lengths) if assistant_lengths else 0

    # Calculate user to assistant ratio
    user_assistant_ratio = len(user_messages) / len(assistant_messages) if assistant_messages else 0

    # Get sample messages (last 3)
    sample_messages = []
    for msg in messages[-3:]:
        sample_messages.append({
            'role': msg.get('role', 'unknown'),
            'content': msg.get('content', '')[:200] + ('...' if len(msg.get('content', '')) > 200 else ''),
            'has_files': len(msg.get('files', [])) > 0
        })

    # Total character count
    total_chars = sum([len(m.get('content', '')) for m in messages])

    return {
        'total_messages': len(messages),
        'user_messages': len(user_messages),
        'assistant_messages': len(assistant_messages),
        'avg_user_length': round(avg_user_length, 1),
        'avg_assistant_length': round(avg_assistant_length, 1),
        'user_assistant_ratio': round(user_assistant_ratio, 2),
        'sample_messages': sample_messages,
        'total_chars': total_chars
    }

def analyze_usage_trends(chats_data):
    """Analyze usage trends over time from chat data"""
    daily_counts = defaultdict(int)
    weekly_counts = defaultdict(int)
    monthly_counts = defaultdict(int)

    for chat in chats_data:
        ts = chat.get('created_at')
        if not ts:
            continue

        dt = datetime.fromtimestamp(ts)

        # Daily
        day_key = dt.strftime('%Y-%m-%d')
        daily_counts[day_key] += 1

        # Weekly
        week_key = dt.strftime('%Y-W%U')
        weekly_counts[week_key] += 1

        # Monthly
        month_key = dt.strftime('%Y-%m')
        monthly_counts[month_key] += 1

    return {
        'daily': dict(sorted(daily_counts.items())),
        'weekly': dict(sorted(weekly_counts.items())),
        'monthly': dict(sorted(monthly_counts.items()))
    }

def analyze_database(db_path, skip_azure=False):
    """
    Analyze OpenWebUI database and generate report.

    Args:
        db_path (str): Path to SQLite database file
        skip_azure (bool): Skip Azure cost fetching
    """
    print("="*70)
    print(f"DATABASE ANALYSIS: {os.path.basename(db_path)}")
    print("="*70)

    # Connect to database
    print(f"\nConnecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Extract instance name from filename
    instance_name = os.path.basename(db_path).replace('.db', '').replace('gpt', 'GPT')

    # Fetch users
    print(f"\nFetching users...")
    users_query = cursor.execute('''
        SELECT id, name, email, role, created_at, last_active_at, settings, info
        FROM user
        ORDER BY name
    ''').fetchall()

    users = []
    for user in users_query:
        users.append({
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3],
            'created_at': user[4],
            'last_active_at': user[5],
            'settings': user[6],
            'info': user[7]
        })
    print(f"  Found {len(users)} users")

    # Fetch models
    print(f"Fetching models...")
    models_query = cursor.execute('''
        SELECT id, name, base_model_id, params, meta, is_active
        FROM model
        WHERE is_active = 1
        ORDER BY name
    ''').fetchall()

    models = []
    for model in models_query:
        models.append({
            'id': model[0],
            'name': model[1],
            'base_model_id': model[2]
        })
    print(f"  Found {len(models)} active models")

    # Fetch knowledge bases
    print(f"Fetching knowledge bases...")
    kb_query = cursor.execute('''
        SELECT id, name, description
        FROM knowledge
        ORDER BY name
    ''').fetchall()

    knowledge_bases = []
    for kb in kb_query:
        knowledge_bases.append({
            'id': kb[0],
            'name': kb[1],
            'description': kb[2] if kb[2] else ''
        })
    print(f"  Found {len(knowledge_bases)} knowledge bases")

    # Fetch and analyze chats
    print(f"Fetching and analyzing chats...")
    chats_query = cursor.execute('''
        SELECT id, user_id, title, created_at, updated_at, chat, archived
        FROM chat
        ORDER BY created_at DESC
    ''').fetchall()

    all_user_data = []
    all_chats = []
    global_model_usage = Counter()

    # Group chats by user
    user_chats = defaultdict(list)
    for chat_row in chats_query:
        user_id = chat_row[1]
        user_chats[user_id].append(chat_row)

    print(f"  Analyzing {len(chats_query)} chats across {len(users)} users...")

    for i, user in enumerate(users, 1):
        user_id = user['id']
        user_name = user['name']

        print(f"  [{i:2}/{len(users)}] {user_name}...", end="", flush=True)

        chats = user_chats.get(user_id, [])
        chat_count = len(chats)

        print(f" {chat_count} chats")

        # Model usage and message tracking for this user
        user_model_usage = Counter()
        user_message_stats = {
            'total_messages': 0,
            'user_messages': 0,
            'assistant_messages': 0,
            'total_chars': 0,
            'avg_messages_per_chat': 0,
            'avg_user_length': 0,
            'avg_assistant_length': 0
        }

        for chat_row in chats:
            chat_id = chat_row[0]
            title = chat_row[2]
            created_at = chat_row[3]
            updated_at = chat_row[4]
            chat_json_str = chat_row[5]
            archived = chat_row[6]

            # Parse chat JSON
            chat_json = {}
            models_list = []
            if chat_json_str:
                try:
                    chat_json = json.loads(chat_json_str)
                    models_list = chat_json.get('models', [])
                except:
                    pass

            # Track model usage
            if models_list:
                for model in models_list:
                    user_model_usage[model] += 1
                    global_model_usage[model] += 1
            else:
                user_model_usage['unknown'] += 1
                global_model_usage['unknown'] += 1

            # Analyze messages
            message_analysis = analyze_message_content_from_json(chat_json)

            # Accumulate message statistics
            user_message_stats['total_messages'] += message_analysis['total_messages']
            user_message_stats['user_messages'] += message_analysis['user_messages']
            user_message_stats['assistant_messages'] += message_analysis['assistant_messages']
            user_message_stats['total_chars'] += message_analysis['total_chars']

            # Store chat data
            chat_data = {
                'id': chat_id,
                'user_id': user_id,
                'title': title,
                'created_at': created_at,
                'updated_at': updated_at,
                'models': models_list,
                'message_count': message_analysis['total_messages'],
                'user_message_count': message_analysis['user_messages'],
                'assistant_message_count': message_analysis['assistant_messages'],
                'archived': archived
            }
            all_chats.append(chat_data)

        # Calculate averages for the user
        if chat_count > 0:
            user_message_stats['avg_messages_per_chat'] = round(
                user_message_stats['total_messages'] / chat_count, 1
            )

        user_data = {
            'name': user_name,
            'email': user['email'],
            'role': user['role'],
            'chat_count': chat_count,
            'model_usage': user_model_usage,
            'message_stats': user_message_stats,
            'instance': instance_name
        }

        all_user_data.append(user_data)

    # Analyze trends
    print("\nAnalyzing usage trends...")
    trends = analyze_usage_trends(all_chats)

    # Get Azure costs
    if skip_azure:
        print("\nSkipping Azure cost data (--skip-azure flag)")
        azure_costs = {
            'total_cost': 0,
            'by_resource_group': {},
            'by_service': {},
            'by_location': {},
            'by_resource': {},
            'daily_costs': {},
            'forecast_30d': 0,
            'forecast_mtd': 0,
            'currency': 'USD',
            'skipped': True
        }
    else:
        azure_costs = get_azure_costs()

    # Close database connection
    conn.close()

    # Prepare report data
    report_data = {
        'instance_name': instance_name,
        'users': all_user_data,
        'models': models,
        'knowledge_bases': knowledge_bases,
        'total_chats': len(all_chats),
        'model_usage': dict(global_model_usage),
        'trends': trends,
        'azure_costs': azure_costs,
        'timestamp': datetime.now()
    }

    print("\nGenerating HTML report...")
    generate_html_report(report_data)

    print(f"\n[SUCCESS] Enhanced HTML report generated for {instance_name}")
    print(f"[SUCCESS] Report saved to: {OUTPUT_DIR}/{instance_name}_Report.html")

def generate_html_report(data):
    """Generate beautiful HTML report"""

    ensure_output_dir()

    instance_name = data['instance_name']
    output_file = os.path.join(OUTPUT_DIR, f"{instance_name}_Report.html")

    # Calculate summary stats
    active_users = sum(1 for u in data['users'] if u['chat_count'] > 0)
    total_users = len(data['users'])

    # Sort users by chats
    top_users_by_chats = sorted([u for u in data['users'] if u['chat_count'] > 0],
                                 key=lambda x: x['chat_count'], reverse=True)[:10]

    # Model distribution data
    model_labels = list(data['model_usage'].keys())[:10]
    model_values = [data['model_usage'][m] for m in model_labels]

    # Trends data
    trend_labels = list(data['trends']['daily'].keys())[-30:]  # Last 30 days
    trend_values = [data['trends']['daily'][d] for d in trend_labels]

    # Azure cost data
    azure_costs = data.get('azure_costs', {})
    total_azure_cost = azure_costs.get('total_cost', 0)
    forecast = azure_costs.get('forecast_30d', 0)

    # Top services by cost
    services_by_cost = sorted(azure_costs.get('by_service', {}).items(), key=lambda x: x[1], reverse=True)[:5]

    # Top resource groups by cost
    rg_by_cost = sorted(azure_costs.get('by_resource_group', {}).items(), key=lambda x: x[1], reverse=True)[:5]

    # Calculate message statistics
    total_messages = sum(u.get('message_stats', {}).get('total_messages', 0) for u in data['users'])
    total_user_messages = sum(u.get('message_stats', {}).get('user_messages', 0) for u in data['users'])
    total_assistant_messages = sum(u.get('message_stats', {}).get('assistant_messages', 0) for u in data['users'])
    avg_messages_per_chat = round(total_messages / max(data['total_chats'], 1), 1)
    user_assistant_ratio = round(total_user_messages / max(total_assistant_messages, 1), 2)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{instance_name} Analytics Report (DB)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .header .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 8px 16px;
            border-radius: 20px;
            margin-top: 10px;
            font-size: 0.9em;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}

        .stat-card .label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}

        .stat-card .subvalue {{
            font-size: 0.9em;
            color: #999;
            margin-top: 5px;
        }}

        .section {{
            padding: 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 25px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}

        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .model-badge {{
            display: inline-block;
            padding: 5px 10px;
            background: #667eea;
            color: white;
            border-radius: 15px;
            font-size: 0.85em;
            margin: 2px;
        }}

        .kb-card {{
            background: white;
            padding: 20px;
            margin: 10px 0;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }}

        .kb-card h3 {{
            color: #667eea;
            margin-bottom: 10px;
        }}

        .cost-section {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
        }}

        .cost-section h3 {{
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .cost-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .cost-item {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 10px;
        }}

        .cost-item .cost-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}

        .cost-item .cost-value {{
            font-size: 1.8em;
            font-weight: bold;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{instance_name} Analytics Dashboard</h1>
            <div class="subtitle">Generated from Database Export</div>
            <div class="badge">Database Analysis Mode - Fast & Offline</div>
            <div class="subtitle" style="margin-top: 10px;">Generated on {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Users</div>
                <div class="value">{total_users}</div>
                <div class="subvalue">{active_users} active ({active_users/max(total_users,1)*100:.1f}%)</div>
            </div>

            <div class="stat-card">
                <div class="label">Total Chats</div>
                <div class="value">{data['total_chats']:,}</div>
                <div class="subvalue">{data['total_chats']/max(active_users,1):.1f} per active user</div>
            </div>

            <div class="stat-card">
                <div class="label">Azure Cost (MTD)</div>
                <div class="value">${total_azure_cost:.2f}</div>
                <div class="subvalue">Month to date</div>
            </div>

            <div class="stat-card">
                <div class="label">Models</div>
                <div class="value">{len(data['models'])}</div>
                <div class="subvalue">{len(data['model_usage'])} actively used</div>
            </div>

            <div class="stat-card">
                <div class="label">Knowledge Bases</div>
                <div class="value">{len(data['knowledge_bases'])}</div>
                <div class="subvalue">Available resources</div>
            </div>

            <div class="stat-card">
                <div class="label">30-Day Forecast</div>
                <div class="value">${forecast:.2f}</div>
                <div class="subvalue">Projected spend</div>
            </div>

            <div class="stat-card">
                <div class="label">Total Messages</div>
                <div class="value">{total_messages:,}</div>
                <div class="subvalue">{avg_messages_per_chat} avg per chat</div>
            </div>

            <div class="stat-card">
                <div class="label">User Messages</div>
                <div class="value">{total_user_messages:,}</div>
                <div class="subvalue">{total_user_messages/max(total_messages,1)*100:.1f}% of total</div>
            </div>

            <div class="stat-card">
                <div class="label">AI Responses</div>
                <div class="value">{total_assistant_messages:,}</div>
                <div class="subvalue">Ratio: {user_assistant_ratio}:1</div>
            </div>
        </div>

        <div class="section">
            <div class="cost-section">
                <h3>Azure Cost Breakdown</h3>
                <div class="cost-grid">
                    <div class="cost-item">
                        <div class="cost-label">Total Actual Cost</div>
                        <div class="cost-value">${total_azure_cost:.2f}</div>
                    </div>
                    <div class="cost-item">
                        <div class="cost-label">Forecast (30d)</div>
                        <div class="cost-value">${forecast:.2f}</div>
                    </div>
                    <div class="cost-item">
                        <div class="cost-label">Daily Average</div>
                        <div class="cost-value">${total_azure_cost/max((datetime.now().day),1):.2f}</div>
                    </div>
                </div>

                <h4 style="margin-top: 25px; margin-bottom: 15px;">Top Services by Cost</h4>
                <table style="background: rgba(255,255,255,0.95);">
                    <thead>
                        <tr>
                            <th>Service Name</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{service}</td><td>${cost:.2f}</td></tr>' for service, cost in services_by_cost) if services_by_cost else '<tr><td colspan="2">No cost data available</td></tr>'}
                    </tbody>
                </table>

                <h4 style="margin-top: 25px; margin-bottom: 15px;">Top Resource Groups by Cost</h4>
                <table style="background: rgba(255,255,255,0.95);">
                    <thead>
                        <tr>
                            <th>Resource Group</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f'<tr><td>{rg}</td><td>${cost:.2f}</td></tr>' for rg, cost in rg_by_cost) if rg_by_cost else '<tr><td colspan="2">No cost data available</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Usage Trends - Last 30 Days</h2>
            <div class="chart-container">
                <canvas id="trendsChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Model Distribution</h2>
            <div class="chart-container">
                <canvas id="modelChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Top Users by Activity</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Chats</th>
                        <th>Messages</th>
                        <th>Avg Msg/Chat</th>
                        <th>Primary Models</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{idx+1}</td>
                        <td>{user['name']}</td>
                        <td>{user['email']}</td>
                        <td>{user['chat_count']}</td>
                        <td>{user.get('message_stats', {}).get('total_messages', 0):,}</td>
                        <td>{user.get('message_stats', {}).get('avg_messages_per_chat', 0)}</td>
                        <td>{''.join(f'<span class="model-badge">{m[:30]}</span>' for m in list(user['model_usage'].keys())[:3])}</td>
                    </tr>
                    ''' for idx, user in enumerate(top_users_by_chats))}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2 class="section-title">Available Models ({len(data['models'])} total)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Model Name</th>
                        <th>Model ID</th>
                        <th>Usage Count</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{model.get('name', model.get('id', 'Unknown'))}</td>
                        <td><code>{model.get('id', 'N/A')}</code></td>
                        <td>{data['model_usage'].get(model.get('id', ''), 0)}</td>
                    </tr>
                    ''' for model in data['models'][:20])}
                </tbody>
            </table>
            {f'<p style="text-align: center; color: #666; margin-top: 20px;">... and {len(data["models"]) - 20} more models</p>' if len(data['models']) > 20 else ''}
        </div>

        <div class="section">
            <h2 class="section-title">Knowledge Bases ({len(data['knowledge_bases'])} total)</h2>
            {''.join(f'''
            <div class="kb-card">
                <h3>{kb.get('name', 'Unnamed KB')}</h3>
                <p><strong>ID:</strong> {kb.get('id', 'N/A')}</p>
                <p>{kb.get('description', '')[:200]}</p>
            </div>
            ''' for kb in data['knowledge_bases'][:20])}
            {f'<p style="text-align: center; color: #666; margin-top: 20px;">... and {len(data["knowledge_bases"]) - 20} more</p>' if len(data['knowledge_bases']) > 20 else ''}
        </div>
    </div>

    <script>
        // Trends Chart
        const trendsCtx = document.getElementById('trendsChart').getContext('2d');
        new Chart(trendsCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(trend_labels)},
                datasets: [{{
                    label: 'Daily Chats',
                    data: {json.dumps(trend_values)},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});

        // Model Distribution Chart
        const modelCtx = document.getElementById('modelChart').getContext('2d');
        new Chart(modelCtx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(model_labels)},
                datasets: [{{
                    data: {json.dumps(model_values)},
                    backgroundColor: [
                        '#667eea', '#764ba2', '#f093fb', '#4facfe',
                        '#43e97b', '#fa709a', '#fee140', '#30cfd0',
                        '#a8edea', '#fed6e3'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python db_usage_analyzer.py <db_path> [--skip-azure]")
        print("\nExamples:")
        print("  python db_usage_analyzer.py ./data/berkshiregpt.db")
        print("  python db_usage_analyzer.py ./data/berkshiregpt.db --skip-azure")
        print("\nOptions:")
        print("  --skip-azure    Skip Azure cost fetching (for offline mode)")
        sys.exit(1)

    db_path = sys.argv[1]
    skip_azure = '--skip-azure' in sys.argv

    # Check if database file exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found: {db_path}")
        sys.exit(1)

    # Analyze database
    analyze_database(db_path, skip_azure=skip_azure)

if __name__ == "__main__":
    main()
