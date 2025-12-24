"""
Cilow Python SDK Client
Async-first client for the Cilow AI Agent Platform
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    Memory,
    MemoryStats,
    SearchResult,
    AgentConfig,
    Agent,
    AgentExecutionResult,
    HealthStatus,
    ExtractedFact,
    User,
    AuthResponse,
    ApiKey,
    Session,
)
from .errors import (
    CilowError,
    ConnectionError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)


class CilowClient:
    """
    Async Python client for Cilow AI Agent Platform

    This client provides high-level methods for interacting with the Cilow API,
    including memory management, semantic search, and agent orchestration.

    Example:
        async with CilowClient(api_key="your-key") as client:
            # Add a memory
            memory_id = await client.add_memory("User prefers Python")

            # Search memories
            results = await client.search_memories("programming")

            # Create an agent
            agent_id = await client.create_agent("assistant", "react")

            # Execute a task
            result = await client.execute_task(agent_id, "What do I like?")
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Cilow client.

        Args:
            base_url: Base URL of the Cilow API server
            api_key: Optional API key for authentication (X-API-Key header)
            access_token: Optional JWT access token (Bearer auth)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._access_token = access_token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "CilowClient":
        """Enter async context manager."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        self._session = aiohttp.ClientSession(
            headers=headers,
            timeout=self.timeout,
        )
        return self

    def set_access_token(self, token: str) -> None:
        """
        Set the JWT access token for Bearer authentication.
        Note: Takes effect on next context manager entry.

        Args:
            token: JWT access token
        """
        self._access_token = token

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self._session:
            await self._session.close()
            self._session = None

    def _get_session(self) -> aiohttp.ClientSession:
        """Get the current session or raise an error."""
        if self._session is None:
            raise RuntimeError(
                "Client must be used as async context manager: "
                "async with CilowClient() as client: ..."
            )
        return self._session

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make API request with error handling."""
        url = f"{self.base_url}/api/v1{endpoint}"
        session = self._get_session()

        kwargs: Dict[str, Any] = {}
        if data is not None:
            kwargs['json'] = data
        if params:
            kwargs['params'] = params

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid API key or unauthorized")
                elif response.status == 404:
                    raise NotFoundError(f"Resource not found: {endpoint}")
                elif response.status == 422:
                    error_text = await response.text()
                    raise ValidationError(f"Validation error: {error_text}")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise CilowError(f"API error {response.status}: {error_text}")

                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Cilow API: {e}")

    # ==========================================================================
    # Health & Status
    # ==========================================================================

    async def health_check(self) -> HealthStatus:
        """Check API server health."""
        session = self._get_session()
        async with session.get(f"{self.base_url}/health") as response:
            data = await response.json()
            return HealthStatus(**data)

    # ==========================================================================
    # Memory Operations
    # ==========================================================================

    async def add_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> str:
        """
        Add a new memory to the system.

        Args:
            content: The memory content
            metadata: Optional metadata dictionary
            tags: Optional list of tags
            user_id: Optional user ID for multi-tenant isolation

        Returns:
            Memory ID
        """
        data: Dict[str, Any] = {"content": content}
        if metadata:
            data["metadata"] = metadata
        if tags:
            data["tags"] = tags
        if user_id:
            data["user_id"] = user_id

        response = await self._request("POST", "/memory/add", data)
        return response["memory_id"]

    async def get_memory(self, memory_id: str, user_id: Optional[str] = None) -> Memory:
        """
        Retrieve a specific memory by ID.

        Args:
            memory_id: The memory identifier
            user_id: Optional user ID for multi-tenant isolation

        Returns:
            Memory object
        """
        endpoint = f"/memory/{memory_id}"
        if user_id:
            endpoint += f"?user_id={user_id}"
        response = await self._request("GET", endpoint)

        # Normalize the response structure
        # API returns nested structure with metadata.tags, but SDK expects flat structure
        if "metadata" in response:
            metadata = response.get("metadata", {})
            # Extract tags from nested metadata if not at top level
            if "tags" not in response or not response["tags"]:
                response["tags"] = metadata.get("tags", [])
            # Extract other fields from metadata
            if "id" not in response:
                response["id"] = str(metadata.get("id", ""))
            if "user_id" not in response:
                response["user_id"] = metadata.get("user_id")
            # Handle created_at - API returns SystemTime struct {secs_since_epoch, nanos_since_epoch}
            if "created_at" not in response or response.get("created_at") is None:
                raw_created = metadata.get("created_at")
                if isinstance(raw_created, dict) and "secs_since_epoch" in raw_created:
                    # Convert Rust SystemTime to ISO datetime string
                    from datetime import datetime, timezone
                    secs = raw_created.get("secs_since_epoch", 0)
                    response["created_at"] = datetime.fromtimestamp(secs, tz=timezone.utc).isoformat()
                else:
                    response["created_at"] = raw_created

        # Normalize content field
        if "compressed_content" in response and "content" not in response:
            response["content"] = response["compressed_content"]

        return Memory(**response)

    async def update_memory(
        self,
        memory_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing memory.

        Args:
            memory_id: The memory identifier
            content: New content (optional)
            metadata: New metadata (optional)
            tags: New tags (optional)
            user_id: Optional user ID for multi-tenant isolation

        Returns:
            Dict with memory_id, message, and updated_fields
        """
        data: Dict[str, Any] = {}
        if content is not None:
            data["content"] = content
        if metadata is not None:
            data["metadata"] = metadata
        if tags is not None:
            data["tags"] = tags
        if user_id is not None:
            data["user_id"] = user_id

        return await self._request("PUT", f"/memory/{memory_id}", data)

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: The memory identifier

        Returns:
            True if deleted successfully
        """
        await self._request("DELETE", f"/memory/{memory_id}")
        return True

    async def search_memories(
        self,
        query: str,
        limit: int = 10,
        tags: Optional[List[str]] = None,
        tag_mode: str = "any",
        min_relevance: float = 0.0,
        user_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Search memories with semantic similarity.

        Args:
            query: Search query
            limit: Maximum results to return
            tags: Optional tag filtering
            tag_mode: "any" or "all" for tag matching
            min_relevance: Minimum relevance threshold (0.0-1.0)
            user_id: Optional user ID for multi-tenant isolation

        Returns:
            List of SearchResult objects
        """
        data: Dict[str, Any] = {"query": query, "limit": limit}
        if tags:
            data["tags"] = tags
            data["tag_mode"] = tag_mode
        if min_relevance > 0:
            data["min_relevance"] = min_relevance
        if user_id:
            data["user_id"] = user_id

        response = await self._request("POST", "/memory/search", data)

        # Handle both list response and dict with "memories" key
        memories_list = response if isinstance(response, list) else response.get("memories", [])

        results = []
        for i, mem_data in enumerate(memories_list):
            # Handle different field names from API
            content = mem_data.get("content") or mem_data.get("compressed_content", "")
            memory = Memory(
                id=mem_data.get("memory_id") or mem_data.get("id"),
                content=content,
                compressed_content=mem_data.get("compressed_content"),
                created_at=mem_data.get("created_at"),
                tier=mem_data.get("tier", "hot"),
                salience=mem_data.get("salience", 1.0),
                access_count=mem_data.get("access_count", 0),
                tags=mem_data.get("tags", []),
                metadata=mem_data.get("metadata", {}),
                user_id=mem_data.get("user_id"),
            )
            results.append(SearchResult(
                memory=memory,
                score=mem_data.get("score", 1.0 - i * 0.1),
                rank=i + 1,
            ))

        return results

    async def get_memory_stats(self) -> MemoryStats:
        """Get memory system statistics."""
        response = await self._request("GET", "/memory/stats")
        return MemoryStats(**response)

    # ==========================================================================
    # Tag Operations
    # ==========================================================================

    async def add_tags(
        self,
        memory_id: str,
        tags: List[str],
    ) -> Memory:
        """
        Add tags to a memory.

        Args:
            memory_id: The memory identifier
            tags: List of tags to add

        Returns:
            Updated Memory object
        """
        data: Dict[str, Any] = {"tags": tags}
        response = await self._request("POST", f"/memory/{memory_id}/tags/add", data)
        return Memory(**response)

    async def remove_tags(
        self,
        memory_id: str,
        tags: List[str],
    ) -> Memory:
        """
        Remove tags from a memory.

        Args:
            memory_id: The memory identifier
            tags: List of tags to remove

        Returns:
            Updated Memory object
        """
        data: Dict[str, Any] = {"tags": tags}
        response = await self._request("POST", f"/memory/{memory_id}/tags/remove", data)
        return Memory(**response)

    async def list_memories(
        self,
        limit: int = 100,
        offset: int = 0,
        tags: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> List[Memory]:
        """
        List memories with pagination.

        Args:
            limit: Maximum number of memories to return
            offset: Number of memories to skip
            tags: Optional tag filter
            user_id: Optional user ID for multi-tenant isolation

        Returns:
            List of Memory objects
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tags:
            params["tags"] = ",".join(tags)
        if user_id:
            params["user_id"] = user_id

        response = await self._request("GET", "/memory/list", params=params)
        memories_list = response if isinstance(response, list) else response.get("memories", [])
        return [Memory(**mem) for mem in memories_list]

    # ==========================================================================
    # Vector Operations
    # ==========================================================================

    async def store_vector(
        self,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> str:
        """
        Store a vector embedding directly.

        Args:
            embedding: The vector embedding
            metadata: Optional metadata dictionary
            content: Optional content associated with the vector

        Returns:
            Vector ID
        """
        data: Dict[str, Any] = {"embedding": embedding}
        if metadata:
            data["metadata"] = metadata
        if content:
            data["content"] = content

        response = await self._request("POST", "/vectors", data)
        return response.get("vector_id", response.get("id"))

    async def batch_store_vectors(
        self,
        vectors: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Store multiple vectors in a batch.

        Args:
            vectors: List of vector entries, each with 'embedding' and optional 'metadata', 'content'

        Returns:
            List of Vector IDs
        """
        data: Dict[str, Any] = {"vectors": vectors}
        response = await self._request("POST", "/vectors/batch", data)
        return response.get("vector_ids", [])

    async def search_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.

        Args:
            query_vector: The query embedding
            limit: Maximum results to return
            min_score: Minimum similarity score

        Returns:
            List of search results with scores
        """
        data: Dict[str, Any] = {
            "embedding": query_vector,
            "limit": limit,
            "min_score": min_score,
        }
        response = await self._request("POST", "/vectors/search", data)
        return response if isinstance(response, list) else response.get("results", [])

    async def get_vector(self, vector_id: str) -> Dict[str, Any]:
        """
        Retrieve a vector by ID.

        Args:
            vector_id: The vector identifier

        Returns:
            Vector data including embedding and metadata
        """
        return await self._request("GET", f"/vectors/{vector_id}")

    async def delete_vector(self, vector_id: str) -> bool:
        """
        Delete a vector.

        Args:
            vector_id: The vector identifier

        Returns:
            True if deleted successfully
        """
        await self._request("DELETE", f"/vectors/{vector_id}")
        return True

    # ==========================================================================
    # Graph Operations
    # ==========================================================================

    async def query_graph(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge graph with natural language.

        Args:
            query: Natural language query
            limit: Maximum results to return

        Returns:
            List of relevant graph nodes/edges
        """
        data: Dict[str, Any] = {"query": query, "limit": limit}
        response = await self._request("POST", "/graph/query", data)
        return response if isinstance(response, list) else response.get("results", [])

    async def add_graph_node(
        self,
        label: str,
        properties: Dict[str, Any],
        node_type: Optional[str] = None,
    ) -> str:
        """
        Add a node to the knowledge graph.

        Args:
            label: Node label (e.g., "Person", "Concept")
            properties: Node properties
            node_type: Optional node type

        Returns:
            Node ID
        """
        data: Dict[str, Any] = {
            "label": label,
            "properties": properties,
        }
        if node_type:
            data["type"] = node_type

        response = await self._request("POST", "/graph/nodes", data)
        return response.get("node_id", response.get("id"))

    async def get_graph_node(self, node_id: str) -> Dict[str, Any]:
        """
        Get a graph node by ID.

        Args:
            node_id: The node identifier

        Returns:
            Node data
        """
        return await self._request("GET", f"/graph/nodes/{node_id}")

    async def delete_graph_node(self, node_id: str) -> bool:
        """
        Delete a graph node.

        Args:
            node_id: The node identifier

        Returns:
            True if deleted successfully
        """
        await self._request("DELETE", f"/graph/nodes/{node_id}")
        return True

    async def add_graph_edge(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an edge between graph nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship_type: Type of relationship
            properties: Optional edge properties

        Returns:
            Edge ID
        """
        data: Dict[str, Any] = {
            "source": source_id,
            "target": target_id,
            "type": relationship_type,
        }
        if properties:
            data["properties"] = properties

        response = await self._request("POST", "/graph/edges", data)
        return response.get("edge_id", response.get("id"))

    async def traverse_graph(
        self,
        start_node_id: str,
        max_depth: int = 2,
        relationship_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Traverse the graph from a starting node.

        Args:
            start_node_id: Starting node ID
            max_depth: Maximum traversal depth
            relationship_types: Optional filter for relationship types

        Returns:
            List of connected nodes and edges
        """
        data: Dict[str, Any] = {
            "start_node": start_node_id,
            "max_depth": max_depth,
        }
        if relationship_types:
            data["relationship_types"] = relationship_types

        response = await self._request("POST", "/graph/traverse", data)
        return response if isinstance(response, list) else response.get("results", [])

    async def find_paths(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5,
    ) -> List[List[Dict[str, Any]]]:
        """
        Find paths between two nodes.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_depth: Maximum path length

        Returns:
            List of paths (each path is a list of nodes/edges)
        """
        data: Dict[str, Any] = {
            "source": source_id,
            "target": target_id,
            "max_depth": max_depth,
        }
        response = await self._request("POST", "/graph/paths", data)
        return response if isinstance(response, list) else response.get("paths", [])

    async def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get knowledge graph statistics.

        Returns:
            Graph statistics including node/edge counts
        """
        return await self._request("GET", "/graph/stats")

    async def get_nodes_by_label(
        self,
        label: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get nodes by label.

        Args:
            label: Node label to filter by
            limit: Maximum nodes to return

        Returns:
            List of nodes with matching label
        """
        params = {"limit": limit}
        return await self._request("GET", f"/graph/nodes/by-label/{label}", params=params)

    async def create_relationship(
        self,
        source_name: str,
        target_name: str,
        relationship_type: str,
        source_memory_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a relationship between entities by name.

        Args:
            source_name: Source entity name
            target_name: Target entity name
            relationship_type: Type of relationship
            source_memory_id: Optional source memory for attribution

        Returns:
            Created relationship data
        """
        data: Dict[str, Any] = {
            "source_name": source_name,
            "target_name": target_name,
            "relationship_type": relationship_type,
        }
        if source_memory_id:
            data["source_memory_id"] = source_memory_id

        return await self._request("POST", "/graph/relationships", data)

    # ==========================================================================
    # Conversation Management
    # ==========================================================================

    async def add_conversation(
        self,
        user_message: str,
        assistant_message: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a conversation turn as a memory.

        Args:
            user_message: User's message
            assistant_message: Assistant's response
            session_id: Optional session identifier
            metadata: Optional metadata

        Returns:
            Memory ID
        """
        content = f"User: {user_message}\nAssistant: {assistant_message}"

        combined_metadata = metadata.copy() if metadata else {}
        if session_id:
            combined_metadata["session_id"] = session_id

        return await self.add_memory(
            content=content,
            metadata=combined_metadata,
            tags=["conversation"],
        )

    # ==========================================================================
    # Agent Operations
    # ==========================================================================

    async def create_agent(
        self,
        name: str,
        agent_type: str = "react",
        config: Optional[AgentConfig] = None,
    ) -> str:
        """
        Create a new AI agent.

        Args:
            name: Agent name
            agent_type: Type of agent ("react", "chain_of_note")
            config: Optional agent configuration

        Returns:
            Agent ID
        """
        data: Dict[str, Any] = {
            "name": name,
            "type": agent_type,
        }
        if config:
            data["config"] = config.dict(exclude_none=True)

        response = await self._request("POST", "/agents/create", data)
        return response["agent_id"]

    async def get_agent(self, agent_id: str) -> Agent:
        """Get agent details."""
        response = await self._request("GET", f"/agents/{agent_id}")
        return Agent(**response)

    async def execute_task(
        self,
        agent_id: str,
        task: str,
        context_limit: int = 4000,
        include_reasoning: bool = False,
    ) -> AgentExecutionResult:
        """
        Execute a task with an AI agent.

        Args:
            agent_id: Agent to use
            task: Task description
            context_limit: Token limit for context
            include_reasoning: Whether to include reasoning trace

        Returns:
            AgentExecutionResult
        """
        data: Dict[str, Any] = {
            "task": task,
            "context_limit": context_limit,
            "include_reasoning": include_reasoning,
        }

        response = await self._request("POST", f"/agents/{agent_id}/execute", data)
        return AgentExecutionResult(**response)

    # ==========================================================================
    # Fact Extraction
    # ==========================================================================

    async def extract_facts(
        self,
        content: str,
        source_context: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """
        Extract facts from content using intelligent extraction.

        Args:
            content: Content to extract facts from
            source_context: Optional source context identifier

        Returns:
            List of ExtractedFact objects
        """
        data: Dict[str, Any] = {"content": content}
        if source_context:
            data["source_context"] = source_context

        response = await self._request("POST", "/memory/extract", data)
        return [ExtractedFact(**fact) for fact in response.get("facts", [])]

    # ==========================================================================
    # Authentication Operations
    # ==========================================================================

    async def _auth_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        authenticated: bool = False,
    ) -> Dict[str, Any]:
        """Make auth API request (doesn't require /api/v1 prefix for some endpoints)."""
        url = f"{self.base_url}/api/v1{endpoint}"
        session = self._get_session()

        kwargs: Dict[str, Any] = {}
        if data is not None:
            kwargs['json'] = data

        # Add auth header if authenticated request
        headers = {}
        if authenticated and self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"

        try:
            async with session.request(method, url, headers=headers, **kwargs) as response:
                if response.status == 401:
                    raise AuthenticationError("Invalid credentials or unauthorized")
                elif response.status == 404:
                    raise NotFoundError(f"Resource not found: {endpoint}")
                elif response.status == 422:
                    error_text = await response.text()
                    raise ValidationError(f"Validation error: {error_text}")
                elif response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise CilowError(f"API error {response.status}: {error_text}")

                return await response.json()
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Failed to connect to Cilow API: {e}")

    async def register(
        self,
        email: str,
        password: str,
        name: Optional[str] = None,
    ) -> AuthResponse:
        """
        Register a new user account.

        Args:
            email: User email address
            password: User password (min 8 characters)
            name: Optional display name

        Returns:
            AuthResponse with access token and user info
        """
        data: Dict[str, Any] = {"email": email, "password": password}
        if name:
            data["name"] = name

        response = await self._auth_request("POST", "/auth/register", data)

        # Store the access token for subsequent requests
        self._access_token = response.get("access_token")

        return AuthResponse(**response)

    async def login(
        self,
        email: str,
        password: str,
    ) -> AuthResponse:
        """
        Login with email and password.

        Args:
            email: User email address
            password: User password

        Returns:
            AuthResponse with access token and user info
        """
        data: Dict[str, Any] = {"email": email, "password": password}
        response = await self._auth_request("POST", "/auth/login", data)

        # Store the access token for subsequent requests
        self._access_token = response.get("access_token")

        return AuthResponse(**response)

    async def refresh_token(self) -> AuthResponse:
        """
        Refresh the current access token.

        Returns:
            AuthResponse with new access token
        """
        response = await self._auth_request("POST", "/auth/refresh", authenticated=True)

        # Update stored token
        self._access_token = response.get("access_token")

        return AuthResponse(**response)

    async def get_current_user(self) -> User:
        """
        Get the currently authenticated user.

        Returns:
            User information
        """
        response = await self._auth_request("GET", "/auth/me", authenticated=True)
        return User(**response)

    async def logout(self) -> bool:
        """
        Logout and invalidate current session.

        Returns:
            True if successful
        """
        await self._auth_request("POST", "/auth/logout", authenticated=True)
        self._access_token = None
        return True

    async def create_api_key(
        self,
        name: str,
        permissions: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
        ip_whitelist: Optional[List[str]] = None,
    ) -> ApiKey:
        """
        Create a new API key for programmatic access.

        Args:
            name: API key name/description
            permissions: List of permissions (e.g., ["memory:read", "memory:write"])
            expires_in_days: Optional expiration in days
            ip_whitelist: Optional list of allowed IPs

        Returns:
            ApiKey with the key value (shown only once!)
        """
        data: Dict[str, Any] = {"name": name}
        if permissions:
            data["permissions"] = permissions
        if expires_in_days:
            data["expires_in_days"] = expires_in_days
        if ip_whitelist:
            data["ip_whitelist"] = ip_whitelist

        response = await self._auth_request("POST", "/auth/api-keys", data, authenticated=True)

        # API returns different field names, normalize them
        return ApiKey(
            key_id=response.get("key_id", response.get("id", "")),
            name=response.get("name", name),
            key=response.get("api_key", response.get("key")),
            permissions=response.get("permissions", []),
            expires_at=response.get("expires_at"),
        )

    async def list_api_keys(self) -> List[ApiKey]:
        """
        List all API keys for the current user.

        Returns:
            List of ApiKey objects (without key values)
        """
        response = await self._auth_request("GET", "/auth/api-keys", authenticated=True)
        keys_list = response if isinstance(response, list) else response.get("keys", [])
        return [ApiKey(**key) for key in keys_list]

    async def revoke_api_key(self, key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            key_id: The API key identifier to revoke

        Returns:
            True if revoked successfully
        """
        await self._auth_request("DELETE", f"/auth/api-keys/{key_id}", authenticated=True)
        return True

    async def list_sessions(self) -> List[Session]:
        """
        List all active sessions for the current user.

        Returns:
            List of Session objects
        """
        response = await self._auth_request("GET", "/auth/sessions", authenticated=True)
        sessions_list = response if isinstance(response, list) else response.get("sessions", [])
        return [Session(**sess) for sess in sessions_list]

    async def revoke_session(self, session_id: str) -> bool:
        """
        Revoke a specific session.

        Args:
            session_id: The session identifier to revoke

        Returns:
            True if revoked successfully
        """
        await self._auth_request("DELETE", f"/auth/sessions/{session_id}", authenticated=True)
        return True

    async def revoke_all_sessions(self) -> bool:
        """
        Revoke all sessions except the current one.

        Returns:
            True if revoked successfully
        """
        await self._auth_request("DELETE", "/auth/sessions", authenticated=True)
        return True


# ==============================================================================
# Synchronous Convenience Functions
# ==============================================================================


def add_memory_sync(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    tags: Optional[List[str]] = None,
    base_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> str:
    """Synchronous version of add_memory."""
    async def _add():
        async with CilowClient(base_url, api_key) as client:
            return await client.add_memory(content, metadata, tags)
    return asyncio.run(_add())


def search_memories_sync(
    query: str,
    limit: int = 10,
    base_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> List[SearchResult]:
    """Synchronous version of search_memories."""
    async def _search():
        async with CilowClient(base_url, api_key) as client:
            return await client.search_memories(query, limit)
    return asyncio.run(_search())


def get_memory_stats_sync(
    base_url: str = "http://localhost:8080",
    api_key: Optional[str] = None,
) -> MemoryStats:
    """Synchronous version of get_memory_stats."""
    async def _stats():
        async with CilowClient(base_url, api_key) as client:
            return await client.get_memory_stats()
    return asyncio.run(_stats())


# ==============================================================================
# Synchronous Auth Convenience Functions
# ==============================================================================


def register_sync(
    email: str,
    password: str,
    name: Optional[str] = None,
    base_url: str = "http://localhost:8080",
) -> AuthResponse:
    """Synchronous version of register."""
    async def _register():
        async with CilowClient(base_url) as client:
            return await client.register(email, password, name)
    return asyncio.run(_register())


def login_sync(
    email: str,
    password: str,
    base_url: str = "http://localhost:8080",
) -> AuthResponse:
    """Synchronous version of login."""
    async def _login():
        async with CilowClient(base_url) as client:
            return await client.login(email, password)
    return asyncio.run(_login())
