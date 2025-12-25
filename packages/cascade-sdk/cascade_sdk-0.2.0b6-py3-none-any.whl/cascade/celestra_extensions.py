"""
Cascade extensions for capturing reasoning and other custom span types
"""
import time
import inspect
import functools
import logging
from typing import Any, Callable, Optional
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from cascade.tracing import get_tracer

logger = logging.getLogger(__name__)

# Maximum size for input/output values (in characters)
# Set to None for unlimited (no truncation)
MAX_VALUE_SIZE = None


def _truncate_text(text: str, max_length: Optional[int] = MAX_VALUE_SIZE) -> str:
    """Truncate text if it's too long, preserving structure."""
    if max_length is None:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (truncated, total length: {len(text)})"


def _extract_reasoning(text: str) -> str:
    """
    Extract reasoning lines from text that contain 'REASONING:'.
    
    Args:
        text: The input text that may contain reasoning
        
    Returns:
        Extracted reasoning lines joined by newlines, or empty string if none found
    """
    if not text or "REASONING:" not in text:
        return ""
    
    reasoning_lines = [line.strip() for line in text.split('\n') if 'REASONING:' in line]
    return '\n'.join(reasoning_lines)


def capture_reasoning(func: Optional[Callable] = None, name: Optional[str] = None):
    """
    Decorator to capture reasoning extraction from text.
    
    Automatically creates spans for reasoning extraction, recording:
    - Input text (full text passed to function)
    - Output reasoning (extracted reasoning lines)
    - Execution time
    
    Works with instance methods (handles 'self' parameter).
    
    Args:
        func: Function to decorate (when used as @capture_reasoning)
        name: Optional custom name for the span (defaults to function name)
    
    Example:
        ```python
        @capture_reasoning
        def _log_reasoning(self, text: str):
            if not self.log_file:
                return
            # ... existing logic ...
        ```
    """
    def decorator(f: Callable) -> Callable:
        # Use provided name or function name
        span_name = name if name is not None else f.__name__
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            """Sync wrapper for capture_reasoning decorator."""
            start_time = time.time()
            tracer = get_tracer()
            
            if not tracer:
                # No tracer, just execute function
                return f(*args, **kwargs)
            
            # Use start_as_current_span for automatic context propagation (like tool decorator)
            with tracer.start_as_current_span(
                span_name,
                kind=SpanKind.INTERNAL
            ) as span_context:
                span = trace.get_current_span()
                
                # Set span attributes
                span.set_attribute("cascade.span_type", "reasoning")
                span.set_attribute("reasoning.name", span_name)
                
                # Extract input (text parameter)
                # Handle both instance methods (self) and regular functions
                try:
                    sig = inspect.signature(f)
                    param_names = list(sig.parameters.keys())
                    
                    # Find the 'text' parameter
                    text_value = None
                    if 'text' in kwargs:
                        text_value = kwargs['text']
                    else:
                        # Check positional arguments
                        # Skip 'self' if it's an instance method
                        start_idx = 1 if param_names and param_names[0] == 'self' else 0
                        for i, arg_value in enumerate(args[start_idx:], start=start_idx):
                            if i < len(param_names):
                                param_name = param_names[i]
                                if param_name == 'text':
                                    text_value = arg_value
                                    break
                    
                    # Store input (no truncation - store full text)
                    if text_value is not None:
                        input_text = str(text_value)
                        span.set_attribute("reasoning.input", input_text)
                        
                        # Extract reasoning from input
                        extracted_reasoning = _extract_reasoning(input_text)
                        if extracted_reasoning:
                            span.set_attribute("reasoning.output", extracted_reasoning)
                        else:
                            span.set_attribute("reasoning.output", "(no reasoning found)")
                    else:
                        # Fallback: serialize all args/kwargs
                        input_dict = {}
                        for i, arg_value in enumerate(args):
                            if i < len(param_names):
                                param_name = param_names[i]
                                if param_name != 'self':  # Skip self
                                    input_dict[param_name] = arg_value
                            else:
                                input_dict[f"arg_{i}"] = arg_value
                        input_dict.update({k: v for k, v in kwargs.items() if k != 'self'})
                        
                        import json
                        try:
                            input_json = json.dumps(input_dict, default=str)
                            span.set_attribute("reasoning.input", input_json)
                        except Exception:
                            span.set_attribute("reasoning.input", str(input_dict))
                        
                        # Try to extract reasoning from any text-like value
                        all_text = ' '.join([str(v) for v in input_dict.values() if isinstance(v, str)])
                        extracted_reasoning = _extract_reasoning(all_text)
                        if extracted_reasoning:
                            span.set_attribute("reasoning.output", extracted_reasoning)
                        else:
                            span.set_attribute("reasoning.output", "(no reasoning found)")
                            
                except Exception as e:
                    logger.warning(f"Error capturing reasoning input: {e}")
                    span.set_attribute("reasoning.input", f"<error: {e}>")
                    span.set_attribute("reasoning.output", "<error extracting reasoning>")
                
                try:
                    # Execute function
                    result = f(*args, **kwargs)
                    
                    # Calculate duration
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("reasoning.duration_ms", duration_ms)
                    
                    # Create Final Reasoning Summary span
                    # Get current trace_id from span context
                    try:
                        span_context = span.get_span_context()
                        trace_id = format(span_context.trace_id, '032x')  # Convert to hex string
                        
                        # Query backend API to get all spans in this trace
                        # We'll do this asynchronously or in a background thread to avoid blocking
                        import threading
                        import os
                        
                        def create_reasoning_summary():
                            try:
                                import time
                                import requests
                                
                                # Wait a bit for spans to be exported and stored
                                time.sleep(0.5)
                                
                                backend_url = os.getenv("CASCADE_BACKEND_URL", "http://localhost:8000")
                                
                                # Get all spans in trace
                                response = requests.get(f"{backend_url}/api/traces/{trace_id}", timeout=5)
                                if response.status_code == 200:
                                    trace_data = response.json()
                                    spans = trace_data.get("spans", [])
                                    
                                    # Filter for LLM spans with reasoning
                                    llm_reasoning_spans = []
                                    for span_data in spans:
                                        attrs = span_data.get("attributes", {})
                                        if attrs.get("cascade.span_type") == "llm" and attrs.get("llm.reasoning"):
                                            llm_reasoning_spans.append({
                                                "name": span_data.get("name", "Unknown"),
                                                "reasoning": attrs["llm.reasoning"],
                                                "start_time": span_data.get("start_time", 0)
                                            })
                                    
                                    # Sort by start_time to maintain order
                                    llm_reasoning_spans.sort(key=lambda x: x["start_time"])
                                    
                                    # Create summary span with numbered reasoning statements
                                    if llm_reasoning_spans:
                                        tracer = get_tracer()
                                        if tracer:
                                            with tracer.start_as_current_span(
                                                "Final Reasoning Summary",
                                                kind=SpanKind.INTERNAL
                                            ) as summary_span_context:
                                                summary_span = trace.get_current_span()
                                                summary_span.set_attribute("cascade.span_type", "reasoning")
                                                summary_span.set_attribute("reasoning.name", "Final Reasoning Summary")
                                                
                                                # Build numbered reasoning list
                                                numbered_reasoning = []
                                                for idx, llm_span in enumerate(llm_reasoning_spans, 1):
                                                    reasoning_lines = llm_span["reasoning"].split('\n')
                                                    for line in reasoning_lines:
                                                        if line.strip():
                                                            numbered_reasoning.append(f"[{idx}] {line.strip()}")
                                                
                                                summary_text = "\n".join(numbered_reasoning)
                                                summary_span.set_attribute("reasoning.input", summary_text)
                                                summary_span.set_attribute("reasoning.output", summary_text)
                                                summary_span.set_status(Status(StatusCode.OK))
                            except Exception as e:
                                logger.debug(f"Could not create reasoning summary: {e}")
                        
                        # Run in background thread to avoid blocking
                        thread = threading.Thread(target=create_reasoning_summary, daemon=True)
                        thread.start()
                    except Exception as e:
                        logger.debug(f"Could not get trace_id for reasoning summary: {e}")
                    
                    # Mark span as successful
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    # Mark span as error
                    duration_ms = (time.time() - start_time) * 1000
                    span.set_attribute("reasoning.duration_ms", duration_ms)
                    span.set_attribute("reasoning.error", str(e))
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        return wrapper
    
    # Handle both @capture_reasoning and @capture_reasoning() usage
    if func is None:
        # Called as @capture_reasoning() with optional args
        return decorator
    else:
        # Called as @capture_reasoning without parentheses
        return decorator(func)

