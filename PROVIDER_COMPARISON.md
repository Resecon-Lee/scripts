# LLM Provider Comparison for University Contact Finder

## Quick Recommendation

**🏆 Best Overall: Perplexity**
- Built-in web search (no separate API needed)
- Most accurate for current information
- Cost-effective ($0.50-$2 per 100 universities)
- Easy setup

---

## Detailed Comparison

### 1. Perplexity (Recommended)

**Model:** `llama-3.1-sonar-large-128k-online`

**Pros:**
- ✅ Built-in web search (no separate search API needed)
- ✅ Most accurate for finding current contact info
- ✅ Specifically designed for research tasks
- ✅ Good citation/source tracking
- ✅ Cost-effective
- ✅ Simple setup (only one API key needed)

**Cons:**
- ❌ Newer service (less established than OpenAI/Anthropic)
- ❌ Smaller model selection

**Cost per 100 universities:**
- $0.50 - $2.00

**Best for:**
- Most users (recommended default)
- When you want accuracy and simplicity
- When you want to minimize setup complexity

**Setup:**
```powershell
# 1. Get API key from https://www.perplexity.ai/settings/api
# 2. Add to .env: PERPLEXITY_API_KEY=pplx-...
# 3. Run:
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity
```

---

### 2. OpenAI (GPT-4o-mini or GPT-4)

**Models:**
- `gpt-4o-mini` (recommended, cost-effective)
- `gpt-4o` (higher quality, more expensive)

**Pros:**
- ✅ Well-established, reliable service
- ✅ Excellent JSON extraction
- ✅ Good reasoning for complex cases
- ✅ Multiple model options
- ✅ Fast response times

**Cons:**
- ❌ Requires separate search API (Tavily, Brave, etc.)
- ❌ More expensive than Perplexity
- ❌ Two APIs to manage

**Cost per 100 universities:**
- GPT-4o-mini + Tavily: $1.00 - $3.00
- GPT-4o + Tavily: $5.00 - $15.00

**Best for:**
- Users already with OpenAI accounts
- When you need specific GPT-4 capabilities
- Production environments with existing OpenAI infrastructure

**Setup:**
```powershell
# 1. Get OpenAI key: https://platform.openai.com/api-keys
# 2. Get Tavily key: https://tavily.com
# 3. Add to .env:
#    OPENAI_API_KEY=sk-...
#    TAVILY_API_KEY=tvly-...
# 4. Run:
python university_contact_finder.py input.xlsx output.xlsx --provider openai --search-api tavily
```

---

### 3. Anthropic Claude

**Model:** `claude-3-5-sonnet-20241022`

**Pros:**
- ✅ Excellent at structured data extraction
- ✅ Very good reasoning and accuracy
- ✅ Strong at handling ambiguous information
- ✅ Good at following complex instructions
- ✅ Latest models very competitive

**Cons:**
- ❌ Requires separate search API
- ❌ More expensive than OpenAI/Perplexity
- ❌ Slightly slower response times
- ❌ Two APIs to manage

**Cost per 100 universities:**
- Claude Sonnet + Tavily: $3.00 - $8.00

**Best for:**
- Users already with Claude accounts
- When you need highest quality extraction
- Complex extraction scenarios
- When accuracy is more important than cost

**Setup:**
```powershell
# 1. Get Claude key: https://console.anthropic.com/
# 2. Get Tavily key: https://tavily.com
# 3. Add to .env:
#    ANTHROPIC_API_KEY=sk-ant-...
#    TAVILY_API_KEY=tvly-...
# 4. Run:
python university_contact_finder.py input.xlsx output.xlsx --provider anthropic --search-api tavily
```

---

### 4. Ollama (Local, Free)

**Models:**
- `llama3.1:8b` (recommended)
- `llama3.1:70b` (better quality, much slower)
- `mistral:7b` (alternative)

**Pros:**
- ✅ Completely free for LLM processing
- ✅ No usage limits
- ✅ Privacy (runs locally)
- ✅ No API key needed for LLM
- ✅ Good for development/testing

**Cons:**
- ❌ Still need paid search API (Tavily, Brave, etc.)
- ❌ Slower (especially on CPU)
- ❌ Lower accuracy than commercial models
- ❌ Requires local setup and resources
- ❌ Need decent hardware (8GB+ RAM recommended)

**Cost per 100 universities:**
- Free (LLM) + $0.50-$2.00 (search API)
- Or free if using free search API tiers

