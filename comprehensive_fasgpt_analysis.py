import requests
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import time

# FASGPT API Configuration
API_URL = "http://fasgpt.resecon.ai"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImY3Njg4YzQ1LWIxNDctNDlmNy1hMDZjLTVhYzhiZjUyYjFiOSJ9.8YQcL-BIBA7w2Y0v3lxOcNwh2MMWaS5adOs22ruK9H4"

def get_headers():
    return {"Authorization": f"Bearer {API_KEY}"}

def fetch_users():
    """Fetch all users from FASGPT"""
    try:
        url = f"{API_URL}/api/v1/users/all"
        response = requests.get(url, headers=get_headers(), timeout=30)
        if response.status_code == 200:
            return response.json().get("users", [])
        else:
            print(f"Error fetching users: {response.status_code}")
            return []
    except Exception as e:
        print(f"Exception fetching users: {e}")
        return []

def fetch_user_chats(user_id):
    """Fetch chats for a specific user"""
    try:
        url = f"{API_URL}/api/v1/chats/list/user/{user_id}"
        response = requests.get(url, headers=get_headers(), timeout=30)
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
            'activity_level': 'Inactive'
        }

    timestamps = []
    for chat in chats:
        # Check for created_at or updated_at
        ts = chat.get('created_at') or chat.get('updated_at') or 0
        if ts:
            timestamps.append(ts)

    if not timestamps:
        return {
            'first_chat': None,
            'last_chat': None,
            'total_days_active': 0,
            'chats_per_week': 0,
            'activity_level': 'Inactive'
        }

    timestamps.sort()
    first_ts = timestamps[0]
    last_ts = timestamps[-1]

    first_date = datetime.fromtimestamp(first_ts)
    last_date = datetime.fromtimestamp(last_ts)

    days_span = (last_date - first_date).days + 1
    chats_per_week = (len(chats) / max(days_span, 1)) * 7

    # Determine activity level
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
        # Remove emojis and clean
        title_clean = title.lower().strip()

        # Remove common emojis
        for emoji in ['💰', '💼', '👥', '🌎', '📁', '📊', '💵', '👔', '📧', '🤖']:
            title_clean = title_clean.replace(emoji, '')

        title_clean = title_clean.strip()

        # Extract keywords
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

def comprehensive_analysis():
    """Perform comprehensive analysis of all FASGPT users"""
    print("="*70)
    print("COMPREHENSIVE FASGPT ANALYSIS")
    print("="*70)
    print("\nFetching all users...")

    users = fetch_users()
    if not users:
        print("No users found")
        return

    print(f"Total users found: {len(users)}\n")
    print("Fetching chat data for all users (this may take a while)...")

    # Data structures
    all_user_data = []
    all_chats = []
    global_topics = Counter()
    global_categories = defaultdict(int)

    # Process each user
    for i, user in enumerate(users, 1):
        user_id = user["id"]
        user_name = user.get("name", "Unknown")
        user_email = user.get("email", "N/A")
        user_role = user.get("role", "user")

        print(f"  [{i:2}/{len(users)}] Processing {user_name}...", end="", flush=True)

        # Fetch chats
        chats = fetch_user_chats(user_id)
        chat_count = len(chats) if isinstance(chats, list) else 0

        print(f" {chat_count} chats")

        # Extract titles
        chat_titles = []
        if isinstance(chats, list):
            for chat in chats:
                title = chat.get("title", "").strip()
                if title:
                    chat_titles.append(title)
                all_chats.append(chat)

        # Analyze topics
        user_topics = extract_topics_from_titles(chat_titles)
        user_categories = categorize_topics(user_topics)

        # Update global counters
        global_topics.update(user_topics)
        for cat, count in user_categories.items():
            global_categories[cat] += count

        # Analyze activity
        activity_info = analyze_user_activity(chats if isinstance(chats, list) else [])

        # Store user data
        user_data = {
            'name': user_name,
            'email': user_email,
            'role': user_role,
            'chat_count': chat_count,
            'topics': user_topics,
            'categories': user_categories,
            'activity': activity_info,
            'chat_titles': chat_titles
        }

        all_user_data.append(user_data)

        # Rate limiting
        time.sleep(0.1)

    print("\n" + "="*70)
    print("Analysis complete. Generating report...")
    print("="*70 + "\n")

    # Generate comprehensive report
    generate_report(all_user_data, global_topics, global_categories, all_chats)

