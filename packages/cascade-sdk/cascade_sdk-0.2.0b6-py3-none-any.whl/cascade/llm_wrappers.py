"""
LLM client wrappers for tracking LLM calls
"""
import time
import logging
from typing import Optional, Dict, Any, Union
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode, SpanKind
from cascade.tracing import get_tracer

logger = logging.getLogger(__name__)

# Cost per 1K tokens (input, output) for Anthropic models
# Prices as of 2024 - update as needed
ANTHROPIC_COST_PER_1K_TOKENS = {
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.0008, "output": 0.004},
    "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
    "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-opus-20241022": {"input": 0.015, "output": 0.075},
}

# Default cost for unknown models
DEFAULT_COST = {"input": 0.003, "output": 0.015}


def _calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate estimated cost in USD based on model and token usage."""
    costs = ANTHROPIC_COST_PER_1K_TOKENS.get(model, DEFAULT_COST)
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    return input_cost + output_cost


def _truncate_text(text: str, max_length: Optional[int] = None) -> str:
    """Truncate text if it's too long, preserving structure."""
    if max_length is None:
        return text
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"\n... (truncated, total length: {len(text)})"


def _extract_messages(messages: list) -> Dict[str, Any]:
    """Extract and format messages for span attributes."""
    formatted_messages = []
    system_message = None
    
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "system":
                system_message = content
            else:
                formatted_messages.append({
                    "role": role,
                    "content": _truncate_text(str(content))
                })
        else:
            # Handle Anthropic message objects
            formatted_messages.append({
                "role": getattr(msg, "role", "unknown"),
                "content": _truncate_text(str(getattr(msg, "content", "")))
            })
    
    return {
        "system": system_message,
        "messages": formatted_messages
    }


