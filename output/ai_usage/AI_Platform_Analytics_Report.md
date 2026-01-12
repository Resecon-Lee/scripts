# AI Platform Analytics Report
**Generated:** November 13, 2025 at 03:59 PM

---

## Executive Summary

This report provides a comprehensive analysis of three AI platform instances: **ResGPT**, **FASGPT**, and **BerkshireGPT**. These platforms serve 91 users across Resecon and Berkshire Associates organizations, providing AI-powered assistance for various business functions.

### Key Highlights

- **Total Users:** 91 across all instances
- **Active Users (30 days):** 59 (64.8%)
- **Total AI Models:** 0 models (0 active)
- **Estimated Token Usage:** ~70,300 tokens (based on sampled data)
- **Platform Health:** All instances operational with active user engagement

---

## 1. User Statistics

### Global Overview

| Metric | Value |
|--------|-------|
| Total Registered Users | 91 |
| Active Users (30 days) | 59 |
| Activity Rate | 64.8% |

### Users by Instance

- **RESGPT:** 38 users (41.8%)
- **FASGPT:** 38 users (41.8%)
- **BERKSHIREGPT:** 15 users (16.5%)


### User Role Distribution

Based on the collected data from all instances:

- **User:** 80 users
- **Admin:** 9 users
- **Pending:** 2 users


---

## 2. Model Distribution

### Model Overview


| Instance | Total Models | Active Models |
|----------|--------------|---------------|


### Active Models by Instance



---

## 3. Usage Analytics

### Top Active Users (by sampled chat count)

| User ID | Chat Count |
|---------|------------|
| `06032998-f9b9-46...` | 60 |
| `f7688c45-b147-49...` | 60 |
| `a97f0a59-ff32-4e...` | 60 |
| `3682f48b-091b-40...` | 60 |
| `3f689aae-639e-4a...` | 60 |
| `bf6b60e9-2c8e-40...` | 59 |
| `e430c047-5b5e-4b...` | 38 |
| `2c4be3d1-98a7-4d...` | 32 |
| `538ef6e2-c1ed-4d...` | 29 |
| `243f353a-cc0c-42...` | 29 |


### Popular Topics

Based on analysis of chat titles from sampled data:

- **analysis**: 123 mentions
- **overview**: 53 mentions
- **workforce**: 51 mentions
- **employee**: 37 mentions
- **summary**: 34 mentions
- **employment**: 25 mentions
- **report**: 24 mentions
- **count**: 23 mentions
- **clone**: 23 mentions
- **article**: 20 mentions
- **extraction**: 19 mentions
- **comparison**: 19 mentions
- **review**: 19 mentions
- **analytics**: 19 mentions
- **deposition**: 17 mentions


---

## 4. Knowledge Bases & Files

### Knowledge Base Summary


#### RESGPT
- **Total Knowledge Bases:** 13
- **Knowledge Bases:**
  - TEST 3
  - Test
  - test  2
  - Seattle CBA Produced 1.1
  - Seattle CBA Originals deDuped

#### FASGPT
- **Total Knowledge Bases:** 45
- **Knowledge Bases:**
  - Marketing email
  - LA Valuation RFP 
  - Project Charge
  - LDR EXCEL
  - Training

#### BERKSHIREGPT
- **Total Knowledge Bases:** 9
- **Knowledge Bases:**
  - Lee Dev
  - Executive Summary
  - Data checks
  - Data Checks
  - Data Cleanup Testing


---

## 5. Platform Health & Activity

### Recent Activity Summary


#### RESGPT

- **Active in last 24 hours:** 6 users
- **Active in last 7 days:** 12 users
- **Active in last 30 days:** 17 users

#### FASGPT

- **Active in last 24 hours:** 11 users
- **Active in last 7 days:** 17 users
- **Active in last 30 days:** 30 users

#### BERKSHIREGPT

- **Active in last 24 hours:** 1 users
- **Active in last 7 days:** 6 users
- **Active in last 30 days:** 12 users


---

## 6. Token Usage Estimate

### Methodology

Token usage is estimated based on:
- Number of chats per user (sampled data)
- Average tokens per conversation: ~100 tokens
- This is a conservative estimate; actual usage may be higher

### Estimated Usage

- **Estimated Total Tokens:** ~70,300
- **Estimated Monthly Cost (GPT-4):** ~$2.11

*Note: This is based on limited sampling of top 10 users per instance and should be considered a lower bound estimate.*


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
