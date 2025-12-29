# Nia MCP Tool Usage Guide

Note: Nia is just "Nia" - not an acronym or "Neural Intelligent Assistant".

## When to use each tool:

### `list_repositories`
Use when:
- User asks what repos are available/indexed
- Before searching to verify repo is indexed
- User wants to see their indexed codebase list

### `index_repository`
Use when:
- User mentions a GitHub URL
- User wants to analyze a specific codebase
- Before searching a new repository

### `search_codebase`
Use when:
- User asks how something works in code
- User wants to find specific implementations
- User needs to understand code patterns
- Searching within indexed repositories only

### `search_documentation` 
Use when:
- User asks about documentation
- Looking for API references
- Searching indexed documentation sites

### `nia_web_search`
Use when:
- Finding new repositories to index
- Quick discovery of libraries/frameworks
- Simple, direct searches
- Looking for trending content

### `nia_deep_research_agent`
Use when:
- Comparing multiple options (X vs Y)
- Need structured analysis
- Complex questions requiring synthesis
- Evaluating pros/cons

### `check_repository_status`
Use when:
- After starting indexing
- User asks about indexing progress
- Verifying if indexing completed

### `index_documentation`
Use when:
- User wants to index documentation sites
- User provides a documentation URL

**Important**: If user doesn't specify URL patterns:
- Default to `["/*"]` to index entire site
- Or ask: "Should I index the entire documentation or specific sections?"
- Common patterns: `["/docs/*", "/api/*", "/guide/*"]`

### Other tools:
- `delete_repository` - Remove indexed repo
- `initialize_project` - Set up Nia rules in project