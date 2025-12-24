import os
import json
import logging
import requests
from typing import List, Generator, Any, Dict

from langextract import providers
from langextract.core import base_model, types

logger = logging.getLogger(__name__)

@providers.registry.register(r"^openrouter/.*")
class OpenRouterProvider(base_model.BaseLanguageModel):
    """
    Custom provider for OpenRouter API to be used with LangExtract.
    Matches model_id starting with 'openrouter/'.
    """
    def __init__(self, model_id: str, **kwargs):
        super().__init__()
        # Strip the prefix to get the actual model name for OpenRouter
        self.model_name = model_id.replace("openrouter/", "")
        
        # Check for API key in kwargs or env
        # Prioritize OPENROUTER_API_KEY from environment, then kwargs
        # This prevents collisions where 'gemini' in model_id causes the factory 
        # to inject a Google API key into kwargs.
        self.api_key = (os.environ.get("OPENROUTER_API_KEY") or kwargs.get("api_key") or "").strip()
        # Remove any surrounding quotes that might have been added by shell
        if self.api_key.startswith('"') and self.api_key.endswith('"'):
            self.api_key = self.api_key[1:-1]
        if self.api_key.startswith("'") and self.api_key.endswith("'"):
            self.api_key = self.api_key[1:-1]

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not found in environment or kwargs.")
            
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google/langextract",
            "X-Title": "LangExtract-Plugin"
        }
        
        # Allow passing default provider options in init kwargs
        # This allows users to set defaults for this model instance in config
        self.default_provider_options = kwargs.get("provider_options", {})


    def infer(self, batch_prompts: List[str], **kwargs) -> Generator[List[types.ScoredOutput], None, None]:
        """
        Generates text using OpenRouter.
        """
        logger.debug(f"OpenRouterProvider.infer called with {len(batch_prompts)} prompts")
        
        for prompt in batch_prompts:
            messages = [{"role": "user", "content": prompt}]
            
            # Prepare provider options merging defaults with per-call kwargs if any
            provider_params = {
                "allow_fallbacks": True,
                "sort": "price",
                "data_collection": "allow"
            }
            # Update with instance defaults
            provider_params.update(self.default_provider_options)
            # Update with call-specific overrides
            if "provider_options" in kwargs:
                provider_params.update(kwargs["provider_options"])
                
            # Handle 'effort' option for reasoning
            # Defaults to 'minimal' as requested
            reasoning_effort = provider_params.pop("effort", "minimal")
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "provider": provider_params,
                "reasoning": {
                    "effort": reasoning_effort
                }
            }
            # Merge extra kwargs into payload if needed, or specific OpenRouter params
            # For now keeping it simple as per original script

            try:
                logger.debug(f"Sending request to OpenRouter for model {self.model_name}")
                response = requests.post(self.url, headers=self.headers, data=json.dumps(payload))
                response.raise_for_status()
                data = response.json()
                
                if 'choices' not in data:
                    raise ValueError(f"OpenRouter response missing 'choices': {data}")
                    
                content = data['choices'][0]['message']['content']
                
                # Usage logging
                usage = data.get('usage', {})
                usage_msg = f"Token Usage - Prompt: {usage.get('prompt_tokens')}, Completion: {usage.get('completion_tokens')}, Total: {usage.get('total_tokens')}"
                logger.info(usage_msg)
                # Print to stdout as well (since the user requested to see it)
                print(f"[OpenRouter] {usage_msg}")
                
                # Clean up content (remove markdown code blocks if present)
                # This logic is preserved from the original script as it seems important for the user's workflow
                if content.startswith("```"):
                    lines = content.split("\n", 1)
                    if len(lines) > 1:
                        content = lines[1]
                        if content.endswith("```"):
                            content = content.rsplit("\n", 1)[0]
                
                content = content.strip()
                
                yield [types.ScoredOutput(score=1.0, output=content)]
                
            except Exception as e:
                logger.error(f"Error during OpenRouter API call: {e}")
                raise e
