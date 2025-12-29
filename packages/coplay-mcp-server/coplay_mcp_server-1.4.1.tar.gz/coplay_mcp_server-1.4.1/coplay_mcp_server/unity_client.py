"""Unity RPC client for file-based communication with Unity Editor."""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
import concurrent.futures

import aiofiles
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from mcp.server.fastmcp.utilities.types import Image

logger = logging.getLogger(__name__)


class UnityProjectRootError(Exception):
    """Base exception for Unity project root related errors."""
    pass


class NoUnityInstancesError(UnityProjectRootError):
    """Raised when no Unity Editor instances are found."""
    pass


class MultipleUnityInstancesError(UnityProjectRootError):
    """Raised when multiple Unity Editor instances are found and auto-detection cannot proceed."""
    
    def __init__(self, message: str, project_roots: list[str]):
        super().__init__(message)
        self.project_roots = project_roots


def discover_unity_project_roots():
    """Import and call the discover_unity_project_roots function."""
    from coplay_mcp_server.process_discovery import discover_unity_project_roots as _discover
    return _discover()


class UnityRpcClient:
    """Client for communicating with Unity Editor via file-based RPC."""

    def __init__(self) -> None:
        self._unity_project_root: Optional[str] = None
        self._pending_requests: Dict[str, concurrent.futures.Future[Any]] = {}
        self._observer: Optional[Observer] = None
        self._response_handler: Optional[ResponseFileHandler] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_unity_project_root(self, project_root: str) -> None:
        """Set the Unity project root and start watching for responses."""
        if self._unity_project_root == project_root:
            return

        # Stop existing watcher if any
        self._stop_file_watcher()

        self._unity_project_root = project_root
        self._start_file_watcher()
        logger.info(f"Unity project root set to: {project_root}")

    def auto_detect_unity_project_root(self) -> bool:
        """
        Automatically detect and set Unity project root if exactly one Unity instance is running.
        
        Returns:
            bool: True if successfully auto-detected and set, False otherwise.
        """
        try:
            project_roots = discover_unity_project_roots()
            
            if len(project_roots) == 1:
                # Exactly one Unity instance found - auto-set it
                project_root = project_roots[0]
                self.set_unity_project_root(project_root)
                logger.info(f"Auto-detected Unity project root: {project_root}")
                return True
            elif len(project_roots) == 0:
                logger.warning("No Unity instances found for auto-detection")
                return False
            else:
                logger.warning(f"Multiple Unity instances found ({len(project_roots)}), cannot auto-detect. Available projects: {project_roots}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to auto-detect Unity project root: {e}")
            return False

    def _start_file_watcher(self) -> None:
        """Start watching for response files."""
        if not self._unity_project_root:
            return

        requests_dir = (
            Path(self._unity_project_root) / "Temp" / "Coplay" / "MCPRequests"
        )
        if not requests_dir.exists():
            logger.warning(f"Unity requests directory does not exist: {requests_dir}")
            return

        # Store the current event loop for thread-safe communication
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            logger.warning(
                "No running event loop found, file watching may not work properly"
            )
            return

        self._response_handler = ResponseFileHandler(
            self._handle_response_file_sync, self._loop
        )
        self._observer = Observer()
        self._observer.schedule(
            self._response_handler, str(requests_dir), recursive=False
        )
        self._observer.start()
        logger.info(f"Started watching for responses in: {requests_dir}")

    def _stop_file_watcher(self) -> None:
        """Stop watching for response files."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
            self._response_handler = None

    def _handle_response_file_sync(self, file_path: Path) -> None:
        """Handle a response file from Unity (synchronous version for thread safety)."""
        try:
            logger.info(f"Handling file change: {file_path}")

            if not file_path.name.startswith(
                "response_"
            ) or not file_path.name.endswith(".json"):
                return

            # Read response file synchronously
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    response_json = f.read()
            except Exception as e:
                logger.error(f"Failed to read response file {file_path}: {e}")
                return

            response_data = json.loads(response_json)
            request_id = response_data.get("id")
            if request_id not in self._pending_requests:
                logger.warning(f"No pending request found for ID: {request_id}")
                return

            future = self._pending_requests.pop(request_id)

            if "error" in response_data and response_data["error"]:
                error_msg = response_data["error"]
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                future.set_exception(Exception(str(error_msg)))
            else:
                future.set_result(response_data.get("result"))

            # Clean up response file
            try:
                file_path.unlink()
                logger.debug(f"Deleted response file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete response file {file_path}: {e}")

        except Exception as e:
            logger.error(f"Error handling response file {file_path}: {e}")

    def _is_image_function(self, method: str) -> bool:
        """Check if this is a function that returns images."""
        image_functions = {
            "get_scene_view_screenshot",
            "capture_ui_canvas",
        }
        return method in image_functions

    def _process_image_response(self, response: Any) -> Any:
        """Convert ImagePath to FastMCP Image object for proper MCP compatibility."""
        if isinstance(response, dict) and "ImagePath" in response:
            image_path = response["ImagePath"]
            if image_path and isinstance(image_path, str):
                logger.debug(f"Processing image response with path: {image_path}")
                try:
                    # Create FastMCP Image object from the file path
                    return Image(path=image_path)
                except Exception as e:
                    logger.warning(
                        f"Failed to create FastMCP Image from path {image_path}: {e}"
                    )
        return response

    async def execute_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: float = 60.0,
    ) -> Any:
        """Execute an RPC request to Unity Editor."""
        if not self._unity_project_root:
            # Try to auto-detect Unity project root
            if not self.auto_detect_unity_project_root():
                # Auto-detection failed, provide helpful error message
                try:
                    project_roots = discover_unity_project_roots()
                    if len(project_roots) == 0:
                        raise NoUnityInstancesError(
                            "No Unity Editor instances found. Please start Unity Editor and call set_unity_project_root with the project path."
                        )
                    else:
                        project_list = "\n".join([f"  - {root}" for root in project_roots])
                        raise MultipleUnityInstancesError(
                            f"Multiple Unity Editor instances found. Please call set_unity_project_root with one of these project paths:\n{project_list}",
                            project_roots
                        )
                except UnityProjectRootError:
                    # Re-raise our custom exceptions as-is
                    raise
                except Exception as e:
                    raise RuntimeError(
                        "Unity project root is not set and auto-detection failed. Call set_unity_project_root first."
                    ) from e

        requests_dir = (
            Path(self._unity_project_root) / "Temp" / "Coplay" / "MCPRequests"
        )
        if not requests_dir.exists():
            raise RuntimeError(
                "Unity Editor is not running at the specified project root"
            )

        request_id = str(uuid.uuid4())
        request_file = requests_dir / f"req_{request_id}.json"

        # Create request data
        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {},
        }

        # Create concurrent.futures.Future for thread-safe completion
        future: concurrent.futures.Future[Any] = concurrent.futures.Future()
        self._pending_requests[request_id] = future

        try:
            # Write request file
            async with aiofiles.open(request_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(request_data, indent=2))

            logger.debug(f"Created request file: {request_file}")

            # Wait for response with timeout using asyncio.wrap_future
            try:
                wrapped_future = asyncio.wrap_future(future)
                result = await asyncio.wait_for(wrapped_future, timeout=timeout)

                # Post-process response for image functions
                if self._is_image_function(method):
                    result = self._process_image_response(result)

                return result
            except asyncio.TimeoutError:
                raise TimeoutError(
                    f"Request {method} timed out after {timeout} seconds"
                )

        except Exception as e:
            # Clean up on error
            self._pending_requests.pop(request_id, None)
            try:
                if request_file.exists():
                    request_file.unlink()
            except Exception:
                pass
            raise e

    def close(self) -> None:
        """Close the Unity RPC client and clean up resources."""
        self._stop_file_watcher()

        # Cancel any pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()


class ResponseFileHandler(FileSystemEventHandler):
    """File system event handler for Unity response files."""

    def __init__(
        self, callback, loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        super().__init__()
        self._callback = callback
        self._loop = loop
        self._processed_files: set[str] = set()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    def on_created(self, event) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.name.startswith("response_") and file_path.name.endswith(".json"):
            self._process_file_threadsafe(file_path)

    def on_modified(self, event) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.name.startswith("response_") and file_path.name.endswith(".json"):
            # Avoid processing the same file multiple times
            if str(file_path) not in self._processed_files:
                self._processed_files.add(str(file_path))
                self._process_file_threadsafe(file_path)

    def _process_file_threadsafe(self, file_path: Path) -> None:
        """Process a response file in a thread-safe manner."""

        def process_with_delay():
            # Small delay to ensure file is fully written
            import time

            time.sleep(0.1)

            if file_path.exists():
                self._callback(file_path)

        # Submit to thread pool to avoid blocking the file watcher
        self._executor.submit(process_with_delay)
