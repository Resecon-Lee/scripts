"""
AI Usage Analyzer - Comprehensive OpenWebUI Analytics Tool

This script analyzes usage across multiple OpenWebUI instances (FASGpt, RESGpt, BerkshireGPT)
and generates detailed HTML reports with:
- User activity and engagement metrics
- Model usage distribution and trends
- Chat and message content analysis
- Knowledge base utilization
- Azure cost tracking and forecasts
- Beautiful visualizations with Chart.js

Usage:
    python ai_usage_analyzer.py <instance_name>

    instance_name: fasgpt, resgpt, berkshiregpt, or globalAI

Author: AI Usage Analytics Team
Date: November 2025
"""

import requests
import json
import sys
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time

# ============================================================================
# AZURE CONFIGURATION
# ============================================================================
# Azure credentials for retrieving actual cost data via Cost Management API
# Set these in your .env file or environment variables
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", "")

# Output directory for generated reports
OUTPUT_DIR = "output/ai_usage"

# ============================================================================
# OPENWEBUI API CONFIGURATIONS
# ============================================================================
# API endpoints and authentication tokens for each OpenWebUI instance
APIS = {
    "resgpt": {
        "url": "http://resgpt.resecon.ai",
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjA2MDMyOTk4LWY5YjktNDY0ZS1iMmI2LTc1Zjg2MTRlMjBmMCJ9.sVAkpP6TZsg0VdXZ7GAKLxNTgPNAYvPBXDlr3tkH0wE"
    },
    "fasgpt": {
        "url": "http://fasgpt.resecon.ai",
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImY3Njg4YzQ1LWIxNDctNDlmNy1hMDZjLTVhYzhiZjUyYjFiOSJ9.8YQcL-BIBA7w2Y0v3lxOcNwh2MMWaS5adOs22ruK9H4"
    },
    "berkshiregpt": {
        "url": "http://berkshiregpt.resecon.ai",
        "key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE5N2YwYTU5LWZmMzItNGUwZC1iYmZjLTkwZWVmNDQ4MTE1ZCJ9.EcZtwL23v-OjaI-t0m8-Epz-lrjRvGawcjfUpwyQ2_8"
    }
}

