"""
NIA API Client for communicating with production NIA API
"""
import os
import httpx
import asyncio
from typing import Dict, Any, List, Optional, AsyncIterator
import json
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception for API errors with status code."""
    def __init__(self, message: str, status_code: int = None, detail: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail

class NIAApiClient:
    """Client for interacting with NIA's production API."""
    
    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        # Remove trailing slash from base URL to prevent double slashes
        self.base_url = (base_url or os.getenv("NIA_API_URL", "https://apigcp.trynia.ai")).rstrip('/')
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "nia-mcp-server/1.0.27",
                "Content-Type": "application/json"
            },
            timeout=720.0  # 12 minute timeout for deep research operations
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _handle_api_error(self, e: httpx.HTTPStatusError) -> APIError:
        """Convert HTTP errors to more specific API errors."""
        error_detail = ""
        response_text = None

        # Safely access response body; streaming responses may not be readable yet.
        try:
            response_text = e.response.text
            error_detail = response_text
        except RuntimeError:
            logger.warning(
                "Unable to read streaming response body while handling HTTP error."
            )
            # Fall back to reason phrase if available.
            error_detail = e.response.reason_phrase or ""

        if response_text:
            try:
                error_json = e.response.json()
                error_detail = error_json.get("detail", error_detail)
                logger.debug(f"Parsed error JSON: {error_json}")
            except (json.JSONDecodeError, ValueError) as parse_error:
                # Failed to parse JSON response, keep original error_detail
                logger.warning(f"Failed to parse error response as JSON: {parse_error}")

        status_code = e.response.status_code

        if not error_detail:
            error_detail = f"HTTP {status_code} Error"

        # Log the full error for debugging
        logger.error(f"API error - Status: {status_code}, Detail: {error_detail}")
        
        # Handle specific error cases
        if status_code == 401:
            return APIError(
                "Invalid or missing API key. Please check your API key at https://trynia.ai/api-keys",
                status_code,
                error_detail,
            )
        elif status_code == 403:
            # Check for various forms of usage limit errors
            error_lower = error_detail.lower()
            if any(
                phrase in error_lower
                for phrase in [
                    "lifetime limit",
                    "monthly limit",
                    "reached your monthly limit",
                    "resets on the 1st",
                    "indexing credits",
                    "indexing operations",
                    "no chat credits",
                    "free api requests",
                    "3 free",
                    "usage limit",
                    "upgrade to pro",
                ]
            ):
                # Use the exact error message from the API for clarity
                return APIError(error_detail, status_code, error_detail)
            else:
                return APIError(
                    f"Access forbidden: {error_detail}", status_code, error_detail
                )
        elif status_code == 429:
            return APIError(f"Rate limit exceeded: {error_detail}", status_code, error_detail)
        elif status_code == 400:
            # Bad Request - return the full error detail from backend
            return APIError(error_detail, status_code, error_detail)
        elif status_code == 404:
            return APIError(f"Resource not found: {error_detail}", status_code, error_detail)
        elif status_code == 500:
            # For 500 errors, try to extract more meaningful error details
            if error_detail:
                error_lower = error_detail.lower()
                # Check if it's actually a wrapped error from middleware or API
                if any(
                    phrase in error_lower
                    for phrase in [
                        "lifetime limit",
                        "free api requests",
                        "3 free",
                        "usage limit",
                        "monthly limit",
                        "reached your monthly limit",
                        "resets on the 1st",
                        "indexing credits",
                        "indexing operations",
                        "upgrade to pro",
                    ]
                ):
                    return APIError(error_detail, 403, error_detail)
                else:
                    return APIError(f"Server error: {error_detail}", status_code, error_detail)
            else:
                return APIError(
                    "Internal server error. Please try again later.",
                    status_code,
                    error_detail,
                )
        else:
            return APIError(
                f"API error (status {status_code}): {error_detail}",
                status_code,
                error_detail,
            )
    async def validate_api_key(self) -> bool:
        """
        Validate the API key by making a lightweight request.

        Important nuance: some backends return 403 for "valid key but forbidden/quota exceeded"
        and 429 for rate limiting. Those should NOT be treated as "invalid API key", otherwise
        users see a misleading auth error when they're actually out of credits.
        """
        try:
            response = await self.client.get(f"{self.base_url}/v2/repositories")
            if response.status_code == 200:
                return True
            if response.status_code == 401:
                return False
            if response.status_code in (403, 429):
                return True
            # For anything else (esp. 5xx), fail closed.
            return False
        except httpx.HTTPStatusError as e:
            # Log the specific error but return False for validation
            error = self._handle_api_error(e)
            logger.error(f"API key validation failed: {error}")
            if error.status_code == 401:
                return False
            if error.status_code in (403, 429):
                return True
            return False
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    async def list_repositories(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List indexed repositories (supports optional filtering/pagination)."""
        try:
            params: Dict[str, Any] = {}
            if q:
                params["q"] = q
            if status:
                params["status"] = status
            if limit is not None:
                params["limit"] = limit
            if offset:
                params["offset"] = offset

            response = await self.client.get(
                f"{self.base_url}/v2/repositories",
                params=params or None,
            )
            response.raise_for_status()
            data = response.json()
            
            # Ensure we always return a list
            if not isinstance(data, list):
                logger.error(f"Unexpected response type from list_repositories: {type(data)}, data: {data}")
                # If it's a dict with an error message, raise it
                if isinstance(data, dict) and "error" in data:
                    raise APIError(f"API returned error: {data['error']}")
                # Otherwise return empty list
                return []
            
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"Caught HTTPStatusError in list_repositories: status={e.response.status_code}, detail={e.response.text}")
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to list repositories: {e}")
            raise APIError(f"Failed to list repositories: {str(e)}")
    
    async def index_repository(self, repo_url: str, branch: str = None) -> Dict[str, Any]:
        """Index a GitHub repository."""
        try:
            # Handle different input formats
            if "github.com" in repo_url:
                # Remove query parameters and fragments
                clean_url = repo_url.split('?')[0].split('#')[0]
                
                # Check if it's a folder URL (contains /tree/)
                if "/tree/" in clean_url:
                    # Extract everything after github.com/
                    parts = clean_url.split('github.com/', 1)
                    if len(parts) > 1:
                        repository_path = parts[1].rstrip('/')
                    else:
                        repository_path = repo_url
                else:
                    # Regular repo URL - extract owner/repo
                    parts = clean_url.rstrip('/').split('/')
                    if len(parts) >= 2:
                        repo_name = parts[-1]
                        # Remove .git suffix if present
                        if repo_name.endswith('.git'):
                            repo_name = repo_name[:-4]
                        repository_path = f"{parts[-2]}/{repo_name}"
                    else:
                        repository_path = repo_url
            else:
                # Assume it's already in the right format
                repository_path = repo_url
            
            payload = {
                "repository": repository_path,
                "branch": branch
            }
            
            response = await self.client.post(
                f"{self.base_url}/v2/repositories",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to index repository: {str(e)}")

    async def index_research_paper(self, url_or_id: str) -> Dict[str, Any]:
        """Index a research paper from arXiv.

        Args:
            url_or_id: arXiv URL or raw ID (e.g., '2312.00752', 'https://arxiv.org/abs/2312.00752')

        Returns:
            Dict containing paper metadata and indexing status
        """
        try:
            payload = {"url": url_or_id}

            response = await self.client.post(
                f"{self.base_url}/v2/research-papers",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to index research paper: {str(e)}")

    async def get_repository_status(self, owner_repo: str) -> Dict[str, Any]:
        """Get the status of a repository."""
        try:
            # Check if this looks like owner/repo format (contains /)
            if '/' in owner_repo:
                # First, list all repositories to find the matching one
                repos = await self.list_repositories()
                
                # Extract base repository path for matching
                # Handle both "owner/repo" and "owner/repo/folder" formats
                base_repo = owner_repo
                if owner_repo.count('/') > 1:
                    # This might be a folder path like "owner/repo/folder"
                    # Extract just the owner/repo part
                    parts = owner_repo.split('/')
                    base_repo = f"{parts[0]}/{parts[1]}"
                
                # Look for a repository matching this owner/repo
                matching_repo = None
                for repo in repos:
                    repo_path = repo.get("repository", "")
                    # Check exact match first
                    if repo_path == owner_repo:
                        matching_repo = repo
                        break
                    # Then check if it's the base repository
                    elif repo_path == base_repo:
                        matching_repo = repo
                        break
                    # Also check if the stored repo is a folder path that starts with our base
                    elif repo_path.startswith(base_repo + "/"):
                        matching_repo = repo
                        break
                
                if not matching_repo:
                    logger.warning(f"Repository {owner_repo} not found in list")
                    return None
                
                # Use the repository_id from the matched repo
                repo_id = matching_repo.get("repository_id") or matching_repo.get("id")
                if not repo_id:
                    logger.error(f"No repository ID found for {owner_repo}")
                    return None
                    
                # Now get the status using the ID
                response = await self.client.get(f"{self.base_url}/v2/repositories/{repo_id}")
                response.raise_for_status()
                
                # Merge the response with what we know
                status = response.json()
                # Ensure repository field is included for consistency
                if "repository" not in status:
                    status["repository"] = owner_repo
                return status
            else:
                # Assume it's already a repository ID
                response = await self.client.get(f"{self.base_url}/v2/repositories/{owner_repo}")
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get repository status: {e}")
            return None
    
    async def query_repositories(
        self,
        messages: List[Dict[str, str]],
        repositories: List[str],
        stream: bool = True,
        include_sources: bool = True
    ) -> AsyncIterator[str]:
        """Query indexed repositories with streaming support."""
        try:
            # Format repositories for the API
            repo_list = []
            for repo in repositories:
                if "/" in repo:
                    repo_list.append({"repository": repo})
                else:
                    # Assume it's a project ID or other identifier
                    repo_list.append({"repository": repo})
            
            payload = {
                "messages": messages,
                "repositories": repo_list,
                "stream": stream,
                "include_sources": include_sources
            }
            
            if stream:
                # Use new /v2/search/query endpoint
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/v2/search/query",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            if line.startswith("data: "):
                                data = line[6:]  # Remove "data: " prefix
                                if data == "[DONE]":
                                    break
                                yield data
            else:
                # Use new /v2/search/query endpoint
                response = await self.client.post(
                    f"{self.base_url}/v2/search/query",
                    json=payload
                )
                response.raise_for_status()
                yield json.dumps(response.json())
                
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Query failed: {str(e)}")
    
    async def wait_for_indexing(self, owner_repo: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for a repository to finish indexing."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await self.get_repository_status(owner_repo)
            
            if not status:
                raise Exception(f"Repository {owner_repo} not found")
            
            if status["status"] == "completed":
                return status
            elif status["status"] == "failed":
                raise Exception(f"Indexing failed: {status.get('error', 'Unknown error')}")
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise Exception(f"Indexing timeout after {timeout} seconds")
            
            # Wait before next check
            await asyncio.sleep(2)
    
    async def delete_repository(self, owner_repo: str) -> bool:
        """Delete an indexed repository."""
        try:
            # Check if this looks like owner/repo format (contains /)
            if '/' in owner_repo:
                # First, get the repository ID
                status = await self.get_repository_status(owner_repo)
                if not status:
                    logger.warning(f"Repository {owner_repo} not found")
                    return False
                
                # Extract the repository ID from status
                repo_id = status.get("repository_id") or status.get("id")
                if not repo_id:
                    # Try to get it from list as fallback
                    repos = await self.list_repositories()
                    for repo in repos:
                        if repo.get("repository") == owner_repo:
                            repo_id = repo.get("repository_id") or repo.get("id")
                            break
                
                if not repo_id:
                    logger.error(f"No repository ID found for {owner_repo}")
                    return False
                    
                # Delete using the ID
                response = await self.client.delete(f"{self.base_url}/v2/repositories/{repo_id}")
                response.raise_for_status()
                return True
            else:
                # Assume it's already a repository ID
                response = await self.client.delete(f"{self.base_url}/v2/repositories/{owner_repo}")
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete repository: {e}")
            return False
    
    async def rename_repository(self, owner_repo: str, new_name: str) -> Dict[str, Any]:
        """Rename a repository's display name."""
        try:
            # Check if this looks like owner/repo format (contains /)
            if '/' in owner_repo:
                # First, get the repository ID
                status = await self.get_repository_status(owner_repo)
                if not status:
                    raise APIError(f"Repository {owner_repo} not found", 404)
                
                # Extract the repository ID from status
                repo_id = status.get("repository_id") or status.get("id")
                if not repo_id:
                    # Try to get it from list as fallback
                    repos = await self.list_repositories()
                    for repo in repos:
                        if repo.get("repository") == owner_repo:
                            repo_id = repo.get("repository_id") or repo.get("id")
                            break
                
                if not repo_id:
                    raise APIError(f"No repository ID found for {owner_repo}", 404)
                    
                # Rename using the ID
                response = await self.client.patch(
                    f"{self.base_url}/v2/repositories/{repo_id}/rename",
                    json={"new_name": new_name}
                )
                response.raise_for_status()
                return response.json()
            else:
                # Assume it's already a repository ID
                response = await self.client.patch(
                    f"{self.base_url}/v2/repositories/{owner_repo}/rename",
                    json={"new_name": new_name}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to rename repository: {e}")
            raise APIError(f"Failed to rename repository: {str(e)}")
            
    async def get_github_tree(
        self,
        owner_repo: str,
        branch: Optional[str] = None,
        include_paths: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        file_extensions: Optional[List[str]] = None,
        exclude_extensions: Optional[List[str]] = None,
        show_full_paths: bool = False
    ) -> Dict[str, Any]:
        """Get file tree directly from GitHub API (no FalkorDB dependency).

        Args:
            owner_repo: Repository in owner/repo format or repository ID
            branch: Optional branch name (defaults to repository's default branch)
            include_paths: Only include files in these paths (e.g., ["src/", "lib/"])
            exclude_paths: Exclude files in these paths (e.g., ["node_modules/", "dist/"])
            file_extensions: Only include these file extensions (e.g., [".py", ".js"])
            exclude_extensions: Exclude these file extensions (e.g., [".md", ".lock"])
            show_full_paths: Show full file paths instead of hierarchical tree

        Returns:
            GitHub tree structure with files, directories, and stats
        """
        try:
            # Check if this looks like owner/repo format (contains /)
            if '/' in owner_repo:
                # First, get the repository ID
                status = await self.get_repository_status(owner_repo)
                if not status:
                    raise APIError(f"Repository {owner_repo} not found", 404)

                # Extract the repository ID from status
                repo_id = status.get("repository_id") or status.get("id")
                if not repo_id:
                    # Try to get it from list as fallback
                    repos = await self.list_repositories()
                    for repo in repos:
                        if repo.get("repository") == owner_repo:
                            repo_id = repo.get("repository_id") or repo.get("id")
                            break

                if not repo_id:
                    raise APIError(f"No repository ID found for {owner_repo}", 404)

                # Get tree using the ID
                params = {}
                if branch:
                    params["branch"] = branch
                if include_paths:
                    params["include_paths"] = ",".join(include_paths)
                if exclude_paths:
                    params["exclude_paths"] = ",".join(exclude_paths)
                if file_extensions:
                    params["file_extensions"] = ",".join(file_extensions)
                if exclude_extensions:
                    params["exclude_extensions"] = ",".join(exclude_extensions)
                if show_full_paths:
                    params["show_full_paths"] = "true"

                # Use new /tree endpoint
                response = await self.client.get(
                    f"{self.base_url}/v2/repositories/{repo_id}/tree",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            else:
                # Assume it's already a repository ID
                params = {}
                if branch:
                    params["branch"] = branch
                if include_paths:
                    params["include_paths"] = ",".join(include_paths)
                if exclude_paths:
                    params["exclude_paths"] = ",".join(exclude_paths)
                if file_extensions:
                    params["file_extensions"] = ",".join(file_extensions)
                if exclude_extensions:
                    params["exclude_extensions"] = ",".join(exclude_extensions)
                if show_full_paths:
                    params["show_full_paths"] = "true"

                # Use new /tree endpoint
                response = await self.client.get(
                    f"{self.base_url}/v2/repositories/{owner_repo}/tree",
                    params=params
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except APIError:
            raise
        except Exception as e:
            logger.error(f"Failed to get GitHub tree: {e}")
            raise APIError(f"Failed to get GitHub tree: {str(e)}")

    # Data Source methods
    
    async def create_data_source(
        self, 
        url: str, 
        url_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        max_age: int = None,
        only_main_content: bool = True,
        wait_for: int = None,
        include_screenshot: bool = None,
        check_llms_txt: bool = None,
        llms_txt_strategy: str = None
    ) -> Dict[str, Any]:
        """Create a new documentation/web data source."""
        try:
            effective_max_age = 3600 if max_age is None else max_age

            payload = {
                "url": url,
                "url_patterns": url_patterns or [],
                "exclude_patterns": exclude_patterns or [],
                "max_age": effective_max_age
            }
            
            # Add optional parameters
            # Don't hardcode formats - let backend defaults apply
            # This allows screenshots to be captured by default
            if only_main_content is not None:
                payload["only_main_content"] = only_main_content
            if wait_for is not None:
                payload["wait_for"] = wait_for
            if include_screenshot is not None:
                payload["include_screenshot"] = include_screenshot
            if check_llms_txt is not None:
                payload["check_llms_txt"] = check_llms_txt
            if llms_txt_strategy is not None:
                payload["llms_txt_strategy"] = llms_txt_strategy
            
            response = await self.client.post(
                f"{self.base_url}/v2/data-sources",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to create data source: {str(e)}")
    
    async def list_data_sources(
        self,
        q: Optional[str] = None,
        status: Optional[str] = None,
        source_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List data sources for the authenticated user (supports optional filtering/pagination)."""
        try:
            params: Dict[str, Any] = {
                "limit": limit,
                "offset": offset,
            }
            if q:
                params["q"] = q
            if status:
                params["status"] = status
            if source_type:
                params["source_type"] = source_type

            response = await self.client.get(
                f"{self.base_url}/v2/data-sources",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to list data sources: {e}")
            raise APIError(f"Failed to list data sources: {str(e)}")
    
    async def get_data_source_status(self, source_id: str) -> Dict[str, Any]:
        """Get the status of a data source."""
        try:
            response = await self.client.get(f"{self.base_url}/v2/data-sources/{source_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to get data source status: {e}")
            return None
    
    async def delete_data_source(self, source_id: str) -> bool:
        """Delete a data source."""
        try:
            response = await self.client.delete(f"{self.base_url}/v2/data-sources/{source_id}")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to delete data source: {e}")
            return False
    
    async def rename_data_source(self, source_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a data source's display name."""
        try:
            # Use primary endpoint (takes source_id in body, not path)
            response = await self.client.patch(
                f"{self.base_url}/v2/data-sources/rename",
                json={"source_id": source_id, "new_name": new_name}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to rename data source: {e}")
            raise APIError(f"Failed to rename data source: {str(e)}")
    
    # Documentation Virtual Filesystem Methods
    
    async def get_doc_tree(self, source_id: str) -> Dict[str, Any]:
        """Get filesystem tree structure of indexed documentation."""
        try:
            response = await self.client.get(f"{self.base_url}/v2/data-sources/{source_id}/tree")
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to get documentation tree: {e}")
            raise APIError(f"Failed to get documentation tree: {str(e)}")
    
    async def get_doc_ls(self, source_id: str, path: str = "/") -> Dict[str, Any]:
        """List contents of a virtual directory in the documentation."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v2/data-sources/{source_id}/ls",
                params={"path": path}
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to list documentation directory: {e}")
            raise APIError(f"Failed to list documentation directory: {str(e)}")
    
    async def get_doc_read(
        self, 
        source_id: str, 
        path: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read content of a documentation page by virtual filesystem path.
        
        Args:
            source_id: Data source ID
            path: Virtual path to the page
            line_start: Start line (1-based, inclusive)
            line_end: End line (1-based, inclusive)
            max_length: Max characters to return
        """
        try:
            params = {"path": path}
            if line_start is not None:
                params["line_start"] = line_start
            if line_end is not None:
                params["line_end"] = line_end
            if max_length is not None:
                params["max_length"] = max_length
            
            response = await self.client.get(
                f"{self.base_url}/v2/data-sources/{source_id}/read",
                params=params
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to read documentation file: {e}")
            raise APIError(f"Failed to read documentation file: {str(e)}")
    
    async def post_doc_grep(
        self, 
        source_id: str, 
        pattern: str, 
        path: str = "/",
        context_lines: Optional[int] = None,
        A: Optional[int] = None,
        B: Optional[int] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        fixed_string: bool = False,
        max_matches_per_file: int = 10,
        max_total_matches: int = 100,
        output_mode: str = "content",
        highlight: bool = False
    ) -> Dict[str, Any]:
        """Search documentation content with regex pattern.
        
        Args:
            source_id: Data source ID
            pattern: Regex pattern to search for
            path: Limit search to this path prefix
            context_lines: Lines before AND after (shorthand for A/B)
            A: Lines after each match (like grep -A)
            B: Lines before each match (like grep -B)
            case_sensitive: Case-sensitive matching
            whole_word: Match whole words only
            fixed_string: Treat pattern as literal string
            max_matches_per_file: Max matches per file
            max_total_matches: Max total matches
            output_mode: Output format ('content', 'files_with_matches', 'count')
            highlight: Add >>markers<< around matched text
        """
        try:
            body = {
                    "pattern": pattern,
                    "path": path,
                "case_sensitive": case_sensitive,
                "whole_word": whole_word,
                "fixed_string": fixed_string,
                "max_matches_per_file": max_matches_per_file,
                "max_total_matches": max_total_matches,
                "output_mode": output_mode,
                "highlight": highlight
            }
            
            # Only include optional context parameters if provided
            if context_lines is not None:
                body["context_lines"] = context_lines
            if A is not None:
                body["A"] = A
            if B is not None:
                body["B"] = B
            
            response = await self.client.post(
                f"{self.base_url}/v2/data-sources/{source_id}/grep",
                json=body
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to grep documentation: {e}")
            raise APIError(f"Failed to grep documentation: {str(e)}")
    
    async def post_code_grep(
        self, 
        repository: str, 
        pattern: str, 
        path: str = "",
        context_lines: Optional[int] = None,
        A: Optional[int] = None,
        B: Optional[int] = None,
        case_sensitive: bool = False,
        whole_word: bool = False,
        fixed_string: bool = False,
        max_matches_per_file: int = 10,
        max_total_matches: int = 100,
        output_mode: str = "content",
        highlight: bool = False,
        exhaustive: bool = False
    ) -> Dict[str, Any]:
        """Search repository code with regex pattern.
        
        Args:
            repository: Repository identifier (owner/repo format)
            pattern: Regex pattern to search for
            path: Limit search to this file path prefix
            context_lines: Lines before AND after (shorthand for A/B)
            A: Lines after each match (like grep -A)
            B: Lines before each match (like grep -B)
            case_sensitive: Case-sensitive matching
            whole_word: Match whole words only
            fixed_string: Treat pattern as literal string
            max_matches_per_file: Max matches per file
            max_total_matches: Max total matches
            output_mode: Output format ('content', 'files_with_matches', 'count')
            highlight: Add >>markers<< around matched text
            exhaustive: When True, searches ALL chunks instead of BM25 top-k
        """
        try:
            body = {
                "pattern": pattern,
                "path": path,
                "case_sensitive": case_sensitive,
                "whole_word": whole_word,
                "fixed_string": fixed_string,
                "max_matches_per_file": max_matches_per_file,
                "max_total_matches": max_total_matches,
                "output_mode": output_mode,
                "highlight": highlight,
                "exhaustive": exhaustive
            }
            
            # Only include optional context parameters if provided
            if context_lines is not None:
                body["context_lines"] = context_lines
            if A is not None:
                body["A"] = A
            if B is not None:
                body["B"] = B
            
            response = await self.client.post(
                f"{self.base_url}/v2/repositories/{quote(repository, safe='')}/grep",
                json=body
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to grep repository code: {e}")
            raise APIError(f"Failed to grep repository code: {str(e)}")
    
    async def query_unified(
        self,
        messages: List[Dict[str, str]],
        repositories: List[str] = None,
        data_sources: List[str] = None,
        search_mode: str = "unified",
        stream: bool = True,
        include_sources: bool = True
    ) -> AsyncIterator[str]:
        """Query across repositories and/or documentation sources."""
        try:
            # Build repository list
            repo_list = []
            if repositories:
                for repo in repositories:
                    repo_list.append({"repository": repo})
            
            # Build data source list
            source_list = []
            if data_sources:
                for source in data_sources:
                    # Handle flexible identifier formats:
                    # 1. String directly (display_name, URL, or source_id) - NEW
                    # 2. Dict with "source_id" (backwards compatible)
                    # 3. Dict with "identifier" (new format)
                    if isinstance(source, str):
                        # Pass string directly - backend will resolve it
                        source_list.append(source)
                    elif isinstance(source, dict):
                        # Keep dict format as-is (backwards compatible)
                        source_list.append(source)
                    else:
                        # Convert other types to string
                        source_list.append(str(source))

            # NOTE: Don't validate here - let backend handle auto-hint generation
            # The backend will generate hints if both lists are empty

            payload = {
                "messages": messages,
                "repositories": repo_list,
                "data_sources": source_list,
                "search_mode": search_mode,
                "stream": stream,
                "include_sources": include_sources
            }
            
            if stream:
                # Use new /v2/search/query endpoint
                async with self.client.stream(
                    "POST",
                    f"{self.base_url}/v2/search/query",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            if line.startswith("data: "):
                                data = line[6:]  # Remove "data: " prefix
                                if data == "[DONE]":
                                    break
                                yield data
            else:
                # Use new /v2/search/query endpoint
                response = await self.client.post(
                    f"{self.base_url}/v2/search/query",
                    json=payload
                )
                response.raise_for_status()
                yield json.dumps(response.json())
                
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Query failed: {str(e)}")
    
    async def web_search(
        self,
        query: str,
        num_results: int = 5,
        category: Optional[str] = None,
        days_back: Optional[int] = None,
        find_similar_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform AI-powered web search."""
        try:
            payload = {
                "query": query,
                "num_results": min(num_results, 10),
            }
            
            # Add optional parameters
            if category:
                payload["category"] = category
            if days_back:
                payload["days_back"] = days_back
            if find_similar_to:
                payload["find_similar_to"] = find_similar_to
            
            # Use new /v2/search/web endpoint
            response = await self.client.post(
                f"{self.base_url}/v2/search/web",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Web search failed: {str(e)}")
    
    async def deep_research(
        self,
        query: str,
        output_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform deep research using AI agent."""
        try:
            payload = {
                "query": query,
            }

            if output_format:
                payload["output_format"] = output_format

            # Use new /v2/search/deep endpoint
            response = await self.client.post(
                f"{self.base_url}/v2/search/deep",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Deep research failed: {str(e)}")

    async def oracle_research(
        self,
        query: str,
        repositories: Optional[List[str]] = None,
        data_sources: Optional[List[str]] = None,
        output_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """Call the in-house Oracle research agent."""
        try:
            payload: Dict[str, Any] = {
                "query": query,
            }

            if repositories:
                payload["repositories"] = repositories
            if data_sources:
                payload["data_sources"] = data_sources
            if output_format:
                payload["output_format"] = output_format

            response = await self.client.post(
                f"{self.base_url}/v2/oracle",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Oracle research failed: {str(e)}")

    async def get_source_content(
        self,
        source_type: str,
        source_identifier: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get full content of a specific source file or document.
        
        Args:
            source_type: Either "repository" or "documentation"
            source_identifier: For repository: "owner/repo:path/to/file.ext"
                              For documentation: source_id, URL, or display_name
            metadata: Optional metadata (may contain path, url for docs)
        
        Returns:
            Dict with success, content, and metadata fields
        """
        try:
            meta = metadata or {}
            
            if source_type == "repository":
                # Parse repository source identifier: "owner/repo:path/to/file.ext"
                if ":" not in source_identifier:
                    return {
                        "success": False,
                        "error": "Repository source_identifier must be in 'owner/repo:path/to/file' format"
                    }
                
                repo_part, file_path = source_identifier.split(":", 1)
                file_path = file_path.lstrip("/")
                
                # URL encode the repository identifier for path parameter
                encoded_repo = quote(repo_part, safe="")
                
                params = {"path": file_path}
                if meta.get("branch"):
                    params["branch"] = meta["branch"]
                
                response = await self.client.get(
                    f"{self.base_url}/v2/repositories/{encoded_repo}/content",
                    params=params
                )
                response.raise_for_status()
                return response.json()
                
            elif source_type == "documentation":
                # For documentation, source_identifier can be source_id, URL, or display_name
                # The path or url can come from metadata
                doc_path = meta.get("path") or meta.get("file_path")
                doc_url = meta.get("url") or meta.get("source_url")
                
                # If source_identifier looks like a URL, use it as the doc_url
                if source_identifier.startswith(("http://", "https://")) and not doc_url:
                    doc_url = source_identifier
                    # Try to find the source_id from metadata
                    source_id = meta.get("source_id") or meta.get("id")
                    if not source_id:
                        return {
                            "success": False,
                            "error": "Documentation source requires source_id when using URL as identifier"
                        }
                else:
                    source_id = source_identifier
                
                if not doc_path and not doc_url:
                    return {
                        "success": False,
                        "error": "Documentation source requires either 'path' or 'url' in metadata"
                    }
                
                params = {}
                if doc_path:
                    params["path"] = doc_path
                elif doc_url:
                    params["url"] = doc_url
                
                response = await self.client.get(
                    f"{self.base_url}/v2/data-sources/{source_id}/content",
                    params=params
                )
                response.raise_for_status()
                return response.json()
            else:
                return {
                    "success": False,
                    "error": f"Unknown source_type: {source_type}. Must be 'repository' or 'documentation'"
                }

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to get source content: {str(e)}")

    async def submit_bug_report(
        self,
        description: str,
        bug_type: str = "bug",
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit a bug report or feature request."""
        try:
            payload = {
                "description": description,
                "bug_type": bug_type,
                "additional_context": additional_context
            }

            response = await self.client.post(
                f"{self.base_url}/v2/bug-report",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to submit bug report: {str(e)}")

    # ========================================================================
    # CHROMA PACKAGE SEARCH METHODS
    # ========================================================================

    async def package_search_grep(
        self,
        registry: str,
        package_name: str,
        pattern: str,
        version: Optional[str] = None,
        language: Optional[str] = None,
        filename_sha256: Optional[str] = None,
        a: Optional[int] = None,
        b: Optional[int] = None,
        c: Optional[int] = None,
        head_limit: Optional[int] = None,
        output_mode: str = "content"
    ) -> Dict[str, Any]:
        """Execute grep search on package source code via Chroma."""
        try:
            payload = {
                "registry": registry,
                "package_name": package_name,
                "pattern": pattern,
                "version": version,
                "language": language,
                "filename_sha256": filename_sha256,
                "a": a,
                "b": b,
                "c": c,
                "head_limit": head_limit,
                "output_mode": output_mode
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = await self.client.post(
                f"{self.base_url}/v2/package-search/grep",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to search package with grep: {str(e)}")

    async def package_search_hybrid(
        self,
        registry: str,
        package_name: str,
        semantic_queries: List[str],
        version: Optional[str] = None,
        filename_sha256: Optional[str] = None,
        pattern: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute hybrid semantic search on package source code via Chroma."""
        try:
            payload = {
                "registry": registry,
                "package_name": package_name,
                "semantic_queries": semantic_queries,
                "version": version,
                "filename_sha256": filename_sha256,
                "pattern": pattern,
                "language": language
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = await self.client.post(
                f"{self.base_url}/v2/package-search/hybrid",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to search package with hybrid search: {str(e)}")

    async def package_search_read_file(
        self,
        registry: str,
        package_name: str,
        filename_sha256: str,
        start_line: int,
        end_line: int,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read specific lines from a package file via Chroma."""
        try:
            payload = {
                "registry": registry,
                "package_name": package_name,
                "filename_sha256": filename_sha256,
                "start_line": start_line,
                "end_line": end_line,
                "version": version
            }

            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = await self.client.post(
                f"{self.base_url}/v2/package-search/read-file",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to read package file: {str(e)}")

    # ========================================================================
    # CONTEXT SHARING METHODS
    # ========================================================================

    async def save_context(
        self,
        title: str,
        summary: str,
        content: str,
        agent_source: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        nia_references: Optional[Dict[str, Any]] = None,
        edited_files: Optional[List[Dict[str, Any]]] = None,
        workspace_metadata: Optional[Dict[str, Any]] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
        workspace_override: Optional[str] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save a conversation context for cross-agent sharing with workspace awareness."""
        try:
            payload = {
                "title": title,
                "summary": summary,
                "content": content,
                "agent_source": agent_source,
                "tags": tags or [],
                "metadata": metadata or {}
            }

            # Add new structured fields if provided
            if nia_references is not None:
                payload["nia_references"] = nia_references
            if edited_files is not None:
                payload["edited_files"] = edited_files

            # Add workspace-aware fields
            if workspace_metadata is not None:
                payload["workspace_metadata"] = workspace_metadata
            if file_metadata is not None:
                payload["file_metadata"] = file_metadata
            if workspace_override is not None:
                payload["workspace_override"] = workspace_override
            if cwd is not None:
                payload["cwd"] = cwd

            response = await self.client.post(
                f"{self.base_url}/v2/contexts",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to save context: {str(e)}")

    async def list_contexts(
        self,
        limit: int = 20,
        offset: int = 0,
        tags: Optional[str] = None,
        agent_source: Optional[str] = None,
        scope: Optional[str] = None,
        workspace: Optional[str] = None,
        directory: Optional[str] = None,
        file_overlap: Optional[str] = None,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """List user's conversation contexts with pagination, filtering, and workspace awareness."""
        try:
            params = {
                "limit": limit,
                "offset": offset
            }

            if tags:
                params["tags"] = tags
            if agent_source:
                params["agent_source"] = agent_source

            # Add workspace-aware filters
            if scope:
                params["scope"] = scope
            if workspace:
                params["workspace"] = workspace
            if directory:
                params["directory"] = directory
            if file_overlap:
                params["file_overlap"] = file_overlap
            if cwd:
                params["cwd"] = cwd

            response = await self.client.get(
                f"{self.base_url}/v2/contexts",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to list contexts: {str(e)}")

    async def get_context(self, context_id: str) -> Dict[str, Any]:
        """Get a specific conversation context by ID."""
        try:
            response = await self.client.get(f"{self.base_url}/v2/contexts/{context_id}")
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to get context: {str(e)}")

    async def update_context(
        self,
        context_id: str,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Update an existing conversation context."""
        try:
            payload = {}

            if title is not None:
                payload["title"] = title
            if summary is not None:
                payload["summary"] = summary
            if content is not None:
                payload["content"] = content
            if tags is not None:
                payload["tags"] = tags
            if metadata is not None:
                payload["metadata"] = metadata

            response = await self.client.put(
                f"{self.base_url}/v2/contexts/{context_id}",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to update context: {str(e)}")

    async def delete_context(self, context_id: str) -> bool:
        """Delete a conversation context."""
        try:
            response = await self.client.delete(f"{self.base_url}/v2/contexts/{context_id}")
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Failed to delete context: {e}")
            return False

    async def search_contexts(
        self,
        query: str,
        limit: int = 20,
        tags: Optional[str] = None,
        agent_source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search conversation contexts by content, title, or summary (keyword search)."""
        try:
            params = {
                "q": query,
                "limit": limit
            }

            if tags:
                params["tags"] = tags
            if agent_source:
                params["agent_source"] = agent_source

            response = await self.client.get(
                f"{self.base_url}/v2/contexts/search",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to search contexts: {str(e)}")

    async def search_contexts_semantic(
        self,
        query: str,
        limit: int = 20,
        organization_id: Optional[str] = None,
        cwd: Optional[str] = None,
        include_highlights: bool = True,
        workspace_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search conversation contexts using semantic search (vector + BM25 hybrid)."""
        try:
            params = {
                "q": query,
                "limit": limit,
                "include_highlights": include_highlights
            }

            if organization_id:
                params["organization_id"] = organization_id
            if cwd:
                params["cwd"] = cwd
            if workspace_filter:
                params["workspace_filter"] = workspace_filter

            response = await self.client.get(
                f"{self.base_url}/v2/contexts/semantic-search",
                params=params
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            raise APIError(f"Failed to search contexts semantically: {str(e)}")

    # =========================================================================
    # Universal Search
    # =========================================================================

    async def universal_search(
        self,
        query: str,
        top_k: int = 20,
        include_repos: bool = True,
        include_docs: bool = True,
        alpha: float = 0.7,
        compress_output: bool = False
    ) -> Dict[str, Any]:
        """
        Search across ALL indexed public sources using TurboPuffer hybrid search.
        
        Args:
            query: Natural language search query
            top_k: Total number of results to return (default: 20, max: 100)
            include_repos: Include repository sources (default: True)
            include_docs: Include documentation sources (default: True)
            alpha: Weight for vector search vs BM25 (default: 0.7 = 70% vector)
            compress_output: Use AI (Gemini Flash) to compress results into concise answer
            
        Returns:
            Dict with results, sources_searched, query_time_ms, optional errors, and optional answer
        """
        try:
            payload = {
                "query": query,
                "top_k": top_k,
                "include_repos": include_repos,
                "include_docs": include_docs,
                "alpha": alpha,
                "compress_output": compress_output
            }
            
            # Use new /v2/search/universal endpoint
            response = await self.client.post(
                f"{self.base_url}/v2/search/universal",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            raise self._handle_api_error(e)
        except Exception as e:
            logger.error(f"Universal search failed: {e}")
            raise APIError(f"Failed to perform universal search: {str(e)}")