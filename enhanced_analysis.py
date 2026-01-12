import requests
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time
import re

# API Configurations for all instances
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

# Model pricing (per 1M tokens)
MODEL_PRICING = {
    'gpt-4': {'input': 30.0, 'output': 60.0},
    'gpt-4-turbo': {'input': 10.0, 'output': 30.0},
    'gpt-3.5-turbo': {'input': 0.5, 'output': 1.5},
    'claude-3-opus': {'input': 15.0, 'output': 75.0},
    'claude-3-sonnet': {'input': 3.0, 'output': 15.0},
    'claude-3-haiku': {'input': 0.25, 'output': 1.25},
    'claude-3.5-sonnet': {'input': 3.0, 'output': 15.0},
    'default': {'input': 5.0, 'output': 15.0}
}

def get_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}

def fetch_api(instance_name, endpoint):
    """Generic API fetch function"""
    try:
        url = f"{APIS[instance_name]['url']}{endpoint}"
        headers = get_headers(APIS[instance_name]['key'])
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        return None

def fetch_users(instance_name):
    """Fetch all users"""
    data = fetch_api(instance_name, "/api/v1/users/all")
    return data.get("users", []) if data else []

def fetch_user_chats(instance_name, user_id):
    """Fetch chats for a user"""
    data = fetch_api(instance_name, f"/api/v1/chats/list/user/{user_id}")
    return data if isinstance(data, list) else []

def fetch_chat_messages(instance_name, chat_id):
    """Fetch messages for a chat - for token estimation"""
    data = fetch_api(instance_name, f"/api/v1/chats/{chat_id}")
    if data and 'chat' in data:
        return data['chat'].get('messages', [])
    return []

def fetch_models(instance_name):
    """Fetch available models"""
    data = fetch_api(instance_name, "/api/v1/models/")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data", [])
    return []

def fetch_knowledge_bases(instance_name):
    """Fetch knowledge bases"""
    data = fetch_api(instance_name, "/api/v1/knowledge/")
    if isinstance(data, dict):
        return data.get("data", [])
    elif isinstance(data, list):
        return data
    return []

def estimate_tokens(text):
    """Estimate token count from text (rough approximation)"""
    if not text:
        return 0
    # Rough estimate: ~4 characters per token for English text
    return len(text) // 4

def get_model_pricing(model_id):
    """Get pricing for a model"""
    model_lower = model_id.lower()

    for key in MODEL_PRICING.keys():
        if key in model_lower:
            return MODEL_PRICING[key]

    return MODEL_PRICING['default']

