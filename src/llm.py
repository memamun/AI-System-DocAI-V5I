"""
Unified LLM Interface for AI-System-DocAI V5I (CPU-only)
Supports OpenAI, Anthropic, Gemini, Ollama, HuggingFace, LlamaCpp, and NoLLM backends
"""
from __future__ import annotations
import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Generator
from pathlib import Path

# Force CPU-only operation
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import torch

logger = logging.getLogger(__name__)

class BaseLLM(ABC):
    """Base class for all LLM backends"""
    
    def __init__(self):
        self.name = "base"
        self.device_string = "CPU"
    
    @abstractmethod
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response from LLM"""
        pass
    
    def generate_stream(self, system: str, user: str, max_tokens: int = 600) -> Generator[str, None, None]:
        """Generate streaming response from LLM (default implementation)"""
        # Default implementation: yield the full response at once
        response = self.generate(system, user, max_tokens)
        yield response
    
    def get_info(self) -> Dict[str, Any]:
        """Get LLM information"""
        return {
            "name": self.name,
            "device": self.device_string,
            "type": self.__class__.__name__
        }

class LlamaCppLLM(BaseLLM):
    """LlamaCpp GGUF model using llama-cpp-python (CPU-only)"""
    
    def __init__(self, model_path: Optional[str] = None, **kwargs):
        super().__init__()
        
        # Check if llama-cpp-python is available
        try:
            from llama_cpp import Llama
            self.Llama = Llama
        except ImportError:
            raise RuntimeError(
                "llama-cpp-python not installed. Install with: pip install llama-cpp-python"
            )
        
        # Get model path
        if model_path is None:
            from config import config_manager
            model_path = str(config_manager.config.llm.model_path)
        
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                f"Please download a GGUF model and configure the path in settings."
            )
        
        # CPU-only configuration
        logger.info("Using CPU for LlamaCpp model")
        
        # Initialize model
        try:
            self.llm = self.Llama(
                model_path=model_path,
                n_gpu_layers=0,  # CPU-only
                n_batch=128,
                n_ctx=2048,
                use_mmap=True,
                use_mlock=False,
                verbose=False
            )
            
            self.name = f"llamacpp-gguf (CPU)"
            logger.info(f"LlamaCpp model loaded successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to load LlamaCpp model: {e}")
            raise
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using LlamaCpp"""
        try:
            # Generic prompt format
            prompt = f"<s>[INST] {system}\n\n{user} [/INST]"
            
            start_time = time.time()
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                top_p=0.9,
                stop=["</s>", "[INST]", "[/INST]"]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"LlamaCpp generated response in {elapsed:.2f}s")
            
            return response["choices"][0]["text"].strip()
            
        except Exception as e:
            logger.error(f"LlamaCpp generation failed: {e}")
            raise

class OpenAIChat(BaseLLM):
    """OpenAI/OpenRouter/Compatible API client"""
    
    def __init__(self, model: str = "gpt-4o-mini"):
        super().__init__()
        
        from openai import OpenAI
        
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        
        # Ensure base_url has proper protocol
        if base_url and not base_url.startswith(("http://", "https://")):
            base_url = f"https://{base_url}"
        
        # Configure for OpenRouter if using their endpoint
        if base_url and "openrouter.ai" in base_url:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/ai-system-solutions/docai-v5i",
                    "X-Title": "AI-System-DocAI V5I"
                }
            )
        else:
            self.client = OpenAI(base_url=base_url, api_key=api_key) if base_url else OpenAI(api_key=api_key)
        
        self.model = model
        self.name = f"openai:{model}"
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using OpenAI API"""
        try:
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            elapsed = time.time() - start_time
            logger.info(f"OpenAI API generated response in {elapsed:.2f}s")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API generation failed: {e}")
            raise
    
    def generate_stream(self, system: str, user: str, max_tokens: int = 600) -> Generator[str, None, None]:
        """Generate streaming response using OpenAI API"""
        try:
            start_time = time.time()
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
            
            elapsed = time.time() - start_time
            logger.info(f"OpenAI API streaming completed in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"OpenAI API streaming failed: {e}")
            # Fallback to non-streaming
            response = self.generate(system, user, max_tokens)
            yield response

class AnthropicChat(BaseLLM):
    """Anthropic Claude API client"""
    
    def __init__(self, model: str = "claude-3-haiku-20240307"):
        super().__init__()
        
        try:
            import anthropic
        except ImportError:
            raise RuntimeError("anthropic package not installed. Install with: pip install anthropic")
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.name = f"anthropic:{model}"
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using Anthropic API"""
        try:
            start_time = time.time()
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.7,
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ]
            )
            
            elapsed = time.time() - start_time
            logger.info(f"Anthropic API generated response in {elapsed:.2f}s")
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic API generation failed: {e}")
            raise

