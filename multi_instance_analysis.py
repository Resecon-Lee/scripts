import requests
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time

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

def get_headers(api_key):
    return {"Authorization": f"Bearer {api_key}"}

def fetch_users(instance_name):
    """Fetch all users from specified instance"""
    try:
        url = f"{APIS[instance_name]['url']}/api/v1/users/all"
        headers = get_headers(APIS[instance_name]['key'])
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get("users", [])
        else:
            print(f"Error fetching users from {instance_name}: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching users from {instance_name}: {e}")
        return []

def fetch_user_chats(instance_name, user_id):
    """Fetch chats for a specific user from specified instance"""
    try:
        url = f"{APIS[instance_name]['url']}/api/v1/chats/list/user/{user_id}"
        headers = get_headers(APIS[instance_name]['key'])
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) else []
        else:
            return []
    except Exception as e:
        return []

def analyze_user_activity(chats):
    """Analyze activity patterns from chat timestamps"""
    if not chats:
        return {
            'first_chat': None,
            'last_chat': None,
            'total_days_active': 0,
            'chats_per_week': 0,
            'activity_level': 'Inactive',
            'days_since_last_chat': 9999
        }

    timestamps = []
    for chat in chats:
        ts = chat.get('created_at') or chat.get('updated_at') or 0
        if ts:
            timestamps.append(ts)

    if not timestamps:
        return {
            'first_chat': None,
            'last_chat': None,
            'total_days_active': 0,
            'chats_per_week': 0,
            'activity_level': 'Inactive',
            'days_since_last_chat': 9999
        }

    timestamps.sort()
    first_ts = timestamps[0]
    last_ts = timestamps[-1]

    first_date = datetime.fromtimestamp(first_ts)
    last_date = datetime.fromtimestamp(last_ts)

    days_span = (last_date - first_date).days + 1
    chats_per_week = (len(chats) / max(days_span, 1)) * 7

    now = datetime.now()
    days_since_last = (now - last_date).days

    if days_since_last <= 7:
        activity_level = 'Very Active'
    elif days_since_last <= 30:
        activity_level = 'Active'
    elif days_since_last <= 90:
        activity_level = 'Moderate'
    else:
        activity_level = 'Inactive'

    return {
        'first_chat': first_date.strftime('%Y-%m-%d'),
        'last_chat': last_date.strftime('%Y-%m-%d'),
        'total_days_active': days_span,
        'chats_per_week': round(chats_per_week, 2),
        'activity_level': activity_level,
        'days_since_last_chat': days_since_last
    }

def extract_topics_from_titles(titles):
    """Extract and count topics from chat titles"""
    topic_counter = Counter()

    for title in titles:
        title_clean = title.lower().strip()

        # Remove common emojis
        for emoji in ['💰', '💼', '👥', '🌎', '📁', '📊', '💵', '👔', '📧', '🤖']:
            title_clean = title_clean.replace(emoji, '')

        title_clean = title_clean.strip()

        words = title_clean.split()
        for word in words:
            word = word.strip('.,!?:;()[]{}"\'-')
            if len(word) > 4 and word.isalpha():
                topic_counter[word] += 1

    return topic_counter

def categorize_topics(topics):
    """Categorize topics into business areas"""
    categories = {
        'Employment & HR': ['employment', 'employee', 'salary', 'wage', 'workforce', 'labor', 'compensation', 'occupational'],
        'Financial Analysis': ['financial', 'revenue', 'profit', 'income', 'expense', 'accounting', 'fiscal'],
        'Economic Analysis': ['economic', 'economics', 'market', 'industry', 'growth', 'trends'],
        'Legal/Litigation': ['deposition', 'expert', 'litigation', 'dispute', 'damages', 'legal', 'testimony'],
        'Data Analytics': ['analysis', 'statistics', 'excel', 'report', 'overview', 'summary', 'insights'],
        'Valuation': ['valuation', 'appraisal', 'worth', 'value', 'pricing'],
        'Compliance': ['compliance', 'regulatory', 'audit', 'policy', 'rules'],
        'Advisory': ['advisory', 'consulting', 'guidance', 'recommendation']
    }

    user_categories = defaultdict(int)

    for topic, count in topics.items():
        for category, keywords in categories.items():
            if topic in keywords:
                user_categories[category] += count
                break

    return dict(user_categories)

