"""
PromptGuard Client - Drop-in replacement for OpenAI client

Provides the same interface as OpenAI's client but routes through PromptGuard
for security scanning, caching, and cost optimization.
"""

import json
import os
from typing import Any, Dict, Iterator, List, Optional, Union

import httpx

from promptguard.config import Config


class ChatCompletions:
    """Chat completions API (OpenAI-compatible)"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def create(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """
        Create a chat completion.

        This is a drop-in replacement for openai.chat.completions.create()
        but routes through PromptGuard for security scanning.

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-sonnet")
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters passed to the model

        Returns:
            Completion response (same format as OpenAI)
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        if stream:
            return self._stream_completion(payload)

        response = self._client._request("POST", "/chat/completions", json=payload)
        return response

    def _stream_completion(
        self,
        payload: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream a chat completion"""
        payload["stream"] = True

        with self._client._client.stream(
            "POST",
            f"{self._client.config.base_url}/chat/completions",
            json=payload,
            headers=self._client._get_headers(),
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    yield json.loads(data)


class Chat:
    """Chat API namespace"""

    def __init__(self, client: "PromptGuard"):
        self.completions = ChatCompletions(client)


class Completions:
    """Legacy completions API (OpenAI-compatible)"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def create(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create a completion (legacy API)"""
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        return self._client._request("POST", "/completions", json=payload)


class Embeddings:
    """Embeddings API"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def create(
        self,
        model: str,
        input: Union[str, List[str]],
        **kwargs,
    ) -> Dict[str, Any]:
        """Create embeddings"""
        payload = {
            "model": model,
            "input": input,
            **kwargs,
        }

        return self._client._request("POST", "/embeddings", json=payload)


class Security:
    """PromptGuard-specific security APIs"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def scan(
        self,
        content: str,
        content_type: str = "prompt",
    ) -> Dict[str, Any]:
        """
        Scan content for security issues.

        Args:
            content: Text to scan
            content_type: "prompt" or "response"

        Returns:
            Scan result with threats detected
        """
        return self._client._request(
            "POST",
            "/security/scan",
            json={"content": content, "type": content_type},
        )

    def redact(
        self,
        content: str,
        pii_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Redact PII from content.

        Args:
            content: Text to redact
            pii_types: Specific PII types to redact (default: all)

        Returns:
            Redacted content
        """
        return self._client._request(
            "POST",
            "/security/redact",
            json={"content": content, "pii_types": pii_types},
        )


class Memory:
    """PromptGuard Memory API"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def store(
        self,
        agent_id: str,
        content: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> Dict[str, Any]:
        """
        Store a memory for an AI agent.

        Args:
            agent_id: Unique identifier for the agent
            content: Content to store in memory
            session_id: Optional session identifier
            metadata: Optional metadata dict
            importance: Importance score (0.0 to 1.0)

        Returns:
            Dict with entry_id and status
        """
        return self._client._request(
            "POST",
            "/memory/store",
            json={
                "agent_id": agent_id,
                "content": content,
                "session_id": session_id,
                "metadata": metadata,
                "importance": importance,
            },
        )

    def retrieve(
        self,
        agent_id: str,
        query: str,
        top_k: int = 5,
        min_relevance: float = 0.5,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve relevant memories for an AI agent.

        Args:
            agent_id: Unique identifier for the agent
            query: Query string to match against memories
            top_k: Number of results to return
            min_relevance: Minimum relevance score
            session_id: Optional session filter

        Returns:
            Dict with memories and stats
        """
        return self._client._request(
            "POST",
            "/memory/retrieve",
            json={
                "agent_id": agent_id,
                "query": query,
                "top_k": top_k,
                "min_relevance": min_relevance,
                "session_id": session_id,
            },
        )

    def clear(
        self,
        agent_id: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clear memories for an agent.

        Args:
            agent_id: Unique identifier for the agent
            session_id: Optional - clear only this session

        Returns:
            Dict with deletion status
        """
        url = f"/memory/{agent_id}"
        if session_id:
            url += f"?session_id={session_id}"
        return self._client._request("DELETE", url)

    def stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        return self._client._request("GET", "/memory/stats")


class Scrape:
    """PromptGuard Secure Web Scraping API"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def url(
        self,
        url: str,
        render_js: bool = False,
        extract_text: bool = True,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Securely scrape a URL with threat scanning.

        Args:
            url: URL to scrape
            render_js: Whether to render JavaScript
            extract_text: Whether to extract clean text
            timeout: Request timeout in seconds

        Returns:
            Dict with content and threat analysis
        """
        return self._client._request(
            "POST",
            "/scrape",
            json={
                "url": url,
                "render_js": render_js,
                "extract_text": extract_text,
                "timeout": timeout,
            },
        )

    def batch(
        self,
        urls: List[str],
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Batch scrape multiple URLs.

        Args:
            urls: List of URLs to scrape
            **kwargs: Same options as single scrape

        Returns:
            Dict with job_id for tracking
        """
        return self._client._request(
            "POST",
            "/scrape/batch",
            json={"urls": urls, **kwargs},
        )


class Agent:
    """PromptGuard AI Agent Security API"""

    def __init__(self, client: "PromptGuard"):
        self._client = client

    def validate_tool(
        self,
        agent_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate a tool call before execution.

        Args:
            agent_id: Unique identifier for the agent
            tool_name: Name of the tool being called
            arguments: Arguments being passed to the tool
            session_id: Optional session identifier

        Returns:
            Dict with allowed status, risk score, and warnings
        """
        return self._client._request(
            "POST",
            "/agent/validate-tool",
            json={
                "agent_id": agent_id,
                "tool_name": tool_name,
                "arguments": arguments,
                "session_id": session_id,
            },
        )

    def analyze_behavior(
        self,
        agent_id: str,
        recent_actions: List[Dict[str, Any]],
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze agent behavior for anomalies.

        Args:
            agent_id: Unique identifier for the agent
            recent_actions: List of recent tool calls/actions
            session_id: Optional session identifier

        Returns:
            Dict with anomaly analysis
        """
        return self._client._request(
            "POST",
            "/agent/analyze-behavior",
            json={
                "agent_id": agent_id,
                "recent_actions": recent_actions,
                "session_id": session_id,
            },
        )

    def stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for an agent"""
        return self._client._request("GET", f"/agent/{agent_id}/stats")


class RedTeam:
    """PromptGuard Red Team Testing API"""

    def __init__(self, client: "PromptGuard"):
        self._client = client
        # Note: RedTeam API requires internal/admin access
        self._base = "/internal/redteam"

    def list_tests(self) -> Dict[str, Any]:
        """List all available red team tests"""
        return self._client._request("GET", f"{self._base}/tests")

    def run_test(
        self,
        test_name: str,
        target_preset: str = "default",
    ) -> Dict[str, Any]:
        """
        Run a specific red team test.

        Args:
            test_name: Name of the test to run
            target_preset: Policy preset to test against

        Returns:
            Test result with decision and details
        """
        return self._client._request(
            "POST",
            f"{self._base}/test/{test_name}",
            json={"target_preset": target_preset},
        )

    def run_all(
        self,
        target_preset: str = "default",
    ) -> Dict[str, Any]:
        """
        Run all red team tests.

        Args:
            target_preset: Policy preset to test against

        Returns:
            Summary with all test results
        """
        return self._client._request(
            "POST",
            f"{self._base}/test-all",
            json={"target_preset": target_preset},
        )

    def run_custom(
        self,
        prompt: str,
        target_preset: str = "default",
    ) -> Dict[str, Any]:
        """
        Run a custom adversarial prompt test.

        Args:
            prompt: Custom adversarial prompt to test
            target_preset: Policy preset to test against

        Returns:
            Test result
        """
        return self._client._request(
            "POST",
            f"{self._base}/test-custom",
            json={
                "custom_prompt": prompt,
                "target_preset": target_preset,
            },
        )


class PromptGuard:
    """
    PromptGuard client - Drop-in security for AI applications.

    Usage:
        from promptguard import PromptGuard

        # Initialize client
        pg = PromptGuard(api_key="pg_xxx")

        # Use like OpenAI client
        response = pg.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello!"}]
        )

        # Security-specific features
        scan_result = pg.security.scan("Check this content")

        # Memory features
        pg.memory.store("User prefers Python", memory_type="preference")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Config] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize PromptGuard client.

        Args:
            api_key: PromptGuard API key (or set PROMPTGUARD_API_KEY env var)
            base_url: API base URL (default: https://api.promptguard.co/api/v1/proxy)
            config: Optional Config object
            timeout: Request timeout in seconds
        """
        self.config = config or Config(
            api_key=api_key or os.environ.get("PROMPTGUARD_API_KEY", ""),
            base_url=base_url or os.environ.get(
                "PROMPTGUARD_BASE_URL",
                "https://api.promptguard.co/api/v1/proxy"
            ),
        )

        if not self.config.api_key:
            raise ValueError(
                "API key required. Pass api_key parameter or set PROMPTGUARD_API_KEY environment variable."
            )

        self._client = httpx.Client(timeout=timeout)

        # API namespaces (OpenAI-compatible)
        self.chat = Chat(self)
        self.completions = Completions(self)
        self.embeddings = Embeddings(self)

        # PromptGuard-specific APIs
        self.security = Security(self)
        self.memory = Memory(self)
        self.scrape = Scrape(self)
        self.agent = Agent(self)
        self.redteam = RedTeam(self)

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "X-PromptGuard-SDK": "python",
            "X-PromptGuard-Version": "0.1.0",
        }

    def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make API request"""
        url = f"{self.config.base_url}{path}"
        headers = self._get_headers()

        response = self._client.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            raise PromptGuardError(
                message=error_data.get("error", {}).get("message", "Request failed"),
                code=error_data.get("error", {}).get("code", "UNKNOWN"),
                status_code=response.status_code,
            )

        return response.json()

    def close(self):
        """Close the client"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class PromptGuardAsync:
    """Async version of PromptGuard client"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        config: Optional[Config] = None,
        timeout: float = 30.0,
    ):
        self.config = config or Config(
            api_key=api_key or os.environ.get("PROMPTGUARD_API_KEY", ""),
            base_url=base_url or os.environ.get(
                "PROMPTGUARD_BASE_URL",
                "https://api.promptguard.co/api/v1/proxy"
            ),
        )

        if not self.config.api_key:
            raise ValueError("API key required")

        self._client = httpx.AsyncClient(timeout=timeout)

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> Dict[str, Any]:
        """Make async API request"""
        url = f"{self.config.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

        response = await self._client.request(
            method,
            url,
            headers=headers,
            **kwargs,
        )

        if response.status_code >= 400:
            error_data = response.json() if response.content else {}
            raise PromptGuardError(
                message=error_data.get("error", {}).get("message", "Request failed"),
                code=error_data.get("error", {}).get("code", "UNKNOWN"),
                status_code=response.status_code,
            )

        return response.json()

    async def close(self):
        """Close the client"""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


class PromptGuardError(Exception):
    """Error from PromptGuard API"""

    def __init__(self, message: str, code: str, status_code: int):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(f"{code}: {message}")
