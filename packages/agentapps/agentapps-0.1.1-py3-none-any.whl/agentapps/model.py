# ============================================================================
# File: agentapps/model.py
# ============================================================================

"""Model implementations for AgentApps"""

from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    # Try new package first
    import google.genai as genai
    GENAI_VERSION = "new"
except ImportError:
    try:
        # Fall back to old package
        import google.generativeai as genai
        GENAI_VERSION = "old"
    except ImportError:
        genai = None
        GENAI_VERSION = None

try:
    from openai import OpenAI as OpenAIClient
except ImportError:
    OpenAIClient = None


class Model(ABC):
    """Base class for LLM models"""
    
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from the model"""
        pass
    
    @abstractmethod
    def stream(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ):
        """Stream a response from the model"""
        pass


class OpenAIChat(Model):
    """OpenAI Chat model implementation"""
    
    def __init__(
        self,
        id: str = "gpt-4",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize OpenAI Chat model
        
        Args:
            id: Model ID (e.g., "gpt-4", "gpt-4o", "gpt-3.5-turbo")
            api_key: OpenAI API key
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters
        """
        if OpenAI is None:
            raise ImportError(
                "OpenAI package not installed. "
                "Install it with: pip install openai"
            )
        
        self.id = id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from OpenAI"""
        params = {
            "model": self.id,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        # Add tools if provided
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        params.update({k: v for k, v in kwargs.items() if k not in params and k not in ["tools", "tool_choice"]})
        
        try:
            # Add timeout to prevent hanging
            import time
            start_time = time.time()
            
            response = self.client.chat.completions.create(**params)
            
            elapsed = time.time() - start_time
            if elapsed > 30:
                print(f"⚠ Warning: API call took {elapsed:.1f}s")
            
            # Check if there are tool calls
            message = response.choices[0].message
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Return full response for tool handling
                return {
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                }
            
            # Regular text response
            return message.content or ""
            
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise
    
    def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from OpenAI"""
        params = {
            "model": self.id,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        params.update({k: v for k, v in kwargs.items() if k not in params})
        
        stream = self.client.chat.completions.create(**params)
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def __repr__(self) -> str:
        return f"OpenAIChat(id='{self.id}')"


class GeminiChat(Model):
    """Google Gemini model implementation"""
    
    def __init__(
        self,
        id: str = "gemini-pro",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize Google Gemini model
        
        Args:
            id: Model ID (e.g., "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro")
            api_key: Google API key
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters
        """
        if genai is None:
            raise ImportError(
                "Google Generative AI package not installed. "
                "Install with: pip install google-genai (new) or pip install google-generativeai (legacy)"
            )
        
        self.id = id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # Configure based on package version
        if GENAI_VERSION == "new":
            # New google.genai package
            from google import genai as genai_client
            self.client = genai_client.Client(api_key=api_key)
            self.use_new_api = True
        else:
            # Legacy google.generativeai package
            if api_key:
                genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(id)
            self.use_new_api = False
        
        # Generation config
        self.generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            self.generation_config["max_output_tokens"] = max_tokens
    
    def _convert_messages_to_gemini_format(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert OpenAI-style messages to Gemini format"""
        gemini_messages = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                # Gemini doesn't have system role, we'll prepend to first user message
                system_instruction = content
            elif role == "user":
                if system_instruction:
                    content = f"{system_instruction}\n\n{content}"
                    system_instruction = None
                gemini_messages.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                gemini_messages.append({"role": "model", "parts": [content]})
            elif role == "tool":
                # Handle tool results
                gemini_messages.append({"role": "user", "parts": [f"Tool result: {content}"]})
        
        return gemini_messages
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from Gemini"""
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Update generation config
            gen_config = self.generation_config.copy()
            if "temperature" in kwargs:
                gen_config["temperature"] = kwargs["temperature"]
            
            if self.use_new_api:
                # New API (google.genai)
                # Note: New API has different interface - simplified for now
                prompt = "\n\n".join([msg["parts"][0] for msg in gemini_messages])
                response = self.client.models.generate_content(
                    model=self.id,
                    contents=prompt,
                    config=gen_config
                )
                return response.text
            else:
                # Legacy API (google.generativeai)
                # For Gemini, we need to handle chat differently
                if len(gemini_messages) == 1:
                    # Single message - use generate_content
                    response = self.model.generate_content(
                        gemini_messages[0]["parts"][0],
                        generation_config=gen_config
                    )
                    return response.text
                else:
                    # Multi-turn conversation - use chat
                    chat = self.model.start_chat(history=gemini_messages[:-1])
                    response = chat.send_message(
                        gemini_messages[-1]["parts"][0],
                        generation_config=gen_config
                    )
                    return response.text
            
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            raise
    
    def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from Gemini"""
        try:
            # Convert messages to Gemini format
            gemini_messages = self._convert_messages_to_gemini_format(messages)
            
            # Update generation config
            gen_config = self.generation_config.copy()
            if "temperature" in kwargs:
                gen_config["temperature"] = kwargs["temperature"]
            
            if self.use_new_api:
                # New API streaming
                prompt = "\n\n".join([msg["parts"][0] for msg in gemini_messages])
                response = self.client.models.generate_content_stream(
                    model=self.id,
                    contents=prompt,
                    config=gen_config
                )
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            else:
                # Legacy API streaming
                if len(gemini_messages) == 1:
                    # Single message
                    response = self.model.generate_content(
                        gemini_messages[0]["parts"][0],
                        generation_config=gen_config,
                        stream=True
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                else:
                    # Multi-turn conversation
                    chat = self.model.start_chat(history=gemini_messages[:-1])
                    response = chat.send_message(
                        gemini_messages[-1]["parts"][0],
                        generation_config=gen_config,
                        stream=True
                    )
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
            
        except Exception as e:
            print(f"Gemini Streaming Error: {str(e)}")
            raise
    
    def __repr__(self) -> str:
        return f"GeminiChat(id='{self.id}')"


class GrokChat(Model):
    """X.AI Grok model implementation (uses OpenAI-compatible API)"""
    
    # Available Grok models
    AVAILABLE_MODELS = {
        # Latest Grok 4 models (reasoning)
        "grok-4-1-fast-reasoning": {"context": 4_000_000, "rpm": 2_000_000},
        "grok-4-1-fast-non-reasoning": {"context": 4_000_000, "rpm": 2_000_000},
        "grok-4-fast-reasoning": {"context": 4_000_000, "rpm": 2_000_000},
        "grok-4-fast-non-reasoning": {"context": 4_000_000, "rpm": 2_000_000},
        
        # Grok 4 standard
        "grok-4-0709": {"context": 2_000_000, "rpm": 256_000},
        
        # Code model
        "grok-code-fast-1": {"context": 2_000_000, "rpm": 256_000},
        
        # Grok 3 models
        "grok-3-mini": {"context": 131_072, "rpm": 480},
        "grok-3": {"context": 131_072, "rpm": 600},
        
        # Grok 2 with vision
        "grok-2-vision-1212": {"context": 32_768, "rpm": 600},
        
        # Legacy/beta
        "grok-beta": {"context": 131_072, "rpm": 480},
        "grok-vision-beta": {"context": 32_768, "rpm": 600},
    }
    
    def __init__(
        self,
        id: str = "grok-beta",
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize X.AI Grok model
        
        Args:
            id: Model ID - Available models:
                - grok-4-1-fast-reasoning (4M context, best reasoning)
                - grok-4-1-fast-non-reasoning (4M context, faster)
                - grok-4-fast-reasoning (4M context)
                - grok-4-fast-non-reasoning (4M context)
                - grok-4-0709 (2M context)
                - grok-code-fast-1 (2M context, optimized for code)
                - grok-3-mini (131K context, fastest)
                - grok-3 (131K context)
                - grok-2-vision-1212 (32K context, supports vision)
                - grok-beta (legacy)
                - grok-vision-beta (legacy vision)
            api_key: X.AI API key (get from console.x.ai)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters
        """
        if OpenAIClient is None:
            raise ImportError(
                "OpenAI package not installed (needed for Grok API). "
                "Install it with: pip install openai"
            )
        
        self.id = id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # Validate model
        if id not in self.AVAILABLE_MODELS:
            print(f"⚠️ Warning: '{id}' not in known models list. It may still work if it's a new model.")
            print(f"Available models: {', '.join(list(self.AVAILABLE_MODELS.keys())[:5])}...")
        
        # Grok uses OpenAI-compatible API with custom base URL
        self.client = OpenAIClient(
            api_key=api_key,
            base_url="https://api.x.ai/v1"
        )
    
    @classmethod
    def list_models(cls):
        """List all available Grok models with their specs"""
        print("Available Grok Models:")
        print("="*80)
        for model_id, specs in cls.AVAILABLE_MODELS.items():
            context_str = f"{specs['context']:,}" if specs['context'] >= 1000 else str(specs['context'])
            print(f"{model_id:35} | Context: {context_str:>12} | RPM: {specs['rpm']:,}")
        print("="*80)
    
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from Grok"""
        params = {
            "model": self.id,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        # Add tools if provided (Grok supports function calling)
        if "tools" in kwargs:
            params["tools"] = kwargs["tools"]
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        params.update({k: v for k, v in kwargs.items() if k not in params and k not in ["tools", "tool_choice"]})
        
        try:
            response = self.client.chat.completions.create(**params)
            
            # Check if there are tool calls
            message = response.choices[0].message
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Return full response for tool handling
                return {
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                }
            
            # Regular text response
            return message.content or ""
            
        except Exception as e:
            print(f"Grok API Error: {str(e)}")
            raise
    
    def stream(self, messages: List[Dict[str, str]], **kwargs):
        """Stream a response from Grok"""
        params = {
            "model": self.id,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": True
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        
        params.update({k: v for k, v in kwargs.items() if k not in params})
        
        try:
            stream = self.client.chat.completions.create(**params)
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            print(f"Grok Streaming Error: {str(e)}")
            raise
    
    def __repr__(self) -> str:
        return f"GrokChat(id='{self.id}')"