def analyze_single_instance(instance_name):
    """Analyze a single OpenWebUI instance"""
    print("="*70)
    print(f"COMPREHENSIVE {instance_name.upper()} ANALYSIS")
    print("="*70)
    print(f"\nFetching users from {instance_name}...")

    users = fetch_users(instance_name)
    if not users:
        print("No users found")
        return

    print(f"Total users found: {len(users)}\n")
    print("Fetching chat data for all users...")

    all_user_data = []
    all_chats = []
    global_topics = Counter()
    global_categories = defaultdict(int)

    for i, user in enumerate(users, 1):
        user_id = user["id"]
        user_name = user.get("name", "Unknown")
        user_email = user.get("email", "N/A")
        user_role = user.get("role", "user")

        print(f"  [{i:2}/{len(users)}] Processing {user_name}...", end="", flush=True)

        chats = fetch_user_chats(instance_name, user_id)
        chat_count = len(chats) if isinstance(chats, list) else 0

        print(f" {chat_count} chats")

        chat_titles = []
        if isinstance(chats, list):
            for chat in chats:
                title = chat.get("title", "").strip()
                if title:
                    chat_titles.append(title)
                all_chats.append(chat)

        user_topics = extract_topics_from_titles(chat_titles)
        user_categories = categorize_topics(user_topics)

        global_topics.update(user_topics)
        for cat, count in user_categories.items():
            global_categories[cat] += count

        activity_info = analyze_user_activity(chats if isinstance(chats, list) else [])

        user_data = {
            'name': user_name,
            'email': user_email,
            'role': user_role,
            'chat_count': chat_count,
            'topics': user_topics,
            'categories': user_categories,
            'activity': activity_info,
            'chat_titles': chat_titles,
            'instance': instance_name
        }

        all_user_data.append(user_data)
        time.sleep(0.1)

    print("\n" + "="*70)
    print("Analysis complete. Generating report...")
    print("="*70 + "\n")

    generate_instance_report(instance_name, all_user_data, global_topics, global_categories, all_chats)

def analyze_global():
    """Analyze all instances and create combined global report"""
    print("="*70)
    print("GLOBAL AI PLATFORM ANALYSIS - ALL INSTANCES")
    print("="*70)

    all_instances_data = {}
    combined_user_data = []
    user_by_email = {}  # Track users by email to identify cross-instance users

    # Fetch data from all instances
    for instance_name in ['resgpt', 'fasgpt', 'berkshiregpt']:
        print(f"\nFetching data from {instance_name.upper()}...")

        users = fetch_users(instance_name)
        if not users:
            print(f"  No users found in {instance_name}")
            continue

        print(f"  Total users: {len(users)}")

        instance_data = {
            'users': [],
            'total_chats': 0,
            'topics': Counter(),
            'categories': defaultdict(int)
        }

        for i, user in enumerate(users, 1):
            user_id = user["id"]
            user_name = user.get("name", "Unknown")
            user_email = user.get("email", "N/A")
            user_role = user.get("role", "user")

            print(f"  [{i:2}/{len(users)}] {user_name}...", end="", flush=True)

            chats = fetch_user_chats(instance_name, user_id)
            chat_count = len(chats) if isinstance(chats, list) else 0

            print(f" {chat_count} chats")

            chat_titles = []
            if isinstance(chats, list):
                for chat in chats:
                    title = chat.get("title", "").strip()
                    if title:
                        chat_titles.append(title)

            user_topics = extract_topics_from_titles(chat_titles)
            user_categories = categorize_topics(user_topics)

            instance_data['topics'].update(user_topics)
            for cat, count in user_categories.items():
                instance_data['categories'][cat] += count
            instance_data['total_chats'] += chat_count

            activity_info = analyze_user_activity(chats if isinstance(chats, list) else [])

            user_data = {
                'name': user_name,
                'email': user_email,
                'role': user_role,
                'chat_count': chat_count,
                'topics': user_topics,
                'categories': user_categories,
                'activity': activity_info,
                'chat_titles': chat_titles,
                'instance': instance_name,
                'instances': [instance_name]  # Track which instances user appears in
            }

            # Check if user exists in another instance (by email)
            if user_email in user_by_email and user_email != "N/A":
                # User exists in multiple instances
                existing_user = user_by_email[user_email]
                existing_user['instances'].append(instance_name)
                existing_user['chat_count'] += chat_count
                existing_user['topics'].update(user_topics)
                for cat, count in user_categories.items():
                    existing_user['categories'][cat] = existing_user['categories'].get(cat, 0) + count
                existing_user['chat_titles'].extend(chat_titles)
            else:
                user_by_email[user_email] = user_data
                combined_user_data.append(user_data)

            instance_data['users'].append(user_data)
            time.sleep(0.1)

        all_instances_data[instance_name] = instance_data

    print("\n" + "="*70)
    print("Global analysis complete. Generating combined report...")
    print("="*70 + "\n")

    generate_global_report(all_instances_data, combined_user_data)