def ensure_output_dir():
    """
    Ensure output directory exists for saving reports.
    Creates the directory if it doesn't exist.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_headers(api_key):
    """
    Generate authorization headers for API requests.

    Args:
        api_key (str): JWT bearer token for authentication

    Returns:
        dict: Headers with authorization token
    """
    return {"Authorization": f"Bearer {api_key}"}

def fetch_api(instance_name, endpoint):
    """
    Generic API fetch function for OpenWebUI instances.

    Args:
        instance_name (str): Instance name (fasgpt, resgpt, berkshiregpt)
        endpoint (str): API endpoint path (e.g., '/api/v1/users/all')

    Returns:
        dict/list: JSON response data or None if request fails
    """
    try:
        url = f"{APIS[instance_name]['url']}{endpoint}"
        headers = get_headers(APIS[instance_name]['key'])
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"    Error fetching {endpoint}: {e}")
        return None

def fetch_users(instance_name):
    """
    Fetch all users from an OpenWebUI instance.

    Args:
        instance_name (str): Instance name (fasgpt, resgpt, berkshiregpt)

    Returns:
        list: List of user objects with id, name, email, role, etc.
    """
    data = fetch_api(instance_name, "/api/v1/users/all")
    return data.get("users", []) if data else []

def fetch_user_chats(instance_name, user_id):
    """
    Fetch chat list for a specific user.

    Args:
        instance_name (str): Instance name
        user_id (str): User UUID

    Returns:
        list: List of chat objects (id, title, created_at, updated_at)
    """
    data = fetch_api(instance_name, f"/api/v1/chats/list/user/{user_id}")
    return data if isinstance(data, list) else []

def fetch_chat_detail(instance_name, chat_id):
    """
    Fetch detailed chat data including models, messages, and metadata.

    Args:
        instance_name (str): Instance name
        chat_id (str): Chat UUID

    Returns:
        dict: Complete chat object with structure:
            - id, user_id, title, created_at, updated_at
            - chat: {models, messages, history, params, tags, files}
    """
    data = fetch_api(instance_name, f"/api/v1/chats/{chat_id}")
    return data if data else {}

def fetch_models(instance_name):
    """
    Fetch available AI models from an OpenWebUI instance.

    Args:
        instance_name (str): Instance name

    Returns:
        list: List of model objects with id, name, capabilities, etc.

    Note:
        Tries endpoint with trailing slash first (/api/v1/models/) then
        falls back to without slash for compatibility.
    """
    # Try with trailing slash first
    data = fetch_api(instance_name, "/api/v1/models/")
    if not data:
        # Try without trailing slash as fallback
        data = fetch_api(instance_name, "/api/v1/models")

    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []

def fetch_knowledge_bases(instance_name):
    """
    Fetch knowledge bases (document collections) from an OpenWebUI instance.

    Args:
        instance_name (str): Instance name

    Returns:
        list: List of knowledge base objects with metadata
    """
    data = fetch_api(instance_name, "/api/v1/knowledge/")
    if isinstance(data, dict):
        return data.get("data", [])
    elif isinstance(data, list):
        return data
    return []

def analyze_message_content(chat_detail):
    """
    Extract and analyze message content from a detailed chat object.

    Args:
        chat_detail (dict): Full chat object from fetch_chat_detail()

    Returns:
        dict: Message statistics containing:
            - total_messages (int): Total number of messages
            - user_messages (int): Count of user messages
            - assistant_messages (int): Count of AI responses
            - avg_user_length (float): Average character count of user messages
            - avg_assistant_length (float): Average character count of AI responses
            - user_assistant_ratio (float): Ratio of user to assistant messages
            - sample_messages (list): Sample of recent messages (up to 3)
            - total_chars (int): Total character count
    """
    messages = []
    if chat_detail and 'chat' in chat_detail:
        messages = chat_detail['chat'].get('messages', [])

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

def analyze_usage_trends(chats):
    """Analyze usage trends over time"""
    daily_counts = defaultdict(int)
    weekly_counts = defaultdict(int)
    monthly_counts = defaultdict(int)

    for chat in chats:
        ts = chat.get('created_at') or chat.get('updated_at')
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

# Azure token cache
_azure_token_cache = {
    'token': None,
    'expires_at': None
}

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

def analyze_single_instance_enhanced(instance_name):
    """Enhanced analysis of a single instance"""
    print("="*70)
    print(f"ENHANCED {instance_name.upper()} ANALYSIS")
    print("="*70)

    # Fetch models
    print(f"\nFetching models from {instance_name}...")
    models = fetch_models(instance_name)
    print(f"  Found {len(models)} models")

    # Print model details for verification
    if models:
        print(f"  Models available:")
        for model in models[:5]:  # Show first 5
            model_id = model.get('id', 'unknown')
            model_name = model.get('name', model_id)
            print(f"    - {model_name}")
        if len(models) > 5:
            print(f"    ... and {len(models) - 5} more")

    # Fetch knowledge bases
    print(f"Fetching knowledge bases...")
    knowledge_bases = fetch_knowledge_bases(instance_name)
    print(f"  Found {len(knowledge_bases)} knowledge bases")

    # Fetch users
    print(f"Fetching users...")
    users = fetch_users(instance_name)
    print(f"  Found {len(users)} users")

    # Analysis data structures
    all_user_data = []
    all_chats = []
    global_model_usage = Counter()

    print(f"\nAnalyzing users and chats...")

    for i, user in enumerate(users, 1):
        user_id = user["id"]
        user_name = user.get("name", "Unknown")
        user_email = user.get("email", "N/A")

        print(f"  [{i:2}/{len(users)}] {user_name}...", end="", flush=True)

        chats = fetch_user_chats(instance_name, user_id)
        chat_count = len(chats)

        print(f" {chat_count} chats")

        # Model usage and message tracking
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

        for chat in chats:
            # Fetch detailed chat data to get model info and messages
            chat_detail = fetch_chat_detail(instance_name, chat['id'])

            # Extract models from nested structure: chat_detail['chat']['models']
            models_list = []
            if chat_detail and 'chat' in chat_detail:
                models_list = chat_detail['chat'].get('models', [])

            # If models is a list, use all models; if empty, mark as unknown
            if models_list:
                for model in models_list:
                    user_model_usage[model] += 1
                    global_model_usage[model] += 1
            else:
                user_model_usage['unknown'] += 1
                global_model_usage['unknown'] += 1

            # Analyze message content for this chat
            message_analysis = analyze_message_content(chat_detail)

            # Accumulate message statistics for the user
            user_message_stats['total_messages'] += message_analysis['total_messages']
            user_message_stats['user_messages'] += message_analysis['user_messages']
            user_message_stats['assistant_messages'] += message_analysis['assistant_messages']
            user_message_stats['total_chars'] += message_analysis['total_chars']

            # Store chat with model info and message stats
            chat_with_model = {
                **chat,
                'models': models_list,
                'message_count': message_analysis['total_messages'],
                'user_message_count': message_analysis['user_messages'],
                'assistant_message_count': message_analysis['assistant_messages']
            }
            all_chats.append(chat_with_model)

        # Calculate averages for the user
        if chat_count > 0:
            user_message_stats['avg_messages_per_chat'] = round(user_message_stats['total_messages'] / chat_count, 1)

        user_data = {
            'name': user_name,
            'email': user_email,
            'role': user.get("role", "user"),
            'chat_count': chat_count,
            'model_usage': user_model_usage,
            'message_stats': user_message_stats,
            'instance': instance_name
        }

        all_user_data.append(user_data)
        time.sleep(0.05)

    # Analyze trends
    print("\nAnalyzing usage trends...")
    trends = analyze_usage_trends(all_chats)

    # Get Azure costs
    azure_costs = get_azure_costs()

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

    print(f"\n[SUCCESS] Enhanced HTML report generated for {instance_name.upper()}")

def analyze_global_enhanced():
    """Enhanced global analysis"""
    print("="*70)
    print("ENHANCED GLOBAL AI ANALYSIS - ALL INSTANCES")
    print("="*70)

    all_instances_data = {}
    combined_model_usage = Counter()
    combined_chats = 0
    all_models = []
    all_knowledge_bases = []
    combined_trends = {'daily': defaultdict(int), 'weekly': defaultdict(int), 'monthly': defaultdict(int)}
    all_users_combined = []

    for instance_name in ['resgpt', 'fasgpt', 'berkshiregpt']:
        print(f"\n{'='*70}")
        print(f"Processing {instance_name.upper()}...")
        print(f"{'='*70}")

        # Fetch data
        models = fetch_models(instance_name)
        knowledge_bases = fetch_knowledge_bases(instance_name)
        users = fetch_users(instance_name)

        print(f"  Models: {len(models)}")
        print(f"  Knowledge Bases: {len(knowledge_bases)}")
        print(f"  Users: {len(users)}")

        all_models.extend([{**m, 'instance': instance_name} for m in models])
        all_knowledge_bases.extend([{**kb, 'instance': instance_name} for kb in knowledge_bases])

        instance_data = {
            'users': [],
            'total_chats': 0,
            'model_usage': Counter(),
            'trends': {'daily': {}, 'weekly': {}, 'monthly': {}}
        }

        all_chats = []

        for i, user in enumerate(users, 1):
            user_name = user.get('name', 'Unknown')
            print(f"  [{i:2}/{len(users)}] {user_name}...", end="", flush=True)

            chats = fetch_user_chats(instance_name, user['id'])
            chat_count = len(chats)
            print(f" {chat_count} chats")

            user_model_usage = Counter()
            user_message_stats = {
                'total_messages': 0,
                'user_messages': 0,
                'assistant_messages': 0,
                'total_chars': 0,
                'avg_messages_per_chat': 0
            }

            for chat in chats:
                # Fetch detailed chat data to get model info and messages
                chat_detail = fetch_chat_detail(instance_name, chat['id'])

                # Extract models from nested structure: chat_detail['chat']['models']
                models_list = []
                if chat_detail and 'chat' in chat_detail:
                    models_list = chat_detail['chat'].get('models', [])

                # If models is a list, use all models; if empty, mark as unknown
                if models_list:
                    for model in models_list:
                        user_model_usage[model] += 1
                        instance_data['model_usage'][model] += 1
                        combined_model_usage[model] += 1
                else:
                    user_model_usage['unknown'] += 1
                    instance_data['model_usage']['unknown'] += 1
                    combined_model_usage['unknown'] += 1

                # Analyze message content for this chat
                message_analysis = analyze_message_content(chat_detail)

                # Accumulate message statistics for the user
                user_message_stats['total_messages'] += message_analysis['total_messages']
                user_message_stats['user_messages'] += message_analysis['user_messages']
                user_message_stats['assistant_messages'] += message_analysis['assistant_messages']
                user_message_stats['total_chars'] += message_analysis['total_chars']

                # Store chat with model info and message stats
                chat_with_model = {
                    **chat,
                    'models': models_list,
                    'message_count': message_analysis['total_messages'],
                    'user_message_count': message_analysis['user_messages'],
                    'assistant_message_count': message_analysis['assistant_messages']
                }
                all_chats.append(chat_with_model)

            # Calculate averages for the user
            if chat_count > 0:
                user_message_stats['avg_messages_per_chat'] = round(user_message_stats['total_messages'] / chat_count, 1)

            user_data = {
                'name': user_name,
                'email': user.get('email', 'N/A'),
                'chat_count': chat_count,
                'model_usage': dict(user_model_usage),
                'message_stats': user_message_stats,
                'instance': instance_name
            }

            instance_data['users'].append(user_data)
            all_users_combined.append(user_data)

            time.sleep(0.05)

        instance_data['total_chats'] = len(all_chats)
        instance_data['trends'] = analyze_usage_trends(all_chats)

        combined_chats += instance_data['total_chats']

        # Merge trends
        for period in ['daily', 'weekly', 'monthly']:
            for key, val in instance_data['trends'][period].items():
                combined_trends[period][key] += val

        all_instances_data[instance_name] = instance_data

    # Convert combined_trends defaultdicts to regular dicts
    for period in combined_trends:
        combined_trends[period] = dict(sorted(combined_trends[period].items()))

    # Get Azure costs
    azure_costs = get_azure_costs()

    global_report_data = {
        'instance_name': 'GlobalAI',
        'instances': all_instances_data,
        'all_models': all_models,
        'all_knowledge_bases': all_knowledge_bases,
        'combined_model_usage': dict(combined_model_usage),
        'combined_total_chats': combined_chats,
        'combined_trends': combined_trends,
        'all_users': all_users_combined,
        'azure_costs': azure_costs,
        'timestamp': datetime.now()
    }

    print("\n" + "="*70)
    print("Generating Global HTML Report...")
    print("="*70)

    generate_global_html_report(global_report_data)

    print(f"\n[SUCCESS] Enhanced Global HTML report generated")

def generate_html_report(data):
    """Generate beautiful HTML report for single instance"""

    ensure_output_dir()

    instance_name = data['instance_name']
    output_file = os.path.join(OUTPUT_DIR, f"{instance_name.upper()}_Report.html")

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
    <title>{instance_name.upper()} Analytics Report</title>
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
            <h1>{instance_name.upper()} Analytics Dashboard</h1>
            <div class="subtitle">Generated on {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}</div>
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
                <h3>💰 Azure Cost Breakdown</h3>
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
                        {''.join(f'<tr><td>{service}</td><td>${cost:.2f}</td></tr>' for service, cost in services_by_cost)}
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
                        {''.join(f'<tr><td>{rg}</td><td>${cost:.2f}</td></tr>' for rg, cost in rg_by_cost)}
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
                        <td>{''.join(f'<span class="model-badge">{m}</span>' for m in list(user['model_usage'].keys())[:3])}</td>
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

    print(f"[SUCCESS] HTML report saved: {output_file}")

def generate_global_html_report(data):
    """Generate beautiful HTML report for global analysis"""

    ensure_output_dir()
    output_file = os.path.join(OUTPUT_DIR, "GlobalAI_Report.html")

    # Prepare instance comparison data
    instance_names = list(data['instances'].keys())
    instance_chats = [data['instances'][name]['total_chats'] for name in instance_names]

    # Model distribution
    model_labels = list(data['combined_model_usage'].keys())[:15]
    model_values = [data['combined_model_usage'][m] for m in model_labels]

    # Trends
    trend_labels = list(data['combined_trends']['daily'].keys())[-30:]
    trend_values = [data['combined_trends']['daily'][d] for d in trend_labels]

    # Azure cost data
    azure_costs = data.get('azure_costs', {})
    total_azure_cost = azure_costs.get('total_cost', 0)
    forecast = azure_costs.get('forecast_30d', 0)

    # Top users across all platforms
    top_users_global = sorted(data['all_users'], key=lambda x: x['chat_count'], reverse=True)[:15]

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global AI Platform Analytics</title>
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
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 50px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
            text-align: center;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }}

        .stat-card .label {{
            font-size: 0.85em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .value {{
            font-size: 2.2em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .stat-card .subvalue {{
            font-size: 0.85em;
            color: #999;
            margin-top: 8px;
        }}

        .section {{
            padding: 40px;
        }}

        .section-title {{
            font-size: 2em;
            margin-bottom: 30px;
            color: #333;
            border-bottom: 4px solid #667eea;
            padding-bottom: 15px;
            display: inline-block;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}

        .chart-title {{
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #667eea;
            font-weight: 600;
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
            padding: 18px 15px;
            text-align: left;
            font-weight: 600;
            font-size: 1em;
        }}

        td {{
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .instance-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            margin: 2px;
        }}

        .badge-resgpt {{
            background: #e3f2fd;
            color: #1976d2;
        }}

        .badge-fasgpt {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}

        .badge-berkshiregpt {{
            background: #e8f5e9;
            color: #388e3c;
        }}

        .cost-section {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin: 20px 0;
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
            <h1>🌐 Global AI Platform Analytics</h1>
            <div class="subtitle">Comprehensive Analysis Across ResGPT, FASGPT, and BerkshireGPT</div>
            <div class="subtitle" style="margin-top: 10px; font-size: 0.9em;">Generated on {data['timestamp'].strftime('%B %d, %Y at %I:%M %p')}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Platforms</div>
                <div class="value">3</div>
                <div class="subvalue">ResGPT, FASGPT, BerkshireGPT</div>
            </div>

            <div class="stat-card">
                <div class="label">Total Chats</div>
                <div class="value">{data['combined_total_chats']:,}</div>
                <div class="subvalue">Across all platforms</div>
            </div>

            <div class="stat-card">
                <div class="label">Azure Cost (MTD)</div>
                <div class="value">${total_azure_cost:.2f}</div>
                <div class="subvalue">Month to date</div>
            </div>

            <div class="stat-card">
                <div class="label">30-Day Forecast</div>
                <div class="value">${forecast:.2f}</div>
                <div class="subvalue">Projected spend</div>
            </div>

            <div class="stat-card">
                <div class="label">Total Models</div>
                <div class="value">{len(data['all_models'])}</div>
                <div class="subvalue">{len(data['combined_model_usage'])} actively used</div>
            </div>

            <div class="stat-card">
                <div class="label">Knowledge Bases</div>
                <div class="value">{len(data['all_knowledge_bases'])}</div>
                <div class="subvalue">Across all platforms</div>
            </div>
        </div>

        <div class="section">
            <div class="cost-section">
                <h3>💰 Azure Cost Analysis</h3>
                <div class="cost-grid">
                    <div class="cost-item">
                        <div class="cost-label">Total Actual Cost</div>
                        <div class="cost-value">${total_azure_cost:.2f}</div>
                    </div>
                    <div class="cost-item">
                        <div class="cost-label">30-Day Forecast</div>
                        <div class="cost-value">${forecast:.2f}</div>
                    </div>
                    <div class="cost-item">
                        <div class="cost-label">Daily Average</div>
                        <div class="cost-value">${total_azure_cost/max((datetime.now().day),1):.2f}</div>
                    </div>
                    <div class="cost-item">
                        <div class="cost-label">Cost per Chat</div>
                        <div class="cost-value">${total_azure_cost/max(data['combined_total_chats'],1):.3f}</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Platform Comparison</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">Chats by Instance</div>
                    <canvas id="instanceChatsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Global Usage Trends - Last 30 Days</h2>
            <div class="chart-container" style="height: 450px;">
                <canvas id="trendsChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Model Distribution Across All Platforms</h2>
            <div class="chart-container" style="height: 500px;">
                <canvas id="modelChart"></canvas>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">Top Users Across All Platforms</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Instance</th>
                        <th>Chats</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{idx+1}</td>
                        <td>{user['name']}</td>
                        <td>{user['email']}</td>
                        <td><span class="instance-badge badge-{user['instance']}">{user['instance'].upper()}</span></td>
                        <td>{user['chat_count']}</td>
                    </tr>
                    ''' for idx, user in enumerate(top_users_global))}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2 class="section-title">Instance Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Instance</th>
                        <th>Total Chats</th>
                        <th>Active Models</th>
                        <th>Knowledge Bases</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td><span class="instance-badge badge-{name}">{name.upper()}</span></td>
                        <td>{inst_data['total_chats']:,}</td>
                        <td>{len(inst_data['model_usage'])}</td>
                        <td>{len([kb for kb in data['all_knowledge_bases'] if kb.get('instance') == name])}</td>
                    </tr>
                    ''' for name, inst_data in data['instances'].items())}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // Instance Chats Comparison
        const chatsCtx = document.getElementById('instanceChatsChart').getContext('2d');
        new Chart(chatsCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([n.upper() for n in instance_names])},
                datasets: [{{
                    label: 'Total Chats',
                    data: {json.dumps(instance_chats)},
                    backgroundColor: ['#667eea', '#764ba2', '#43e97b']
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Global Trends
        const trendsCtx = document.getElementById('trendsChart').getContext('2d');
        new Chart(trendsCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(trend_labels)},
                datasets: [{{
                    label: 'Daily Chats (All Platforms)',
                    data: {json.dumps(trend_values)},
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3
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
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});

        // Model Distribution
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
                        '#a8edea', '#fed6e3', '#ffecd2', '#fcb69f',
                        '#ff9a9e', '#fad0c4', '#ffd1ff'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{ size: 11 }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[SUCCESS] Global HTML report saved: {output_file}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python ai_usage_analyzer.py <instance_name>")
        print("Options: fasgpt, resgpt, berkshiregpt, globalAI")
        sys.exit(1)

    instance_name = sys.argv[1].lower()

    if instance_name == "globalai":
        analyze_global_enhanced()
    elif instance_name in ['fasgpt', 'resgpt', 'berkshiregpt']:
        analyze_single_instance_enhanced(instance_name)
    else:
        print(f"Invalid instance name: {instance_name}")
        print("Valid options: fasgpt, resgpt, berkshiregpt, globalAI")
        sys.exit(1)

if __name__ == "__main__":
    main()
