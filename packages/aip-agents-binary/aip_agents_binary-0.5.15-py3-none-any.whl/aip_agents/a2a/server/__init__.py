"""Defines an A2A server for GLLM agents.

Authors:
    Christian Trisno Sen Long Chen (christian.t.s.l.chen@gdplabs.id)
"""

from aip_agents.a2a.server.google_adk_executor import GoogleADKExecutor
from aip_agents.a2a.server.langgraph_executor import LangGraphA2AExecutor

__all__ = ["LangGraphA2AExecutor", "GoogleADKExecutor"]
