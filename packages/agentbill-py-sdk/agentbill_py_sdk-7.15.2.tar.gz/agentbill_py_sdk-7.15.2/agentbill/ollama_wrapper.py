"""
Ollama Wrapper for AgentBill
Tracks local Ollama model usage (no API costs, but tracks metrics)
"""

import time
from typing import Any


def wrap_ollama(agentbill_instance: Any, client: Any) -> Any:
    """
    Wrap Ollama client with usage tracking
    
    NOTE: Ollama runs locally so there are no API costs, but we track
    metrics for usage monitoring and optimization.
    
    Example:
        from agentbill import AgentBill
        from ollama import Client
        
        agentbill = AgentBill.init({"api_key": "..."})
        ollama = agentbill.wrap_ollama(Client())
        
        response = ollama.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    
    # Track chat
    original_chat = client.chat
    
    def tracked_chat(*args, **kwargs):
        model = kwargs.get("model", "llama3.2")
        messages = kwargs.get("messages", [])
        
        # Extract event_name from agentbill_options if provided
        agentbill_options = kwargs.pop("agentbill_options", {})
        event_name = agentbill_options.get("event_name", "ollama_local")
        
        if agentbill_instance.config.get("debug"):
            print(f"[AgentBill] Intercepting Ollama chat with model: {model} (LOCAL - NO API COST)")
        
        start_time = time.time()
            span = agentbill_instance.tracer.start_span("ollama.chat", {
                # OTEL GenAI compliant attributes (using ollama as custom system)
                "gen_ai.system": "ollama",
                "gen_ai.request.model": model,
                "gen_ai.operation.name": "chat",
                # Backward compatibility
                "model": model,
                "provider": "ollama"
            })
        
        try:
            response = original_chat(*args, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            # Track usage metrics (cost is $0.00 for local)
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)
            cost = 0.0  # Local execution, no cost
            
            agentbill_instance._track_usage(
                f"ollama/{model}", "ollama", input_tokens, output_tokens, latency, cost, event_name, span.trace_id, span.span_id
            )
            
            span.set_attributes({
                # OTEL GenAI compliant attributes
                "gen_ai.usage.input_tokens": input_tokens,
                "gen_ai.usage.output_tokens": output_tokens,
                "gen_ai.usage.total_tokens": input_tokens + output_tokens,
                # Backward compatibility
                "response.prompt_tokens": input_tokens,
                "response.completion_tokens": output_tokens,
                "response.total_tokens": input_tokens + output_tokens,
                "latency_ms": latency,
                "cost": 0.0
            })
            span.set_status(0)
            
            if agentbill_instance.config.get("debug"):
                print(f"[AgentBill] ✓ Ollama call tracked: {input_tokens + output_tokens} tokens (LOCAL, $0.00)")
            
            return response
        except Exception as e:
            span.set_status(1, str(e))
            raise
        finally:
            span.end()
    
    client.chat = tracked_chat
    
    # Track generate
    original_generate = client.generate
    
    def tracked_generate(*args, **kwargs):
        model = kwargs.get("model", "llama3.2")
        prompt = kwargs.get("prompt", "")
        
        # Extract event_name from agentbill_options if provided
        agentbill_options = kwargs.pop("agentbill_options", {})
        event_name = agentbill_options.get("event_name", "ollama_generate")
        
        if agentbill_instance.config.get("debug"):
            print(f"[AgentBill] Intercepting Ollama generate with model: {model} (LOCAL - NO API COST)")
        
        start_time = time.time()
        span = agentbill_instance.tracer.start_span("ollama.generate", {
            # OTEL GenAI compliant attributes (using ollama as custom system)
            "gen_ai.system": "ollama",
            "gen_ai.request.model": model,
            "gen_ai.operation.name": "text_completion",
            # Backward compatibility
            "model": model,
            "provider": "ollama"
        })
        
        try:
            response = original_generate(*args, **kwargs)
            latency = (time.time() - start_time) * 1000
            
            # Track usage metrics (cost is $0.00 for local)
            input_tokens = response.get("prompt_eval_count", 0)
            output_tokens = response.get("eval_count", 0)
            cost = 0.0  # Local execution, no cost
            
            agentbill_instance._track_usage(
                f"ollama/{model}", "ollama", input_tokens, output_tokens, latency, cost, event_name, span.trace_id, span.span_id
            )
            
            span.set_attributes({
                # OTEL GenAI compliant attributes
                "gen_ai.usage.input_tokens": input_tokens,
                "gen_ai.usage.output_tokens": output_tokens,
                # Backward compatibility
                "response.prompt_tokens": input_tokens,
                "response.completion_tokens": output_tokens,
                "latency_ms": latency,
                "cost": 0.0
            })
            span.set_status(0)
            
            if agentbill_instance.config.get("debug"):
                print(f"[AgentBill] ✓ Ollama generation tracked: {input_tokens + output_tokens} tokens (LOCAL, $0.00)")
            
            return response
        except Exception as e:
            span.set_status(1, str(e))
            raise
        finally:
            span.end()
    
    client.generate = tracked_generate
    
    return client
