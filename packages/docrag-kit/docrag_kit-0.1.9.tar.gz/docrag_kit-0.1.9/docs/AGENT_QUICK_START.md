# Quick Start Guide for AI Agents

This guide helps AI agents quickly understand and use DocRAG Kit tools.

## TL;DR

Two search tools available:
- **`search_docs`**: Fast fragments (1s, no tokens) → Use first
- **`answer_question`**: Full answer (3-5s, uses tokens) → Use for complex questions

## Quick Decision

```
Need quick lookup? → search_docs
Need explanation? → answer_question
```

## Tool Comparison

| Feature | search_docs | answer_question |
|---------|-------------|-----------------|
| Speed | ~1 second | ~3-5 seconds |
| Tokens | 0 | Uses tokens |
| Output | Raw fragments | Synthesized answer |
| Sources | Always included | Optional |
| Best for | Quick lookups | Complex questions |

## Basic Usage

### Fast Search (Recommended First)

```python
search_docs(
    question="deployment process",
    max_results=3  # optional, default: 3
)
```

**Returns**:
```
🔍 Found 3 relevant document(s):

--- Result 1 ---
📄 Source: docs/DEPLOYMENT.md

To deploy the application:
1. Run npm run build
2. Execute ./deploy.sh
...
```

### Comprehensive Answer

```python
answer_question(
    question="How do I deploy this project?",
    include_sources=True  # optional, default: true
)
```

**Returns**:
```
The deployment process consists of three steps:
1. Build the application using npm run build
2. Run tests with npm test
3. Deploy using ./deploy.sh

Sources:
  • docs/DEPLOYMENT.md
  • README.md
```

## Common Patterns

### Pattern 1: Quick Lookup
```python
# Find specific information fast
result = search_docs(question="API endpoint", max_results=2)
# Read fragments, extract what you need
```

### Pattern 2: Progressive Search
```python
# Start fast
fragments = search_docs(question="authentication", max_results=3)

# If not enough, get full answer
if need_more_detail:
    answer = answer_question(question="How does authentication work?")
```

### Pattern 3: Exploration
```python
# See what's available
docs = list_indexed_docs()

# Search specific topic
result = search_docs(question="configuration", max_results=5)
```

## When to Use Each Tool

### Use `search_docs` when:
- Looking for specific code/config examples
- Need exact quotes from documentation
- Want to read and interpret yourself
- Speed is important
- Want to save tokens

### Use `answer_question` when:
- Need explanation, not just facts
- Question requires synthesis from multiple sources
- Want a direct answer
- Need context and reasoning

## Error Handling

Both tools return clear error messages:

```
Question cannot be empty
Vector database not found. Run 'docrag index' first.
OpenAI API key not found. Add OPENAI_API_KEY to .env file.
```

If you get an error:
1. Check documentation is indexed: `list_indexed_docs()`
2. Verify API keys are configured
3. Try rephrasing the question

## Performance Tips

### Save Tokens
```python
# Expensive: Always using answer_question
answer = answer_question(question="simple lookup")

# Efficient: Use search_docs first
fragments = search_docs(question="simple lookup", max_results=2)
# Only use answer_question if fragments aren't enough
```

### Adjust Results
```python
# Quick check: 1 result
search_docs(question="topic", max_results=1)

# Standard: 3 results (default)
search_docs(question="topic")

# Comprehensive: 5-10 results
search_docs(question="topic", max_results=7)
```

## Examples

### Example 1: Find Configuration
```python
# Fast: Get config examples
search_docs(question="database configuration", max_results=2)

# Output: Raw config snippets from docs
```

### Example 2: Understand Process
```python
# Comprehensive: Get explained workflow
answer_question(question="What is the CI/CD pipeline?")

# Output: Synthesized explanation with sources
```

### Example 3: Troubleshooting
```python
# Fast: Find error mentions
search_docs(question="connection timeout", max_results=3)

# If needed: Get troubleshooting steps
answer_question(question="How to fix connection timeout?")
```

## Best Practices

1. **Start with `search_docs`** - It's faster and free
2. **Use `max_results=1-3`** for quick checks
3. **Use `max_results=5-10`** for comprehensive search
4. **Switch to `answer_question`** only when needed
5. **Combine tools** for best results

## Full Documentation

For detailed information:
- **Tool usage guide**: `.kiro/steering/docrag-tools-usage.md`
- **MCP integration**: `docs/MCP_INTEGRATION.md`
- **Examples**: `docs/EXAMPLES.md`

## Summary

```
Quick lookup → search_docs (fast, free)
Complex question → answer_question (slow, uses tokens)
Exploration → list_indexed_docs + search_docs
```

Start with `search_docs`, escalate to `answer_question` only when needed.
