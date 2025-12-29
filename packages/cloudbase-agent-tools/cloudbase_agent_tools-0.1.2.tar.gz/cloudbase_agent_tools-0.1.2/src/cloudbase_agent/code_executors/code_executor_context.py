#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Code executor context management.

This module provides context management for code execution sessions,
allowing for persistent state across multiple code executions.
"""

from typing import Any, Dict, Optional

try:
    from e2b_code_interpreter import CodeContext, Sandbox
except ImportError:
    Sandbox = None
    CodeContext = None


class CodeExecutorContext:
    """Code executor context manager.

    This class manages the execution context for code execution sessions,
    providing persistent state and session management.

    :param sandbox: E2B sandbox instance
    :type sandbox: Sandbox
    :param context_options: Context creation options
    :type context_options: Dict[str, Any]
    :param session_state: Session state data
    :type session_state: Optional[Dict[str, Any]]
    """

    def __init__(
        self,
        sandbox: "Sandbox",
        context_options: Optional[Dict[str, Any]] = None,
        session_state: Optional[Dict[str, Any]] = None,
    ):
        """Initialize code executor context.

        :param sandbox: E2B sandbox instance
        :type sandbox: Sandbox
        :param context_options: Context creation options
        :type context_options: Optional[Dict[str, Any]]
        :param session_state: Session state data
        :type session_state: Optional[Dict[str, Any]]
        """
        if Sandbox is None or CodeContext is None:
            raise ImportError(
                "e2b_code_interpreter is required for CodeExecutorContext. "
                "Install it with: pip install e2b-code-interpreter"
            )

        self.sandbox = sandbox
        self.context_options = context_options or {}
        self.session_state = session_state or {}
        self._context: Optional[CodeContext] = None
        self._create_context_future: Optional[Any] = None

    async def _ensure_context(self) -> "CodeContext":
        """Ensure context is initialized.

        :return: The code context
        :rtype: CodeContext
        """
        if self._context is None:
            if self._create_context_future is None:
                try:
                    self._create_context_future = True
                    self._context = self.sandbox.create_code_context(**self.context_options)
                except Exception:
                    self._create_context_future = None
                    raise

        return self._context

    async def get_execution_id(self) -> str:
        """Get the execution context ID.

        :return: Context execution ID
        :rtype: str
        """
        context = await self._ensure_context()
        return context.id if hasattr(context, "id") else ""

    def get_context(self) -> Optional["CodeContext"]:
        """Get the current context.

        :return: Current code context
        :rtype: Optional[CodeContext]
        """
        return self._context

    def reset_context(self):
        """Reset the execution context."""
        self._context = None
        self._create_context_future = None

    def update_session_state(self, state: Dict[str, Any]):
        """Update session state.

        :param state: State data to update
        :type state: Dict[str, Any]
        """
        self.session_state.update(state)

    def get_session_state(self) -> Dict[str, Any]:
        """Get session state.

        :return: Current session state
        :rtype: Dict[str, Any]
        """
        return self.session_state.copy()

    def clear_session_state(self):
        """Clear session state."""
        self.session_state.clear()