def generate_instance_report(instance_name, all_user_data, global_topics, global_categories, all_chats):
    """Generate report for a single instance"""

    output_file = f"{instance_name.upper()}_Comprehensive_Analysis.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# {instance_name.upper()} Comprehensive Usage Analysis\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        f.write("---\n\n")

        # EXECUTIVE SUMMARY
        f.write("## Executive Summary\n\n")

        total_users = len(all_user_data)
        total_chats = sum(u['chat_count'] for u in all_user_data)
        active_users = sum(1 for u in all_user_data if u['chat_count'] > 0)
        very_active_users = sum(1 for u in all_user_data if u['activity']['activity_level'] == 'Very Active')

        f.write(f"### Platform Statistics\n\n")
        f.write(f"- **Instance:** {instance_name.upper()}\n")
        f.write(f"- **Total Registered Users:** {total_users}\n")
        f.write(f"- **Users with Chats:** {active_users} ({active_users/max(total_users,1)*100:.1f}%)\n")
        f.write(f"- **Very Active Users (last 7 days):** {very_active_users}\n")
        f.write(f"- **Total Chats Created:** {total_chats}\n")
        f.write(f"- **Average Chats per Active User:** {total_chats/max(active_users,1):.1f}\n\n")

        f.write(f"### Primary Use Cases\n\n")
        f.write(f"Based on comprehensive analysis of all chat titles and content, {instance_name.upper()} is primarily used for:\n\n")

        sorted_categories = sorted(global_categories.items(), key=lambda x: x[1], reverse=True)
        for i, (category, count) in enumerate(sorted_categories[:8], 1):
            percentage = (count / sum(global_categories.values()) * 100) if global_categories else 0
            f.write(f"{i}. **{category}** - {count} mentions ({percentage:.1f}% of categorized topics)\n")

        f.write("\n### Key Insights\n\n")

        top_user = max(all_user_data, key=lambda x: x['chat_count']) if all_user_data else None
        avg_chats_per_week = sum(u['activity']['chats_per_week'] for u in all_user_data if u['chat_count'] > 0) / max(active_users, 1) if active_users > 0 else 0

        if top_user:
            f.write(f"- Most active user: **{top_user['name']}** with {top_user['chat_count']} chats\n")
        f.write(f"- Average activity rate: **{avg_chats_per_week:.1f} chats per week** per active user\n")
        if global_topics:
            f.write(f"- Top topic across all users: **{global_topics.most_common(1)[0][0]}** ({global_topics.most_common(1)[0][1]} mentions)\n")

        activity_dist = Counter(u['activity']['activity_level'] for u in all_user_data)
        f.write(f"\n### User Activity Distribution\n\n")
        f.write(f"- Very Active (last 7 days): {activity_dist['Very Active']} users\n")
        f.write(f"- Active (last 30 days): {activity_dist['Active']} users\n")
        f.write(f"- Moderate (last 90 days): {activity_dist['Moderate']} users\n")
        f.write(f"- Inactive (90+ days): {activity_dist['Inactive']} users\n\n")

        f.write("---\n\n")

        # TOP 30 GLOBAL TOPICS
        f.write("## Top 30 Most Common Topics Across All Users\n\n")
        f.write("| Rank | Topic | Mentions |\n")
        f.write("|------|-------|----------|\n")
        for i, (topic, count) in enumerate(global_topics.most_common(30), 1):
            f.write(f"| {i} | {topic} | {count} |\n")
        f.write("\n---\n\n")

        # DETAILED USER ANALYSIS
        f.write("## Individual User Analysis\n\n")

        sorted_users = sorted(all_user_data, key=lambda x: x['chat_count'], reverse=True)

        for user_data in sorted_users:
            write_user_section(f, user_data)

    print(f"[SUCCESS] Report generated: {output_file}")

    # Create summary
    summary_file = f"{instance_name.upper()}_Executive_Summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write(f"{instance_name.upper()} EXECUTIVE SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Report Date: {datetime.now().strftime('%B %d, %Y')}\n\n")
        f.write(f"Total Users: {total_users}\n")
        f.write(f"Active Users: {active_users} ({active_users/max(total_users,1)*100:.1f}%)\n")
        f.write(f"Total Chats: {total_chats}\n\n")

        f.write("TOP 10 USERS BY ACTIVITY\n")
        f.write("-" * 70 + "\n")
        for i, user in enumerate(sorted_users[:10], 1):
            f.write(f"{i:2}. {user['name']:30} - {user['chat_count']:3} chats - {user['activity']['activity_level']}\n")

    print(f"[SUCCESS] Summary generated: {summary_file}")

