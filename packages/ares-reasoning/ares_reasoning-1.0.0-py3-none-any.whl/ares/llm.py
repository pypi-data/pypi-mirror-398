"""
LLM Provider abstraction for ARES.
Supports Ollama (local) and OpenRouter (API).
"""

import os
import json
import requests
from abc import ABC, abstractmethod
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            raise RuntimeError(f"Ollama generation failed: {e}")
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False


class OpenRouterProvider(LLMProvider):
    """OpenRouter API provider."""
    
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=120
            )
            
            # Handle rate limits with retry
            if response.status_code == 429:
                import time
                print("Rate limited, waiting 30 seconds...")
                time.sleep(30)
                response = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120
                )
            
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenRouter generation failed: {e}")
    
    def is_available(self) -> bool:
        return bool(self.api_key)


def get_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    provider_name = os.getenv("ARES_LLM_PROVIDER", "ollama").lower()
    
    if provider_name == "ollama":
        provider = OllamaProvider()
        if not provider.is_available():
            print("Warning: Ollama not available, trying OpenRouter...")
            provider = OpenRouterProvider()
    elif provider_name == "openrouter":
        provider = OpenRouterProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return provider


# Simple test
if __name__ == "__main__":
    provider = get_provider()
    print(f"Provider available: {provider.is_available()}")
    if provider.is_available():
        response = provider.generate("What is 2 + 2?")
        print(f"Response: {response}")