**Best for:**
- Testing and development
- When you have many universities (1000+)
- Privacy-sensitive applications
- Users with good local hardware
- Learning and experimentation

**Setup:**
```powershell
# 1. Install Ollama: https://ollama.ai/
# 2. Pull model:
ollama pull llama3.1:8b
# 3. Start Ollama:
ollama serve
# 4. Get Tavily key (optional): https://tavily.com
# 5. Add to .env (if using Tavily):
#    TAVILY_API_KEY=tvly-...
# 6. Run:
python university_contact_finder.py input.xlsx output.xlsx --provider ollama --search-api tavily
```

---

## Search API Comparison

If not using Perplexity, you'll need a search API:

### Tavily (Recommended)
- ✅ Designed for AI/LLM use
- ✅ Clean, structured results
- ✅ 1,000 free searches/month
- ✅ Good for research
- Cost: Free tier or $0.001/search
- https://tavily.com

### Brave Search
- ✅ Privacy-focused
- ✅ 2,000 free queries/month
- ✅ Good coverage
- Cost: Free tier or $0.001/search
- https://brave.com/search/api/

### SerpAPI (Google)
- ✅ Google search results
- ✅ Comprehensive
- ❌ Only 100 free searches/month
- ❌ More expensive
- Cost: $0.002/search
- https://serpapi.com

---

## Decision Matrix

| Use Case | Recommended Provider | Why |
|----------|---------------------|-----|
| **Getting started** | Perplexity | Simplest setup, one API key |
| **Best accuracy** | Perplexity or Claude | Built-in search or best extraction |
| **Lowest cost (small scale)** | Perplexity | $0.50-$2 per 100 |
| **Lowest cost (large scale)** | Ollama + free search | Free LLM, use free API tiers |
| **Already have OpenAI** | OpenAI + Tavily | Use existing account |
| **Privacy sensitive** | Ollama | Runs locally |
| **Production/reliable** | Perplexity or OpenAI | Established services |
| **Testing/development** | Ollama | Free, unlimited local testing |

---

## Speed Comparison

Approximate time per university:

| Provider | Speed |
|----------|-------|
| Perplexity | 2-3 seconds |
| OpenAI + Tavily | 3-5 seconds |
| Claude + Tavily | 4-6 seconds |
| Ollama (8B) + Tavily | 5-10 seconds |
| Ollama (70B) + Tavily | 20-60 seconds |

*Times vary based on internet speed, API load, and hardware*

---

## Quality Comparison

Based on typical contact extraction accuracy:

| Provider | Accuracy | Notes |
|----------|----------|-------|
| Perplexity | ⭐⭐⭐⭐⭐ | Excellent for current info |
| Claude Sonnet | ⭐⭐⭐⭐⭐ | Best structured extraction |
| GPT-4o | ⭐⭐⭐⭐⭐ | Excellent overall |
| GPT-4o-mini | ⭐⭐⭐⭐ | Very good, cost-effective |
| Ollama (llama3.1:70b) | ⭐⭐⭐⭐ | Good with more retries |
| Ollama (llama3.1:8b) | ⭐⭐⭐ | Decent, may miss details |

---

## Final Recommendation

**For most users:**
```powershell
# Use Perplexity - best balance of accuracy, cost, and simplicity
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity
```

**For budget-conscious (small scale < 100 universities):**
```powershell
# Use Perplexity - still cheapest overall
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity
```

**For large scale (1000+ universities):**
```powershell
# Use Ollama with free Tavily tier
python university_contact_finder.py input.xlsx output.xlsx --provider ollama --search-api tavily
```

**For maximum accuracy:**
```powershell
# Use Claude Sonnet
python university_contact_finder.py input.xlsx output.xlsx --provider anthropic --search-api tavily
```

---

## Mixing Providers

You can use different providers for different batches:

```powershell
# Process first 50 with Perplexity (fast)
python university_contact_finder.py input.xlsx output.xlsx --provider perplexity --max 50

# Process next 50 with Claude (higher accuracy) starting from row 50
python university_contact_finder.py input.xlsx output.xlsx --provider anthropic --start-row 50 --max 50

# Process remaining with Ollama (free) starting from row 100
python university_contact_finder.py input.xlsx output.xlsx --provider ollama --start-row 100
```

This lets you optimize for cost vs accuracy based on your needs!