def generate_global_report(all_instances_data, combined_user_data):
    """Generate combined global report"""

    output_file = "GlobalAI_Comprehensive_Analysis.md"

    # Calculate global statistics
    total_instance_users = sum(len(data['users']) for data in all_instances_data.values())
    unique_users = len(combined_user_data)
    total_chats = sum(u['chat_count'] for u in combined_user_data)
    active_users = sum(1 for u in combined_user_data if u['chat_count'] > 0)

    # Combine all topics and categories
    global_topics = Counter()
    global_categories = defaultdict(int)

    for user in combined_user_data:
        global_topics.update(user['topics'])
        for cat, count in user['categories'].items():
            global_categories[cat] += count

    # Find cross-instance users
    cross_instance_users = [u for u in combined_user_data if len(u['instances']) > 1]

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Global AI Platform - Comprehensive Analysis\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        f.write("**Instances Analyzed:** ResGPT, FASGPT, BerkshireGPT\n\n")
        f.write("---\n\n")

        # EXECUTIVE SUMMARY
        f.write("## Executive Summary\n\n")

        f.write("### Global Platform Statistics\n\n")
        f.write(f"- **Total Instance Accounts:** {total_instance_users}\n")
        f.write(f"- **Unique Users (deduplicated):** {unique_users}\n")
        f.write(f"- **Cross-Instance Users:** {len(cross_instance_users)}\n")
        f.write(f"- **Total Chats Across All Platforms:** {total_chats}\n")
        f.write(f"- **Active Users:** {active_users} ({active_users/max(unique_users,1)*100:.1f}%)\n")
        f.write(f"- **Average Chats per Active User:** {total_chats/max(active_users,1):.1f}\n\n")

        f.write("### Platform Breakdown\n\n")
        f.write("| Instance | Users | Total Chats | Active Users | Avg Chats/User |\n")
        f.write("|----------|-------|-------------|--------------|----------------|\n")

        for instance_name, data in all_instances_data.items():
            inst_users = len(data['users'])
            inst_chats = data['total_chats']
            inst_active = sum(1 for u in data['users'] if u['chat_count'] > 0)
            avg_chats = inst_chats / max(inst_active, 1)
            f.write(f"| {instance_name.upper():12} | {inst_users:5} | {inst_chats:11} | {inst_active:12} | {avg_chats:14.1f} |\n")

        f.write("\n### Primary Use Cases (Combined)\n\n")

        sorted_categories = sorted(global_categories.items(), key=lambda x: x[1], reverse=True)
        for i, (category, count) in enumerate(sorted_categories[:8], 1):
            percentage = (count / sum(global_categories.values()) * 100) if global_categories else 0
            f.write(f"{i}. **{category}** - {count} mentions ({percentage:.1f}% of categorized topics)\n")

        f.write("\n### Cross-Instance Usage\n\n")

        if cross_instance_users:
            f.write(f"**{len(cross_instance_users)} users** are active across multiple platforms:\n\n")
            cross_instance_users.sort(key=lambda x: len(x['instances']), reverse=True)

            for user in cross_instance_users[:15]:
                instances_str = ", ".join([inst.upper() for inst in user['instances']])
                f.write(f"- **{user['name']}** ({user['email']}): {instances_str} - {user['chat_count']} total chats\n")
        else:
            f.write("No users found across multiple platforms.\n")

        f.write("\n---\n\n")

        # TOP USERS GLOBALLY
        f.write("## Top 20 Most Active Users (Global)\n\n")
        f.write("| Rank | Name | Email | Instances | Total Chats | Activity |\n")
        f.write("|------|------|-------|-----------|-------------|----------|\n")

        sorted_users = sorted(combined_user_data, key=lambda x: x['chat_count'], reverse=True)
        for i, user in enumerate(sorted_users[:20], 1):
            instances_str = ", ".join([inst[:3].upper() for inst in user['instances']])
            f.write(f"| {i} | {user['name'][:25]} | {user['email'][:30]} | {instances_str} | {user['chat_count']} | {user['activity']['activity_level']} |\n")

        f.write("\n---\n\n")

        # TOP 50 GLOBAL TOPICS
        f.write("## Top 50 Most Common Topics (Global)\n\n")
        f.write("| Rank | Topic | Mentions |\n")
        f.write("|------|-------|----------|\n")
        for i, (topic, count) in enumerate(global_topics.most_common(50), 1):
            f.write(f"| {i} | {topic} | {count} |\n")

        f.write("\n---\n\n")

        # INSTANCE COMPARISONS
        f.write("## Platform Comparison\n\n")

        f.write("### Top Topics by Instance\n\n")

        for instance_name, data in all_instances_data.items():
            f.write(f"#### {instance_name.upper()}\n\n")
            top_topics = data['topics'].most_common(10)
            for topic, count in top_topics:
                f.write(f"- {topic}: {count}\n")
            f.write("\n")

        f.write("### Use Case Distribution by Instance\n\n")

        for instance_name, data in all_instances_data.items():
            f.write(f"#### {instance_name.upper()}\n\n")
            sorted_cats = sorted(data['categories'].items(), key=lambda x: x[1], reverse=True)
            for category, count in sorted_cats[:5]:
                percentage = (count / sum(data['categories'].values()) * 100) if data['categories'] else 0
                f.write(f"- {category}: {count} ({percentage:.1f}%)\n")
            f.write("\n")

        f.write("---\n\n")

        # DETAILED USER PROFILES
        f.write("## Detailed User Profiles (All Platforms)\n\n")

        for user_data in sorted_users:
            write_user_section(f, user_data)

    print(f"[SUCCESS] Global report generated: {output_file}")

    # Global summary
    summary_file = "GlobalAI_Executive_Summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("GLOBAL AI PLATFORM EXECUTIVE SUMMARY\n")
        f.write("="*70 + "\n\n")
        f.write(f"Report Date: {datetime.now().strftime('%B %d, %Y')}\n\n")

        f.write("PLATFORM STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Instance Accounts: {total_instance_users}\n")
        f.write(f"Unique Users: {unique_users}\n")
        f.write(f"Cross-Instance Users: {len(cross_instance_users)}\n")
        f.write(f"Total Chats: {total_chats}\n")
        f.write(f"Active Users: {active_users}\n\n")

        f.write("INSTANCE BREAKDOWN\n")
        f.write("-" * 70 + "\n")
        for instance_name, data in all_instances_data.items():
            f.write(f"{instance_name.upper():15} - {len(data['users']):3} users, {data['total_chats']:4} chats\n")

        f.write("\nTOP 15 GLOBAL USERS\n")
        f.write("-" * 70 + "\n")
        for i, user in enumerate(sorted_users[:15], 1):
            instances_str = "/".join([inst[:3].upper() for inst in user['instances']])
            f.write(f"{i:2}. {user['name']:25} [{instances_str}] - {user['chat_count']:3} chats\n")

        f.write("\nTOP 20 GLOBAL TOPICS\n")
        f.write("-" * 70 + "\n")
        for i, (topic, count) in enumerate(global_topics.most_common(20), 1):
            f.write(f"{i:2}. {topic:25} - {count:3} mentions\n")

    print(f"[SUCCESS] Global summary generated: {summary_file}")

