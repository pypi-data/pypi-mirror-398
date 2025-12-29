#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tool adapters for different frameworks.

This module provides adapters to convert Cloudbase Agent tools to different
framework-specific tool formats, and vice versa.

Inspired by Google ADK's approach to tool integration, these adapters
provide seamless bidirectional conversion between Cloudbase Agent and other frameworks.
"""

from .langchain import AGKitTool, LangChainTool, from_langchain

# LlamaIndex adapter - optional import
try:
    from .llamaindex import (
        LlamaIndexTool,
        from_llamaindex,
    )

    _LLAMAINDEX_AVAILABLE = True
except ImportError:
    _LLAMAINDEX_AVAILABLE = False
    LlamaIndexTool = None
    from_llamaindex = None

__all__ = [
    # LangChain adapters
    "AGKitTool",
    "LangChainTool",
    "from_langchain",
    # LlamaIndex adapters
    "LlamaIndexTool",
    "from_llamaindex",
]
