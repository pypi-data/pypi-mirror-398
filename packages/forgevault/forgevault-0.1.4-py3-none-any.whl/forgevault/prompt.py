"""
ForgeVault SDK - Prompt Class

Copyright (c) 2025 ForgeVault. All Rights Reserved.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class PromptVariable:
    """Represents a variable in a prompt template"""
    name: str
    type: str = "string"
    description: Optional[str] = None
    required: bool = True
    default: Optional[str] = None


@dataclass
class PromptMetadata:
    """Metadata about a prompt"""
    id: str
    name: str
    description: Optional[str]
    prompt_type: str
    version: str
    variables: List[PromptVariable]
    created_at: str
    updated_at: str


class Prompt:
    """
    Represents a prompt fetched from ForgeVault.
    Provides methods to render and run the prompt.
    """

    def __init__(
        self,
        client,  # Reference to Forge client
        prompt_id: str,
        name: str,
        description: Optional[str],
        use_case: Optional[str],
        prompt_type: str,
        version: str,
        variables: List[Dict[str, Any]],
        system_prompt: Optional[str],
        user_prompt: str,
        few_shot_examples: Optional[str],
        created_at: str,
        updated_at: str,
        config: Dict[str, Any] = None
    ):
        self._client = client
        self.id = prompt_id
        self.name = name
        self.description = description
        self.use_case = use_case
        self.prompt_type = prompt_type
        self.version = version
        self.variables = [PromptVariable(**v) for v in variables]
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.few_shot_examples = few_shot_examples
        self.created_at = created_at
        self.updated_at = updated_at
        self._config = config or {}

    @property
    def metadata(self) -> PromptMetadata:
        """Get prompt metadata"""
        return PromptMetadata(
            id=self.id,
            name=self.name,
            description=self.description,
            prompt_type=self.prompt_type,
            version=self.version,
            variables=self.variables,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @property
    def variable_names(self) -> List[str]:
        """Get list of variable names"""
        return [v.name for v in self.variables]

    @property
    def required_variables(self) -> List[str]:
        """Get list of required variable names"""
        return [v.name for v in self.variables if v.required]

    def render(self, variables: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """
        Render the prompt with provided variables.
        
        Args:
            variables: Dict of variable values (or pass as kwargs)
            **kwargs: Variable values as keyword arguments
            
        Returns:
            Dict with 'messages' list in OpenAI format
        """
        all_variables = variables or {}
        all_variables.update(kwargs)
        
        return self._client.render_prompt(
            prompt_id=self.id,
            variables=all_variables,
            version=self.version
        )

    def run(
        self,
        model: str,
        variables: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Render and execute the prompt.
        
        Args:
            model: The LLM model to use (required)
            variables: Dict of variable values (or pass as kwargs)
            temperature: Override temperature (0-2)
            max_tokens: Override max tokens
            return_metadata: If True (default), return dict with token_usage, cost, llm_config
            **kwargs: Variable values as keyword arguments
            
        Returns:
            dict: Full response with output, token_usage, cost, llm_config (default)
            str: Just the LLM response (if return_metadata=False)
        """
        # Support both: variables={} dict or keyword arguments
        all_variables = variables or {}
        all_variables.update(kwargs)
        
        return self._client.run_prompt(
            model=model,
            prompt_id=self.id,
            variables=all_variables,
            version=self.version,
            temperature=temperature,
            max_tokens=max_tokens,
            return_metadata=return_metadata
        )

    async def run_async(
        self,
        model: str,
        variables: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        return_metadata: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Async version of run().
        
        Args:
            model: The LLM model to use (required)
            variables: Dict of variable values (or pass as kwargs)
            temperature: Override temperature (0-2)
            max_tokens: Override max tokens
            return_metadata: If True (default), return dict with token_usage, cost, llm_config
            **kwargs: Variable values as keyword arguments
            
        Returns:
            dict: Full response with output, token_usage, cost, llm_config (default)
            str: Just the LLM response (if return_metadata=False)
        """
        all_variables = variables or {}
        all_variables.update(kwargs)
        
        return await self._client.run_prompt_async(
            model=model,
            prompt_id=self.id,
            variables=all_variables,
            version=self.version,
            temperature=temperature,
            max_tokens=max_tokens,
            return_metadata=return_metadata
        )

    def validate_variables(self, variables: Dict[str, Any]) -> List[str]:
        """
        Check if all required variables are provided.
        
        Returns:
            List of missing required variable names
        """
        provided = set(variables.keys())
        required = set(self.required_variables)
        return list(required - provided)

    def __repr__(self) -> str:
        return f"Prompt(id='{self.id}', name='{self.name}', version='{self.version}')"

    def __str__(self) -> str:
        return f"Prompt: {self.name} (v{self.version})"