class GeminiChat(BaseLLM):
    """Google Gemini API client"""
    
    def __init__(self, model: str = "gemini-1.5-flash"):
        super().__init__()
        
        try:
            import google.generativeai as genai
        except ImportError:
            raise RuntimeError("google-generativeai package not installed. Install with: pip install google-generativeai")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set")
        
        genai.configure(api_key=api_key)
        
        # Ensure model name has the correct format
        if not model.startswith("models/"):
            model_name = f"models/{model}"
        else:
            model_name = model
            
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        self.name = f"gemini:{model_name}"
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using Gemini API"""
        try:
            start_time = time.time()
            
            # Combine system and user prompts
            prompt = f"{system}\n\n{user}"
            
            # Configure safety settings to be more permissive
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": 0.7,
                },
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if response.candidates and response.candidates[0].finish_reason == 2:
                logger.warning("Gemini response blocked by safety filters")
                return "I apologize, but I cannot provide a response to this query due to content safety policies."
            
            if not response.text:
                logger.warning("Gemini returned empty response")
                return "I apologize, but I was unable to generate a response."
            
            elapsed = time.time() - start_time
            logger.info(f"Gemini API generated response in {elapsed:.2f}s")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini API generation failed: {e}")
            return f"Error: {str(e)}"
    
    def generate_stream(self, system: str, user: str, max_tokens: int = 600) -> Generator[str, None, None]:
        """Generate streaming response using Gemini API"""
        try:
            prompt = f"{system}\n\n{user}"
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            
            response = self.model.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens, "temperature": 0.7},
                safety_settings=safety_settings,
                stream=True
            )
            
            for chunk in response:
                if hasattr(chunk, 'candidates') and chunk.candidates and chunk.candidates[0].finish_reason == 2:
                    yield "I apologize, but I cannot provide a response to this query due to content safety policies."
                    return
                if chunk.text:
                    yield chunk.text
            
        except Exception as e:
            logger.error(f"Gemini API streaming failed: {e}")
            response = self.generate(system, user, max_tokens)
            yield response

class OllamaChat(BaseLLM):
    """Ollama local API client"""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        super().__init__()
        
        try:
            import requests
        except ImportError:
            raise RuntimeError("requests package not installed. Install with: pip install requests")
        
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.name = f"ollama:{model}"
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama server not responding at {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Cannot connect to Ollama server at {self.base_url}: {e}")
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using Ollama API"""
        try:
            import requests
            from config import config_manager
            
            start_time = time.time()
            
            prompt = f"{system}\n\n{user}"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": float(config_manager.config.llm.temperature),
                        "top_p": float(config_manager.config.llm.top_p),
                        "top_k": int(config_manager.config.llm.top_k),
                        "repeat_penalty": float(config_manager.config.llm.repeat_penalty),
                        "num_ctx": int(config_manager.config.llm.num_ctx),
                    }
                },
                timeout=60
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Ollama API error: {response.status_code}")
            
            result = response.json()
            elapsed = time.time() - start_time
            logger.info(f"Ollama API generated response in {elapsed:.2f}s")
            
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Ollama API generation failed: {e}")
            raise

    def generate_stream(self, system: str, user: str, max_tokens: int = 600) -> Generator[str, None, None]:
        """Stream response using Ollama API.
        Uses the /api/generate endpoint with stream=true and yields incremental
        tokens from line-delimited JSON payloads.
        """
        try:
            import requests, json
            from config import config_manager

            prompt = f"{system}\n\n{user}"

            with requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": float(config_manager.config.llm.temperature),
                        "top_p": float(config_manager.config.llm.top_p),
                        "top_k": int(config_manager.config.llm.top_k),
                        "repeat_penalty": float(config_manager.config.llm.repeat_penalty),
                        "num_ctx": int(config_manager.config.llm.num_ctx),
                    },
                },
                stream=True,
                timeout=60,
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"Ollama API error: {response.status_code}")

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue

                    # Emit incremental text if present
                    text = data.get("response")
                    if text:
                        yield text

                    if data.get("done") is True:
                        break

        except Exception as e:
            logger.error(f"Ollama API streaming failed: {e}")
            # Fallback to non-streaming
            response = self.generate(system, user, max_tokens)
            yield response

