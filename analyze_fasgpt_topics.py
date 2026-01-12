import requests
import json
from collections import Counter

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
            return response.json()
        else:
            return []
    except Exception as e:
        print(f"Exception fetching chats for user {user_id}: {e}")
        return []

def analyze_topics():
    """Analyze chat topics from FASGPT"""
    print("Fetching FASGPT users...")
    users = fetch_users()

    if not users:
        print("No users found")
        return

    # Sort users by last_active_at
    active_users = sorted(users, key=lambda x: x.get("last_active_at", 0), reverse=True)
    print(f"Total users: {len(users)}")
    print(f"Analyzing top 20 most active users...")

    # Analyze top 20 users
    topic_counter = Counter()
    all_chat_titles = []
    total_chats = 0
    user_chat_counts = []

    for i, user in enumerate(active_users[:20]):
        user_id = user["id"]
        user_name = user.get("name", "Unknown")

        print(f"  [{i+1}/20] {user_name}...", end="")

        chats = fetch_user_chats(user_id)
        if isinstance(chats, list):
            chat_count = len(chats)
            total_chats += chat_count
            user_chat_counts.append((user_name, chat_count))
            print(f" {chat_count} chats")

            # Analyze chat titles
            for chat in chats:
                title = chat.get("title", "").lower().strip()
                if title and len(title) > 3:
                    all_chat_titles.append(title)

                    # Extract keywords (words longer than 4 characters)
                    words = title.split()
                    for word in words:
                        # Clean word
                        word = word.strip('.,!?:;()[]{}\"\'')
                        if len(word) > 4 and word.isalpha():
                            topic_counter[word] += 1
        else:
            print(" no chats")

    print(f"\n{'='*60}")
    print(f"FASGPT Topic Analysis Results")
    print(f"{'='*60}")
    print(f"Total chats analyzed: {total_chats}")
    print(f"Unique chat titles: {len(all_chat_titles)}")

    print(f"\n{'='*60}")
    print("Top 30 Most Popular Topics (by keyword frequency):")
    print(f"{'='*60}")

    for i, (topic, count) in enumerate(topic_counter.most_common(30), 1):
        print(f"{i:2}. {topic:20} - {count:3} mentions")

    print(f"\n{'='*60}")
    print("Top 10 Most Active Users:")
    print(f"{'='*60}")

    for i, (name, count) in enumerate(sorted(user_chat_counts, key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"{i:2}. {name:30} - {count:3} chats")

    # Save detailed results to file first (before printing titles with special chars)
    output_file = "FASGPT_Topic_Analysis.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("FASGPT Detailed Topic Analysis\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Total chats analyzed: {total_chats}\n")
        f.write(f"Unique chat titles: {len(all_chat_titles)}\n\n")

        f.write("=" * 60 + "\n")
        f.write("Top 50 Topics:\n")
        f.write("=" * 60 + "\n")
        for i, (topic, count) in enumerate(topic_counter.most_common(50), 1):
            f.write(f"{i:2}. {topic:25} - {count:3} mentions\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("All Chat Titles:\n")
        f.write("=" * 60 + "\n")
        for i, title in enumerate(all_chat_titles, 1):
            f.write(f"{i:4}. {title}\n")

    print(f"\n[SUCCESS] Detailed results saved to: {output_file}")

    # Print sample titles (with error handling for unicode)
    print(f"\n{'='*60}")
    print("Sample Chat Titles (first 20):")
    print(f"{'='*60}")

    for i, title in enumerate(all_chat_titles[:20], 1):
        try:
            print(f"{i:2}. {title}")
        except UnicodeEncodeError:
            # Replace problematic characters
            safe_title = title.encode('ascii', 'replace').decode('ascii')
            print(f"{i:2}. {safe_title}")

if __name__ == "__main__":
    analyze_topics()
