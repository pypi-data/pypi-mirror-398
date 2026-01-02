"""
Logs Namespace - Herald structured logging operations.

Provides zero-friction logging to BetterStack via Herald service.
SDK automatically captures callsite (file, function) - users just call:
    await dominus.logs.info("message", {"key": "value"})
"""
import inspect
import json
import sys
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..start import Dominus


class LogsNamespace:
    """
    Logging namespace for Herald service.

    All methods automatically capture callsite information (file, function)
    and send to the Herald backend at /api/herald/*.

    Log levels: debug, info, notice, warn, error, critical

    Usage:
        # Basic logging
        await dominus.logs.info("User logged in", {"user_id": "123"})
        await dominus.logs.error("Payment failed", {"order_id": "456"})

        # With category
        await dominus.logs.info("Cache hit", {"key": "user:123"}, category="cache")

        # With exception
        try:
            do_something()
        except Exception as e:
            await dominus.logs.error("Operation failed", exception=e)

        # Query logs (admin or scoped to your project)
        logs = await dominus.logs.query(level="error", limit=50)
    """

    def __init__(self, client: "Dominus"):
        self._client = client

    def _capture_callsite(self, depth: int = 3) -> Tuple[Optional[str], Optional[str]]:
        """Capture file and function from call stack.

        Args:
            depth: Stack frame depth to inspect (default: 3)

        Returns:
            Tuple of (filepath, function_name)
        """
        frame = inspect.currentframe()
        try:
            for _ in range(depth):
                if frame is not None:
                    frame = frame.f_back
            if frame is None:
                return None, None

            filepath = frame.f_code.co_filename
            function = frame.f_code.co_name

            # Normalize filepath - strip common prefixes
            for prefix in ['/app/', '/home/', 'C:\\', '/Users/']:
                if filepath.startswith(prefix):
                    filepath = filepath[len(prefix):]
                    break

            # Also strip any remaining absolute path prefix
            if '/' in filepath:
                # Keep last 3 path components max
                parts = filepath.split('/')
                if len(parts) > 3:
                    filepath = '/'.join(parts[-3:])
            elif '\\' in filepath:
                parts = filepath.split('\\')
                if len(parts) > 3:
                    filepath = '/'.join(parts[-3:])

            return filepath, function
        finally:
            del frame

    def _fallback_log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Print to stderr as fallback when backend unavailable."""
        try:
            from datetime import datetime, timezone
            entry = {
                "dt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "level": level.upper(),
                "message": message,
                "_fallback": True
            }
            if context:
                entry["context"] = context
            print(json.dumps(entry, separators=(",", ":")), file=sys.stderr)
        except Exception:
            pass

    async def _log(
        self,
        level: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> bool:
        """Internal log method with callsite capture.

        Args:
            level: Log level
            message: Log message
            context: Optional context dict
            category: Optional category (default: "general")
            exception: Optional exception to include

        Returns:
            True if successfully sent, False otherwise
        """
        file, function = self._capture_callsite(depth=3)

        body: Dict[str, Any] = {
            "level": level,
            "message": message,
        }
        if context:
            body["context"] = context
        if category:
            body["category"] = category
        if file:
            body["file"] = file
        if function:
            body["function"] = function
        if exception:
            body["context"] = body.get("context", {})
            body["context"]["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }

        try:
            result = await self._client._request(
                endpoint="/api/herald/log",
                body=body
            )
            return result.get("stored", False)
        except Exception:
            # Never raise - fallback to local
            self._fallback_log(level, message, context)
            return False

    async def debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> bool:
        """Log debug message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("debug", message, context, category)

    async def info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> bool:
        """Log info message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("info", message, context, category)

    async def notice(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> bool:
        """Log notice message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("notice", message, context, category)

    async def warn(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> bool:
        """Log warning message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("warn", message, context, category)

    async def error(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> bool:
        """Log error message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")
            exception: Optional exception to include

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("error", message, context, category, exception)

    async def critical(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None,
        exception: Optional[Exception] = None
    ) -> bool:
        """Log critical message.

        Args:
            message: Log message
            context: Optional structured context
            category: Optional category (default: "general")
            exception: Optional exception to include

        Returns:
            True if successfully sent to Herald
        """
        return await self._log("critical", message, context, category, exception)

    async def query(
        self,
        level: Optional[str] = None,
        category: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        file: Optional[str] = None,
        function: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        # Admin only:
        project: Optional[str] = None,
        environment: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query logs from Herald.

        Args:
            level: Filter by log level
            category: Filter by category
            start_time: Start of time range (ISO 8601)
            end_time: End of time range (ISO 8601)
            file: Filter by file (partial match)
            function: Filter by function (partial match)
            search: Message text search
            limit: Maximum results (1-1000, default: 100)
            project: Admin only - query specific project
            environment: Admin only - query specific environment

        Returns:
            List of log entries
        """
        body: Dict[str, Any] = {"limit": limit}
        if level:
            body["level"] = level
        if category:
            body["category"] = category
        if start_time:
            body["start_time"] = start_time
        if end_time:
            body["end_time"] = end_time
        if file:
            body["file"] = file
        if function:
            body["function"] = function
        if search:
            body["search"] = search
        if project:
            body["project"] = project
        if environment:
            body["environment"] = environment

        try:
            result = await self._client._request(
                endpoint="/api/herald/query",
                body=body
            )
            return result.get("logs", [])
        except Exception:
            return []

    async def batch(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send multiple log events in one request.

        Args:
            events: List of log event dicts, each with:
                - level (required): debug, info, notice, warn, error, critical
                - message (required): Log message
                - context (optional): Structured context
                - category (optional): Log category

        Returns:
            Dict with total, stored, failed counts
        """
        try:
            result = await self._client._request(
                endpoint="/api/herald/batch",
                body={"events": events[:100]}
            )
            return result
        except Exception:
            # Fallback - log each locally
            for event in events:
                self._fallback_log(
                    event.get("level", "info"),
                    event.get("message", ""),
                    event.get("context")
                )
            return {
                "total": len(events),
                "stored": 0,
                "failed": len(events)
            }
