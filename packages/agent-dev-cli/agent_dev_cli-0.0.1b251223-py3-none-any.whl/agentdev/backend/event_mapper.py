import time
from typing import Callable, Type, Any
from functools import wraps
import uuid
from datetime import datetime
import sys
import logging

from agent_framework import WorkflowEvent, WorkflowStartedEvent, WorkflowFailedEvent, WorkflowStatusEvent, WorkflowRunState, ExecutorEvent, AgentRunUpdateEvent, ExecutorInvokedEvent, ExecutorCompletedEvent, AgentRunResponseUpdate, FunctionCallContent, FunctionResultContent, TextContent

from ._utils import serialize_data
from .structs.request import AgentFrameworkRequest


# Access or store common data across different events
class MapperContext:
    # Input
    request: AgentFrameworkRequest

    # Generated
    # global
    response_id: str | None
    response_created_at: float | None

    # The last seen item id
    item_id: str | None = None
    output_index: int = 0

    # The last seen call_id for function calling
    call_id: str | None = None


def event_mapper(event_type: Type[Any]) -> Callable:
    """Decorator to register an event mapper method for a specific event type.
    
    Args:
        event_type: The event type class this mapper handles
        
    Returns:
        Decorator function that registers the mapper
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self: 'EventMapper', ctx: MapperContext, event: Any) -> list[dict]:
            return func(self, ctx, event)
        
        # Store event type on the wrapper for registration
        wrapper._event_type = event_type  # type: ignore
        return wrapper
    
    return decorator

class EventMapper():
    
    def __init__(self):
        """Initialize the EventMapper and register all decorated mapper methods."""
        self._event_mappers = {}
        
        # Scan all methods for event_mapper decorators and register them
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if callable(attr) and hasattr(attr, '_event_type'):
                event_type = attr._event_type
                self._event_mappers[event_type] = attr
    
    def _get_event_mapper(self, event_type: Type[Any]) -> Callable | None:
        # Direct lookup for exact type match
        if event_type in self._event_mappers:
            return self._event_mappers[event_type]
        
        for registered_type, mapper in self._event_mappers.items():
            try:
                if isinstance(event_type, type) and issubclass(event_type, registered_type):
                    return mapper
            except TypeError:
                # Not a class type, skip
                pass
        
        return None
    
    @event_mapper(WorkflowEvent)
    def _map_workflow_event(self, ctx: MapperContext, event: WorkflowEvent) -> list[dict]:
        if isinstance(event, WorkflowStartedEvent):
            ctx.response_id = str(uuid.uuid4())
            ctx.response_created_at = time.time()
        
        event_type = None
        if isinstance(event, WorkflowStartedEvent):
            event_type = "response.created"
        elif isinstance(event, WorkflowFailedEvent):
            return [{
                "type": "response.failed",
                "response":{
                    "id": ctx.response_id,
                    "created_at": ctx.response_created_at,
                    "model": ctx.request.model,
                    "error": {
                        "code": event.details.error_type,
                        "message": event.details.message,
                        "traceback": event.details.traceback,
                    },
                },
            }]
        elif isinstance(event, WorkflowStatusEvent):
            if event.state == WorkflowRunState.IN_PROGRESS:
                event_type = "response.in_progress"

        if event_type:
            return [{
                "type": event_type,
                "response":{
                    "id": ctx.response_id,
                    "created_at": ctx.response_created_at,
                    "model": ctx.request.model,
                },
            }]
        
        return []
    
    @event_mapper(AgentRunUpdateEvent)
    def _map_agent_run_update_event(self, ctx: MapperContext, event: AgentRunUpdateEvent) -> list[dict]:
        return [
            {
                "type":"response.output_text.delta",
                "content_index":0,
                "delta": event.data.text,
                "item_id": ctx.item_id + "_message",
                "logprobs":[],
                "output_index":ctx.output_index,
            }
        ]

    @event_mapper(ExecutorEvent)
    def _map_executor_event(self, ctx: MapperContext, event: ExecutorEvent) -> list[dict]:
        event_type = None
        status = None
        if isinstance(event, ExecutorInvokedEvent):
            ctx.item_id = f"exec_{event.executor_id}_{str(uuid.uuid4())[:8]}"
            ctx.output_index += 1
            event_type = "response.output_item.added"
            status = "in_progress"
        elif isinstance(event, ExecutorCompletedEvent):
            event_type = "response.output_item.done"
            status = "completed"
        else:
            return []

        events = []
        if event_type:
            # Serialize event data for frontend display
            serialized_data = None
            if event.data is not None:
                try:
                    serialized_data = serialize_data(event.data)
                    logging.debug(f"[Executor] {event.executor_id} serialized data: {serialized_data}")
                except Exception as e:
                    logging.warning(f"Failed to serialize event data: {e}")
                    serialized_data = str(event.data)
            
            # Build executor item with input/output data based on event type
            executor_item: dict[str, Any] = {
                "type": "executor_action",
                "id": ctx.item_id,
                "executor_id": event.executor_id,
                "status": status,
            }
            
            # For ExecutorInvokedEvent, include input data
            if isinstance(event, ExecutorInvokedEvent):
                executor_item["input"] = serialized_data
            # For ExecutorCompletedEvent, include output data  
            elif isinstance(event, ExecutorCompletedEvent):
                executor_item["output"] = serialized_data
            
            events.append(
                # Agent framework extended executor item
                {
                    "type": event_type,
                    "output_index": ctx.output_index,
                    "item": executor_item,
                }
            )
            events.append(
                # Standard OpenAI message item
                {
                    "type": event_type,
                    "output_index": ctx.output_index,
                    "item": {
                        "type": "message",
                        "id": ctx.item_id + "_message",
                        "status": status,
                        "role": "assistant",
                        "content": [],
                    }
                }
            )
        
        # OpenAI standard content part added event
        if isinstance(event, ExecutorInvokedEvent):
            events.append({
                "type": "response.content_part.added",
                "output_index": ctx.output_index,
                "item_id": ctx.item_id + "_message",
                "content_index": 0,
                "part":{
                    "text":"",
                    "type":"output_text"
                }
            })
        return events

    @event_mapper(AgentRunResponseUpdate)
    def _map_agent_run_response_update(self, ctx: MapperContext, event: AgentRunResponseUpdate) -> list[dict]:
        item_id = event.message_id
        results = []
        if item_id and item_id != ctx.item_id:
            ctx.item_id = item_id
            ctx.output_index += 1
            results.append({
                "type":"response.output_item.added",           
                "output_index": ctx.output_index,
                "item":{
                    "type":"message",       
                    "id":"msg_a6a8c564",
                    "content":[],
                    "role":"assistant",
                    "status":"in_progress"
                },
            })
            results.append({
                "type":"response.content_part.added",
                "output_index": ctx.output_index,
                "content_index": 0,
                "item_id": ctx.item_id,
                "part": {
                    "type":"output_text",
                    "text":"",
                }
            })
        
        for content in event.contents:
            if isinstance(content, FunctionCallContent):
                # Arguments are always streamed in OpenAI. But not always in Agent Framework.
                # Argument streaming use last call_id to track the function call instance.
                if ctx.call_id and content.arguments:
                    results.append({
                        "type": "response.function_call_arguments.delta",
                        "output_index": ctx.output_index,
                        # DevUI set OpenAI's item_id to the value of Agent Framework's call_id, which might be a bug
                        "item_id": ctx.call_id,
                        "delta": content.arguments,
                    })
                else:
                    if content.call_id != ctx.call_id:
                        ctx.call_id = content.call_id
                        ctx.output_index += 1
                    results.append({
                        "type":"response.output_item.added",           
                        "output_index": ctx.output_index,
                        "item":{
                            "type":"function_call",     
                            "arguments":"",
                            "call_id": ctx.call_id,
                            "name": content.name,
                            "id": content.call_id,
                            "status":"in_progress",
                        },
                    })
            elif isinstance(content, FunctionResultContent):
                results.append({
                    "type":"response.function_result.complete",           
                    "call_id": content.call_id,
                    "output_index": ctx.output_index,
                    "output":content.result,
                    "status":"completed",
                    "item_id": ctx.item_id,
                    "timestamp":datetime.now().isoformat(),
                })

            elif isinstance(content, TextContent):
                results.append(
                    {
                        "type":"response.output_text.delta",
                        "content_index":0,
                        "delta": content.text,
                        "item_id": ctx.item_id,
                        "output_index": ctx.output_index,
                    }
                )
            else:
                print("Unknown content: " + str(type(content)), file=sys.stderr)
        return results

    def map_event(self, ctx: MapperContext, event: Any) -> list[dict]:
        """Map an Agent Framework event to OpenAI Responses API events"""
        mapper = self._get_event_mapper(type(event))
        if not mapper:
            print("Unknown event: " + type(event))
            return []
        
        return mapper(ctx, event)
    