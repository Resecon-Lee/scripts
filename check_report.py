import re

with open('output/ai_usage/BERKSHIREGPT_Report.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find model usage table
table_match = re.search(r'<h3>Model Usage</h3>.*?<tbody>(.*?)</tbody>', content, re.DOTALL)
if table_match:
    entries = re.findall(r'<td>(.*?)</td>', table_match.group(1))
    print("Model table entries (first 30):")
    for i in range(0, min(30, len(entries)), 3):
        if i+2 < len(entries):
            print(f"  {entries[i]} | {entries[i+1]} | {entries[i+2]}")

# Find model distribution chart
chart_match = re.search(r'modelDistributionCtx.*?labels:\s*(\[.*?\]).*?data:\s*(\[.*?\])', content, re.DOTALL)
if chart_match:
    print("\nModel Distribution Chart:")
    print(f"  Labels: {chart_match.group(1)[:200]}...")
    print(f"  Data: {chart_match.group(2)[:200]}...")

# Find key metrics
metrics = re.findall(r'<div class="metric-label">(.*?)</div>.*?<div class="metric-value">(.*?)</div>', content, re.DOTALL)
print("\nKey Metrics:")
for label, value in metrics[:10]:
    label_clean = re.sub(r'<.*?>', '', label).strip()
    value_clean = re.sub(r'<.*?>', '', value).strip()
    print(f"  {label_clean}: {value_clean}")
