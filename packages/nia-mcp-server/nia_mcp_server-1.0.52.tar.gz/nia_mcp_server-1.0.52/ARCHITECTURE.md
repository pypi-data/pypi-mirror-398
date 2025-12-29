# NIA MCP Server Architecture

## Overview

The NIA MCP Server is a lightweight proxy that enables any MCP-compatible AI assistant to interact with NIA's production API. Users only need their NIA API key to get started.

## Design Principles

1. **Zero Infrastructure**: Users don't need MongoDB, vector stores, or any backend setup
2. **API Key Only**: Single configuration requirement - just the NIA API key
3. **Stateless**: All state is managed by NIA's backend
4. **Lightweight**: Minimal dependencies (mcp, httpx, pydantic)
5. **Universal**: Works with any MCP client (Claude Desktop, Continue, etc.)

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│   MCP Client    │────▶│  NIA MCP Server  │────▶│   NIA API      │
│ (Claude, etc.)  │◀────│   (Local Proxy)  │◀────│  (Production)  │
└─────────────────┘     └──────────────────┘     └────────────────┘
        MCP                    HTTPS                   Backend
     Protocol                Requests               Infrastructure
```

## Components

### 1. MCP Server (`server.py`)
- Implements MCP protocol
- Exposes tools and resources
- Handles async operations
- Manages API client lifecycle

### 2. API Client (`api_client.py`)
- HTTP client for NIA's V2 API
- Handles authentication
- Streaming response support
- Error handling and retries

### 3. Tools
- `index_repository` - Start indexing a GitHub repo
- `search` - Unified natural-language search across repositories and docs
- `list_repositories` - List indexed repos
- `check_repository_status` - Check indexing progress
- `delete_repository` - Remove indexed repo

### 4. Resources
- Exposes indexed repositories as MCP resources
- Provides metadata about each repository
- Enables AI assistants to understand available codebases

## API Endpoints Used

The proxy communicates with NIA's V2 API:

- `GET /v2/repositories` - List repositories
- `POST /v2/repositories` - Index new repository
- `GET /v2/repositories/{owner/repo}` - Get repository status
- `DELETE /v2/repositories/{owner/repo}` - Delete repository
- `POST /v2/query` - Unified repository/documentation search (streaming)

## Authentication

All requests include the API key in the Authorization header:
```
Authorization: Bearer YOUR-API-KEY
```

## Error Handling

1. **Invalid API Key**: Clear error message with link to get key
2. **Rate Limiting**: Passes through API rate limit errors
3. **Network Errors**: Retries with exponential backoff
4. **Indexing Failures**: Reports detailed error messages

## Distribution

### PyPI Package
```bash
pip install nia-mcp-server
```

### NPM Wrapper (Optional)
```bash
npx @trynia/mcp-server
```

## Security

- API keys are never logged or stored
- All communication uses HTTPS
- No data is stored locally
- User isolation handled by NIA backend

## Future Enhancements

1. **Caching**: Local caching of repository lists
2. **Offline Mode**: Queue operations when offline
3. **Advanced Search**: More search options
4. **Web/Text Sources**: Support for non-code content
5. **Batch Operations**: Index multiple repos at once