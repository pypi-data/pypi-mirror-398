"""
Tool decorator for tracking tool executions
"""
import time
import json
import inspect
import functools
import logging
from typing import Any, Callable, Optional, Dict
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


def _serialize_value(value: Any) -> str:
    """
    Serialize a value to JSON string, handling non-serializable types.
    
    Args:
        value: Value to serialize
        
    Returns:
        JSON string representation
    """
    try:
        # Try JSON serialization first
        json_str = json.dumps(value, default=str, ensure_ascii=False)
        return _truncate_text(json_str)
    except (TypeError, ValueError) as e:
        # Fallback to string representation
        str_repr = str(value)
        return _truncate_text(str_repr)


def _create_tool_span(func: Callable, args: tuple, kwargs: dict) -> trace.Span:
    """
    Create a span for a tool execution.
    
    Args:
        func: The function being called
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        The created span
    """
    tracer = get_tracer()
    if not tracer:
        return None
    
    # Get function name (this function is deprecated but kept for compatibility)
    span_name = func.__name__
    
    # Create span
    span = tracer.start_span(span_name, kind=SpanKind.INTERNAL)
    
    # Set span attributes
    span.set_attribute("cascade.span_type", "tool")
    span.set_attribute("tool.name", span_name)
    
    # Add docstring if available
    if func.__doc__:
        docstring = func.__doc__.strip().split('\n')[0]  # First line only
        span.set_attribute("tool.description", _truncate_text(docstring, 200))
    
    # Serialize and store inputs
    try:
        # Build input dict
        input_dict = {}
        
        # Get function signature to name positional args
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        
        # Add positional arguments
        for i, arg_value in enumerate(args):
            if i < len(param_names):
                param_name = param_names[i]
                input_dict[param_name] = arg_value
            else:
                input_dict[f"arg_{i}"] = arg_value
        
        # Add keyword arguments
        input_dict.update(kwargs)
        
        # Serialize input
        input_json = _serialize_value(input_dict)
        span.set_attribute("tool.input", input_json)
        
    except Exception as e:
        logger.warning(f"Error serializing tool input: {e}")
        span.set_attribute("tool.input", f"<error serializing: {e}>")
    
    return span