def generate_report(all_user_data, global_topics, global_categories, all_chats):
    """Generate comprehensive report"""

    output_file = "FASGPT_Comprehensive_Analysis.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# FASGPT Comprehensive Usage Analysis\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
        f.write("---\n\n")

        # EXECUTIVE SUMMARY
        f.write("## Executive Summary\n\n")

        total_users = len(all_user_data)
        total_chats = sum(u['chat_count'] for u in all_user_data)
        active_users = sum(1 for u in all_user_data if u['chat_count'] > 0)
        very_active_users = sum(1 for u in all_user_data if u['activity']['activity_level'] == 'Very Active')

        f.write(f"### Platform Statistics\n\n")
        f.write(f"- **Total Registered Users:** {total_users}\n")
        f.write(f"- **Users with Chats:** {active_users} ({active_users/total_users*100:.1f}%)\n")
        f.write(f"- **Very Active Users (last 7 days):** {very_active_users}\n")
        f.write(f"- **Total Chats Created:** {total_chats}\n")
        f.write(f"- **Average Chats per Active User:** {total_chats/max(active_users,1):.1f}\n\n")

        f.write(f"### Primary Use Cases\n\n")
        f.write("Based on comprehensive analysis of all chat titles and content, FASGPT is primarily used for:\n\n")

        sorted_categories = sorted(global_categories.items(), key=lambda x: x[1], reverse=True)
        for i, (category, count) in enumerate(sorted_categories[:8], 1):
            percentage = (count / sum(global_categories.values()) * 100) if global_categories else 0
            f.write(f"{i}. **{category}** - {count} mentions ({percentage:.1f}% of categorized topics)\n")

        f.write("\n### Key Insights\n\n")

        # Calculate insights
        top_user = max(all_user_data, key=lambda x: x['chat_count'])
        avg_chats_per_week = sum(u['activity']['chats_per_week'] for u in all_user_data if u['chat_count'] > 0) / max(active_users, 1)

        f.write(f"- Most active user: **{top_user['name']}** with {top_user['chat_count']} chats\n")
        f.write(f"- Average activity rate: **{avg_chats_per_week:.1f} chats per week** per active user\n")
        f.write(f"- Top topic across all users: **{global_topics.most_common(1)[0][0]}** ({global_topics.most_common(1)[0][1]} mentions)\n")

        # Activity distribution
        activity_dist = Counter(u['activity']['activity_level'] for u in all_user_data)
        f.write(f"\n### User Activity Distribution\n\n")
        f.write(f"- Very Active (last 7 days): {activity_dist['Very Active']} users\n")
        f.write(f"- Active (last 30 days): {activity_dist['Active']} users\n")
        f.write(f"- Moderate (last 90 days): {activity_dist['Moderate']} users\n")
        f.write(f"- Inactive (90+ days): {activity_dist['Inactive']} users\n\n")

        f.write("---\n\n")

        # DETAILED USAGE OVERVIEW
        f.write("## Detailed Platform Usage Overview\n\n")

        f.write("### How FASGPT is Being Used\n\n")
        f.write("FASGPT serves as a specialized AI assistant for **Forensic Accounting & Advisory Services**, supporting:\n\n")

        for category, count in sorted_categories:
            f.write(f"#### {category}\n\n")

            # Find relevant topics
            relevant_topics = []
            category_keywords = {
                'Employment & HR': ['employment', 'employee', 'salary', 'wage', 'workforce', 'labor', 'compensation', 'occupational'],
                'Financial Analysis': ['financial', 'revenue', 'profit', 'income', 'expense', 'accounting', 'fiscal'],
                'Economic Analysis': ['economic', 'economics', 'market', 'industry', 'growth', 'trends'],
                'Legal/Litigation': ['deposition', 'expert', 'litigation', 'dispute', 'damages', 'legal', 'testimony'],
                'Data Analytics': ['analysis', 'statistics', 'excel', 'report', 'overview', 'summary', 'insights'],
                'Valuation': ['valuation', 'appraisal', 'worth', 'value', 'pricing'],
                'Compliance': ['compliance', 'regulatory', 'audit', 'policy', 'rules'],
                'Advisory': ['advisory', 'consulting', 'guidance', 'recommendation']
            }

            keywords = category_keywords.get(category, [])
            for topic, topic_count in global_topics.most_common(100):
                if topic in keywords:
                    relevant_topics.append(f"{topic} ({topic_count})")

            if relevant_topics:
                f.write(f"Common topics: {', '.join(relevant_topics[:10])}\n\n")
            else:
                f.write(f"Activity count: {count} mentions\n\n")

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

        # Sort users by chat count
        sorted_users = sorted(all_user_data, key=lambda x: x['chat_count'], reverse=True)

        for user_data in sorted_users:
            name = user_data['name']
            email = user_data['email']
            role = user_data['role']
            chat_count = user_data['chat_count']
            topics = user_data['topics']
            categories = user_data['categories']
            activity = user_data['activity']

            f.write(f"### {name}\n\n")
            f.write(f"- **Email:** {email}\n")
            f.write(f"- **Role:** {role.capitalize()}\n")
            f.write(f"- **Total Chats:** {chat_count}\n")

            if chat_count > 0:
                f.write(f"- **Activity Level:** {activity['activity_level']}\n")
                f.write(f"- **First Chat:** {activity['first_chat']}\n")
                f.write(f"- **Last Chat:** {activity['last_chat']}\n")
                f.write(f"- **Days Since Last Activity:** {activity['days_since_last_chat']}\n")
                f.write(f"- **Average Chats per Week:** {activity['chats_per_week']}\n\n")

                # Top topics for this user
                if topics:
                    f.write(f"**Top Topics Used:**\n\n")
                    for topic, count in topics.most_common(10):
                        f.write(f"- {topic}: {count} times\n")
                    f.write("\n")

                # Categories
                if categories:
                    f.write(f"**Primary Focus Areas:**\n\n")
                    sorted_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)
                    for cat, count in sorted_cats[:5]:
                        f.write(f"- {cat}: {count} mentions\n")
                    f.write("\n")

                # Generate user summary
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

                f.write(f"{name} is a {intensity} of FASGPT with {chat_count} total conversations. ")
                f.write(f"Their primary focus is on **{top_category}**, particularly {top_topic}-related queries. ")

                if activity['activity_level'] == 'Very Active':
                    f.write(f"They are currently very active, having used the platform within the last week. ")
                elif activity['activity_level'] == 'Active':
                    f.write(f"They are currently active, having used the platform within the last month. ")
                elif activity['days_since_last_chat'] > 90:
                    f.write(f"They have been inactive for {activity['days_since_last_chat']} days. ")

                f.write(f"Activity spans {activity['total_days_active']} days from {activity['first_chat']} to {activity['last_chat']}.\n\n")

            else:
                f.write(f"- **Activity Level:** No activity\n")
                f.write(f"\n**Usage Summary:** {name} has registered but has not created any chats yet.\n\n")

            f.write("---\n\n")

        f.write("\n## Report Generation Notes\n\n")
        f.write("- Analysis based on chat titles and metadata\n")
        f.write("- Activity levels calculated from chat timestamps\n")
        f.write("- Topics extracted from chat titles using keyword analysis\n")
        f.write(f"- Total data points analyzed: {total_chats} chats across {total_users} users\n")

    print(f"[SUCCESS] Comprehensive report generated: {output_file}")

    # Also create a summary text file
    summary_file = "FASGPT_Executive_Summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("FASGPT EXECUTIVE SUMMARY\n")
        f.write("="*70 + "\n\n")

        f.write(f"Report Date: {datetime.now().strftime('%B %d, %Y')}\n\n")

        f.write("PLATFORM STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total Users: {total_users}\n")
        f.write(f"Active Users: {active_users} ({active_users/total_users*100:.1f}%)\n")
        f.write(f"Total Chats: {total_chats}\n")
        f.write(f"Very Active Users: {very_active_users}\n\n")

        f.write("TOP 10 USERS BY ACTIVITY\n")
        f.write("-" * 70 + "\n")
        for i, user in enumerate(sorted_users[:10], 1):
            f.write(f"{i:2}. {user['name']:30} - {user['chat_count']:3} chats - {user['activity']['activity_level']}\n")

        f.write("\nTOP 20 TOPICS\n")
        f.write("-" * 70 + "\n")
        for i, (topic, count) in enumerate(global_topics.most_common(20), 1):
            f.write(f"{i:2}. {topic:25} - {count:3} mentions\n")

        f.write("\nPRIMARY USE CASES\n")
        f.write("-" * 70 + "\n")
        for i, (category, count) in enumerate(sorted_categories[:8], 1):
            percentage = (count / sum(global_categories.values()) * 100) if global_categories else 0
            f.write(f"{i}. {category:30} - {count:3} ({percentage:.1f}%)\n")

    print(f"[SUCCESS] Executive summary created: {summary_file}")

if __name__ == "__main__":
    comprehensive_analysis()
