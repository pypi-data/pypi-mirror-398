#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unsafe local code executor implementation.

This module provides a code executor that runs code directly on the local
system. WARNING: This executor is unsafe and should only be used in trusted
environments as it can execute arbitrary code.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .._tools_utils import ToolExecutionContext
from .base_code_executor import BaseCodeExecutor, CodeExecutorInput


@dataclass
class ExecutionError:
    """Execution error information.

    :param name: Name of the error
    :type name: str
    :param value: Value/message of the error
    :type value: str
    :param traceback: Error traceback
    :type traceback: str
    """

    name: str
    value: str
    traceback: str


@dataclass
class Logs:
    """Execution logs.

    :param stdout: Standard output lines
    :type stdout: List[str]
    :param stderr: Standard error lines
    :type stderr: List[str]
    """

    stdout: List[str] = field(default_factory=list)
    stderr: List[str] = field(default_factory=list)


@dataclass
class Result:
    """Execution result data.

    :param is_main_result: Whether this is the main result
    :type is_main_result: bool
    :param text: Text representation
    :type text: Optional[str]
    :param html: HTML representation
    :type html: Optional[str]
    :param markdown: Markdown representation
    :type markdown: Optional[str]
    :param json_data: JSON data
    :type json_data: Optional[str]
    :param data: Structured data
    :type data: Optional[Dict[str, Any]]
    :param raw: Raw data
    :type raw: Dict[str, Any]
    """

    is_main_result: bool
    text: Optional[str] = None
    html: Optional[str] = None
    markdown: Optional[str] = None
    json_data: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    raw: Dict[str, Any] = field(default_factory=dict)

    def formats(self) -> List[str]:
        """Get available formats.

        :return: List of available format names
        :rtype: List[str]
        """
        formats = []
        if self.text:
            formats.append("text")
        if self.html:
            formats.append("html")
        if self.markdown:
            formats.append("markdown")
        if self.json_data:
            formats.append("json")
        if self.data:
            formats.append("data")
        return formats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        :return: Dictionary representation
        :rtype: Dict[str, Any]
        """
        return {
            "text": self.text,
            "html": self.html,
            "markdown": self.markdown,
            "json": self.json_data,
            "data": self.data,
        }


@dataclass
class Execution:
    """Code execution result.

    :param results: List of results
    :type results: List[Result]
    :param logs: Execution logs
    :type logs: Logs
    :param error: Execution error if any
    :type error: Optional[ExecutionError]
    :param execution_count: Execution count
    :type execution_count: Optional[int]
    """

    results: List[Result] = field(default_factory=list)
    logs: Logs = field(default_factory=Logs)
    error: Optional[ExecutionError] = None
    execution_count: Optional[int] = None

    @property
    def text(self) -> Optional[str]:
        """Get main result text.

        :return: Main result text
        :rtype: Optional[str]
        """
        for result in self.results:
            if result.is_main_result:
                return result.text
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        :return: Dictionary representation
        :rtype: Dict[str, Any]
        """
        return {
            "results": [r.to_dict() for r in self.results],
            "logs": {
                "stdout": self.logs.stdout,
                "stderr": self.logs.stderr,
            },
            "error": {
                "name": self.error.name,
                "value": self.error.value,
                "traceback": self.error.traceback,
            }
            if self.error
            else None,
        }