def tool(func: Optional[Callable] = None, name: Optional[str] = None, **decorator_kwargs):
    """
    Decorator to track tool executions.
    
    Automatically creates spans for each tool call, recording:
    - Input parameters
    - Output value
    - Execution time
    - Errors (if any)
    
    Works with both sync and async functions.
    
    Args:
        func: Function to decorate (when used as @tool)
        name: Optional custom name for the tool span (defaults to function name)
        **decorator_kwargs: Additional decorator arguments
    
    Example:
        ```python
        @tool
        def read_file(filepath: str) -> str:
            with open(filepath, 'r') as f:
                return f.read()
        
        @tool(name="CustomToolName")
        async def execute(self, input: Dict) -> Dict:
            # Custom name will be used instead of "execute"
            ...
        
        @tool
        async def async_tool(url: str) -> str:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    return await response.text()
        ```
    """
    def decorator(f: Callable) -> Callable:
        # Use provided name or function name
        tool_name = name if name is not None else f.__name__
        # Check if function is async
        is_async = inspect.iscoroutinefunction(f)
        
        if is_async:
            @functools.wraps(f)
            async def async_wrapper(*args, **kwargs):
                """Async wrapper for tool decorator."""
                start_time = time.time()
                tracer = get_tracer()
                
                if not tracer:
                    # No tracer, just execute function
                    return await f(*args, **kwargs)
                
                # Use start_as_current_span for automatic context propagation
                # This ensures the tool span is correctly nested under the parent span
                with tracer.start_as_current_span(
                    tool_name,
                    kind=SpanKind.INTERNAL
                ) as span_context:
                    span = trace.get_current_span()
                    
                    # Set span attributes
                    span.set_attribute("cascade.span_type", "tool")
                    span.set_attribute("tool.name", tool_name)
                    
                    # Add agent context if available
                    from cascade.tracing import get_current_agent
                    current_agent = get_current_agent()
                    if current_agent:
                        span.set_attribute("cascade.agent_name", current_agent)
                    
                    # Add docstring if available
                    if f.__doc__:
                        docstring = f.__doc__.strip().split('\n')[0]
                        span.set_attribute("tool.description", _truncate_text(docstring, 200))
                    
                    # Serialize and store inputs
                    try:
                        sig = inspect.signature(f)
                        param_names = list(sig.parameters.keys())
                        
                        input_dict = {}
                        for i, arg_value in enumerate(args):
                            if i < len(param_names):
                                input_dict[param_names[i]] = arg_value
                            else:
                                input_dict[f"arg_{i}"] = arg_value
                        input_dict.update(kwargs)
                        
                        input_json = _serialize_value(input_dict)
                        span.set_attribute("tool.input", input_json)
                    except Exception as e:
                        logger.warning(f"Error serializing tool input: {e}")
                        span.set_attribute("tool.input", f"<error serializing: {e}>")
                    
                    try:
                        # Execute function
                        result = await f(*args, **kwargs)
                        
                        # Calculate duration
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Record output
                        try:
                            output_json = _serialize_value(result)
                            span.set_attribute("tool.output", output_json)
                        except Exception as e:
                            logger.warning(f"Error serializing tool output: {e}")
                            span.set_attribute("tool.output", f"<error serializing: {e}>")
                        
                        # Set duration and status
                        span.set_attribute("tool.duration_ms", duration_ms)
                        span.set_status(Status(StatusCode.OK))
                        
                        return result
                        
                    except Exception as e:
                        # Handle errors
                        duration_ms = (time.time() - start_time) * 1000
                        span.set_attribute("tool.duration_ms", duration_ms)
                        span.set_attribute("tool.error", str(e))
                        span.set_status(Status(StatusCode.ERROR, str(e)))
                        span.record_exception(e)
                        raise
            
            return async_wrapper
        
        else:
            @functools.wraps(f)
            def sync_wrapper(*args, **kwargs):
                """Sync wrapper for tool decorator."""
                start_time = time.time()
                span = None
                
                try:
                    # Create span using start_as_current_span for automatic context propagation
                    tracer = get_tracer()
                    if tracer:
                        with tracer.start_as_current_span(
                            tool_name,
                            kind=SpanKind.INTERNAL
                        ) as span_context:
                            span = trace.get_current_span()
                            
                            # Set span attributes
                            span.set_attribute("cascade.span_type", "tool")
                            span.set_attribute("tool.name", tool_name)
                            
                            # Add agent context if available
                            from cascade.tracing import get_current_agent
                            current_agent = get_current_agent()
                            if current_agent:
                                span.set_attribute("cascade.agent_name", current_agent)
                            
                            # Add docstring if available
                            if f.__doc__:
                                docstring = f.__doc__.strip().split('\n')[0]
                                span.set_attribute("tool.description", _truncate_text(docstring, 200))
                            
                            # Serialize and store inputs
                            try:
                                sig = inspect.signature(f)
                                param_names = list(sig.parameters.keys())
                                
                                input_dict = {}
                                for i, arg_value in enumerate(args):
                                    if i < len(param_names):
                                        input_dict[param_names[i]] = arg_value
                                    else:
                                        input_dict[f"arg_{i}"] = arg_value
                                input_dict.update(kwargs)
                                
                                input_json = _serialize_value(input_dict)
                                span.set_attribute("tool.input", input_json)
                            except Exception as e:
                                logger.warning(f"Error serializing tool input: {e}")
                                span.set_attribute("tool.input", f"<error serializing: {e}>")
                            
                            try:
                                # Execute function
                                result = f(*args, **kwargs)
                                
                                # Calculate duration
                                duration_ms = (time.time() - start_time) * 1000
                                
                                # Record output
                                try:
                                    output_json = _serialize_value(result)
                                    span.set_attribute("tool.output", output_json)
                                except Exception as e:
                                    logger.warning(f"Error serializing tool output: {e}")
                                    span.set_attribute("tool.output", f"<error serializing: {e}>")
                                
                                # Set duration and status
                                span.set_attribute("tool.duration_ms", duration_ms)
                                span.set_status(Status(StatusCode.OK))
                                
                                return result
                                
                            except Exception as e:
                                # Handle errors
                                duration_ms = (time.time() - start_time) * 1000
                                span.set_attribute("tool.duration_ms", duration_ms)
                                span.set_attribute("tool.error", str(e))
                                span.set_status(Status(StatusCode.ERROR, str(e)))
                                span.record_exception(e)
                                raise
                    else:
                        # No tracer, just execute function
                        return f(*args, **kwargs)
                        
                except Exception as e:
                    # If span wasn't created, still re-raise
                    raise
            
            return sync_wrapper
    
    # Handle both @tool and @tool() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)
