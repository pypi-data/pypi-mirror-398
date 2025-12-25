# LLM-Based Commit Classification Guide

This guide explains how to enable and use LLM-based commit classification in GitFlow Analytics to get meaningful commit categorization instead of everything showing up as "Other".

## Quick Start

### 1. Use Enhanced Rule-Based Classification (No API Key Required)

The simplest way to get better commit classification is to use the enhanced rule-based system:

```yaml
# config.yaml
version: "1.0"

repositories:
  - name: "your-repo"
    path: "/path/to/repo"
    project_key: "PROJECT"

analysis:
  weeks: 4
  ml_categorization:
    enabled: true  # This enables enhanced rule-based classification
    
output:
  directory: "reports"
  formats:
    - csv
    - markdown
```

**Run**: `gitflow-analytics -c config.yaml --weeks 4`

### 2. Use LLM Classification (Requires API Key)

For even better accuracy, configure LLM-based classification:

```yaml
# config.yaml  
version: "1.0"

repositories:
  - name: "your-repo"
    path: "/path/to/repo"
    project_key: "PROJECT"

analysis:
  weeks: 4
  
  # LLM-based classification
  llm_classification:
    enabled: true
    api_key: "${OPENROUTER_API_KEY}"  # Set in .env file
    model: "mistralai/mistral-7b-instruct"  # Affordable model
    confidence_threshold: 0.6
    max_daily_requests: 500
    enable_caching: true
    cache_duration_days: 90
    
output:
  directory: "reports"
  formats:
    - csv
    - markdown
```

**Setup**:
1. Get free API key from [OpenRouter.ai](https://openrouter.ai)
2. Create `.env` file: `OPENROUTER_API_KEY=sk-or-your-key-here`
3. Run: `gitflow-analytics -c config.yaml --weeks 4`

## Classification Categories

Both systems classify commits into these categories:

- **Feature**: New functionality (`feat:`, `add:`, `implement:`)
- **Bug Fix**: Fixes and corrections (`fix:`, `bug:`, `hotfix:`)
- **Maintenance**: Configuration, dependencies, refactoring (`chore:`, `refactor:`, `style:`)
- **Content**: Documentation updates (`docs:`, `readme:`)
- **Media**: Images, videos, assets
- **Integration**: APIs, webhooks, external systems
- **Localization**: Translations, i18n

## Results

Instead of seeing **100% "Other"**, you'll see meaningful breakdowns like:

- Bug Fixes: 15 commits (47%)
- Features: 9 commits (28%)
- Maintenance: 8 commits (25%)

## Cost Optimization

The LLM system includes several cost optimization features:

- **Intelligent Caching**: 90-day cache to avoid re-processing
- **Enhanced Fallback**: Uses smart rules when LLM unavailable
- **Rate Limiting**: Configurable daily request limits
- **Short Responses**: 30-token limit to minimize costs
- **Cheap Model**: Mistral-7B costs ~$0.00025 per 1k tokens

## Troubleshooting

### "All commits showing as Other"
- Enable `ml_categorization: enabled: true` in config
- Use the enhanced rule-based classification
- Check commit message format (conventional commits work best)

### "LLM classification not working"
- Verify `OPENROUTER_API_KEY` environment variable
- Check API key has sufficient credits
- Review rate limits in configuration
- System will fall back to enhanced rules automatically

### "Low classification accuracy"  
- Improve commit message quality
- Use conventional commit format (`feat:`, `fix:`, etc.)
- Adjust `confidence_threshold` in configuration
- Consider providing `domain_terms` for your organization

## Example Results

**Before**: 
- Other: 100% (32 commits)

**After**:
- Bug Fixes: 47% (15 commits) 
- Features: 28% (9 commits)
- Maintenance: 25% (8 commits)
- Average Confidence: 90%
- Processing: 0.3ms per commit

## Configuration Reference

### Enhanced Rule-Based (Free)
```yaml
analysis:
  ml_categorization:
    enabled: true
    hybrid_threshold: 0.5
```

### LLM Classification (Paid)
```yaml
analysis:
  llm_classification:
    enabled: true
    api_key: "${OPENROUTER_API_KEY}"
    model: "mistralai/mistral-7b-instruct"
    confidence_threshold: 0.6
    max_tokens: 30
    temperature: 0.1
    max_daily_requests: 500
    enable_caching: true
    cache_duration_days: 90
```

## Sample Configurations

See the provided sample files:
- `config-rule-enhanced-sample.yaml` - Enhanced rules only
- `config-llm-sample.yaml` - Full LLM configuration

Both configurations will give you meaningful commit classification instead of everything being categorized as "Other".