class _AnthropicMessagesWrapper:
    """Wrapper for Anthropic Messages API to track LLM calls."""
    
    def __init__(self, original_messages, tracer: Optional[trace.Tracer]):
        self._original = original_messages
        self._tracer = tracer
    
    def create(self, *args, **kwargs):
        """Intercept messages.create() to create spans."""
        if not self._tracer:
            # No tracer, just call original
            return self._original.create(*args, **kwargs)
        
        # Extract model and messages
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        max_tokens = kwargs.get("max_tokens")
        
        # Extract message content
        message_data = _extract_messages(messages)
        
        # Start timing
        start_time = time.time()
        
        # Create span
        span_name = f"llm.{model}"
        with self._tracer.start_as_current_span(
            span_name,
            kind=SpanKind.CLIENT
        ) as span_context:
            span = trace.get_current_span()
            
            # Set basic attributes
            span.set_attribute("cascade.span_type", "llm")
            span.set_attribute("llm.model", model)
            span.set_attribute("llm.provider", "anthropic")
            
            # Add agent context if available
            from cascade.tracing import get_current_agent
            current_agent = get_current_agent()
            if current_agent:
                span.set_attribute("cascade.agent_name", current_agent)
            
            if max_tokens:
                span.set_attribute("llm.max_tokens", max_tokens)
            
            # Set prompt attributes
            if message_data["system"]:
                span.set_attribute("llm.system_message", _truncate_text(message_data["system"]))
            
            # Store full messages (truncated)
            user_messages = [msg for msg in message_data["messages"] if msg["role"] == "user"]
            if user_messages:
                full_prompt = "\n".join([msg["content"] for msg in user_messages])
                span.set_attribute("llm.prompt", _truncate_text(full_prompt))
            
            # Store all messages as JSON (for detailed view)
            span.set_attribute("llm.messages", str(message_data["messages"]))
            
            try:
                # Make the actual API call
                response = self._original.create(*args, **kwargs)
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract token usage
                input_tokens = 0
                output_tokens = 0
                total_tokens = 0
                
                if hasattr(response, "usage"):
                    usage = response.usage
                    input_tokens = getattr(usage, "input_tokens", 0)
                    output_tokens = getattr(usage, "output_tokens", 0)
                    total_tokens = input_tokens + output_tokens
                
                # Extract completion text
                completion_text = ""
                reasoning_text = None
                
                if hasattr(response, "content"):
                    content_parts = []
                    reasoning_parts = []
                    
                    for item in response.content:
                        if hasattr(item, "type"):
                            if item.type == "text":
                                content_parts.append(getattr(item, "text", ""))
                            elif item.type == "tool_use":
                                # Tool use content
                                tool_content = f"[Tool Use: {getattr(item, 'name', 'unknown')}]"
                                content_parts.append(tool_content)
                            elif hasattr(item, "text"):  # Fallback
                                content_parts.append(item.text)
                        
                        # Check for reasoning (if available in future API versions)
                        if hasattr(item, "reasoning"):
                            reasoning_parts.append(str(item.reasoning))
                    
                    completion_text = "\n".join(content_parts)
                    if reasoning_parts:
                        reasoning_text = "\n".join(reasoning_parts)
                
                # Set token attributes
                span.set_attribute("llm.input_tokens", input_tokens)
                span.set_attribute("llm.output_tokens", output_tokens)
                span.set_attribute("llm.total_tokens", total_tokens)
                span.set_attribute("llm.latency_ms", latency_ms)
                
                # Set completion (no truncation - store full text)
                if completion_text:
                    span.set_attribute("llm.completion", completion_text)
                    
                    # Extract reasoning from completion text
                    from cascade.celestra_extensions import _extract_reasoning
                    extracted_reasoning = _extract_reasoning(completion_text)
                    if extracted_reasoning:
                        span.set_attribute("llm.reasoning", extracted_reasoning)
                        logger.debug(f"Extracted reasoning from LLM completion: {len(extracted_reasoning)} chars")
                
                if reasoning_text:
                    span.set_attribute("llm.reasoning", reasoning_text)
                
                # Calculate and set cost
                if input_tokens > 0 or output_tokens > 0:
                    cost = _calculate_cost(model, input_tokens, output_tokens)
                    span.set_attribute("llm.cost_usd", cost)
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
                return response
                
            except Exception as e:
                # Mark span as error
                latency_ms = (time.time() - start_time) * 1000
                span.set_attribute("llm.latency_ms", latency_ms)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def stream(self, *args, **kwargs):
        """Intercept messages.stream() for streaming responses."""
        if not self._tracer:
            return self._original.stream(*args, **kwargs)
        
        # Get the stream manager from Anthropic
        stream_manager = self._original.stream(*args, **kwargs)
        
        # Create a wrapper context manager that tracks the stream
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        message_data = _extract_messages(messages)
        start_time = time.time()
        
        class _StreamWrapper:
            """Wrapper for MessageStreamManager that adds tracing."""
            
            def __init__(self, stream_manager, tracer, model, message_data, start_time):
                self._stream_manager = stream_manager
                self._tracer = tracer
                self._model = model
                self._message_data = message_data
                self._start_time = start_time
                self._span = None
                self._chunks = []
                self._text_content = ""
                self._final_message = None  # Store final message for token counts
            
            def __enter__(self):
                # Enter the original stream manager
                self._stream = self._stream_manager.__enter__()
                
                # Create span for streaming
                span_name = f"llm.{self._model}.stream"
                # Store the context manager itself, not the result of __enter__()
                self._span_context = self._tracer.start_as_current_span(
                    span_name,
                    kind=SpanKind.CLIENT
                )
                # Enter the span context
                self._span_context.__enter__()
                self._span = trace.get_current_span()
                
                # Set span attributes
                self._span.set_attribute("cascade.span_type", "llm")
                self._span.set_attribute("llm.model", self._model)
                self._span.set_attribute("llm.provider", "anthropic")
                self._span.set_attribute("llm.streaming", True)
                
                # Add agent context if available
                from cascade.tracing import get_current_agent
                current_agent = get_current_agent()
                if current_agent:
                    self._span.set_attribute("cascade.agent_name", current_agent)
                
                if self._message_data["system"]:
                    self._span.set_attribute("llm.system_message", _truncate_text(self._message_data["system"]))
                
                user_messages = [msg for msg in self._message_data["messages"] if msg["role"] == "user"]
                if user_messages:
                    full_prompt = "\n".join([msg["content"] for msg in user_messages])
                    self._span.set_attribute("llm.prompt", _truncate_text(full_prompt))
                
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # Set final attributes BEFORE span context exits
                # This is critical - attributes must be set while span is still active
                if self._span:
                    # Calculate metrics
                    latency_ms = (time.time() - self._start_time) * 1000
                    
                    # Try to get actual token counts from final message
                    input_tokens = 0
                    output_tokens = 0
                    total_tokens = 0
                    
                    try:
                        # Try to get final message from the stream if available
                        # Note: get_final_message() might be called after __exit__, so we try both
                        final_message = self._final_message
                        if final_message is None:
                            # Try to get it from the stream directly
                            if hasattr(self, '_stream') and hasattr(self._stream, 'get_final_message'):
                                try:
                                    final_message = self._stream.get_final_message()
                                    self._final_message = final_message  # Cache it
                                except Exception:
                                    pass
                        
                        if final_message and hasattr(final_message, "usage"):
                            usage = final_message.usage
                            input_tokens = getattr(usage, "input_tokens", 0)
                            output_tokens = getattr(usage, "output_tokens", 0)
                            total_tokens = input_tokens + output_tokens
                            logger.debug(f"Got token counts from final message: input={input_tokens}, output={output_tokens}")
                    except Exception as e:
                        logger.debug(f"Could not get usage from final message: {e}")
                        # Fallback: estimate tokens (rough approximation: ~4 chars per token)
                        if self._text_content:
                            output_tokens = len(self._text_content) // 4
                            total_tokens = output_tokens
                            logger.debug(f"Using estimated token counts: output={output_tokens}")
                    
                    # Set all attributes while span is still active
                    self._span.set_attribute("llm.latency_ms", latency_ms)
                    self._span.set_attribute("llm.input_tokens", input_tokens)
                    self._span.set_attribute("llm.output_tokens", output_tokens)
                    self._span.set_attribute("llm.total_tokens", total_tokens)
                    
                    # Set completion text if we have it (no truncation - store full text)
                    # Use stored final message text if available, otherwise use accumulated text
                    completion_text = self._text_content
                    if final_message and hasattr(final_message, "content"):
                        # Try to get full text from final message content blocks
                        try:
                            final_text_parts = []
                            for block in final_message.content:
                                if hasattr(block, "type") and block.type == "text":
                                    if hasattr(block, "text"):
                                        final_text_parts.append(block.text)
                            if final_text_parts:
                                completion_text = "\n".join(final_text_parts)
                        except Exception:
                            pass  # Fall back to accumulated text
                    
                    if completion_text:
                        self._span.set_attribute("llm.completion", completion_text)
                        logger.debug(f"Set completion text length: {len(completion_text)}")
                        
                        # Extract reasoning from completion text
                        from cascade.celestra_extensions import _extract_reasoning
                        reasoning_text = _extract_reasoning(completion_text)
                        if reasoning_text:
                            self._span.set_attribute("llm.reasoning", reasoning_text)
                            logger.debug(f"Extracted reasoning from LLM completion: {len(reasoning_text)} chars")
                    
                    # Set status
                    if exc_type:
                        self._span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                        self._span.record_exception(exc_val)
                    else:
                        self._span.set_status(Status(StatusCode.OK))
                
                # Exit span context (this will end the span and flush it)
                # Make sure all attributes are set before this point
                self._span_context.__exit__(exc_type, exc_val, exc_tb)
                
                # Exit original stream manager
                return self._stream_manager.__exit__(exc_type, exc_val, exc_tb)
            
            def __iter__(self):
                """Make the wrapper iterable - returns iterator over the stream."""
                # If __enter__ hasn't been called, call it now
                if not hasattr(self, '_stream'):
                    self.__enter__()
                    self._auto_exit = True
                else:
                    self._auto_exit = False
                
                return self
            
            def __next__(self):
                """Get next event from stream and track it."""
                if not hasattr(self, '_stream'):
                    raise RuntimeError("Stream not initialized. Use 'with stream:' or iterate directly.")
                
                try:
                    event = next(self._stream)
                    self._chunks.append(event)
                    
                    # Extract text content from streaming events
                    # This accumulates the full response text
                    if hasattr(event, "type") and event.type == "content_block_delta":
                        if hasattr(event, "delta") and hasattr(event.delta, "text"):
                            self._text_content += event.delta.text
                    
                    return event
                except StopIteration:
                    # Stream ended - clean up if we auto-entered
                    # This ensures __exit__ is called to set final attributes
                    if hasattr(self, '_auto_exit') and self._auto_exit:
                        self.__exit__(None, None, None)
                    raise
            
            def get_final_message(self):
                """Get the final message from the underlying stream and update span with accurate data."""
                if not hasattr(self, '_stream'):
                    raise RuntimeError("Stream not initialized. Use 'with stream:' first.")
                
                # Delegate to the underlying stream's get_final_message
                # The _stream is the actual MessageStream object returned from stream_manager.__enter__()
                if hasattr(self._stream, 'get_final_message'):
                    self._final_message = self._stream.get_final_message()
                    
                    # Update span with accurate token counts and full completion text if span is still active
                    if self._span and self._final_message:
                        try:
                            # Get accurate token counts
                            if hasattr(self._final_message, "usage"):
                                usage = self._final_message.usage
                                input_tokens = getattr(usage, "input_tokens", 0)
                                output_tokens = getattr(usage, "output_tokens", 0)
                                total_tokens = input_tokens + output_tokens
                                
                                self._span.set_attribute("llm.input_tokens", input_tokens)
                                self._span.set_attribute("llm.output_tokens", output_tokens)
                                self._span.set_attribute("llm.total_tokens", total_tokens)
                            
                            # Get full completion text from final message
                            if hasattr(self._final_message, "content"):
                                final_text_parts = []
                                for block in self._final_message.content:
                                    if hasattr(block, "type") and block.type == "text":
                                        if hasattr(block, "text"):
                                            final_text_parts.append(block.text)
                                if final_text_parts:
                                    full_completion = "\n".join(final_text_parts)
                                    self._span.set_attribute("llm.completion", full_completion)
                                    
                                    # Extract reasoning from completion text
                                    from cascade.celestra_extensions import _extract_reasoning
                                    reasoning_text = _extract_reasoning(full_completion)
                                    if reasoning_text:
                                        self._span.set_attribute("llm.reasoning", reasoning_text)
                                        logger.debug(f"Extracted reasoning from final message: {len(reasoning_text)} chars")
                        except Exception as e:
                            logger.debug(f"Could not update span from final message: {e}")
                    
                    return self._final_message
                else:
                    raise AttributeError(
                        f"get_final_message not available on stream type {type(self._stream)}. "
                        "Make sure you're using Anthropic SDK version that supports get_final_message()."
                    )
        
        return _StreamWrapper(stream_manager, self._tracer, model, message_data, start_time)


