"""
Tests for ForgeVault SDK Client

Copyright (c) 2025 ForgeVault. All Rights Reserved.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from forgevault import Forge
from forgevault.exceptions import (
    AuthenticationError,
    PromptNotFoundError,
    ForgeVaultError
)


class TestForgeInit:
    """Tests for Forge client initialization"""

    def test_init_with_api_key(self):
        """Should initialize with provided API key"""
        forge = Forge(api_key="fv_test123")
        assert forge.api_key == "fv_test123"
        forge.close()

    def test_init_without_api_key_raises(self):
        """Should raise AuthenticationError without API key"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(AuthenticationError):
                Forge(api_key=None)

    def test_init_with_env_var(self):
        """Should use FORGEVAULT_API_KEY env var"""
        with patch.dict("os.environ", {"FORGEVAULT_API_KEY": "fv_env123"}):
            forge = Forge()
            assert forge.api_key == "fv_env123"
            forge.close()

    def test_custom_base_url(self):
        """Should accept custom base URL"""
        forge = Forge(api_key="fv_test", base_url="https://custom.api.com")
        assert forge.base_url == "https://custom.api.com"
        forge.close()

    def test_strips_trailing_slash(self):
        """Should strip trailing slash from base URL"""
        forge = Forge(api_key="fv_test", base_url="https://api.com/")
        assert forge.base_url == "https://api.com"
        forge.close()


class TestForgeGetPrompt:
    """Tests for Forge.get_prompt() method"""

    @pytest.fixture
    def forge(self):
        forge = Forge(api_key="fv_test", cache_enabled=False)
        yield forge
        forge.close()

    @pytest.fixture
    def mock_response_data(self):
        return {
            "metadata": {
                "id": "507f1f77bcf86cd799439011",
                "name": "test-prompt",
                "description": "Test prompt",
                "prompt_type": "System User",
                "version": "abc123",
                "variables": [{"name": "input", "type": "string", "required": True}],
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00"
            },
            "content": {
                "system_prompt": "You are helpful",
                "user_prompt": "Process: {input}",
                "few_shot_examples": None
            },
            "config": {
                "model": "gpt-4",
                "provider": "openai"
            }
        }

    def test_get_by_name(self, forge, mock_response_data):
        """Should fetch prompt by name"""
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            prompt = forge.get_prompt("test-prompt")

            assert prompt.name == "test-prompt"
            assert prompt.id == "507f1f77bcf86cd799439011"
            mock_get.assert_called_once()

    def test_get_by_id(self, forge, mock_response_data):
        """Should fetch prompt by ID"""
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response

            prompt = forge.get_prompt("507f1f77bcf86cd799439011")

            assert prompt.id == "507f1f77bcf86cd799439011"

    def test_get_not_found(self, forge):
        """Should raise PromptNotFoundError for 404"""
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
            mock_get.return_value = mock_response

            with pytest.raises(PromptNotFoundError):
                forge.get_prompt("nonexistent")

    def test_get_auth_error(self, forge):
        """Should raise AuthenticationError for 401"""
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            with pytest.raises(AuthenticationError):
                forge.get_prompt("test")


class TestForgeCache:
    """Tests for caching functionality"""

    def test_cache_hit(self):
        """Should return cached prompt on second call"""
        forge = Forge(api_key="fv_test", cache_enabled=True, cache_ttl=300)
        
        mock_data = {
            "metadata": {
                "id": "123", "name": "test", "description": None,
                "prompt_type": "User Only", "version": "v1",
                "variables": [], "created_at": "2025-01-01", "updated_at": "2025-01-01"
            },
            "content": {"system_prompt": None, "user_prompt": "Hello", "few_shot_examples": None},
            "config": {}
        }
        
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            # First call - hits API
            forge.get_prompt("test")
            # Second call - should use cache
            forge.get_prompt("test")

            # API should only be called once
            assert mock_get.call_count == 1

        forge.close()

    def test_cache_disabled(self):
        """Should not cache when disabled"""
        forge = Forge(api_key="fv_test", cache_enabled=False)
        
        mock_data = {
            "metadata": {
                "id": "123", "name": "test", "description": None,
                "prompt_type": "User Only", "version": "v1",
                "variables": [], "created_at": "2025-01-01", "updated_at": "2025-01-01"
            },
            "content": {"system_prompt": None, "user_prompt": "Hello", "few_shot_examples": None},
            "config": {}
        }
        
        with patch.object(forge._client, 'get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_data
            mock_get.return_value = mock_response

            forge.get_prompt("test")
            forge.get_prompt("test")

            # API should be called twice
            assert mock_get.call_count == 2

        forge.close()


class TestPrompt:
    """Tests for Prompt object"""

    @pytest.fixture
    def prompt(self):
        mock_client = Mock()
        from forgevault.prompt import Prompt
        return Prompt(
            client=mock_client,
            prompt_id="123",
            name="test-prompt",
            description="Test",
            prompt_type="System User",
            version="v1",
            variables=[
                {"name": "input", "type": "string", "required": True},
                {"name": "optional", "type": "string", "required": False}
            ],
            system_prompt="System",
            user_prompt="User: {input}",
            few_shot_examples=None,
            created_at="2025-01-01",
            updated_at="2025-01-01"
        )

    def test_variable_names(self, prompt):
        """Should return list of variable names"""
        assert prompt.variable_names == ["input", "optional"]

    def test_required_variables(self, prompt):
        """Should return only required variables"""
        assert prompt.required_variables == ["input"]

    def test_validate_variables_missing(self, prompt):
        """Should return missing required variables"""
        missing = prompt.validate_variables({"optional": "value"})
        assert missing == ["input"]

    def test_validate_variables_complete(self, prompt):
        """Should return empty list when all required provided"""
        missing = prompt.validate_variables({"input": "value"})
        assert missing == []

