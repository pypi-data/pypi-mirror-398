"""AgentBill SDK Client"""
import time
import json
import hashlib
import httpx
from typing import Any, Optional, Dict
from .tracer import AgentBillTracer
from .types import AgentBillConfig
from .resources.customers import CustomersResource
from .resources.agents import AgentsResource
from .resources.contacts import ContactsResource
from .resources.orders import OrdersResource
from .resources.signal_types import SignalTypesResource
from .resources.orders import OrdersResource

# Cost calculation is now 100% server-side - SDK only sends tokens


class DictToObject:
    """
    v7.6.6: Wrapper class to allow attribute-style access to dict data.
    Used to wrap cached responses so they behave like OpenAI ChatCompletion objects.
    
    Example:
        cached = {"choices": [{"message": {"content": "Hello"}}]}
        obj = DictToObject(cached)
        print(obj.choices[0].message.content)  # "Hello"
    """
    def __init__(self, data: dict):
        self._data = data
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, DictToObject(value))
            elif isinstance(value, list):
                setattr(self, key, [
                    DictToObject(item) if isinstance(item, dict) else item 
                    for item in value
                ])
            else:
                setattr(self, key, value)
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __repr__(self):
        return f"DictToObject({self._data})"
    
    def to_dict(self) -> dict:
        """Return the underlying dict"""
        return self._data


