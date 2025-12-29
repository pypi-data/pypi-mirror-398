# Nia Integration for Claude Desktop

## Claude Desktop Configuration

### 1. Project Structure
When Nia is initialized for Claude Desktop, it creates:
```
.claude/
├── nia_config.json      # Nia-specific settings
├── indexed_repos.json   # Tracked repositories
└── search_patterns.json # Common search patterns
```

### 2. Configuration File
Create `.claude/nia_config.json`:

```json
{
  "version": "1.0",
  "defaultBehavior": {
    "autoSuggestIndexing": true,
    "includeSourcesInResponse": true,
    "searchResultLimit": 5,
    "deepResearchTimeout": 300
  },
  "searchPatterns": {
    "architecture": "How is {feature} architected in {repo}?",
    "implementation": "Show me the implementation of {feature}",
    "patterns": "What patterns are used for {concern}?",
    "debugging": "Find similar issues to {error}"
  },
  "workspaceRepos": [],
  "frequentSearches": []
}
```

## Claude-Specific Interaction Patterns

### 1. Conversational Flow
Claude should maintain context naturally:

```
User: "I'm working on a RAG implementation"
Claude: I'll help you with RAG implementation. Let me search for the best examples and patterns.
[Runs: nia_web_search "RAG implementation examples production ready"]

I found several excellent RAG implementations. Would you like me to:
1. Index these repositories for detailed analysis
2. Compare different approaches
3. Search for specific features you need
```

### 2. Proactive Assistance
Anticipate user needs:

- When user mentions a GitHub URL → Suggest indexing
- When user asks about code → Check if repo is indexed first
- When comparing options → Use deep research agent
- When debugging → Search for similar issues

### 3. Context-Aware Responses
Maintain conversation context:

```
First message: User asks about authentication
- Check indexed repos for auth implementations
- Remember this context for follow-ups

Second message: User asks "how about the middleware?"
- Know they mean auth middleware
- Search specifically for middleware in auth context
- Reference previous findings
```

## Claude Desktop Workflows

### 1. Project Understanding
```markdown
When user opens a new project:
1. Detect project type from files
2. Suggest indexing the repository
3. Offer to index related dependencies
4. Provide architecture overview
```

### 2. Code Generation
```markdown
When generating code:
1. Search indexed repos for patterns
2. Use found examples as reference
3. Adapt to project's style
4. Cite sources for transparency
```

### 3. Problem Solving
```markdown
When solving issues:
1. Search for error messages
2. Find similar problems and solutions
3. Understand the context
4. Provide step-by-step fixes
```

### 4. Learning & Teaching
```markdown
When explaining concepts:
1. Use deep research for comprehensive overview
2. Find real-world examples in indexed repos
3. Show implementation variations
4. Explain trade-offs with evidence
```

## Response Formatting for Claude

### 1. Search Results Presentation
```markdown
## 🔍 Found in indexed repositories:

**Authentication Implementation** (nextjs-app-template)
- 📁 `middleware.ts:23-45` - Route protection
- 📁 `lib/auth/session.ts:12-89` - Session management
- 📁 `app/api/auth/route.ts:5-34` - API endpoints

**Key Pattern:** Uses NextAuth with JWT strategy
[Show relevant code snippet]
```

### 2. Code Examples
Always provide context:
```typescript
// From: awesome-saas-starter/lib/auth/session.ts
// This pattern handles refresh tokens elegantly
export async function refreshSession(token: string) {
  // ... implementation
}
// Note: This repo uses Redis for session storage
```

### 3. Comparative Analysis
Structure comparisons clearly:
```markdown
## Comparison: Prisma vs Drizzle ORM

Based on analysis of 15 production repositories:

| Aspect | Prisma | Drizzle |
|--------|--------|---------|
| Type Safety | Excellent (generated) | Excellent (inferred) |
| Performance | Good | Better |
| Learning Curve | Gentle | Steeper |

**Recommendation:** [Based on your use case...]
```

## Advanced Claude Behaviors

### 1. Multi-Step Research
For complex questions:
```
Step 1: Use nia_deep_research_agent for overview
Step 2: Use nia_web_search for specific examples  
Step 3: Index discovered repositories
Step 4: Search indexed repos for details
Step 5: Synthesize findings with citations
```

### 2. Intelligent Caching
Remember within conversation:
- Previously indexed repositories
- Search results from earlier queries
- User's project context
- Technical preferences

### 3. Error Recovery
Handle failures gracefully:
```
If indexing fails:
- Explain the issue clearly
- Suggest alternatives
- Offer to try again later
- Provide manual workarounds
```

### 4. Documentation Indexing
When users want to index documentation:
```
If user provides just a URL:
- Default to indexing entire site with ["/*"]
- Or ask: "Should I index the entire documentation or specific sections?"
- Suggest common patterns: ["/docs/*", "/api/*", "/guide/*"]
- Example: index_documentation "https://docs.example.com" ["/*"]
```

## Claude-Specific Commands

### Quick Actions
Recognize these patterns:

- "Index this" → Index current repository
- "Search for X" → Use appropriate search tool
- "Compare X and Y" → Use deep research
- "Find examples" → Web search then index
- "Explain this code" → Search for patterns

### Batch Operations
Handle multiple requests:
```
User: "Index these repos: A, B, C and then compare their auth systems"
Claude: I'll index all three repositories and then analyze their authentication approaches.
[Runs multiple index_repository commands]
[Waits for completion]
[Runs search_codebase for auth patterns]
[Provides comparative analysis]
```

## Best Practices for Claude

### 1. Natural Language
- Maintain conversational tone
- Explain technical concepts clearly
- Use analogies when helpful
- Avoid jargon unless necessary

### 2. Progressive Disclosure
- Start with overview
- Provide details on request
- Link to deeper resources
- Offer next steps

### 3. Source Attribution
- Always cite repositories
- Include file paths and line numbers
- Link to specific commits when relevant
- Credit original authors

### 4. Learning from Interaction
- Note user preferences
- Adapt search queries based on feedback
- Refine suggestions over time
- Build on previous conversations

## Example Interactions

### Architecture Understanding
```
User: "How does Vercel handle serverless functions?"
Claude: I'll research how Vercel implements serverless functions.

[Runs: nia_deep_research_agent "Vercel serverless functions architecture implementation"]

Based on my research, Vercel's serverless architecture... [comprehensive explanation]

I found several open-source projects that demonstrate this. Shall I index them for deeper analysis?
```

### Code Pattern Search
```
User: "Show me good examples of React Server Components"
Claude: I'll search for production-ready React Server Components examples.

[Runs: nia_web_search "React Server Components production examples 2024"]

I found 5 excellent repositories using RSC. Let me index the most relevant one:

[Runs: index_repository https://github.com/vercel/next-app-router-playground]

Now I can show you specific patterns... [detailed examples]
```

Remember: Make Nia's capabilities feel like a natural extension of Claude's knowledge!