def analyze_chat_with_messages(instance_name, chat, sample_limit=5):
    """Analyze a single chat including messages for token estimation"""
    chat_id = chat.get('id')
    model_id = chat.get('model', 'unknown')

    # Only sample some chats for detailed analysis to avoid rate limits
    messages = []
    if sample_limit > 0:
        messages = fetch_chat_messages(instance_name, chat_id)
        time.sleep(0.05)  # Rate limiting

    # Estimate tokens from messages
    total_input_tokens = 0
    total_output_tokens = 0

    for msg in messages:
        role = msg.get('role', '')
        content = msg.get('content', '')

        tokens = estimate_tokens(content)

        if role == 'user':
            total_input_tokens += tokens
        elif role == 'assistant':
            total_output_tokens += tokens

    return {
        'model': model_id,
        'input_tokens': total_input_tokens,
        'output_tokens': total_output_tokens,
        'message_count': len(messages)
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

def analyze_single_instance_enhanced(instance_name):
    """Enhanced analysis of a single instance"""
    print("="*70)
    print(f"ENHANCED {instance_name.upper()} ANALYSIS")
    print("="*70)

    # Fetch models
    print(f"\nFetching models from {instance_name}...")
    models = fetch_models(instance_name)
    print(f"  Found {len(models)} models")

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
    total_input_tokens = 0
    total_output_tokens = 0
    model_costs = defaultdict(float)

    print(f"\nAnalyzing users and chats...")

    for i, user in enumerate(users, 1):
        user_id = user["id"]
        user_name = user.get("name", "Unknown")
        user_email = user.get("email", "N/A")

        print(f"  [{i:2}/{len(users)}] {user_name}...", end="", flush=True)

        chats = fetch_user_chats(instance_name, user_id)
        chat_count = len(chats)

        print(f" {chat_count} chats", end="")

        # Model usage tracking
        user_model_usage = Counter()
        user_input_tokens = 0
        user_output_tokens = 0

        # Sample first 3 chats for detailed token analysis
        sample_count = min(3, len(chats))

        if sample_count > 0:
            print(f" (analyzing {sample_count} for tokens)", end="")

        for idx, chat in enumerate(chats):
            all_chats.append(chat)
            model = chat.get('model', 'unknown')
            user_model_usage[model] += 1
            global_model_usage[model] += 1

            # Deep analysis for sample
            if idx < sample_count:
                chat_analysis = analyze_chat_with_messages(instance_name, chat, sample_limit=sample_count)
                user_input_tokens += chat_analysis['input_tokens']
                user_output_tokens += chat_analysis['output_tokens']

        print()  # New line

        # Extrapolate tokens for all chats
        if sample_count > 0:
            avg_input = user_input_tokens / sample_count
            avg_output = user_output_tokens / sample_count
            estimated_total_input = int(avg_input * chat_count)
            estimated_total_output = int(avg_output * chat_count)
        else:
            estimated_total_input = 0
            estimated_total_output = 0

        total_input_tokens += estimated_total_input
        total_output_tokens += estimated_total_output

        # Calculate costs
        user_costs = {}
        for model, count in user_model_usage.items():
            pricing = get_model_pricing(model)
            input_cost = (estimated_total_input / 1_000_000) * pricing['input']
            output_cost = (estimated_total_output / 1_000_000) * pricing['output']
            user_costs[model] = input_cost + output_cost
            model_costs[model] += input_cost + output_cost

        user_data = {
            'name': user_name,
            'email': user_email,
            'role': user.get("role", "user"),
            'chat_count': chat_count,
            'model_usage': user_model_usage,
            'estimated_input_tokens': estimated_total_input,
            'estimated_output_tokens': estimated_total_output,
            'estimated_cost': sum(user_costs.values()),
            'instance': instance_name
        }

        all_user_data.append(user_data)
        time.sleep(0.05)

    # Analyze trends
    print("\nAnalyzing usage trends...")
    trends = analyze_usage_trends(all_chats)

    # Prepare report data
    report_data = {
        'instance_name': instance_name,
        'users': all_user_data,
        'models': models,
        'knowledge_bases': knowledge_bases,
        'total_chats': len(all_chats),
        'total_input_tokens': total_input_tokens,
        'total_output_tokens': total_output_tokens,
        'total_cost': sum(model_costs.values()),
        'model_usage': dict(global_model_usage),
        'model_costs': dict(model_costs),
        'trends': trends,
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
    combined_total_input = 0
    combined_total_output = 0
    combined_total_cost = 0
    combined_chats = 0
    all_models = []
    all_knowledge_bases = []
    combined_trends = {'daily': defaultdict(int), 'weekly': defaultdict(int), 'monthly': defaultdict(int)}

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
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost': 0,
            'model_usage': Counter(),
            'trends': {'daily': {}, 'weekly': {}, 'monthly': {}}
        }

        all_chats = []

        for i, user in enumerate(users, 1):
            print(f"  [{i:2}/{len(users)}] {user.get('name', 'Unknown')}...", end="", flush=True)

            chats = fetch_user_chats(instance_name, user['id'])
            chat_count = len(chats)
            print(f" {chat_count} chats")

            user_model_usage = Counter()
            user_input_tokens = 0
            user_output_tokens = 0

            sample_count = min(2, len(chats))

            for idx, chat in enumerate(chats):
                all_chats.append(chat)
                model = chat.get('model', 'unknown')
                user_model_usage[model] += 1
                instance_data['model_usage'][model] += 1
                combined_model_usage[model] += 1

                if idx < sample_count:
                    chat_analysis = analyze_chat_with_messages(instance_name, chat, sample_limit=sample_count)
                    user_input_tokens += chat_analysis['input_tokens']
                    user_output_tokens += chat_analysis['output_tokens']

            if sample_count > 0:
                estimated_total_input = int((user_input_tokens / sample_count) * chat_count)
                estimated_total_output = int((user_output_tokens / sample_count) * chat_count)
            else:
                estimated_total_input = 0
                estimated_total_output = 0

            user_cost = 0
            for model, count in user_model_usage.items():
                pricing = get_model_pricing(model)
                user_cost += (estimated_total_input / 1_000_000) * pricing['input']
                user_cost += (estimated_total_output / 1_000_000) * pricing['output']

            instance_data['users'].append({
                'name': user.get('name'),
                'email': user.get('email'),
                'chat_count': chat_count,
                'model_usage': dict(user_model_usage),
                'estimated_input_tokens': estimated_total_input,
                'estimated_output_tokens': estimated_total_output,
                'estimated_cost': user_cost,
                'instance': instance_name
            })

            instance_data['total_input_tokens'] += estimated_total_input
            instance_data['total_output_tokens'] += estimated_total_output
            instance_data['total_cost'] += user_cost

            time.sleep(0.05)

        instance_data['total_chats'] = len(all_chats)
        instance_data['trends'] = analyze_usage_trends(all_chats)

        # Aggregate to global
        combined_total_input += instance_data['total_input_tokens']
        combined_total_output += instance_data['total_output_tokens']
        combined_total_cost += instance_data['total_cost']
        combined_chats += instance_data['total_chats']

        # Merge trends
        for period in ['daily', 'weekly', 'monthly']:
            for key, val in instance_data['trends'][period].items():
                combined_trends[period][key] += val

        all_instances_data[instance_name] = instance_data

    # Convert combined_trends defaultdicts to regular dicts
    for period in combined_trends:
        combined_trends[period] = dict(sorted(combined_trends[period].items()))

    global_report_data = {
        'instance_name': 'GlobalAI',
        'instances': all_instances_data,
        'all_models': all_models,
        'all_knowledge_bases': all_knowledge_bases,
        'combined_model_usage': dict(combined_model_usage),
        'combined_total_chats': combined_chats,
        'combined_total_input': combined_total_input,
        'combined_total_output': combined_total_output,
        'combined_total_cost': combined_total_cost,
        'combined_trends': combined_trends,
        'timestamp': datetime.now()
    }

    print("\n" + "="*70)
    print("Generating Global HTML Report...")
    print("="*70)

    generate_global_html_report(global_report_data)

    print(f"\n[SUCCESS] Enhanced Global HTML report generated")

def generate_html_report(data):
    """Generate beautiful HTML report for single instance"""

    instance_name = data['instance_name']
    output_file = f"{instance_name.upper()}_Enhanced_Report.html"

    # Calculate summary stats
    active_users = sum(1 for u in data['users'] if u['chat_count'] > 0)
    total_users = len(data['users'])

    # Sort users by cost
    top_users_by_cost = sorted([u for u in data['users'] if u['chat_count'] > 0],
                                key=lambda x: x['estimated_cost'], reverse=True)[:10]

    # Sort users by chats
    top_users_by_chats = sorted([u for u in data['users'] if u['chat_count'] > 0],
                                 key=lambda x: x['chat_count'], reverse=True)[:10]

    # Model distribution data
    model_labels = list(data['model_usage'].keys())[:10]
    model_values = [data['model_usage'][m] for m in model_labels]

    # Trends data
    trend_labels = list(data['trends']['daily'].keys())[-30:]  # Last 30 days
    trend_values = [data['trends']['daily'][d] for d in trend_labels]

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

        .cost-high {{
            color: #e74c3c;
            font-weight: bold;
        }}

        .cost-medium {{
            color: #f39c12;
            font-weight: bold;
        }}

        .cost-low {{
            color: #27ae60;
            font-weight: bold;
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
                <div class="label">Estimated Tokens</div>
                <div class="value">{(data['total_input_tokens'] + data['total_output_tokens'])/1000:.1f}K</div>
                <div class="subvalue">Input: {data['total_input_tokens']/1000:.0f}K | Output: {data['total_output_tokens']/1000:.0f}K</div>
            </div>

            <div class="stat-card">
                <div class="label">Estimated Cost</div>
                <div class="value">${data['total_cost']:.2f}</div>
                <div class="subvalue">Based on token usage</div>
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
            <h2 class="section-title">Top Users by Cost</h2>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Name</th>
                        <th>Chats</th>
                        <th>Tokens</th>
                        <th>Estimated Cost</th>
                        <th>Primary Models</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td>{idx+1}</td>
                        <td>{user['name']}</td>
                        <td>{user['chat_count']}</td>
                        <td>{(user['estimated_input_tokens'] + user['estimated_output_tokens'])/1000:.1f}K</td>
                        <td class="{'cost-high' if user['estimated_cost'] > 5 else 'cost-medium' if user['estimated_cost'] > 1 else 'cost-low'}">${user['estimated_cost']:.2f}</td>
                        <td>{''.join(f'<span class="model-badge">{m}</span>' for m in list(user['model_usage'].keys())[:3])}</td>
                    </tr>
                    ''' for idx, user in enumerate(top_users_by_cost))}
                </tbody>
            </table>
        </div>

        <div class="section">
            <h2 class="section-title">Knowledge Bases</h2>
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

    output_file = "GlobalAI_Enhanced_Report.html"

    # Prepare instance comparison data
    instance_names = list(data['instances'].keys())
    instance_chats = [data['instances'][name]['total_chats'] for name in instance_names]
    instance_costs = [data['instances'][name]['total_cost'] for name in instance_names]

    # Model distribution
    model_labels = list(data['combined_model_usage'].keys())[:15]
    model_values = [data['combined_model_usage'][m] for m in model_labels]

    # Trends
    trend_labels = list(data['combined_trends']['daily'].keys())[-30:]
    trend_values = [data['combined_trends']['daily'][d] for d in trend_labels]

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

        .cost-indicator {{
            font-weight: bold;
            font-size: 1.1em;
        }}

        .cost-high {{ color: #e74c3c; }}
        .cost-medium {{ color: #f39c12; }}
        .cost-low {{ color: #27ae60; }}
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
                <div class="label">Total Tokens</div>
                <div class="value">{(data['combined_total_input'] + data['combined_total_output'])/1_000_000:.2f}M</div>
                <div class="subvalue">Input: {data['combined_total_input']/1_000_000:.2f}M | Output: {data['combined_total_output']/1_000_000:.2f}M</div>
            </div>

            <div class="stat-card">
                <div class="label">Total Cost</div>
                <div class="value">${data['combined_total_cost']:.2f}</div>
                <div class="subvalue">Estimated spend</div>
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
            <h2 class="section-title">Platform Comparison</h2>
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">Chats by Instance</div>
                    <canvas id="instanceChatsChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Cost by Instance</div>
                    <canvas id="instanceCostsChart"></canvas>
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
            <h2 class="section-title">Instance Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Instance</th>
                        <th>Total Chats</th>
                        <th>Tokens (M)</th>
                        <th>Estimated Cost</th>
                        <th>Active Models</th>
                        <th>Knowledge Bases</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(f'''
                    <tr>
                        <td><span class="instance-badge badge-{name}">{name.upper()}</span></td>
                        <td>{inst_data['total_chats']:,}</td>
                        <td>{(inst_data['total_input_tokens'] + inst_data['total_output_tokens'])/1_000_000:.2f}</td>
                        <td class="cost-indicator cost-{'high' if inst_data['total_cost'] > 20 else 'medium' if inst_data['total_cost'] > 10 else 'low'}">${inst_data['total_cost']:.2f}</td>
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

        // Instance Costs Comparison
        const costsCtx = document.getElementById('instanceCostsChart').getContext('2d');
        new Chart(costsCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([n.upper() for n in instance_names])},
                datasets: [{{
                    label: 'Estimated Cost ($)',
                    data: {json.dumps(instance_costs)},
                    backgroundColor: ['#f093fb', '#4facfe', '#fee140']
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
        print("Usage: python enhanced_analysis.py <instance_name>")
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
