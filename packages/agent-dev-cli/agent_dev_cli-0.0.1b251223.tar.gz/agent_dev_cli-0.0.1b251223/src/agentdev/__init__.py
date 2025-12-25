"""
agentdev Package

Agent Dev CLI - A package for agent debugging and workflow visualization.

This package provides two ways to use agentdev:

1. CLI Wrapper (Recommended - No code changes required):
   
   $ agentdev run my_agent.py
   $ agentdev run workflow.py --port 9000
   
2. Programmatic API (Requires code modification):
   
   from agentdev import setup_test_tool
   setup_test_tool(agent_server)
"""

from .localdebug import setup_test_tool

__version__ = "0.0.1b251223"
__all__ = ["setup_test_tool"]