class CodeExecutor:
    """Local code executor engine."""

    def __init__(self):
        """Initialize code executor."""
        self.execution_count = 0

    async def run_code(
        self,
        language: str,
        code: str,
        timeout_ms: Optional[int] = None,
        envs: Optional[Dict[str, str]] = None,
        on_stdout: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_stderr: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Execution:
        """Run code in specified language.

        :param language: Programming language
        :type language: str
        :param code: Code to execute
        :type code: str
        :param timeout_ms: Timeout in milliseconds
        :type timeout_ms: Optional[int]
        :param envs: Environment variables
        :type envs: Optional[Dict[str, str]]
        :param on_stdout: Callback for stdout
        :type on_stdout: Optional[Callable]
        :param on_stderr: Callback for stderr
        :type on_stderr: Optional[Callable]
        :return: Execution result
        :rtype: Execution
        """
        self.execution_count += 1

        logs = Logs()
        results = []
        error = None

        try:
            config = self._get_language_config(language, code)
            if not config:
                error = ExecutionError(
                    name="UnsupportedLanguage",
                    value=f"Language '{language}' is not supported",
                    traceback="",
                )
                return Execution(
                    results=results,
                    logs=logs,
                    error=error,
                    execution_count=self.execution_count,
                )

            exec_result = await self._execute_code(
                config,
                timeout_ms=timeout_ms,
                envs=envs,
                on_stdout=lambda data: self._handle_stdout(data, logs, on_stdout),
                on_stderr=lambda data: self._handle_stderr(data, logs, on_stderr),
            )

            if exec_result["success"]:
                parsed_results = self._parse_results(
                    exec_result["stdout"],
                    language,
                    code,
                )
                results.extend(parsed_results)
            else:
                stderr = exec_result["stderr"] or f"Process exited with code {exec_result['exit_code']}"
                error = ExecutionError(
                    name="ExecutionError",
                    value=stderr,
                    traceback="\n".join(self._parse_traceback(stderr, language)),
                )
        except Exception as e:
            error = ExecutionError(
                name="SystemError",
                value=str(e),
                traceback=str(e),
            )

        return Execution(
            results=results,
            logs=logs,
            error=error,
            execution_count=self.execution_count,
        )

    def _get_language_config(self, language: str, code: str) -> Optional[Dict[str, Any]]:
        """Get language configuration.

        :param language: Programming language
        :type language: str
        :param code: Code to execute
        :type code: str
        :return: Language configuration
        :rtype: Optional[Dict[str, Any]]
        """
        configs = {
            "python": {"cmd": "python3", "args": ["-c", code]},
            "python3": {"cmd": "python3", "args": ["-c", code]},
            "js": {"cmd": "node", "args": ["-p", "-e", code]},
            "node": {"cmd": "node", "args": ["-p", "-e", code]},
            "bash": {"cmd": "bash", "args": ["-c", code]},
        }
        return configs.get(language)

    async def _execute_code(
        self,
        config: Dict[str, Any],
        timeout_ms: Optional[int] = None,
        envs: Optional[Dict[str, str]] = None,
        on_stdout: Optional[Callable] = None,
        on_stderr: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """Execute code using subprocess.

        :param config: Language configuration
        :type config: Dict[str, Any]
        :param timeout_ms: Timeout in milliseconds
        :type timeout_ms: Optional[int]
        :param envs: Environment variables
        :type envs: Optional[Dict[str, str]]
        :param on_stdout: Callback for stdout
        :type on_stdout: Optional[Callable]
        :param on_stderr: Callback for stderr
        :type on_stderr: Optional[Callable]
        :return: Execution result
        :rtype: Dict[str, Any]
        """
        import os

        env = os.environ.copy()
        if envs:
            env.update(envs)

        timeout = (timeout_ms / 1000) if timeout_ms else 30.0

        try:
            process = await asyncio.create_subprocess_exec(
                config["cmd"],
                *config["args"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout_data = []
            stderr_data = []

            async def read_stdout():
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    text = line.decode("utf-8")
                    stdout_data.append(text)
                    if on_stdout:
                        on_stdout(
                            {
                                "error": False,
                                "line": text,
                                "timestamp": int(time.time() * 1e6),
                            }
                        )

            async def read_stderr():
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    text = line.decode("utf-8")
                    stderr_data.append(text)
                    if on_stderr:
                        on_stderr(
                            {
                                "error": True,
                                "line": text,
                                "timestamp": int(time.time() * 1e6),
                            }
                        )

            # Read stdout and stderr concurrently
            await asyncio.gather(read_stdout(), read_stderr())

            # Wait for process with timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "".join(stdout_data).strip(),
                    "stderr": "Execution timeout exceeded",
                }

            return {
                "success": process.returncode == 0,
                "exit_code": process.returncode,
                "stdout": "".join(stdout_data).strip(),
                "stderr": "".join(stderr_data).strip(),
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": None,
                "stdout": "",
                "stderr": str(e),
            }

    def _handle_stdout(
        self,
        data: Dict[str, Any],
        logs: Logs,
        callback: Optional[Callable],
    ):
        """Handle stdout data.

        :param data: Stdout data
        :type data: Dict[str, Any]
        :param logs: Logs object
        :type logs: Logs
        :param callback: Optional callback
        :type callback: Optional[Callable]
        """
        logs.stdout.append(data["line"])
        if callback:
            callback(data)

    def _handle_stderr(
        self,
        data: Dict[str, Any],
        logs: Logs,
        callback: Optional[Callable],
    ):
        """Handle stderr data.

        :param data: Stderr data
        :type data: Dict[str, Any]
        :param logs: Logs object
        :type logs: Logs
        :param callback: Optional callback
        :type callback: Optional[Callable]
        """
        logs.stderr.append(data["line"])
        if callback:
            callback(data)

    def _parse_results(
        self,
        stdout: str,
        language: str,
        code: Optional[str] = None,
    ) -> List[Result]:
        """Parse execution results.

        :param stdout: Standard output
        :type stdout: str
        :param language: Programming language
        :type language: str
        :param code: Original code
        :type code: Optional[str]
        :return: Parsed results
        :rtype: List[Result]
        """
        results = []

        if not stdout.strip():
            return results

        if language in ("python", "python3"):
            results.extend(self._parse_python_results(stdout))
        elif language in ("js", "node"):
            results.extend(self._parse_javascript_results(stdout, code))
        else:
            # Other languages: treat entire output as text
            results.append(
                Result(
                    is_main_result=True,
                    text=stdout,
                    data={"content": stdout, "type": "text"},
                )
            )

        return results

    def _parse_python_results(self, stdout: str) -> List[Result]:
        """Parse Python execution results.

        :param stdout: Standard output
        :type stdout: str
        :return: Parsed results
        :rtype: List[Result]
        """
        results = []
        lines = stdout.strip().split("\n")

        for line in lines:
            line = line.strip()

            if not line or line.startswith(">>>") or line.startswith("..."):
                continue

            # Try JSON parsing
            if self._is_json_line(line):
                try:
                    json_data = json.loads(line)
                    results.append(
                        Result(
                            is_main_result=len(results) == 0,
                            text=line,
                            json_data=line,
                            data={
                                "result": json_data,
                                "type": "json",
                            },
                        )
                    )
                    continue
                except json.JSONDecodeError:
                    pass

            # Try number parsing
            if self._is_number(line):
                results.append(
                    Result(
                        is_main_result=len(results) == 0,
                        text=line,
                        data={
                            "value": float(line),
                            "type": "number",
                        },
                    )
                )
                continue

            # Regular text
            results.append(
                Result(
                    is_main_result=len(results) == 0,
                    text=line,
                    data={"content": line, "type": "text"},
                )
            )

        if not results and stdout.strip():
            results.append(
                Result(
                    is_main_result=True,
                    text=stdout,
                    data={"content": stdout, "type": "text"},
                )
            )

        return results

    def _parse_javascript_results(
        self,
        stdout: str,
        code: Optional[str] = None,
    ) -> List[Result]:
        """Parse JavaScript execution results.

        :param stdout: Standard output
        :type stdout: str
        :param code: Original code
        :type code: Optional[str]
        :return: Parsed results
        :rtype: List[Result]
        """
        # Check if it's a simple assignment (no output expected)
        if code and re.match(r"^\s*[a-zA-Z_$][\w$]*\s*=\s*[^=].*;?\s*$", code):
            return []

        results = []
        lines = stdout.strip().split("\n")

        for line in lines:
            if not line.strip() or line.strip() == "undefined":
                continue

            results.append(
                Result(
                    is_main_result=len(results) == 0,
                    text=line,
                    data={"content": line, "type": "text"},
                )
            )

        if not results and stdout.strip() and stdout.strip() != "undefined":
            results.append(
                Result(
                    is_main_result=True,
                    text=stdout,
                    data={"content": stdout, "type": "text"},
                )
            )

        return results

    def _is_json_line(self, line: str) -> bool:
        """Check if line is JSON.

        :param line: Line to check
        :type line: str
        :return: True if JSON
        :rtype: bool
        """
        trimmed = line.strip()
        return (trimmed.startswith("{") and trimmed.endswith("}")) or (
            trimmed.startswith("[") and trimmed.endswith("]")
        )

    def _is_number(self, line: str) -> bool:
        """Check if line is a number.

        :param line: Line to check
        :type line: str
        :return: True if number
        :rtype: bool
        """
        return bool(re.match(r"^-?\d+(\.\d+)?$", line.strip()))

    def _parse_traceback(self, stderr: str, language: str) -> List[str]:
        """Parse error traceback.

        :param stderr: Standard error
        :type stderr: str
        :param language: Programming language
        :type language: str
        :return: Traceback lines
        :rtype: List[str]
        """
        if not stderr:
            return []
        return [line for line in stderr.split("\n") if line.strip()]


class UnsafeLocalCodeExecutor(BaseCodeExecutor):
    """Unsafe local code executor.

    WARNING: This executor runs code directly on the local system and should
    only be used in trusted environments.

    :param timeout_ms: Timeout in milliseconds
    :type timeout_ms: int
    :param envs: Environment variables
    :type envs: Optional[Dict[str, str]]
    :param on_stdout: Callback for stdout
    :type on_stdout: Optional[Callable]
    :param on_stderr: Callback for stderr
    :type on_stderr: Optional[Callable]
    """

    def __init__(
        self,
        timeout_ms: int = 30000,
        envs: Optional[Dict[str, str]] = None,
        on_stdout: Optional[Callable] = None,
        on_stderr: Optional[Callable] = None,
    ):
        """Initialize unsafe local code executor.

        :param timeout_ms: Timeout in milliseconds
        :type timeout_ms: int
        :param envs: Environment variables
        :type envs: Optional[Dict[str, str]]
        :param on_stdout: Callback for stdout
        :type on_stdout: Optional[Callable]
        :param on_stderr: Callback for stderr
        :type on_stderr: Optional[Callable]
        """
        super().__init__()
        self.executor = CodeExecutor()
        self.timeout_ms = timeout_ms
        self.envs = envs
        self.on_stdout = on_stdout
        self.on_stderr = on_stderr

    async def _invoke(
        self,
        input_data: CodeExecutorInput,
        context: Optional[ToolExecutionContext] = None,
    ) -> Execution:
        """Execute code locally.

        :param input_data: Code execution input
        :type input_data: CodeExecutorInput
        :param context: Optional execution context
        :type context: Optional[ToolExecutionContext]
        :return: Execution result
        :rtype: Execution
        """
        # Parse input if it's a dict
        if isinstance(input_data, dict):
            input_data = CodeExecutorInput(**input_data)

        language = input_data.language or "python"

        result = await self.executor.run_code(
            language=language,
            code=input_data.code,
            timeout_ms=self.timeout_ms,
            envs=self.envs,
            on_stdout=self.on_stdout,
            on_stderr=self.on_stderr,
        )

        return result
