"""
Workflow visualization setup module.

This module provides functionality to set up workflow or agent visualization
"""

from agent_framework import WorkflowAgent
import os
import sys
import time


def setup_test_tool(agent_server):
    """
    Set up workflow or agent visualization for an agent server.
    
    This function configures a health check endpoint and starts a visualization
    server for workflow agents on port 8090.
    
    Args:
        agent_server: The agent server instance to set up visualization for.
                     Should have 'app' (Starlette) and 'agent' attributes.
    
    Example:
        >>> from azure.ai.agentserver.agentframework import from_agent_framework
        >>> agent_server = from_agent_framework(agent)
        >>> setup_test_tool(agent_server)
        >>> await agent_server.run_async()
    """
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route
    from threading import Thread
    from agentdev.backend.server import TestToolServer
    
    async def health_check(request):
        """Health check endpoint handler."""
        return JSONResponse({"status": "ok"}, status_code=200)
    
    app = agent_server.app
    agent = agent_server.agent

    # Mount health check endpoint
    app.mount(
        "/agentdev/health",
        Starlette(routes=[Route("/", health_check)])
    )

    # Prepare entities for visualization
    entities = []
    if type(agent) == WorkflowAgent:
        entities.append(agent.workflow)
    else:
        entities.append(agent)

    test_tool_server = TestToolServer(entities)
    test_tool_server.mount_backend(app)
    def show_endspattern():
        time.sleep(2)
        print("agentdev: Application startup complete")
    thread = Thread(target=show_endspattern)
    thread.daemon = True
    thread.start()
    
    print(agent)
