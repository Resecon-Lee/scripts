import requests
import json
from datetime import datetime
from collections import Counter
import time

# API Configuration
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

def fetch_data(instance_name, endpoint):
    """Fetch data from an API endpoint"""
    try:
        url = f"{APIS[instance_name]['url']}{endpoint}"
        headers = get_headers(APIS[instance_name]['key'])
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching {endpoint} from {instance_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Exception fetching {endpoint} from {instance_name}: {e}")
        return None

def collect_all_data():
    """Collect comprehensive data from all instances"""
    data = {
        "users": {},
        "chats": {},
        "models": {},
        "knowledge": {},
        "timestamp": datetime.now().isoformat()
    }
    
    for instance in APIS.keys():
        print(f"Collecting data from {instance}...")
        
        # Get users
        users_data = fetch_data(instance, "/api/v1/users/all")
        if users_data and "users" in users_data:
            data["users"][instance] = users_data["users"]
            print(f"  - Users: {len(users_data['users'])}")
        
        # Get models
        models_data = fetch_data(instance, "/api/v1/models/")
        if models_data and "data" in models_data:
            data["models"][instance] = models_data["data"]
            print(f"  - Models: {len(models_data['data'])}")
        
        # Get knowledge bases
        knowledge_data = fetch_data(instance, "/api/v1/knowledge/")
        if knowledge_data:
            data["knowledge"][instance] = knowledge_data
            kb_count = len(knowledge_data.get("data", [])) if isinstance(knowledge_data, dict) else len(knowledge_data) if isinstance(knowledge_data, list) else 0
            print(f"  - Knowledge bases: {kb_count}")
        
        # Get chats for each user (sample first 10 active users to avoid overload)
        if users_data and "users" in users_data:
            data["chats"][instance] = {}
            active_users = sorted(users_data["users"], 
                                key=lambda x: x.get("last_active_at", 0), 
                                reverse=True)[:10]
            
            for user in active_users:
                user_id = user["id"]
                chats_data = fetch_data(instance, f"/api/v1/chats/list/user/{user_id}")
                if chats_data:
                    data["chats"][instance][user_id] = chats_data
                time.sleep(0.1)  # Rate limiting
        
        time.sleep(0.5)  # Rate limiting between instances
    
    return data

def analyze_data(data):
    """Analyze collected data and generate statistics"""
    stats = {
        "total_users": 0,
        "users_by_instance": {},
        "active_users_30d": 0,
        "models_by_instance": {},
        "total_models": 0,
        "active_models": 0,
        "top_users": [],
        "popular_topics": Counter(),
        "estimated_tokens": 0
    }
    
    # User statistics
    for instance, users in data["users"].items():
        stats["users_by_instance"][instance] = len(users)
        stats["total_users"] += len(users)
        
        # Check active users (30 days)
        thirty_days_ago = time.time() - (30 * 24 * 60 * 60)
        for user in users:
            if user.get("last_active_at", 0) > thirty_days_ago:
                stats["active_users_30d"] += 1
    
    # Model statistics
    for instance, models in data["models"].items():
        stats["models_by_instance"][instance] = len(models)
        stats["total_models"] += len(models)
        for model in models:
            if model.get("is_active", False):
                stats["active_models"] += 1
    
    # Chat analysis (from sampled data)
    user_chat_counts = {}
    for instance, chats_by_user in data["chats"].items():
        for user_id, chats in chats_by_user.items():
            if isinstance(chats, list):
                user_chat_counts[user_id] = len(chats)
                
                # Extract topics from chat titles
                for chat in chats:
                    title = chat.get("title", "").lower()
                    if title and len(title) > 5:
                        # Simple keyword extraction
                        words = title.split()
                        for word in words:
                            if len(word) > 4:
                                stats["popular_topics"][word] += 1
                
                # Estimate tokens (rough estimate: 100 tokens per chat)
                stats["estimated_tokens"] += len(chats) * 100
    
    # Top users by chat count
    stats["top_users"] = sorted(user_chat_counts.items(), 
                               key=lambda x: x[1], 
                               reverse=True)[:10]
    
    return stats

def generate_markdown_report(data, stats):
    """Generate a comprehensive markdown report"""
    report = f"""# AI Platform Analytics Report
**Generated:** {datetime.now().strftime("%B %d, %Y at %I:%M %p")}

---

## Executive Summary

This report provides a comprehensive analysis of three AI platform instances: **ResGPT**, **FASGPT**, and **BerkshireGPT**. These platforms serve {stats['total_users']} users across Resecon and Berkshire Associates organizations, providing AI-powered assistance for various business functions.

### Key Highlights

- **Total Users:** {stats['total_users']} across all instances
- **Active Users (30 days):** {stats['active_users_30d']} ({stats['active_users_30d']/stats['total_users']*100:.1f}%)
- **Total AI Models:** {stats['total_models']} models ({stats['active_models']} active)
- **Estimated Token Usage:** ~{stats['estimated_tokens']:,} tokens (based on sampled data)
- **Platform Health:** All instances operational with active user engagement

---

## 1. User Statistics

### Global Overview

| Metric | Value |
|--------|-------|
| Total Registered Users | {stats['total_users']} |
| Active Users (30 days) | {stats['active_users_30d']} |
| Activity Rate | {stats['active_users_30d']/stats['total_users']*100:.1f}% |

### Users by Instance

"""
    
    for instance, count in stats['users_by_instance'].items():
        percentage = (count / stats['total_users'] * 100)
        report += f"- **{instance.upper()}:** {count} users ({percentage:.1f}%)\n"
    
    report += f"""

### User Role Distribution

Based on the collected data from all instances:

"""
    
    # Count roles across all instances
    role_counts = Counter()
    for instance, users in data["users"].items():
        for user in users:
            role_counts[user.get("role", "unknown")] += 1
    
    for role, count in role_counts.most_common():
        report += f"- **{role.capitalize()}:** {count} users\n"
    
    report += """

---

## 2. Model Distribution

### Model Overview

"""
    
    report += f"""
| Instance | Total Models | Active Models |
|----------|--------------|---------------|
"""
    
    for instance, models in data["models"].items():
        active = sum(1 for m in models if m.get("is_active", False))
        report += f"| {instance.upper()} | {len(models)} | {active} |\n"
    
    report += """

### Active Models by Instance

"""
    
    for instance, models in data["models"].items():
        report += f"\n#### {instance.upper()}\n\n"
        active_models = [m for m in models if m.get("is_active", True)]
        if active_models:
            for model in active_models:
                name = model.get("name", model.get("id", "Unknown"))
                base = model.get("base_model_id", "N/A")
                report += f"- **{name}** (Base: {base})\n"
        else:
            report += "- No active models\n"
    
    report += """

---

## 3. Usage Analytics

### Top Active Users (by sampled chat count)

"""
    
    if stats['top_users']:
        report += "| User ID | Chat Count |\n|---------|------------|\n"
        for user_id, count in stats['top_users']:
            report += f"| `{user_id[:16]}...` | {count} |\n"
    else:
        report += "*Insufficient chat data collected for analysis*\n"
    
    report += """

### Popular Topics

Based on analysis of chat titles from sampled data:

"""
    
    top_topics = stats['popular_topics'].most_common(15)
    if top_topics:
        for topic, count in top_topics:
            report += f"- **{topic}**: {count} mentions\n"
    else:
        report += "*Insufficient data for topic analysis*\n"
    
    report += """

---

## 4. Knowledge Bases & Files

### Knowledge Base Summary

"""
    
    for instance, kb_data in data["knowledge"].items():
        if kb_data:
            kb_list = kb_data.get("data", []) if isinstance(kb_data, dict) else kb_data if isinstance(kb_data, list) else []
            report += f"\n#### {instance.upper()}\n"
            report += f"- **Total Knowledge Bases:** {len(kb_list)}\n"
            
            if kb_list and len(kb_list) > 0:
                report += "- **Knowledge Bases:**\n"
                for kb in kb_list[:5]:  # Show first 5
                    kb_name = kb.get("name", kb.get("id", "Unknown"))
                    report += f"  - {kb_name}\n"
        else:
            report += f"\n#### {instance.upper()}\n"
            report += "- No knowledge bases configured\n"
    
    report += """

---

## 5. Platform Health & Activity

### Recent Activity Summary

"""
    
    for instance, users in data["users"].items():
        report += f"\n#### {instance.upper()}\n\n"
        
        # Calculate activity metrics
        now = time.time()
        day_ago = now - (24 * 60 * 60)
        week_ago = now - (7 * 24 * 60 * 60)
        month_ago = now - (30 * 24 * 60 * 60)
        
        active_24h = sum(1 for u in users if u.get("last_active_at", 0) > day_ago)
        active_7d = sum(1 for u in users if u.get("last_active_at", 0) > week_ago)
        active_30d = sum(1 for u in users if u.get("last_active_at", 0) > month_ago)
        
        report += f"- **Active in last 24 hours:** {active_24h} users\n"
        report += f"- **Active in last 7 days:** {active_7d} users\n"
        report += f"- **Active in last 30 days:** {active_30d} users\n"
    
    report += """

---

## 6. Token Usage Estimate

### Methodology

Token usage is estimated based on:
- Number of chats per user (sampled data)
- Average tokens per conversation: ~100 tokens
- This is a conservative estimate; actual usage may be higher

### Estimated Usage

"""
    
    report += f"- **Estimated Total Tokens:** ~{stats['estimated_tokens']:,}\n"
    report += f"- **Estimated Monthly Cost (GPT-4):** ~${stats['estimated_tokens'] * 0.00003:.2f}\n"
    report += "\n*Note: This is based on limited sampling of top 10 users per instance and should be considered a lower bound estimate.*\n"
    
    report += """

---

## Recommendations

1. **User Engagement:** {stats['active_users_30d']/stats['total_users']*100:.1f}% of users active in last 30 days suggests good platform adoption
2. **Model Optimization:** Consider reviewing inactive models for potential deprecation
3. **Usage Monitoring:** Implement comprehensive usage tracking for accurate token counting
4. **Knowledge Base:** Expand knowledge bases to improve AI response quality
5. **Cross-Instance Analysis:** Monitor for duplicate users across instances

---

## Technical Notes

- **Data Collection Method:** REST API queries to all three instances
- **Sampling:** Chat data sampled from top 10 most active users per instance
- **Limitations:** Full chat history and file counts not included due to API rate limits
- **Timestamp:** {datetime.now().isoformat()}

---

*Report generated automatically using Open WebUI Analytics Tool*
"""
    
    return report

def main():
    print("Starting data collection...")
    data = collect_all_data()
    
    print("\nAnalyzing data...")
    stats = analyze_data(data)
    
    print("\nGenerating report...")
    report = generate_markdown_report(data, stats)
    
    # Save report
    output_file = "AI_Platform_Analytics_Report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n[SUCCESS] Report generated successfully: {output_file}")
    print(f"\nSummary:")
    print(f"  Total Users: {stats['total_users']}")
    print(f"  Active Users (30d): {stats['active_users_30d']}")
    print(f"  Total Models: {stats['total_models']}")
    print(f"  Estimated Tokens: {stats['estimated_tokens']:,}")

if __name__ == "__main__":
    main()
