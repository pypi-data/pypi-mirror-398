# NIA Integration for Visual Studio Code

## VSCode-Specific Configuration

### 1. Workspace Settings
Configure `.vscode/settings.json` for NIA integration:

```json
{
  "nia.defaultRepositories": [
    "owner/main-project",
    "owner/dependency-lib"
  ],
  "nia.searchHistory": true,
  "nia.autoIndex": {
    "enabled": true,
    "patterns": ["github.com/*/*"]
  },
  "nia.apiEndpoint": "https://api.trynia.ai",
  "nia.cacheTimeout": 3600
}
```

### 2. Tasks Configuration
Set up `.vscode/tasks.json` for common NIA operations:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "NIA: Index Current Repository",
      "type": "shell",
      "command": "echo 'index_repository ${workspaceFolder}'",
      "problemMatcher": []
    },
    {
      "label": "NIA: List Indexed Repositories",
      "type": "shell",
      "command": "echo 'list_repositories'",
      "problemMatcher": []
    },
    {
      "label": "NIA: Search Codebase",
      "type": "shell",
      "command": "echo 'search_codebase \"${input:searchQuery}\"'",
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "searchQuery",
      "type": "promptString",
      "description": "Enter your search query"
    }
  ]
}
```

### 3. Code Snippets
Add to `.vscode/nia.code-snippets`:

```json
{
  "Nia Index Repository": {
    "prefix": "nia-index",
    "body": [
      "index_repository ${1:https://github.com/owner/repo}"
    ],
    "description": "Index a repository with Nia"
  },
  "Nia Search Code": {
    "prefix": "nia-search",
    "body": [
      "search_codebase \"${1:How does authentication work?}\""
    ],
    "description": "Search indexed codebases"
  },
  "Nia Web Search": {
    "prefix": "nia-web",
    "body": [
      "nia_web_search \"${1:find RAG implementation libraries}\""
    ],
    "description": "Search the web with Nia"
  },
  "Nia Deep Research": {
    "prefix": "nia-research",
    "body": [
      "nia_deep_research_agent \"${1:compare X vs Y for use case}\""
    ],
    "description": "Perform deep research analysis"
  }
}
```

### 4. Launch Configuration
Configure `.vscode/launch.json` for debugging with NIA context:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug with NIA Context",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/index.js",
      "env": {
        "NIA_API_KEY": "${env:NIA_API_KEY}",
        "NIA_INDEXED_REPOS": "${workspaceFolder}/.nia/indexed_repos.json"
      }
    }
  ]
}
```

### 5. Extensions Recommendations
Add to `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "github.copilot",
    "continue.continue",
    "codeium.codeium"
  ]
}
```

## VSCode Command Palette Integration

### Quick Commands
Access via `Cmd/Ctrl + Shift + P`:

1. **Nia: Index This Repository**
   - Automatically indexes the current workspace
   - Shows progress in status bar
   - Notifies when complete

2. **Nia: Search Symbol**
   - Search for functions, classes, or variables
   - Across all indexed repositories
   - Jump to definition support

3. **Nia: Explain Code**
   - Select code and search for explanations
   - Find similar implementations
   - Understand patterns

4. **Nia: Find Examples**
   - Search for usage examples
   - Filter by language or framework
   - Copy-paste ready snippets

## VSCode-Specific Workflows

### 1. Project Onboarding
When opening a new project:
```
1. Check if repo is indexed: list_repositories
2. If not, index it: index_repository [current repo]
3. Index related dependencies
4. Search for architecture overview
5. Create workspace documentation
```

### 2. Code Review Assistance
During code reviews:
```
1. Search for similar patterns in indexed repos
2. Find best practices for the specific feature
3. Check for common pitfalls
4. Suggest improvements based on examples
```

### 3. Debugging Workflow
When debugging issues:
```
1. Search for error messages across repos
2. Find similar bug fixes
3. Understand the problematic code context
4. Search for test cases
```

### 4. Learning & Documentation
For learning new codebases:
```
1. Index the main repository
2. Search for entry points (main, index, app)
3. Understand the architecture
4. Find example usage patterns
```

## Terminal Integration

### Integrated Terminal Commands
Use in VSCode's integrated terminal:

```bash
# Quick index
alias nia-index='echo "index_repository $(git remote get-url origin)"'

# Search current project
alias nia-search='echo "search_codebase"'

# List all indexed
alias nia-list='echo "list_repositories"'
```

### PowerShell Functions
For Windows users in `.vscode/powershell_profile.ps1`:

```powershell
function Nia-Index {
    param($repo)
    Write-Host "index_repository $repo"
}

function Nia-Search {
    param($query)
    Write-Host "search_codebase `"$query`""
}
```

## Output Formatting for VSCode

### 1. File References
Format as clickable links:
```
📁 authentication/middleware.ts:45
📁 lib/auth/session.ts:23-67
📁 pages/api/auth/[...nextauth].ts:12
```

### 2. Code Blocks
Use proper syntax highlighting:
```typescript
// From: lib/auth/session.ts
export async function getSession(req: Request) {
  // Implementation details
}
```

### 3. Problem Markers
For issues found during search:
```
⚠️ Warning: Deprecated pattern found
   File: utils/oldAuth.js:34
   Suggestion: Use new auth method

❌ Error: Security vulnerability
   File: api/user.js:56
   Fix: Validate input parameters
```

## Keyboard Shortcuts
Suggested keybindings for `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+n i",
    "command": "workbench.action.terminal.sendSequence",
    "args": { "text": "index_repository " }
  },
  {
    "key": "ctrl+shift+n s",
    "command": "workbench.action.terminal.sendSequence",
    "args": { "text": "search_codebase \"" }
  },
  {
    "key": "ctrl+shift+n l",
    "command": "workbench.action.terminal.sendSequence",
    "args": { "text": "list_repositories\n" }
  }
]
```

## Performance Optimization

### 1. Workspace-Specific Cache
Store frequently searched queries:
```
.vscode/.nia-cache/
├── search-results.json
├── indexed-files.json
└── common-queries.json
```

### 2. Search Filters
Use repository context for faster searches:
```
search_codebase "authentication" repositories=["current-project"]
```

### 3. Batch Operations
Index related repositories together:
```
index_repository repo1
index_repository repo2
index_repository repo3
```

### 4. Documentation Indexing
When indexing documentation:
- If user provides just a URL without patterns, use `["/*"]` to index everything
- Or ask: "Should I index the entire documentation or specific sections?"
- Common patterns: `["/docs/*", "/api/*", "/guide/*", "/reference/*"]`
- Example: `index_documentation "https://docs.example.com" ["/*"]`
- Can index multiple doc sites for comprehensive searches

Remember: Make Nia feel like a native part of the VSCode experience!