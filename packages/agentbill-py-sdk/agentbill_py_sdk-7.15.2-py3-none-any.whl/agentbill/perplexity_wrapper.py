"""
Perplexity AI Wrapper for AgentBill
Tracks Perplexity's Sonar models with online search capabilities
"""

import time
from typing import Any

# Cost calculation is now 100% server-side - SDK only sends tokens


def wrap_perplexity(agentbill_instance: Any, client: Any) -> Any:
    """
    Wrap Perplexity client with Cost Guard protection
    
    Example:
        from agentbill import AgentBill
        from perplexity import Perplexity
        
        agentbill = AgentBill.init({"api_key": "..."})
        perplexity = agentbill.wrap_perplexity(Perplexity(api_key="pplx-..."))
        
        response = perplexity.chat.completions.create(
            model="llama-3.1-sonar-small-128k-online",
            messages=[{"role": "user", "content": "What's the latest news?"}]
        )
    """
    
    # Track chat completions (Perplexity uses OpenAI-compatible API)
    original_chat_create = client.chat.completions.create
    
    def tracked_chat_create(*args, **kwargs):
        model = kwargs.get("model", "llama-3.1-sonar-small-128k-online")
        messages = kwargs.get("messages", [])
        max_tokens = kwargs.get("max_tokens", 1000)
        
        # Extract event_name from agentbill_options if provided
        agentbill_options = kwargs.pop("agentbill_options", {})
        event_name = agentbill_options.get("event_name", "perplexity_search")
        
        # Phase 1: Validate budget BEFORE API call
        validation = agentbill_instance._validate_request(model, messages, max_tokens)
        if not validation.get("allowed"):
            error_msg = validation.get("reason", "Budget limit reached")
            error = Exception(error_msg)
            error.code = "BUDGET_EXCEEDED"
            if agentbill_instance.config.get("debug"):
                print(f"[AgentBill Cost Guard] ❌ Request blocked: {error_msg}")
            raise error
        
        # Phase 2: Execute AI call
        if agentbill_instance.config.get("debug"):
            print(f"[AgentBill] Intercepting Perplexity chat.completions.create with model: {model}")
        
        start_time = time.time()
        span = agentbill_instance.tracer.start_span("perplexity.chat.completions.create", {
            # OTEL GenAI compliant attributes (using perplexity as custom system)
            "gen_ai.system": "perplexity",
            "gen_ai.request.model": model,
            "gen_ai.operation.name": "chat",
            # Backward compatibility
            "model": model,
            "provider": "perplexity"
        })
        
        try:
            response = original_chat_create(*args, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            # Phase 3: Track actual usage
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = calculate_cost(model, input_tokens, output_tokens, "perplexity")
            
            agentbill_instance._track_usage(
                model, "perplexity", input_tokens, output_tokens, latency, cost, event_name, span.trace_id, span.span_id
            )
            
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
            
            if agentbill_instance.config.get("debug"):
                print(f"[AgentBill Cost Guard] ✓ Perplexity call completed: ${cost:.4f}")
            
            return response
        except Exception as e:
            span.set_status(1, str(e))
            raise
        finally:
            span.end()
    
    client.chat.completions.create = tracked_chat_create
    return client
