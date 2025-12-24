"""
ForgeVault SDK - Main Client

Copyright (c) 2025 ForgeVault. All Rights Reserved.
"""

import os
import json
import httpx
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator, AsyncIterator

from forgevault.prompt import Prompt
from forgevault.cache import PromptCache, FallbackStore
from forgevault.exceptions import (
    ForgeVaultError,
    AuthenticationError,
    PromptNotFoundError,
    ExecutionError,
    RateLimitError,
    ConnectionError
)

# Version - keep in sync with __init__.py
_VERSION = "0.1.4"


class Forge:
    """
    Main ForgeVault client for fetching and running prompts.
    
    Usage:
        forge = Forge(api_key="fv_xxx")
        
        # Get and run a prompt
        prompt = forge.get_prompt("my-prompt")
        result = prompt.run(name="John")
        
        # Or run directly
        result = forge.run_prompt(prompt_name="my-prompt", variables={"name": "John"})
    """

    DEFAULT_BASE_URL = "https://forgevault.onrender.com/api/v1"
    DEFAULT_TIMEOUT = 120  # 2 minutes for LLM calls

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        cache_ttl: int = 300,
        cache_enabled: bool = True,
        fallback_enabled: bool = True,
        fallback_path: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize the ForgeVault client.
        
        Args:
            api_key: Your ForgeVault API key (or set FORGEVAULT_API_KEY env var)
            timeout: Request timeout in seconds
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            cache_enabled: Enable in-memory caching
            fallback_enabled: Enable fallback storage for offline use
            fallback_path: Path to fallback storage file
        """
        self.api_key = api_key or os.getenv("FORGEVAULT_API_KEY") or self._load_saved_key()
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key, set FORGEVAULT_API_KEY env var, or run 'forgevault login'."
            )

        self.base_url = (base_url or os.getenv("FORGEVAULT_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._user_agent = user_agent or f"forgevault-python/{_VERSION}"
        self._cache = PromptCache(ttl=cache_ttl) if cache_enabled else None
        self._fallback = FallbackStore(fallback_path) if fallback_enabled else None
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._get_headers()
        )
        self._async_client: Optional[httpx.AsyncClient] = None

    def _load_saved_key(self) -> Optional[str]:
        """Load API key from CLI config file (~/.forgevault/config.json)"""
        config_file = Path.home() / ".forgevault" / "config.json"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
                return config.get("api_key")
            except Exception:
                pass
        return None

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": self._user_agent
        }

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers=self._get_headers()
            )
        return self._async_client

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        # Try to parse JSON, handle non-JSON responses gracefully
        def safe_json():
            try:
                return response.json()
            except Exception:
                return None
        
        if response.status_code == 401:
            raise AuthenticationError()
        if response.status_code == 403:
            raise AuthenticationError("Insufficient permissions")
        if response.status_code == 404:
            data = safe_json()
            if data and isinstance(data, dict):
                detail = data.get("detail", {})
                msg = detail.get("error", "Prompt not found") if isinstance(detail, dict) else str(detail)
            else:
                msg = "Prompt not found"
            raise PromptNotFoundError(msg)
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)
        if response.status_code >= 500:
            raise ForgeVaultError(f"Server error: {response.status_code}", error_code="SERVER_ERROR")
        if response.status_code >= 400:
            data = safe_json()
            if data and isinstance(data, dict):
                detail = data.get("detail", {})
                msg = detail.get("error", "Unknown error") if isinstance(detail, dict) else str(detail)
                code = detail.get("error_code", "UNKNOWN") if isinstance(detail, dict) else "UNKNOWN"
            else:
                msg = f"Request failed with status {response.status_code}"
                code = "UNKNOWN"
            raise ForgeVaultError(msg, error_code=code)
        
        # Succss - parse JSON
        data = safe_json()
        if data is None:
            raise ForgeVaultError(
                f"Invalid response from server (expected JSON, got: {response.text[:100]}...)" 
                if response.text else "Empty response from server",
                error_code="INVALID_RESPONSE"
            )
        return data

    # ==================== PROMPT OPERATIONS ====================

    def get_prompt(
        self,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Prompt:
        """
        Fetch a prompt by ID or name.
        
        Args:
            prompt_name: The prompt name (use this OR prompt_id)
            prompt_id: The prompt ID (use this OR prompt_name)
            version: Specific version (commit_id) or None for latest
            
        Returns:
            Prompt object
        """
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        cache_key = prompt_id or prompt_name
        if self._cache:
            cached = self._cache.get(cache_key, version)
            if cached:
                return self._create_prompt_from_data(cached)

        payload = {}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version

        try:
            response = self._client.post("/sdk/get_prompt", json=payload)
            data = self._handle_response(response)
        except httpx.ConnectError:
            if self._fallback:
                fallback_data = self._fallback.get(cache_key, version)
                if fallback_data:
                    return self._create_prompt_from_data(fallback_data)
            raise ConnectionError()

        if self._cache:
            self._cache.set(cache_key, data, version)
        if self._fallback:
            self._fallback.save(cache_key, data, version)

        return self._create_prompt_from_data(data)

    async def get_prompt_async(
        self,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        version: Optional[str] = None
    ) -> Prompt:
        """Async version of get_prompt()"""
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        cache_key = prompt_id or prompt_name
        if self._cache:
            cached = self._cache.get(cache_key, version)
            if cached:
                return self._create_prompt_from_data(cached)

        payload = {}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version

        try:
            client = self._get_async_client()
            response = await client.post("/sdk/get_prompt", json=payload)
            data = self._handle_response(response)
        except httpx.ConnectError:
            if self._fallback:
                fallback_data = self._fallback.get(cache_key, version)
                if fallback_data:
                    return self._create_prompt_from_data(fallback_data)
            raise ConnectionError()

        if self._cache:
            self._cache.set(cache_key, data, version)
        if self._fallback:
            self._fallback.save(cache_key, data, version)

        return self._create_prompt_from_data(data)

    def list_prompts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all prompts in the workspace.
        
        Args:
            limit: Maximum number of prompts to return (default 100)
        
        Returns:
            List of prompt metadata dicts
        """
        response = self._client.post("/sdk/list_prompts", json={"limit": limit})
        data = self._handle_response(response)
        return data.get("prompts", [])

    async def list_prompts_async(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Async version of list_prompts()"""
        client = self._get_async_client()
        response = await client.post("/sdk/list_prompts", json={"limit": limit})
        data = self._handle_response(response)
        return data.get("prompts", [])

    def get_versions(
        self,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get version history for a prompt.
        
        Args:
            prompt_name: The prompt name (use this OR prompt_id)
            prompt_id: The prompt ID (use this OR prompt_name)
            
        Returns:
            List of version dicts with 'version' and 'commit_message'
        """
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name

        response = self._client.post("/sdk/get_versions", json=payload)
        data = self._handle_response(response)
        return data.get("versions", [])

    async def get_versions_async(
        self,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Async version of get_versions()"""
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name

        client = self._get_async_client()
        response = await client.post("/sdk/get_versions", json=payload)
        data = self._handle_response(response)
        return data.get("versions", [])

    def _create_prompt_from_data(self, data: Dict[str, Any]) -> Prompt:
        metadata = data.get("metadata", {})
        content = data.get("content", {})
        return Prompt(
            client=self,
            prompt_id=metadata.get("id"),
            name=metadata.get("name"),
            description=metadata.get("description"),
            use_case=metadata.get("use_case"),
            prompt_type=metadata.get("prompt_type"),
            version=metadata.get("version"),
            variables=metadata.get("variables", []),
            system_prompt=content.get("system_prompt"),
            user_prompt=content.get("user_prompt"),
            few_shot_examples=content.get("few_shot_examples"),
            created_at=metadata.get("created_at"),
            updated_at=metadata.get("updated_at"),
            config=data.get("config")
        )

    # ==================== RENDER & RUN ====================

    def render_prompt(
        self,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Render a prompt with variables (no LLM call).
        
        Args:
            prompt_name: The prompt name (use this OR prompt_id)
            prompt_id: The prompt ID (use this OR prompt_name)
            variables: Variables to substitute
            version: Specific version or None for latest
            
        Returns:
            Dict with rendered messages
        """
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {"variables": variables or {}}
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version
            
        response = self._client.post("/sdk/render_prompt", json=payload)
        return self._handle_response(response)

    def run_prompt(
        self,
        model: str,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a prompt with variables.
        
        Args:
            model: The LLM model to use (required)
            prompt_name: The prompt name (use this OR prompt_id)
            prompt_id: The prompt ID (use this OR prompt_name)
            variables: Variables to substitute
            version: Specific version or None for latest
            temperature: Override temperature (0-2)
            max_tokens: Override max tokens
            return_metadata: If True (default), return full response with token_usage, cost, etc.
                             If False, return just the output string.
            
        Returns:
            dict: Full response with output, token_usage, cost, llm_config (default)
                  Keys: output, prompt_id, prompt_name, version, model, llm_config,
                        latency_ms, token_usage, estimated_cost, input_cost, output_cost
            str: Just the LLM response (if return_metadata=False)
        """
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {
            "variables": variables or {},
            "model": model
        }
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response = self._client.post("/sdk/run_prompt", json=payload)
        data = self._handle_response(response)
        
        if not data.get("success"):
            raise ExecutionError(data.get("error", "Execution failed"), model=model)
        
        if return_metadata:
            return {
                "output": data.get("output", ""),
                "prompt_id": data.get("prompt_id"),
                "prompt_name": data.get("prompt_name"),
                "version": data.get("version"),
                "model": data.get("model"),
                "llm_config": data.get("llm_config"),
                "latency_ms": data.get("latency_ms"),
                "token_usage": data.get("token_usage"),
                "estimated_cost": data.get("estimated_cost"),
                "input_cost": data.get("input_cost"),
                "output_cost": data.get("output_cost")
            }
        
        return data.get("output", "")

    async def run_prompt_async(
        self,
        model: str,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True
    ) -> Dict[str, Any]:
        """Async version of run_prompt() - see run_prompt() for full docs"""
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {
            "variables": variables or {},
            "model": model
        }
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        client = self._get_async_client()
        response = await client.post("/sdk/run_prompt", json=payload)
        data = self._handle_response(response)
        
        if not data.get("success"):
            raise ExecutionError(data.get("error", "Execution failed"), model=model)
        
        if return_metadata:
            return {
                "output": data.get("output", ""),
                "prompt_id": data.get("prompt_id"),
                "prompt_name": data.get("prompt_name"),
                "version": data.get("version"),
                "model": data.get("model"),
                "llm_config": data.get("llm_config"),
                "latency_ms": data.get("latency_ms"),
                "token_usage": data.get("token_usage"),
                "estimated_cost": data.get("estimated_cost"),
                "input_cost": data.get("input_cost"),
                "output_cost": data.get("output_cost")
            }
        
        return data.get("output", "")

    # ==================== STREAMING ====================

    def run_prompt_stream(
        self,
        model: str,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True
    ):
        """
        Stream a prompt execution - yields text chunks as they arrive.
        
        Args:
            model: The LLM model to use (required)
            prompt_name: The prompt name (use this OR prompt_id)
            prompt_id: The prompt ID (use this OR prompt_name)
            variables: Variables to substitute
            version: Specific version or None for latest
            temperature: Override temperature (0-2)
            max_tokens: Override max tokens
            return_metadata: If True (default), yields final metadata dict after all chunks
            
        Yields:
            str: Text chunks as they arrive from the LLM
            dict: Final metadata (if return_metadata=True) with token_usage, cost, latency
        """
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {
            "variables": variables or {},
            "model": model
        }
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        with httpx.Client(timeout=None) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/sdk/run_prompt_stream",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status_code != 200:
                    self._handle_response(response)
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "chunk":
                                yield data.get("content", "")
                            elif data.get("type") == "done" and return_metadata:
                                yield {
                                    "type": "metadata",
                                    "latency_ms": data.get("latency_ms"),
                                    "token_usage": data.get("token_usage"),
                                    "estimated_cost": data.get("estimated_cost"),
                                    "input_cost": data.get("input_cost"),
                                    "output_cost": data.get("output_cost")
                                }
                            elif data.get("type") == "error":
                                raise ExecutionError(data.get("error", "Stream error"), model=model)
                        except json.JSONDecodeError:
                            continue

    async def run_prompt_stream_async(
        self,
        model: str,
        prompt_name: Optional[str] = None,
        prompt_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True
    ):
        """Async streaming version of run_prompt - yields text chunks and final metadata"""
        if not prompt_id and not prompt_name:
            raise ValueError("Must provide either prompt_id or prompt_name")
        
        payload = {
            "variables": variables or {},
            "model": model
        }
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if prompt_name:
            payload["prompt_name"] = prompt_name
        if version:
            payload["version"] = version
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/sdk/run_prompt_stream",
                json=payload,
                headers=self._get_headers()
            ) as response:
                if response.status_code != 200:
                    self._handle_response(response)
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("type") == "chunk":
                                yield data.get("content", "")
                            elif data.get("type") == "done" and return_metadata:
                                yield {
                                    "type": "metadata",
                                    "latency_ms": data.get("latency_ms"),
                                    "token_usage": data.get("token_usage"),
                                    "estimated_cost": data.get("estimated_cost"),
                                    "input_cost": data.get("input_cost"),
                                    "output_cost": data.get("output_cost")
                                }
                            elif data.get("type") == "error":
                                raise ExecutionError(data.get("error", "Stream error"), model=model)
                        except json.JSONDecodeError:
                            continue

    # ==================== CACHE MANAGEMENT ====================

    def invalidate_cache(self, prompt: Optional[str] = None, version: Optional[str] = None):
        """
        Invalidate cached prompts.
        
        Args:
            prompt: Specific prompt to invalidate, or None for all
            version: Specific version, or None for all versions of prompt
        """
        if self._cache:
            if prompt:
                self._cache.invalidate(prompt, version)
            else:
                self._cache.invalidate_all()

    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self._cache:
            return self._cache.stats()
        return {"enabled": False}

    # ==================== LIFECYCLE ====================

    def close(self):
        """Close HTTP connections"""
        self._client.close()
        if self._async_client:
            pass  # Async client should be closed in async context

    async def aclose(self):
        """Async close HTTP connections"""
        self._client.close()
        if self._async_client:
            await self._async_client.aclose()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()
