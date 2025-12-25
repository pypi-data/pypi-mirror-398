"""
TestTool server setup module.

This module provides functionality to set up test tool endpoints
for agent servers.
"""
from typing import Any, AsyncGenerator
import json
import uuid
import asyncio
import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

from agent_framework import Workflow, ChatMessage, AgentProtocol, Executor

from .event_mapper import EventMapper, MapperContext
from .structs.request import AgentFrameworkRequest
from .structs.entity_response import EntityResponse
from ._conversations import ConversationStore, InMemoryConversationStore
from .code_analyzer import get_executor_location
from .errors import ExecutorInputNotSupported

class TestToolServer:
    """Server class for mounting test tool endpoints."""
    _entities: list[Workflow | AgentProtocol]
    _events_mapper: EventMapper
    _conversation_store: ConversationStore
    _connection_id: str
    
    def __init__(self, entities: list[Workflow | AgentProtocol]):
        self._events_mapper = EventMapper()
        self._entities = entities
        self._conversation_store = InMemoryConversationStore()
        self._connection_id = str(uuid.uuid4())
    
    def convert_input_data(self, input_data: dict | list[dict], expected_type: type) -> Any:
        """
        Convert input data (always ChatMessage-like dict) to the expected input type of the entity (defined by user app)
        """
        if expected_type == list[ChatMessage]:
            if type(input_data) == list:
                chat_messages = [self.openai_chat_message_to_agent_framework_chat_message(item) for item in input_data]
                return chat_messages
            else:
                chat_message = self.openai_chat_message_to_agent_framework_chat_message(input_data)
                return [chat_message]
        elif expected_type == ChatMessage:
            chat_message = self.openai_chat_message_to_agent_framework_chat_message(input_data if type(input_data) == dict else input_data[0])
            return chat_message
        else:
            raise ExecutorInputNotSupported(f"Unsupported input type for conversion: {expected_type}")
    
    def openai_chat_message_to_agent_framework_chat_message(self, message: dict) -> ChatMessage:
        """Convert OpenAI chat message dict to Agent Framework ChatMessage."""
        role = message.get("role")
        text = message.get("text", None)
        content = message.get("content", "")
        if text:
            return ChatMessage(role=role, text=text)
        elif content:
            contents = []
            for c in content:
                if type(c) == dict:
                    if c["type"] == "input_text":
                        result_content = {
                            "type": "text",
                            "text": c["text"]
                        }
                        contents.append(result_content)
                    # TODO: support other content types like images, files, tool calls, etc.
            return ChatMessage(role=role, contents=contents)
        return ChatMessage(role=role, contents=contents, text=text)
            

    def mount_backend(self, root_app: Starlette):
        app = Starlette(routes=[
            # Responses API for workflow and agent
            Route("/v1/responses", endpoint=self.responses, methods=["POST"]),
            Route("/entities", endpoint=self.list_entities, methods=["GET"]),
            Route("/entities/{entity_id}/info", endpoint=self.get_entity_info, methods=["GET"]),
            Route("/entities/{entity_id}/executor/{executor_id}/location", endpoint=self.get_executor_location, methods=["GET"]),
            Route("/conversations", endpoint=self.list_conversations, methods=["GET"]),
            Route("/conversations", endpoint=self.create_conversation, methods=["POST"]),
            WebSocketRoute("/ws/health", endpoint=self.websocket_health),
        ])
        root_app.mount("/agentdev/", app)
    
    async def list_entities(self, raw_request: Request):
        entities_info = []
        for entity in self._entities:
            entity_info = EntityResponse.from_agent_framework(entity)
            entities_info.append(entity_info.model_dump())
        return JSONResponse({"entities": entities_info})
    
    async def get_entity_info(self, raw_request: Request):
        entity_id = raw_request.path_params["entity_id"]
        entity = self._get_entity(entity_id)
        if not entity:
            return JSONResponse({"error": "Entity not found"}, status_code=404)
        
        return JSONResponse(EntityResponse.from_agent_framework(entity).model_dump())
    
    async def get_executor_location(self, raw_request: Request):
        entity_id = raw_request.path_params["entity_id"]
        executor_id = raw_request.path_params["executor_id"]
        
        entity = self._get_entity(entity_id)
        if not entity:
            return JSONResponse({"error": "Entity not found"}, status_code=404)
        
        # Only workflows have executors
        if not isinstance(entity, Workflow):
            return JSONResponse({"error": "Entity is not a workflow"}, status_code=400)
        
        # Find the executor in the workflow
        executor = self._find_executor(entity, executor_id)
        if not executor:
            return JSONResponse({"error": "Executor not found"}, status_code=404)

        location = get_executor_location(executor)
        if location is None:
            return JSONResponse({"error": f"Could not determine executor location for {executor_id}, type={type(executor)}"}, status_code=400)
        return JSONResponse({
            "file_path": location.file_path,
            "line_number": location.line_number,
        })
    
    async def list_conversations(self, raw_request: Request):
        items = self._conversation_store.list_conversations_by_metadata(metadata_filter=raw_request.query_params)
        return JSONResponse({
            "object": "list",
            "data": items,
            # For simplicity, we do not support pagination in conversation listing for now
            "has_more": False,
        })

    async def create_conversation(self, raw_request: Request):
        request_data = await raw_request.json()
        conversation = self._conversation_store.create_conversation(metadata=request_data.get("metadata", {}))
        return JSONResponse(conversation.model_dump())

    async def responses(self, raw_request: Request):
        raw_data = await raw_request.json()
        request = AgentFrameworkRequest(**raw_data)
        
        entity = self._get_entity(request.model)
        if not entity:
            return JSONResponse({"error": "Model not found"}, status_code=404)

        return StreamingResponse(
            self._stream_execution(entity, request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    async def _stream_execution(self, entity: Workflow | AgentProtocol, request: AgentFrameworkRequest) -> AsyncGenerator[str, None]: 
        if isinstance(entity, Workflow):
            pass
        elif isinstance(entity, AgentProtocol):
            conversation_id = request.conversation["id"] if isinstance(request.conversation, dict) else request.conversation
            if not conversation_id:
                raise RuntimeError("Conversation ID must be provided for agent execution")

        # Extract input from the request
        input_raw = request.input
        if type(input_raw) != dict and type(input_raw) != list:
            raise RuntimeError("Only dict or list input type is supported in test tool server for now")

        if isinstance(entity, Workflow):
            start_executor_type = None
            for input_type in entity.get_start_executor().input_types:
                try:
                    input_data = self.convert_input_data(input_raw, input_type)
                except ExecutorInputNotSupported:
                    continue
            if input_data is None:
                raise ExecutorInputNotSupported("No supported input type found for workflow start executor, start executor input types: " + str(entity.get_start_executor().input_types))
        else:
            # TODO: fetch conversation history from conversation store by ID
            # Agents always support multiple input types including list[ChatMessage]
            input_data = self.convert_input_data(input_raw, list[ChatMessage])

        ctx = MapperContext()
        ctx.request = request
        try:
            async for agent_framework_event in entity.run_stream(input_data):
                if agent_framework_event and hasattr(agent_framework_event, "to_json"):
                    logging.debug("Emit agent framework event: ", agent_framework_event.to_json())
                else:
                    logging.debug("Emit agent framework event: ", agent_framework_event)
                openai_events = self._events_mapper.map_event(ctx, agent_framework_event)
                for openai_event in openai_events:
                    if openai_event:
                        payload = json.dumps(openai_event)
                        yield f"data: {payload}\n\n"
        finally:
            yield f"data: [DONE]\n\n"
    
    def _get_entity(self, model_name: str) -> Workflow | AgentProtocol | None:
        # Because contain agents only support a single agent / workflow for now, we can just return the first one.
        results = list(filter(lambda item: item.id == model_name, self._entities))
        if not results:
            return None
        entity = results[0]
        return entity
    
    def _find_executor(self, workflow: Workflow, executor_id: str) -> Executor | None:
        # Search for the executor with matching ID
        for name in workflow.executors:
            if name == executor_id:
                return workflow.executors[name]
        return None
    
    def _get_entity_start_executor_types(self, entity: Workflow) -> Any:
        return entity.get_start_executor().input_types[0]
    
    async def websocket_health(self, websocket: WebSocket):
        """WebSocket endpoint for health check and connection monitoring."""
        await websocket.accept()
        try:
            # Send initial connection info with unique connection ID
            await websocket.send_json({
                "type": "connected",
                "connection_id": self._connection_id,
                "timestamp": asyncio.get_event_loop().time()
            })
            
            # Keep connection alive with periodic pings
            while True:
                try:
                    # Wait for ping from client or send periodic health check
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                    if data == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "connection_id": self._connection_id,
                            "timestamp": asyncio.get_event_loop().time()
                        })
                except asyncio.TimeoutError:
                    # Send periodic health check
                    await websocket.send_json({
                        "type": "health",
                        "connection_id": self._connection_id,
                        "timestamp": asyncio.get_event_loop().time()
                    })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"WebSocket error: {e}")
            try:
                await websocket.close()
            except:
                pass