class _AnthropicWrapper:
    """Wrapper for Anthropic client to track LLM calls."""
    
    def __init__(self, client, tracer: Optional[trace.Tracer]):
        self._client = client
        self._tracer = tracer
        # Preserve all original attributes
        for attr in dir(client):
            if not attr.startswith("_") and attr != "messages":
                try:
                    setattr(self, attr, getattr(client, attr))
                except:
                    pass
    
    @property
    def messages(self):
        """Return wrapped messages API."""
        return _AnthropicMessagesWrapper(self._client.messages, self._tracer)
    
    def __getattr__(self, name):
        """Delegate any other attribute access to original client."""
        return getattr(self._client, name)


def wrap_llm_client(client: Any) -> Any:
    """
    Wrap an LLM client to automatically track all LLM calls.
    
    Currently supports:
    - Anthropic client (sync)
    
    Args:
        client: The LLM client instance to wrap
        
    Returns:
        Wrapped client that behaves identically but creates spans for LLM calls
        
    Example:
        ```python
        from anthropic import Anthropic
        from cascade.llm_wrappers import wrap_llm_client
        
        client = wrap_llm_client(Anthropic(api_key="..."))
        response = client.messages.create(...)  # Automatically traced!
        ```
    """
    tracer = get_tracer()
    
    # Detect client type
    client_type = type(client).__name__
    client_module = type(client).__module__
    
    # Check if it's an Anthropic client
    # Anthropic client class is typically "Anthropic" from "anthropic" module
    if "anthropic" in client_module.lower() or "Anthropic" in client_type:
        return _AnthropicWrapper(client, tracer)
    
    # Also check by checking if it has the messages attribute with create/stream methods
    # This is a more robust check
    if hasattr(client, "messages"):
        messages_obj = getattr(client, "messages")
        if hasattr(messages_obj, "create") and hasattr(messages_obj, "stream"):
            # Likely an Anthropic-style client
            return _AnthropicWrapper(client, tracer)
    
    # If we don't recognize the client, return as-is with a warning
    logger.warning(
        f"Unknown LLM client type: {client_module}.{client_type}. "
        "Returning unwrapped client. LLM calls will not be traced."
    )
    return client
