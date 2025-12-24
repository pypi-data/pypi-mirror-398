"""
AgentApps - A flexible multi-agent orchestration framework
Package structure for pip installation (Phi-inspired design)
"""

# ============================================================================
# File: agentapps/__init__.py
# ============================================================================

"""
AgentApps - Multi-Agent Orchestration Framework

A Python package for building intelligent agent systems with role-based
collaboration, tools integration, and LLM support.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

from .agent import Agent
from .model import OpenAIChat, GeminiChat, GrokChat, Model
from .tools import Tool, WebSearchTool, WebScraperTool, SearchSummaryTool, CalculatorTool

__all__ = [
    "Agent",
    "OpenAIChat",
    "GeminiChat",
    "GrokChat",
    "Model",
    "Tool",
    "WebSearchTool",
    "WebScraperTool", 
    "SearchSummaryTool",
    "CalculatorTool",
]