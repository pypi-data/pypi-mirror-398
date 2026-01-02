"""AgentBill Auto-Instrumentation

OpenTelemetry-based automatic instrumentation for AI libraries.
Automatically tracks OpenAI, Anthropic, and other AI provider calls.
"""
import os
import time
import uuid
import functools
import httpx
from typing import Optional, Dict, Any, List

from .distributed import get_trace_context, set_trace_context
from .signals import get_signal_config, set_signal_config

# Cost calculation is now 100% server-side - SDK only sends tokens


# Registry of instrumented libraries
_instrumented: Dict[str, bool] = {}


def agentbill_autoinstrument(
    *,
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    base_url: str = "https://bgwyprqxtdreuutzpbgw.supabase.co",
    debug: bool = False,
    providers: Optional[List[str]] = None,
) -> None:
    """
    Enable automatic instrumentation for AI libraries.
    
    This uses OpenTelemetry-style monkey patching to automatically
    track all AI calls without requiring manual wrapping.
    
    Args:
        api_key: AgentBill API key (or set AGENTBILL_API_KEY env var)
        customer_id: Default customer ID for tracking
        agent_id: Optional agent ID for multi-agent tracking
        base_url: AgentBill backend URL
        debug: Enable debug logging
        providers: List of providers to instrument (default: all available)
                   Options: "openai", "anthropic", "cohere", "google"
                   
    Example:
        >>> from agentbill import agentbill_autoinstrument
        >>> import openai
        >>> 
        >>> # Enable auto-instrumentation at startup
        >>> agentbill_autoinstrument(
        ...     api_key="ab_xxx",
        ...     customer_id="default-customer",
        ...     debug=True
        ... )
        >>> 
        >>> # All OpenAI calls are now automatically tracked!
        >>> client = openai.OpenAI()
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    # Get API key from argument or environment
    effective_api_key = api_key or os.environ.get("AGENTBILL_API_KEY")
    if not effective_api_key:
        raise ValueError("api_key is required. Provide it as argument or set AGENTBILL_API_KEY env var.")
    
    # Set global config
    config = {
        "api_key": effective_api_key,
        "customer_id": customer_id,
        "agent_id": agent_id,
        "base_url": base_url,
        "debug": debug,
    }
    set_signal_config(config)
    
    # Determine which providers to instrument
    all_providers = ["openai", "anthropic", "cohere", "google"]
    target_providers = providers or all_providers
    
    for provider in target_providers:
        if provider in _instrumented:
            if debug:
                print(f"[AgentBill] {provider} already instrumented, skipping")
            continue
        
        try:
            if provider == "openai":
                _instrument_openai(config)
            elif provider == "anthropic":
                _instrument_anthropic(config)
            elif provider == "cohere":
                _instrument_cohere(config)
            elif provider == "google":
                _instrument_google(config)
            
            _instrumented[provider] = True
            if debug:
                print(f"[AgentBill] ✓ Auto-instrumented {provider}")
                
        except ImportError:
            if debug:
                print(f"[AgentBill] {provider} not installed, skipping")
        except Exception as e:
            if debug:
                print(f"[AgentBill] Failed to instrument {provider}: {e}")


def _track_ai_call(
    config: Dict[str, Any],
    provider: str,
    model: str,
    operation: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    cost: float,
    attributes: Dict[str, Any] = None,
) -> None:
    """Send tracked AI call to otel-collector."""
    ctx = get_trace_context()
    trace_id = ctx.get("trace_id") if ctx else uuid.uuid4().hex
    span_id = ctx.get("span_id") if ctx else uuid.uuid4().hex[:16]
    
    url = f"{config['base_url']}/functions/v1/otel-collector"
    
    # Build span with gen_ai.* attributes
    span_attributes = {
        "gen_ai.system": provider,
        "gen_ai.request.model": model,
        "gen_ai.operation.name": operation,
        "gen_ai.usage.input_tokens": input_tokens,
        "gen_ai.usage.output_tokens": output_tokens,
        "gen_ai.response.latency_ms": latency_ms,
        "gen_ai.usage.cost": cost,
    }
    
    if attributes:
        span_attributes.update(attributes)
    
    span = {
        "trace_id": trace_id,
        "span_id": uuid.uuid4().hex[:16],
        "parent_span_id": span_id,
        "name": f"{provider}.{operation}",
        "attributes": span_attributes,
        "start_time_unix_nano": int((time.time() - latency_ms / 1000) * 1e9),
        "end_time_unix_nano": int(time.time() * 1e9),
        "status": {"code": 0},
    }
    
    payload = {
        "api_key": config["api_key"],
        "customer_id": config.get("customer_id"),
        "agent_id": config.get("agent_id"),
        "spans": [span],
    }
    
    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(url, json=payload)
            
            if config.get("debug"):
                if response.status_code == 200:
                    print(f"[AgentBill] ✓ Tracked {provider} {operation}: ${cost:.6f}")
                else:
                    print(f"[AgentBill] ⚠️ Tracking failed: {response.status_code}")
                    
    except Exception as e:
        if config.get("debug"):
            print(f"[AgentBill] ⚠️ Tracking error: {e}")


def _cache_ai_response(
    config: Dict[str, Any],
    model: str,
    prompt_hash: str,
    prompt_content: Any,
    response_content: str,
    input_tokens: int,
    output_tokens: int,
    request_id: Optional[str] = None,
) -> None:
    """Cache AI response for semantic cache population (v7.5.0)."""
    import json
    
    url = f"{config['base_url']}/functions/v1/cache-ai-response"
    
    # Serialize prompt content
    try:
        prompt_str = json.dumps(prompt_content, default=str) if not isinstance(prompt_content, str) else prompt_content
    except Exception:
        prompt_str = str(prompt_content)
    
    payload = {
        "api_key": config["api_key"],
        "prompt_hash": prompt_hash,
        "response_content": response_content,
        "model": model,
        "prompt_content": prompt_str,
        "tokens_used": input_tokens + output_tokens,
        "cacheable": True,
        "ttl_hours": 24,
    }
    
    if config.get("customer_id"):
        payload["customer_id"] = config["customer_id"]
    if request_id:
        payload["request_id"] = request_id
    
    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(url, json=payload)
            
            if config.get("debug"):
                if response.status_code == 200:
                    result = response.json()
                    print(f"[AgentBill] ✓ Cached response: {result.get('cached', False)}")
                else:
                    print(f"[AgentBill] ⚠️ Cache failed: {response.status_code}")
                    
    except Exception as e:
        if config.get("debug"):
            print(f"[AgentBill] ⚠️ Cache error (non-blocking): {e}")


def _hash_prompt(messages: Any) -> str:
    """Generate a hash of the prompt for caching.
    
    v7.5.2: CRITICAL - Must match backend algorithm exactly:
    - Backend uses JSON.stringify(messages) - NO sort_keys
    - Full 64-char SHA-256 hash
    """
    import hashlib
    import json
    try:
        # Match backend: JSON.stringify equivalent (no sort_keys, no spaces)
        content = json.dumps(messages, separators=(',', ':'), default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    except Exception:
        return uuid.uuid4().hex


def _instrument_openai(config: Dict[str, Any]) -> None:
    """Instrument OpenAI library."""
    import openai
    
    # Store original methods
    original_chat_create = openai.resources.chat.completions.Completions.create
    
    @functools.wraps(original_chat_create)
    def patched_chat_create(self, *args, **kwargs):
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        prompt_hash = _hash_prompt(messages)
        start_time = time.time()
        
        try:
            response = original_chat_create(self, *args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract usage
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            cost = calculate_cost(model, input_tokens, output_tokens, "openai")
            
            # Extract response content for caching
            response_content = ""
            if response.choices and len(response.choices) > 0:
                response_content = getattr(response.choices[0].message, "content", "") or ""
            
            # Track the call via OTEL
            _track_ai_call(
                config, "openai", model, "chat.completions",
                input_tokens, output_tokens, latency_ms, cost
            )
            
            # v7.5.0: Cache response for semantic cache population
            _cache_ai_response(
                config=config,
                model=model,
                prompt_hash=prompt_hash,
                prompt_content=messages,
                response_content=response_content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            _track_ai_call(
                config, "openai", model, "chat.completions",
                0, 0, latency_ms, 0,
                {"error": str(e), "gen_ai.response.status": "error"}
            )
            raise
    
    # Apply patch
    openai.resources.chat.completions.Completions.create = patched_chat_create
    
    # Also patch async version if available
    try:
        original_async_chat_create = openai.resources.chat.completions.AsyncCompletions.create
        
        @functools.wraps(original_async_chat_create)
        async def patched_async_chat_create(self, *args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            prompt_hash = _hash_prompt(messages)
            start_time = time.time()
            
            try:
                response = await original_async_chat_create(self, *args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                cost = calculate_cost(model, input_tokens, output_tokens, "openai")
                
                # Extract response content for caching
                response_content = ""
                if response.choices and len(response.choices) > 0:
                    response_content = getattr(response.choices[0].message, "content", "") or ""
                
                _track_ai_call(
                    config, "openai", model, "chat.completions",
                    input_tokens, output_tokens, latency_ms, cost
                )
                
                # v7.5.0: Cache response for semantic cache population
                _cache_ai_response(
                    config=config,
                    model=model,
                    prompt_hash=prompt_hash,
                    prompt_content=messages,
                    response_content=response_content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                
                return response
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                _track_ai_call(
                    config, "openai", model, "chat.completions",
                    0, 0, latency_ms, 0,
                    {"error": str(e)}
                )
                raise
        
        openai.resources.chat.completions.AsyncCompletions.create = patched_async_chat_create
    except AttributeError:
        pass  # Async not available


def _instrument_anthropic(config: Dict[str, Any]) -> None:
    """Instrument Anthropic library."""
    import anthropic
    
    original_create = anthropic.resources.messages.Messages.create
    
    @functools.wraps(original_create)
    def patched_create(self, *args, **kwargs):
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        prompt_hash = _hash_prompt(messages)
        start_time = time.time()
        
        try:
            response = original_create(self, *args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            
            input_tokens = response.usage.input_tokens if response.usage else 0
            output_tokens = response.usage.output_tokens if response.usage else 0
            cost = calculate_cost(model, input_tokens, output_tokens, "anthropic")
            
            # Extract response content for caching
            response_content = ""
            if response.content and len(response.content) > 0:
                response_content = getattr(response.content[0], "text", "") or ""
            
            _track_ai_call(
                config, "anthropic", model, "messages.create",
                input_tokens, output_tokens, latency_ms, cost
            )
            
            # v7.5.0: Cache response for semantic cache population
            _cache_ai_response(
                config=config,
                model=model,
                prompt_hash=prompt_hash,
                prompt_content=messages,
                response_content=response_content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
            
            return response
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            _track_ai_call(
                config, "anthropic", model, "messages.create",
                0, 0, latency_ms, 0,
                {"error": str(e)}
            )
            raise
    
    anthropic.resources.messages.Messages.create = patched_create


def _instrument_cohere(config: Dict[str, Any]) -> None:
    """Instrument Cohere library."""
    try:
        import cohere
        
        original_chat = cohere.Client.chat
        
        @functools.wraps(original_chat)
        def patched_chat(self, *args, **kwargs):
            model = kwargs.get("model", "command")
            message = kwargs.get("message", "")
            chat_history = kwargs.get("chat_history", [])
            # Build messages array for hashing
            messages = [{"role": "user", "content": message}]
            if chat_history:
                messages = chat_history + messages
            prompt_hash = _hash_prompt(messages)
            start_time = time.time()
            
            try:
                response = original_chat(self, *args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                
                # Cohere uses different token counting
                input_tokens = getattr(response.meta, 'billed_units', {}).get('input_tokens', 0) if hasattr(response, 'meta') else 0
                output_tokens = getattr(response.meta, 'billed_units', {}).get('output_tokens', 0) if hasattr(response, 'meta') else 0
                cost = calculate_cost(model, input_tokens, output_tokens, "cohere")
                
                # Extract response content for caching
                response_content = getattr(response, 'text', "") or ""
                
                _track_ai_call(
                    config, "cohere", model, "chat",
                    input_tokens, output_tokens, latency_ms, cost
                )
                
                # v7.5.2: Cache response for semantic cache population
                _cache_ai_response(
                    config=config,
                    model=model,
                    prompt_hash=prompt_hash,
                    prompt_content=messages,
                    response_content=response_content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                
                return response
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                _track_ai_call(
                    config, "cohere", model, "chat",
                    0, 0, latency_ms, 0,
                    {"error": str(e)}
                )
                raise
        
        cohere.Client.chat = patched_chat
    except ImportError:
        raise


def _instrument_google(config: Dict[str, Any]) -> None:
    """Instrument Google AI (Gemini) library."""
    try:
        import google.generativeai as genai
        
        original_generate = genai.GenerativeModel.generate_content
        
        @functools.wraps(original_generate)
        def patched_generate(self, *args, **kwargs):
            model = self.model_name if hasattr(self, 'model_name') else "gemini-pro"
            # Build messages array for hashing
            contents = args[0] if args else kwargs.get("contents", "")
            if isinstance(contents, str):
                messages = [{"role": "user", "content": contents}]
            elif isinstance(contents, list):
                messages = contents
            else:
                messages = [{"role": "user", "content": str(contents)}]
            prompt_hash = _hash_prompt(messages)
            start_time = time.time()
            
            try:
                response = original_generate(self, *args, **kwargs)
                latency_ms = (time.time() - start_time) * 1000
                
                # Google provides usage metadata
                input_tokens = 0
                output_tokens = 0
                if hasattr(response, 'usage_metadata'):
                    input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                    output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                
                cost = calculate_cost(model, input_tokens, output_tokens, "google")
                
                # Extract response content for caching
                response_content = ""
                if hasattr(response, 'text'):
                    response_content = response.text or ""
                elif hasattr(response, 'candidates') and response.candidates:
                    if hasattr(response.candidates[0], 'content') and response.candidates[0].content.parts:
                        response_content = response.candidates[0].content.parts[0].text or ""
                
                _track_ai_call(
                    config, "google", model, "generate_content",
                    input_tokens, output_tokens, latency_ms, cost
                )
                
                # v7.5.2: Cache response for semantic cache population
                _cache_ai_response(
                    config=config,
                    model=model,
                    prompt_hash=prompt_hash,
                    prompt_content=messages,
                    response_content=response_content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                
                return response
                
            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                _track_ai_call(
                    config, "google", model, "generate_content",
                    0, 0, latency_ms, 0,
                    {"error": str(e)}
                )
                raise
        
        genai.GenerativeModel.generate_content = patched_generate
    except ImportError:
        raise


def initialize_tracing(
    api_key: Optional[str] = None,
    customer_id: Optional[str] = None,
    **kwargs
) -> None:
    """
    Alias for agentbill_autoinstrument for compatibility.
    
    Example:
        >>> from agentbill import initialize_tracing
        >>> initialize_tracing(api_key="ab_xxx", customer_id="cust-123")
    """
    agentbill_autoinstrument(api_key=api_key, customer_id=customer_id, **kwargs)