class AgentBill:
    """
    AgentBill SDK for Python
    
    Example:
        >>> from agentbill import AgentBill
        >>> import openai
        >>> 
        >>> # Initialize AgentBill
        >>> agentbill = AgentBill.init({
        ...     "api_key": "your-api-key",
        ...     "customer_id": "customer-123",
        ...     "debug": True
        ... })
        >>> 
        >>> # Wrap your OpenAI client
        >>> client = agentbill.wrap_openai(openai.OpenAI(api_key="sk-..."))
        >>> 
        >>> # Use normally - all calls are tracked!
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>>
        >>> # Business Objects CRUD (v7.5.0+)
        >>> # Customers
        >>> customers = agentbill.customers.list(limit=10)
        >>> customer = agentbill.customers.create(name="Acme", email="a@b.com")
        >>>
        >>> # Agents with explicit signal type assignment
        >>> agent = agentbill.agents.create(name="Support Bot")
        >>> agentbill.agents.assign_signal_types(
        ...     agent_id=agent["id"],
        ...     signal_type_names=["ai_call", "completion"]
        ... )
    """
    
    def __init__(self, config: AgentBillConfig):
        self.config = config
        self.tracer = AgentBillTracer(config)
        
        # Business Object Resources (v7.5.0+)
        self.customers = CustomersResource(config)
        self.agents = AgentsResource(config)
        self.contacts = ContactsResource(config)  # v7.8.0
        self.orders = OrdersResource(config)      # v7.8.0
        self.signal_types = SignalTypesResource(config)  # v7.15.0
    
    @classmethod
    def init(cls, config: AgentBillConfig) -> "AgentBill":
        """Initialize AgentBill SDK"""
        return cls(config)
    
    def _estimate_tokens(self, text: str) -> int:
        """Simple token estimation: ~4 chars per token"""
        return max(1, len(str(text)) // 4)
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int, provider: str = "openai") -> float:
        """
        LOCAL ESTIMATION ONLY - for display purposes.
        Actual cost is calculated server-side using model_pricing database.
        """
        # Ollama is free
        if provider == "ollama" or model.startswith("ollama/"):
            return 0.0
        
        # Simple default estimate - server calculates actual cost
        DEFAULT_INPUT_PER_1M = 1.0
        DEFAULT_OUTPUT_PER_1M = 2.0
        input_cost = (input_tokens / 1_000_000) * DEFAULT_INPUT_PER_1M
        output_cost = (output_tokens / 1_000_000) * DEFAULT_OUTPUT_PER_1M
        return input_cost + output_cost
    
    def _validate_request(self, model: str, messages: Any, estimated_output_tokens: int = 1000) -> Dict:
        """
        Call ai-cost-guard-router edge function (tier-based routing)
        
        v7.3.0 CRITICAL FIX: ALWAYS call validation - server decides based on:
        - Company budgets (via api_key)
        - Customer budgets (if customer_id provided)
        - Agent budgets (if agent_id provided)
        
        SDK budgets (daily_budget, monthly_budget) are OPTIONAL overrides that add
        stricter limits on top of DB policies - they are NOT required for validation.
        """
        # v7.3.0: ALWAYS validate - removed customer_id check
        # Server-side validation uses api_key to enforce company budgets even without customer_id
        
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/ai-cost-guard-router"
        
        payload = {
            "api_key": self.config["api_key"],
            "customer_id": self.config.get("customer_id"),
            "model": model,
            "messages": messages,
            # SDK budgets are OPTIONAL overrides - backend uses DB budgets if not set
            "daily_budget_override": self.config.get("daily_budget"),
            "monthly_budget_override": self.config.get("monthly_budget"),
        }
        
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(url, json=payload)
                
                # Handle HTTP errors explicitly - don't fail open on 4xx/5xx
                if response.status_code >= 500:
                    error_text = response.text
                    if self.config.get("debug"):
                        print(f"[AgentBill Cost Guard] ❌ Router error {response.status_code}: {error_text}")
                    # Only fail open on server errors (temporary issues)
                    return {"allowed": True, "reason": "Router server error (failed open)"}
                elif response.status_code >= 400:
                    error_text = response.text
                    if self.config.get("debug"):
                        print(f"[AgentBill Cost Guard] ❌ Router rejected {response.status_code}: {error_text}")
                    # Fail closed on client errors (bad request, auth issues)
                    return {"allowed": False, "reason": f"Router error: {error_text}"}
                
                result = response.json()
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] Router response: {result}")
                    if result.get("tier"):
                        print(f"[AgentBill] Tier: {result['tier']}, Mode: {result.get('mode', 'unknown')}")
                    if not result.get("allowed"):
                        print(f"[AgentBill Cost Guard] ❌ BLOCKED: {result.get('reason', 'Unknown reason')}")
                
                return result
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill Cost Guard] ⚠️ Router network error: {e} (failing open)")
            # Only fail open on network errors (temporary issues)
            return {"allowed": True, "reason": "Router network error (failed open)"}
    
    def _track_usage(self, model: str, provider: str, input_tokens: int, output_tokens: int, latency_ms: float, cost: float, event_name: str = "ai_request", trace_id: str = None, span_id: str = None, parent_span_id: str = None, request_id: str = None, prompt_metadata: Dict = None):
        """Call track-ai-usage edge function with optional trace correlation and Cost Guard linking"""
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/track-ai-usage"
        
        payload = {
            "api_key": self.config["api_key"],
            "customer_id": self.config.get("customer_id"),
            "agent_id": self.config.get("agent_id"),
            "event_name": event_name,
            "model": model,
            "provider": provider,
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "latency_ms": latency_ms,
            "cost": cost,
        }
        
        # Add OTEL correlation if available (v6.8.9: include parent_span_id)
        if trace_id:
            payload["trace_id"] = trace_id
        if span_id:
            payload["span_id"] = span_id
        if parent_span_id:
            payload["parent_span_id"] = parent_span_id
        
        # CRITICAL: Add request_id from router validation for audit log linking
        if request_id:
            payload["request_id"] = request_id
        
        # CRITICAL: Add all prompt metadata for AI Economics / Prompt Profitability
        if prompt_metadata:
            if "prompt_hash" in prompt_metadata:
                payload["prompt_hash"] = prompt_metadata["prompt_hash"]
            if "prompt_name" in prompt_metadata:
                payload["prompt_name"] = prompt_metadata["prompt_name"]
            if "prompt_version" in prompt_metadata:
                payload["prompt_version"] = prompt_metadata["prompt_version"]
            if "prompt_owner" in prompt_metadata:
                payload["prompt_owner"] = prompt_metadata["prompt_owner"]
            if "prompt_sample" in prompt_metadata:
                payload["prompt_sample"] = prompt_metadata["prompt_sample"]
        
        try:
            with httpx.Client(timeout=10) as client:
                client.post(url, json=payload)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] Usage tracked: ${cost:.4f}")
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill Cost Guard] Tracking failed: {e}")
    
    def _cache_response(self, model: str, prompt_hash: str, response_content: str, 
                        input_tokens: int, output_tokens: int, cost: float, prompt_content: str = None):
        """Cache AI response for semantic caching (v7.15.2: now with separate token counts)"""
        if not response_content:
            return
            
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/cache-ai-response"
        
        # v7.15.2: Send prompt_tokens and completion_tokens separately for accurate cost calculation
        payload = {
            "api_key": self.config["api_key"],
            "prompt_hash": prompt_hash,
            "response_content": response_content,
            "model": model,
            "tokens_used": input_tokens + output_tokens,
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "cost": cost,
            "prompt_content": prompt_content,
            "customer_id": self.config.get("customer_id"),
            "cacheable": True,
            "ttl_hours": 24
        }
        
        try:
            with httpx.Client(timeout=5) as client:
                client.post(url, json=payload)
                if self.config.get("debug"):
                    print(f"[AgentBill] ✓ Response cached (hash: {prompt_hash[:16]}...)")
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill] Cache storage failed (non-blocking): {e}")
    
    def wrap_openai(self, client: Any) -> Any:
        """Wrap OpenAI client with Cost Guard protection"""
        
        # Track chat completions
        original_chat_create = client.chat.completions.create
        def tracked_chat_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            temperature = kwargs.get("temperature")
            max_tokens = kwargs.get("max_tokens", kwargs.get("max_completion_tokens"))
            
            # Extract event_name from agentbill_options if provided (don't pass to OpenAI)
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "ai_request")
            
            # Extract prompt metadata for AI Economics analysis
            prompt_metadata = {
                "prompt_hash": agentbill_options.get("prompt_hash"),
                "prompt_name": agentbill_options.get("prompt_name"),
                "prompt_version": agentbill_options.get("prompt_version"),
                "prompt_owner": agentbill_options.get("prompt_owner"),
                "prompt_sample": agentbill_options.get("prompt_sample"),
            }
            # Remove None values
            prompt_metadata = {k: v for k, v in prompt_metadata.items() if v is not None}
            
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI chat.completions.create with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.chat.completions.create", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "openai"
            })
            
            # CRITICAL: ALWAYS validate before AI calls (regardless of SDK budget config)
            # Backend checks company/customer/agent budgets from DB
            # SDK budgets are optional overrides that ADD stricter limits
            validation_request_id = None
            validation = self._validate_request(model, messages)
            
            # Extract request_id for audit log correlation
            validation_request_id = validation.get("request_id")
            
            # CRITICAL: Block request if not allowed
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Request blocked by Cost Guard")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED" if "budget" in error_msg.lower() or "BUDGET" in error_msg else \
                             "RATE_LIMIT_EXCEEDED" if "rate" in error_msg.lower() or "RATE" in error_msg else \
                             "POLICY_VIOLATION"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request BLOCKED: {error_msg}")
                span.set_status(1, str(error))
                span.end()
                raise error
            
            # v7.6.8: Check for cached response from semantic cache
            # The response_data is a full OpenAI ChatCompletion-compatible object
            if validation.get("cached") and validation.get("response_data"):
                if self.config.get("debug"):
                    print("[AgentBill] ✓ Cache hit - returning cached ChatCompletion object")
                    print(f"[AgentBill] Cached response data: {validation.get('response_data')}")
                
                # v7.6.8 FIX: Router sends "cache" not "cache_info"
                cache_info = validation.get("cache", {}) or validation.get("cache_info", {})
                cached_response = validation.get("response_data", {})
                
                # Get tokens_saved from cache info or calculate from response
                tokens_saved = cache_info.get("tokens_saved", 0) or validation.get("tokens_saved", 0)
                cost_saved = cache_info.get("cost_saved", 0) or validation.get("cost_saved", 0)
                usage = cached_response.get("usage", {}) if isinstance(cached_response, dict) else {}
                
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", tokens_saved)
                
                # If no tokens_saved recorded, use total_tokens as saved amount
                if tokens_saved == 0 and total_tokens > 0:
                    tokens_saved = total_tokens
                
                # v7.6.8 FIX: For cache hits, set agentbill.* metrics for SAVED amounts
                # DO NOT set gen_ai.usage.* for cache hits - those indicate CONSUMED tokens
                # OTEL ingestion will calculate cost=0 when agentbill.cache_hit=True
                span.set_attributes({
                    "agentbill.cache_hit": True,
                    "agentbill.from_cache": True,  # Explicit flag for OTEL ingestion
                    "agentbill.tokens_saved": tokens_saved,
                    "agentbill.cost_saved": cost_saved,
                    "agentbill.cached_input_tokens": input_tokens,   # Informational only
                    "agentbill.cached_output_tokens": output_tokens, # Informational only
                    "agentbill.cached_total_tokens": total_tokens,   # Informational only
                    # v7.6.8: Set actual usage to 0 for cache hits (no tokens consumed)
                    "gen_ai.usage.input_tokens": 0,
                    "gen_ai.usage.output_tokens": 0,
                    "gen_ai.usage.total_tokens": 0,
                })
                span.set_status(0)
                span.end()
                self.tracer.flush_sync()
                
                if self.config.get("debug"):
                    print(f"[AgentBill] ✓ Returning cached response (saved {tokens_saved} tokens, ${cost_saved:.6f})")
                
                # v7.6.6 FIX: Wrap dict in DictToObject for attribute-style access
                # This allows response.choices[0].message.content to work
                if isinstance(cached_response, dict):
                    cached_response["_agentbill_cached"] = True
                    return DictToObject(cached_response)
                return cached_response
            
            # Validation passed - proceed with OpenAI call
            if self.config.get("debug"):
                print(f"[AgentBill Cost Guard] ✓ Validation passed: {validation.get('mode', 'validated')}")
                if validation_request_id:
                    print(f"[AgentBill Cost Guard] request_id: {validation_request_id}")
            
            # Step 2: Execute OpenAI call (after validation passed or no customer_id set)
            try:
                response = original_chat_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Step 3: Track usage after successful AI call (with OTEL + Cost Guard correlation)
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                # NOTE: wrap_openai() only creates OTEL spans, NOT signals
                # Signals should only be created when signal() is called explicitly
                # within the trace context. This ensures OTEL spans are "untracked"
                # until the user explicitly tracks business events via signal()
                
                span.set_attributes({
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "gen_ai.usage.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                # v7.6.6: Cache AI response for semantic caching (with prompt_content)
                try:
                    response_content = response.choices[0].message.content if response.choices else ""
                    prompt_text = json.dumps(messages, separators=(',', ':'), default=str)
                    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()
                    # v7.15.2: Pass separate token counts for accurate cost calculation
                    self._cache_response(model, prompt_hash, response_content, input_tokens, output_tokens, cost, prompt_text)
                except Exception as cache_err:
                    if self.config.get("debug"):
                        print(f"[AgentBill] Cache population failed: {cache_err}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
                # Auto-flush spans to prevent data loss on script exit
                self.tracer.flush_sync()
        
        client.chat.completions.create = tracked_chat_create
        
        # Track embeddings
        original_embeddings_create = client.embeddings.create
        def tracked_embeddings_create(*args, **kwargs):
            model = kwargs.get("model", "text-embedding-ada-002")
            
            # Extract event_name from agentbill_options if provided
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "embedding_request")
            
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI embeddings.create with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.embeddings.create", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "text_embedding",
                # Backward compatibility
                "model": model,
                "provider": "openai"
            })
            
            try:
                response = original_embeddings_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # NOTE: wrap_openai() only creates OTEL spans, NOT signals
                input_tokens = response.usage.prompt_tokens
                cost = self._estimate_cost(model, input_tokens, 0, "openai")
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.total_tokens": response.usage.total_tokens,
                    # Backward compatibility
                    "response.prompt_tokens": input_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Embedding tracked: ${cost:.6f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
                # Auto-flush spans to prevent data loss on script exit
                self.tracer.flush_sync()
        
        client.embeddings.create = tracked_embeddings_create
        
        # Track image generation
        original_images_generate = client.images.generate
        def tracked_images_generate(*args, **kwargs):
            model = kwargs.get("model", "dall-e-3")
            size = kwargs.get("size", "1024x1024")
            quality = kwargs.get("quality", "standard")
            n = kwargs.get("n", 1)  # Number of images
            
            # Extract event_name from agentbill_options if provided
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "image_generation")
            
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI images.generate: {model} {size} {quality}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.images.generate", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "image_generation",
                # Backward compatibility
                "model": model,
                "provider": "openai",
                "size": size,
                "quality": quality
            })
            
            try:
                response = original_images_generate(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # NOTE: wrap_openai() only creates OTEL spans, NOT signals
                # Cost calculation is 100% SERVER-SIDE using model_pricing table
                # SDK sends metadata only - server calculates actual cost
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes for image generation
                    "gen_ai.request.image_size": size,
                    "gen_ai.request.image_quality": quality,
                    "gen_ai.request.image_count": n,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Image generation tracked: {model} {size} {quality} ({n} images)")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
                # Auto-flush spans to prevent data loss on script exit
                self.tracer.flush_sync()
        
        client.images.generate = tracked_images_generate
        
        # Track audio transcription (Whisper)
        original_audio_transcriptions_create = client.audio.transcriptions.create
        def tracked_audio_transcriptions_create(*args, **kwargs):
            model = kwargs.get("model", "whisper-1")
            
            # Extract event_name from agentbill_options if provided
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "audio_transcription")
            
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI audio.transcriptions.create")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.audio.transcriptions.create", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "audio_transcription",
                # Backward compatibility
                "model": model,
                "provider": "openai"
            })
            
            try:
                response = original_audio_transcriptions_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # NOTE: wrap_openai() only creates OTEL spans, NOT signals
                # Cost calculation is 100% SERVER-SIDE using model_pricing table
                # SDK sends metadata only - server calculates actual cost
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes for audio transcription
                    "gen_ai.audio.estimated_duration_ms": latency,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Audio transcription OTEL span: ${cost:.6f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
                # Auto-flush spans to prevent data loss on script exit
                self.tracer.flush_sync()
        
        client.audio.transcriptions.create = tracked_audio_transcriptions_create
        original_audio_speech_create = client.audio.speech.create
        def tracked_audio_speech_create(*args, **kwargs):
            model = kwargs.get("model", "tts-1")
            input_text = kwargs.get("input", "")
            voice = kwargs.get("voice", "alloy")
            
            # Extract event_name from agentbill_options if provided
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "text_to_speech")
            
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI audio.speech.create: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.audio.speech.create", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "audio_speech",
                # Backward compatibility
                "model": model,
                "provider": "openai",
                "voice": voice
            })
            
            try:
                response = original_audio_speech_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # NOTE: wrap_openai() only creates OTEL spans, NOT signals
                # Cost calculation is 100% SERVER-SIDE using model_pricing table
                # SDK sends metadata only - server calculates actual cost
                chars = len(input_text)
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes for text-to-speech
                    "gen_ai.tts.character_count": chars,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ TTS OTEL span: ${cost:.6f} ({chars} chars)")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
                # Auto-flush spans to prevent data loss on script exit
                self.tracer.flush_sync()
        
        client.audio.speech.create = tracked_audio_speech_create
        
        # Track moderations
        original_moderations_create = client.moderations.create
        def tracked_moderations_create(*args, **kwargs):
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting OpenAI moderations.create")
            
            start_time = time.time()
            span = self.tracer.start_span("openai.moderations.create", {
                # OTEL GenAI compliant attributes
                "gen_ai.system": "openai",
                "gen_ai.request.model": kwargs.get("model", "text-moderation-latest"),
                "gen_ai.operation.name": "moderation",
                # Backward compatibility
                "model": kwargs.get("model", "text-moderation-latest"),
                "provider": "openai"
            })
            
            try:
                response = original_moderations_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                span.set_attributes({"latency_ms": latency})
                span.set_status(0)
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.moderations.create = tracked_moderations_create
        
        return client
    
    def wrap_anthropic(self, client: Any) -> Any:
        """Wrap Anthropic client with Cost Guard protection"""
        original_create = client.messages.create
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Extract event_name from agentbill_options if provided (don't pass to Anthropic)
            agentbill_options = kwargs.pop("agentbill_options", {})
            event_name = agentbill_options.get("event_name", "ai_request")
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            start_time = time.time()
            span = self.tracer.start_span("anthropic.message", {
                "model": model,
                "provider": "anthropic"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage with trace correlation
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens, "anthropic")
                
                self._track_usage(model, "anthropic", input_tokens, output_tokens, latency, cost, event_name, span.trace_id, span.span_id)
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "gen_ai.response.id": response.id if hasattr(response, 'id') else None,
                    "gen_ai.response.finish_reasons": [response.stop_reason] if hasattr(response, 'stop_reason') else [],
                    # Backward compatibility
                    "response.input_tokens": input_tokens,
                    "response.output_tokens": output_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.messages.create = tracked_create
        return client
    
    def wrap_bedrock(self, client: Any) -> Any:
        """Wrap AWS Bedrock client with Cost Guard protection"""
        original_invoke_model = client.invoke_model
        
        def tracked_invoke_model(*args, **kwargs):
            model = kwargs.get("modelId", "unknown")
            body_str = kwargs.get("body", "{}")
            
            # Parse body for messages
            import json
            try:
                body = json.loads(body_str)
                messages = body.get("messages", body.get("prompt", ""))
                max_tokens = body.get("max_tokens", body.get("max_tokens_to_sample", 1000))
            except:
                messages = ""
                max_tokens = 1000
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Bedrock invoke_model with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("bedrock.invoke_model", {
                # OTEL GenAI compliant attributes (using aws.bedrock as custom system)
                "gen_ai.system": "aws.bedrock",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "bedrock"
            })
            
            try:
                response = original_invoke_model(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Parse response body for token usage
                body = json.loads(response['body'].read())
                
                # Handle different Bedrock model response formats
                input_tokens = 0
                output_tokens = 0
                if 'usage' in body:  # Claude models
                    input_tokens = body['usage'].get('input_tokens', 0)
                    output_tokens = body['usage'].get('output_tokens', 0)
                elif 'inputTextTokenCount' in body:  # Titan models
                    input_tokens = body.get('inputTextTokenCount', 0)
                    output_tokens = body['results'][0].get('tokenCount', 0) if 'results' in body else 0
                
                # Phase 3: Track actual usage with correlation
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._track_usage(model, "bedrock", input_tokens, output_tokens, latency, cost, "ai_request", span.trace_id, span.span_id)
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    # Backward compatibility
                    "response.input_tokens": input_tokens,
                    "response.output_tokens": output_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.invoke_model = tracked_invoke_model
        return client
    
    def wrap_azure_openai(self, client: Any) -> Any:
        """Wrap Azure OpenAI client with Cost Guard protection"""
        original_create = client.chat.completions.create
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Azure OpenAI chat.completions.create")
            
            start_time = time.time()
            span = self.tracer.start_span("azure_openai.chat.completions", {
                # OTEL GenAI compliant attributes (using azure_openai as custom system)
                "gen_ai.system": "azure_openai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "azure_openai"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "azure_openai", input_tokens, output_tokens, latency, cost, "ai_request", span.trace_id, span.span_id)
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "gen_ai.usage.total_tokens": response.usage.total_tokens,
                    # Backward compatibility
                    "response.prompt_tokens": input_tokens,
                    "response.completion_tokens": output_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.chat.completions.create = tracked_create
        return client
    
    def wrap_mistral(self, client: Any) -> Any:
        """Wrap Mistral AI client with Cost Guard protection"""
        original_create = client.chat.complete
        
        def tracked_create(*args, **kwargs):
            model = kwargs.get("model", "unknown")
            messages = kwargs.get("messages", [])
            max_tokens = kwargs.get("max_tokens", 1000)
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, messages, max_tokens)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Mistral chat.complete with model: {model}")
            
            start_time = time.time()
            span = self.tracer.start_span("mistral.chat.complete", {
                # OTEL GenAI compliant attributes (using mistral as custom system)
                "gen_ai.system": "mistral",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "mistral"
            })
            
            try:
                response = original_create(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                
                self._track_usage(model, "mistral", input_tokens, output_tokens, latency, cost, "ai_request", span.trace_id, span.span_id)
                
                span.set_attributes({
                    # OTEL GenAI compliant attributes
                    "gen_ai.usage.input_tokens": input_tokens,
                    "gen_ai.usage.output_tokens": output_tokens,
                    "gen_ai.usage.total_tokens": response.usage.total_tokens,
                    # Backward compatibility
                    "response.prompt_tokens": input_tokens,
                    "response.completion_tokens": output_tokens,
                    "response.total_tokens": response.usage.total_tokens,
                    "latency_ms": latency
                })
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.chat.complete = tracked_create
        return client
    
    def wrap_google_ai(self, client: Any) -> Any:
        """Wrap Google AI (Gemini) client with Cost Guard protection"""
        original_generate_content = client.generate_content
        
        def tracked_generate_content(*args, **kwargs):
            model = getattr(client, '_model_name', 'gemini-pro')
            content = args[0] if args else kwargs.get("contents", "")
            
            # Phase 1: Validate budget BEFORE API call
            validation = self._validate_request(model, content, 1000)
            if not validation.get("allowed"):
                error_msg = validation.get("reason", "Budget limit reached")
                error = Exception(error_msg)
                error.code = "BUDGET_EXCEEDED"
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
                raise error
            
            # Phase 2: Execute AI call
            if self.config.get("debug"):
                print(f"[AgentBill] Intercepting Google AI generate_content")
            
            start_time = time.time()
            span = self.tracer.start_span("google_ai.generate_content", {
                # OTEL GenAI compliant attributes (using google_ai as custom system)
                "gen_ai.system": "google_ai",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "google_ai"
            })
            
            try:
                response = original_generate_content(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Phase 3: Track actual usage
                input_tokens = 0
                output_tokens = 0
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                
                cost = self._estimate_cost(model, input_tokens, output_tokens)
                self._track_usage(model, "google_ai", input_tokens, output_tokens, latency, cost, "ai_request", span.trace_id, span.span_id)
                
                if hasattr(response, 'usage_metadata'):
                    span.set_attributes({
                        # OTEL GenAI compliant attributes
                        "gen_ai.usage.input_tokens": input_tokens,
                        "gen_ai.usage.output_tokens": output_tokens,
                        "gen_ai.usage.total_tokens": response.usage_metadata.total_token_count,
                        # Backward compatibility
                        "response.prompt_tokens": input_tokens,
                        "response.completion_tokens": output_tokens,
                        "response.total_tokens": response.usage_metadata.total_token_count,
                        "latency_ms": latency
                    })
                
                span.set_status(0)
                
                if self.config.get("debug"):
                    print(f"[AgentBill Cost Guard] ✓ Protected call completed: ${cost:.4f}")
                
                return response
            except Exception as e:
                span.set_status(1, str(e))
                raise
            finally:
                span.end()
        
        client.generate_content = tracked_generate_content
        return client
    
    def wrap_perplexity(self, client: Any) -> Any:
        """Wrap Perplexity client with Cost Guard protection"""
        from .perplexity_wrapper import wrap_perplexity
        return wrap_perplexity(self, client)
    
    def wrap_ollama(self, client: Any) -> Any:
        """Wrap Ollama client with usage tracking (local, no API costs)"""
        from .ollama_wrapper import wrap_ollama
        return wrap_ollama(self, client)
    
    def track_signal(self, **kwargs):
        """
        Track a custom signal/event with comprehensive parameters
        
        Supports all 68 parameters including optional trace_id and span_id for OTEL correlation:
        - event_name (required)
        - trace_id (optional) - For correlating with OTEL spans for cost reconciliation
        - span_id (optional) - For correlating with OTEL spans for cost reconciliation
        - agent_external_id (auto-filled from config if not provided)
        - data_source, timestamp
        - customer_external_id, account_external_id, user_external_id, 
          order_external_id, session_id, conversation_id, thread_id
        - model, provider, prompt_hash, prompt_sample, response_sample, function_name, tool_name
        - prompt_tokens, completion_tokens, total_tokens, streaming_tokens, cached_tokens, reasoning_tokens
        - latency_ms, time_to_first_token, time_to_action_ms, queue_time_ms, processing_time_ms
        - revenue, cost, conversion_value, revenue_source
        - experiment_id, experiment_group, variant_id, ab_test_name
        - conversion_type, conversion_step, funnel_stage, goal_achieved
        - feedback_score, user_satisfaction, error_type, error_message, retry_count, success_rate
        - tags, category, priority, severity, compliance_flag, data_classification
        - product_id, feature_flag, environment, deployment_version, region, tenant_id
        - parent_span_id
        - custom_dimensions, metadata, data
        
        Example:
            # Basic tracking
            agentbill.track_signal(
                event_name="user_conversion",
                revenue=99.99,
                customer_external_id="cust_123"
            )
            
            # With OTEL correlation for cost reconciliation
            trace_context = agentbill.tracer.start_span("ai_completion")
            # ... make AI call ...
            agentbill.track_signal(
                event_name="ai_request",
                revenue=5.00,
                trace_id=trace_context.trace_id,  # Optional
                span_id=trace_context.span_id     # Optional
            )
        """
        import httpx
        import time
        
        if "event_name" not in kwargs:
            raise ValueError("event_name is required")
        
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/record-signals"
        
        # Build payload with all provided parameters
        payload = {k: v for k, v in kwargs.items() if v is not None}
        
        # Auto-fill agent_id or agent_external_id from config if not provided (REQUIRED by API)
        if "agent_external_id" not in payload and "agent_id" not in payload:
            if "agent_external_id" in self.config:
                payload["agent_external_id"] = self.config["agent_external_id"]
            elif "agent_id" in self.config:
                payload["agent_id"] = self.config["agent_id"]
            else:
                raise ValueError(
                    "agent_id or agent_external_id is required. Either pass it in track_signal() or set it in AgentBill.init() config. "
                    "Example: AgentBill.init({'api_key': '...', 'agent_id': 'uuid-here'}) or agent_external_id: 'my-agent-1'"
                )
        
        # Auto-fill customer_id or customer_external_id from config if not provided
        if "customer_id" not in payload and "customer_external_id" not in payload:
            if "customer_id" in self.config:
                # Check if it's a UUID format - send as customer_id, else customer_external_id
                import re
                customer_val = self.config["customer_id"]
                is_uuid = bool(re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', customer_val, re.I))
                if is_uuid:
                    payload["customer_id"] = customer_val
                else:
                    payload["customer_external_id"] = customer_val
            elif "customer_external_id" in self.config:
                payload["customer_external_id"] = self.config["customer_external_id"]
        
        # Add timestamp if not provided
        if "timestamp" not in payload:
            payload["timestamp"] = time.time()
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={
                        "X-API-Key": self.config['api_key'],
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                if self.config.get("debug"):
                    trace_info = f" (trace: {kwargs.get('trace_id')})" if kwargs.get('trace_id') else ""
                    print(f"[AgentBill] Signal tracked: {kwargs.get('event_name')}{trace_info}")
                return response.status_code == 200
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill] Failed to track signal: {e}")
            return False
    
    def track_conversion(self, event_type: str, event_value: float, signal_id: Optional[str] = None, 
                         session_id: Optional[str] = None, attribution_window_hours: int = 24,
                         currency: str = "USD", metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Track a conversion event for prompt profitability analysis
        Links conversions to AI prompts to calculate ROI per prompt
        
        Args:
            event_type: Type of conversion (e.g., 'purchase', 'signup', 'trial_start')
            event_value: Revenue amount from the conversion
            signal_id: Optional UUID linking to specific AI signal/prompt
            session_id: Optional session identifier
            attribution_window_hours: Time window for attribution (default: 24 hours)
            currency: Currency code (default: 'USD')
            metadata: Optional additional data
            
        Returns:
            Dict with success status and conversion_id
            
        Example:
            # Track a purchase conversion
            result = agentbill.track_conversion(
                event_type="purchase",
                event_value=99.99,
                currency="USD"
            )
            
            # Link conversion to specific AI prompt
            result = agentbill.track_conversion(
                event_type="trial_signup",
                event_value=29.99,
                signal_id="signal-uuid-from-prompt",
                session_id="session-123"
            )
        """
        import httpx
        
        url = f"{self.config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')}/functions/v1/track-conversion"
        
        payload = {
            "api_key": self.config["api_key"],
            "customer_id": self.config.get("customer_id"),
            "event_type": event_type,
            "event_value": event_value,
            "signal_id": signal_id,
            "session_id": session_id,
            "attribution_window_hours": attribution_window_hours,
            "currency": currency,
            "metadata": metadata
        }
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                data = response.json()
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": data.get("error", f"HTTP {response.status_code}")
                    }
                
                if self.config.get("debug"):
                    print(f"[AgentBill] Conversion tracked: {event_type} = ${event_value} (ID: {data.get('conversion_id')})")
                
                return {
                    "success": True,
                    "conversion_id": data.get("conversion_id")
                }
        except Exception as e:
            if self.config.get("debug"):
                print(f"[AgentBill] Failed to track conversion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def flush(self):
        """Flush pending telemetry data"""
        await self.tracer.flush()
