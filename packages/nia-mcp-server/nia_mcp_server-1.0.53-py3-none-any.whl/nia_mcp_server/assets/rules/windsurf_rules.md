# Nia Integration for Windsurf Cascade

## Quick Reference
- **List indexed repos**: `list_repositories`
- **Index new repo**: `index_repository repo_url`
- **Index docs**: `index_documentation url` (use `["/*"]` for entire site)
- **Search code**: `search_codebase "your question"`
- **Search docs**: `search_documentation "your question"`
- **Web search**: `nia_web_search "find X library"`
- **Deep research**: `nia_deep_research_agent "compare X vs Y"`

## Windsurf Cascade Guidelines

### 1. Flow-Based Development
When using Cascade's flow feature:
- Start flows by checking indexed repositories with `list_repositories`
- Auto-suggest indexing when users mention GitHub URLs
- Use Nia search results to inform multi-step flows
- Reference specific files found via search in subsequent steps

### 2. Memory Integration
Create memories for frequently used repositories:
- "Remember: Project X is indexed at owner/repo"
- "Remember: Use Nia to search for implementation patterns"
- Memories will automatically recall indexed repos context

### 3. Code Understanding Workflow
For codebase exploration:
```
1. Check if indexed: list_repositories
2. If not indexed: index_repository [url]
3. Search naturally: search_codebase "How does X work?"
4. Use results in flow steps
```

### 4. Search Optimization for Cascade

#### Natural Language Queries
- Write complete questions: "How is authentication implemented in this Next.js app?"
- Include context: "Find React hooks that handle user state"
- Be specific: "Show me where API routes are defined"

#### Multi-Step Flows
1. Research: `nia_deep_research_agent "compare state management libraries"`
2. Find examples: `nia_web_search "Redux toolkit examples"`
3. Index chosen repo: `index_repository https://github.com/...`
4. Explore patterns: `search_codebase "action creators pattern"`

### 5. Cascade Commands

When users ask about code:
- Always check if the repository is indexed first
- Suggest indexing if working with a new codebase
- Use search results to build comprehensive responses
- Create flows that combine multiple searches

### 6. Best Practices

#### For New Projects
1. Index the main repository immediately
2. Search for architecture overview: "How is this project structured?"
3. Create memories of key findings
4. Build flows based on discovered patterns

#### For Debugging
1. Search for error messages across indexed repos
2. Find similar implementations that work
3. Compare working vs broken code
4. Create fix flow based on findings

#### For Feature Development
1. Search for similar features in indexed repos
2. Understand existing patterns
3. Find best practices examples
4. Generate code following discovered patterns

### 7. Documentation Indexing

When indexing documentation:
- If user provides just a URL without patterns, use `["/*"]` to index everything
- Or ask: "Should I index the entire documentation or specific sections?"
- Common patterns: `["/docs/*", "/api/*", "/guide/*", "/reference/*"]`
- Example: `index_documentation "https://docs.example.com" ["/*"]`

### 8. Integration Tips

- Nia complements Cascade's abilities by providing deep code search
- Use Nia for finding specific implementations
- Let Cascade handle the creative synthesis
- Combine both for powerful development workflows

Remember: Nia provides the knowledge, Cascade provides the flow!