class HFLocal(BaseLLM):
    """HuggingFace local model (CPU-only)"""
    
    def __init__(self, model_id: str = "microsoft/DialoGPT-medium", lazy_load: bool = True):
        super().__init__()
        
        self.model_id = model_id
        self.name = f"hf:{model_id} (Not Loaded)"
        self.lazy_load = lazy_load
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self._is_loaded = False
        
        if not lazy_load:
            self._load_model()
    
    def _load_model(self):
        """Load the model"""
        if self._is_loaded:
            return
            
        from transformers import AutoTokenizer, AutoModelForCausalLM
        
        try:
            logger.info(f"Loading HuggingFace model: {self.model_id} (CPU)")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.float32
            )
            self.model = self.model.to("cpu")
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self._is_loaded = True
            self.name = f"hf:{self.model_id} (CPU)"
            logger.info(f"HuggingFace model loaded successfully: {self.name}")
            
        except Exception as e:
            logger.error(f"Failed to load HuggingFace model: {e}")
            raise
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Generate response using HuggingFace model"""
        if not self._is_loaded:
            self._load_model()
            
        try:
            prompt = f"{system}\n\nUser: {user}\nAssistant:"
            inputs = self.tokenizer.encode(prompt, return_tensors="pt")
            
            start_time = time.time()
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=max_tokens,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            elapsed = time.time() - start_time
            logger.info(f"HuggingFace model generated response in {elapsed:.2f}s")
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(prompt):].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            raise

class NoLLM(BaseLLM):
    """No LLM - citations only mode"""
    
    def __init__(self):
        super().__init__()
        self.name = "citations-only"
    
    def generate(self, system: str, user: str, max_tokens: int = 600) -> str:
        """Return citations-only response"""
        return "No LLM configured. Please select an LLM backend to generate answers."

def create_llm(backend: str, **kwargs) -> BaseLLM:
    """Factory function to create LLM instances"""
    
    if backend == "llama_cpp":
        return LlamaCppLLM(**kwargs)
    elif backend == "openai":
        return OpenAIChat(**kwargs)
    elif backend == "anthropic":
        return AnthropicChat(**kwargs)
    elif backend == "gemini":
        return GeminiChat(**kwargs)
    elif backend == "ollama":
        return OllamaChat(**kwargs)
    elif backend == "hf_local":
        return HFLocal(**kwargs)
    elif backend == "none":
        return NoLLM()
    else:
        raise ValueError(f"Unknown LLM backend: {backend}")

def get_available_backends() -> List[str]:
    """Get list of available LLM backends"""
    backends = ["none", "openai", "anthropic", "gemini", "ollama", "hf_local"]
    
    try:
        import llama_cpp
        backends.insert(1, "llama_cpp")
    except ImportError:
        pass
    
    return backends

