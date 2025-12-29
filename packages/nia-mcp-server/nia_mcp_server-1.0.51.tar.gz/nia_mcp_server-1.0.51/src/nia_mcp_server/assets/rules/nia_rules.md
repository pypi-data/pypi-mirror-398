# Nia Knowledge Agent Integration Rules

## Overview
These rules guide AI assistants in effectively using Nia's knowledge search capabilities for codebase analysis, documentation search, and AI-powered research.

Note: Nia is just "Nia" - not an acronym. It's the name of the knowledge search platform.

## Core Principles

### 1. Repository Management
- **Always check indexed repositories** before searching with `list_repositories`
- **Proactively suggest indexing** when users mention GitHub repositories
- **Monitor indexing status** using `check_repository_status` for ongoing operations
- **Index relevant repositories** discovered during web searches

### 2. Search Strategy Selection

#### Use `nia_web_search` for:
- Finding specific repositories or documentation
- Quick lookups and discovery tasks
- Trending content searches
- Finding similar content to a known URL
- Simple, direct queries

#### Use `nia_deep_research_agent` for:
- Comparative analysis (X vs Y vs Z)
- Evaluating pros and cons
- Complex questions requiring synthesis
- Structured output needs (tables, lists)
- Questions with "best", "which is better", "compare"

### 3. Repository Identifier Formats

#### Understanding Repository Paths
When using `search_codebase`, repositories can be specified in different formats:

1. **Full Repository Format**: `owner/repo`
   - Example: `facebook/react`
   - Use this when the entire repository was indexed

2. **Folder-Specific Format**: `owner/repo/tree/branch/folder`
   - Example: `PostHog/posthog/tree/master/docs`
   - Use this EXACT format when a specific folder was indexed
   - This format appears in `list_repositories` output - copy it exactly!

#### Important Rules:
- **Always check `list_repositories` first** to see the exact format
- **Copy the repository identifier exactly** as shown in the list
- **Don't modify folder paths** - if it shows `owner/repo/tree/branch/folder`, use that exact string
- **Don't assume** - a repository indexed as a folder won't work with just `owner/repo`

#### Examples:
```python
# Wrong - trying to use base repo when folder was indexed
search_codebase("What is Flox?", ["PostHog/posthog"])  # ❌ Won't find folder-indexed content

# Right - using exact format from list_repositories
search_codebase("What is Flox?", ["PostHog/posthog/tree/master/docs"])  # ✅ Searches the indexed folder

# Wrong - modifying the path
search_codebase("LLM guide", ["mcp-use/mcp-use/docs"])  # ❌ Missing /tree/main/ part

# Right - exact format
search_codebase("LLM guide", ["mcp-use/mcp-use/tree/main/docs"])  # ✅ Correct format
```

### 4. Query Optimization
- **Use natural language queries** - Form complete questions, not just keywords
- **Be specific and detailed** - "How does authentication work in NextAuth.js?" not "auth nextauth"
- **Include context** - Mention specific technologies, frameworks, or use cases
- **Leverage repository context** - Specify repositories when searching indexed codebases

### 5. API Usage Best Practices
- **Handle rate limits gracefully** - Free tier has 3 indexing operations limit
- **Cache results mentally** - Avoid redundant searches in the same conversation
- **Batch operations** - Index multiple related repositories together
- **Monitor status efficiently** - Check status periodically, not continuously

### 6. Result Interpretation
- **Provide actionable next steps** - Always suggest how to use the results
- **Extract indexable content** - Identify repositories and docs from search results
- **Format for readability** - Use markdown formatting for clear presentation
- **Include sources** - Always show where information comes from

### 7. Error Handling
- **Explain API limits clearly** - Help users understand free tier limitations
- **Suggest alternatives** - Provide workarounds when hitting limits
- **Report issues helpfully** - Include enough context for debugging
- **Guide to solutions** - Link to upgrade options when appropriate

## Workflow Patterns

### Pattern 1: New Project Research
1. Use `nia_deep_research_agent` to understand the technology landscape
2. Use `nia_web_search` to find specific implementations
3. Index discovered repositories for detailed analysis
4. Search indexed codebases for implementation details

### Pattern 2: Codebase Understanding
1. Check if repository is already indexed with `list_repositories`
   - Note the EXACT repository format shown (especially for folder paths)
   - Example output: "PostHog/posthog/tree/master/docs" (not just "PostHog/posthog")
2. If not indexed, use `index_repository` and wait for completion
3. Use `search_codebase` with specific technical questions
   - Use the EXACT repository identifier from step 1
   - Don't modify or simplify folder paths
4. Include code snippets and file references in responses

### Pattern 3: Documentation Search
1. Index documentation sites with `index_documentation`
   - If no URL patterns specified, default to `["/*"]` for entire site
   - Or ask user: "Which sections should I index? (e.g., /docs/*, /api/*, or /* for everything)"
   - Common patterns: `["/docs/*", "/api/*", "/guide/*", "/reference/*"]`
2. Use URL patterns to focus on relevant sections
3. Search with `search_documentation` for specific topics
4. Combine with code searches for complete understanding

### Pattern 4: Technology Comparison
1. Start with `nia_deep_research_agent` for structured comparison
2. Follow up with `nia_web_search` for specific examples
3. Index key repositories from each option
4. Search codebases to understand implementation differences

## Configuration

### Environment Setup
- **API Key**: Set `NIA_API_KEY` environment variable
- **Never hardcode API keys** in code or configuration files
- **Use .env files** for local development
- **Secure key storage** in production environments

### Project Structure
When initialized, Nia projects should have:
```
.nia/
├── config.json          # Project-specific settings
├── indexed_repos.json   # Track indexed repositories
└── search_history.json  # Cache common queries
```

## Integration Guidelines

### With Version Control
- Add `.nia/cache/` to `.gitignore`
- Commit `.nia/config.json` for team sharing
- Document indexed repositories in README

### With CI/CD
- Set `NIA_API_KEY` as secret environment variable
- Run repository indexing in setup phase
- Cache search results between builds

### With IDEs
- Configure workspace-specific indexed repositories
- Set up quick search shortcuts
- Integrate with code navigation features

## Post-Initialization Guidance

**After using the `initialize_project` tool, ALWAYS ask the user what they'd like to do next. DO NOT take action automatically.**

Ask something like:
> "Nia is now set up for your project! What would you like to do next?
> 
> 1. **Index your current repository** - I can index this codebase for intelligent search
> 2. **Index documentation** - Index docs from frameworks/libraries you're using  
> 3. **Research new technologies** - Use deep research to compare tools and frameworks
> 4. **Search existing repositories** - Find and index repositories related to your project
> 5. **Just chat** - I'm ready to help with any questions using Nia's tools when needed
> 
> What interests you most?"

**Key rules:**
- Always offer options but don't assume what the user wants
- Explain briefly what each option does
- Wait for the user to choose before taking any indexing actions
- Be helpful but not pushy

## Best Practices Summary

1. **Be Proactive** - Suggest indexing relevant content
2. **Be Efficient** - Use the right tool for each query type  
3. **Be Helpful** - Provide clear next steps and context
4. **Be Smart** - Learn from search results to improve future queries
5. **Be Considerate** - Respect API limits and guide users appropriately
6. **Be Patient** - After project initialization, ask what the user wants to do next

Remember: Nia is designed to make AI-powered code and documentation search accessible. Help users unlock its full potential by following these guidelines.