def write_user_section(f, user_data):
    """Write detailed user section to file"""
    name = user_data['name']
    email = user_data['email']
    role = user_data['role']
    chat_count = user_data['chat_count']
    topics = user_data['topics']
    categories = user_data['categories']
    activity = user_data['activity']
    instances = user_data.get('instances', [user_data.get('instance', 'unknown')])

    f.write(f"### {name}\n\n")
    f.write(f"- **Email:** {email}\n")
    f.write(f"- **Role:** {role.capitalize()}\n")

    if len(instances) > 1:
        f.write(f"- **Active on Instances:** {', '.join([i.upper() for i in instances])}\n")
    else:
        f.write(f"- **Instance:** {instances[0].upper()}\n")

    f.write(f"- **Total Chats:** {chat_count}\n")

    if chat_count > 0:
        f.write(f"- **Activity Level:** {activity['activity_level']}\n")
        if activity['first_chat']:
            f.write(f"- **First Chat:** {activity['first_chat']}\n")
            f.write(f"- **Last Chat:** {activity['last_chat']}\n")
        f.write(f"- **Days Since Last Activity:** {activity['days_since_last_chat']}\n")
        f.write(f"- **Average Chats per Week:** {activity['chats_per_week']}\n\n")

        if topics:
            f.write(f"**Top Topics Used:**\n\n")
            for topic, count in topics.most_common(10):
                f.write(f"- {topic}: {count} times\n")
            f.write("\n")

        # Define sorted_cats before using it
        sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True) if categories else []

        if sorted_cats:
            f.write(f"**Primary Focus Areas:**\n\n")
            for cat, count in sorted_cats[:5]:
                f.write(f"- {cat}: {count} mentions\n")
            f.write("\n")

        f.write(f"**Usage Summary:**\n\n")

        if chat_count >= 40:
            intensity = "power user"
        elif chat_count >= 20:
            intensity = "frequent user"
        elif chat_count >= 10:
            intensity = "regular user"
        elif chat_count >= 5:
            intensity = "occasional user"
        else:
            intensity = "light user"

        top_category = sorted_cats[0][0] if sorted_cats else "general"
        top_topic = topics.most_common(1)[0][0] if topics else "various topics"

        if len(instances) > 1:
            f.write(f"{name} is a {intensity} active across {len(instances)} platforms ({', '.join([i.upper() for i in instances])}) ")
        else:
            f.write(f"{name} is a {intensity} on {instances[0].upper()} ")

        f.write(f"with {chat_count} total conversations. ")
        f.write(f"Their primary focus is on **{top_category}**, particularly {top_topic}-related queries. ")

        if activity['activity_level'] == 'Very Active':
            f.write(f"They are currently very active, having used the platform within the last week. ")
        elif activity['activity_level'] == 'Active':
            f.write(f"They are currently active, having used the platform within the last month. ")
        elif activity['days_since_last_chat'] > 90:
            f.write(f"They have been inactive for {activity['days_since_last_chat']} days. ")

        if activity['first_chat']:
            f.write(f"Activity spans {activity['total_days_active']} days from {activity['first_chat']} to {activity['last_chat']}.\n\n")
        else:
            f.write("\n\n")

    else:
        f.write(f"- **Activity Level:** No activity\n")
        f.write(f"\n**Usage Summary:** {name} has registered but has not created any chats yet.\n\n")

    f.write("---\n\n")

def main():
    """Main function to handle command-line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python multi_instance_analysis.py <instance_name>")
        print("Options: fasgpt, resgpt, berkshiregpt, globalAI")
        sys.exit(1)

    instance_name = sys.argv[1].lower()

    if instance_name == "globalai":
        analyze_global()
    elif instance_name in ['fasgpt', 'resgpt', 'berkshiregpt']:
        analyze_single_instance(instance_name)
    else:
        print(f"Invalid instance name: {instance_name}")
        print("Valid options: fasgpt, resgpt, berkshiregpt, globalAI")
        sys.exit(1)

if __name__ == "__main__":
    main()
