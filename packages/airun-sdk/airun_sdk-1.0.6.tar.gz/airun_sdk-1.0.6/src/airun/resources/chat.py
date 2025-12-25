"""
Chat API Resource

Provides access to chat/completion endpoints.
"""

from typing import Optional, Dict, Any, AsyncGenerator, Callable, Generator
import asyncio
import json
import logging
import threading
import websocket
import websockets
from ..http_client import HTTPClient
from ..models import ChatOptions, ChatResponse

logger = logging.getLogger(__name__)


class ChatResource:
    """Chat API resource for AI conversations."""

    def __init__(self, http_client: HTTPClient):
        """Initialize chat resource."""
        self.client = http_client

    def create(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None,
        async_mode: bool = True
    ) -> Any:
        """
        Create a chat completion.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.
            async_mode: Whether to process asynchronously (queue) or sync.

        Returns:
            Chat completion response.

        Example:
            >>> response = chat.create(
            ...     prompt="What is Python?",
            ...     options=ChatOptions(model="gpt-4", temperature=0.7)
            ... )
            >>> print(response.data.response)
        """
        endpoint = "/api/v1/chat/sync" if not async_mode else "/api/v1/chat"

        payload = {"prompt": prompt}
        if options:
            payload["options"] = options.model_dump(exclude_none=True) if hasattr(options, "model_dump") else options

        response = self.client.post(endpoint, data=payload)
        # API expects a dict but we return it wrapped in APIResponse format
        return response

    def create_sync(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None
    ) -> Any:
        """
        Create a synchronous chat completion.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.

        Returns:
            Chat completion response.
        """
        return self.create(prompt, options, async_mode=False)

    async def create_async(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None
    ) -> Any:
        """
        Create an asynchronous chat completion.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.

        Returns:
            Chat completion response.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.create,
            prompt,
            options
        )

    def get_status(self, job_id: str) -> Any:
        """
        Get the status of an async chat job.

        Args:
            job_id: The job ID returned from async chat creation.

        Returns:
            Job status information.
        """
        response = self.client.get(f"/api/v1/code/status/{job_id}")
        return response

    def stream_chat(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None,
        on_content: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any], str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Stream a chat completion using WebSocket.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.
            on_content: Callback for receiving content chunks.
            on_progress: Callback for progress updates.
            on_complete: Callback when streaming completes (receives response and session_id).
            on_error: Callback for errors.
            timeout: Connection timeout in seconds.

        Returns:
            Final response with session_id and accumulated content.

        Example:
            >>> def on_content(chunk):
            ...     print(chunk, end='', flush=True)
            >>> response = client.chat.stream_chat(
            ...     prompt="Explain quantum computing",
            ...     on_content=on_content
            ... )
            >>> print(f"\\nSession ID: {response['sessionId']}")
        """
        ws_url = f"{self.client.base_url.replace('http', 'ws', 1)}/wss?apiKey={self.client.api_key}"

        # Prepare options
        payload_options = {}
        if options:
            payload_options = options.model_dump(exclude_none=True) if hasattr(options, "model_dump") else options

        # Build request message
        request = {
            "type": "streamChat",
            "prompt": prompt,
            "options": payload_options
        }

        # Add sessionId if provided
        if isinstance(options, dict) and options.get("sessionId"):
            request["sessionId"] = options["sessionId"]
        elif hasattr(options, "sessionId") and options.sessionId:
            request["sessionId"] = options.sessionId

        # Accumulate results
        accumulated_content = []
        final_session_id = None
        final_response = {}
        progress_messages = []

        # Flag to track if complete was received
        complete_received = threading.Event()

        def on_message(ws_client, message):
            nonlocal accumulated_content, final_session_id, final_response
            try:
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type in ("content", "stream_content"):
                    content = data.get("data", "") if msg_type == "content" else data.get("content", "")
                    accumulated_content.append(content)
                    if on_content:
                        on_content(content)

                elif msg_type == "progress":
                    progress_messages.append(data)
                    if on_progress:
                        on_progress(data)

                elif msg_type == "complete":
                    final_response = data.get("data", {})
                    final_session_id = data.get("sessionId") or final_response.get("sessionId")
                    if on_complete:
                        on_complete(final_response, final_session_id)
                    # Signal complete and close connection
                    complete_received.set()
                    ws_client.close()

                elif msg_type == "error":
                    error_msg = data.get("data", "Unknown error")
                    if on_error:
                        on_error(Exception(error_msg))
                    else:
                        logger.error(f"StreamChat error: {error_msg}")
                    complete_received.set()
                    ws_client.close()

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse WebSocket message: {message}")

        def on_error_ws(ws_client, error):
            complete_received.set()
            if on_error:
                on_error(error)

        def on_close(ws_client, close_status_code, close_msg):
            logger.debug(f"WebSocket connection closed: {close_status_code} - {close_msg}")
            complete_received.set()

        def on_open(ws_client):
            logger.debug("WebSocket connection established")
            ws_client.send(json.dumps(request))

        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error_ws,
            on_close=on_close
        )

        # Run WebSocket in a separate thread so we can wait for complete
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # Wait for complete event or timeout
        complete_received.wait(timeout=timeout)

        # Close connection if still open
        try:
            ws.close()
        except:
            pass

        return {
            "content": "".join(accumulated_content),
            "sessionId": final_session_id,
            "response": final_response,
            "progress": progress_messages
        }

    async def stream_chat_async(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None,
        on_content: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_complete: Optional[Callable[[Dict[str, Any], str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Async version of stream_chat.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.
            on_content: Callback for receiving content chunks.
            on_progress: Callback for progress updates.
            on_complete: Callback when streaming completes.
            on_error: Callback for errors.
            timeout: Connection timeout in seconds.

        Returns:
            Final response with session_id and accumulated content.
        """
        ws_url = f"{self.client.base_url.replace('http', 'ws', 1)}/wss?apiKey={self.client.api_key}"

        # Prepare options
        payload_options = {}
        if options:
            payload_options = options.model_dump(exclude_none=True) if hasattr(options, "model_dump") else options

        # Build request message
        request = {
            "type": "streamChat",
            "prompt": prompt,
            "options": payload_options
        }

        # Add sessionId if provided
        if isinstance(options, dict) and options.get("sessionId"):
            request["sessionId"] = options["sessionId"]
        elif hasattr(options, "sessionId") and options.sessionId:
            request["sessionId"] = options.sessionId

        # Accumulate results
        accumulated_content = []
        final_session_id = None
        final_response = {}
        progress_messages = []

        async with websockets.connect(ws_url) as ws:
            # Send request
            await ws.send(json.dumps(request))

            # Receive messages
            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    msg_type = data.get("type")

                    if msg_type in ("content", "stream_content"):
                        content = data.get("data", "") if msg_type == "content" else data.get("content", "")
                        accumulated_content.append(content)
                        if on_content:
                            if asyncio.iscoroutinefunction(on_content):
                                await on_content(content)
                            else:
                                on_content(content)

                    elif msg_type == "progress":
                        progress_messages.append(data)
                        if on_progress:
                            if asyncio.iscoroutinefunction(on_progress):
                                await on_progress(data)
                            else:
                                on_progress(data)

                    elif msg_type == "complete":
                        final_response = data.get("data", {})
                        final_session_id = data.get("sessionId") or final_response.get("sessionId")
                        if on_complete:
                            if asyncio.iscoroutinefunction(on_complete):
                                await on_complete(final_response, final_session_id)
                            else:
                                on_complete(final_response, final_session_id)
                        # Close connection and break
                        await ws.close()
                        break

                    elif msg_type == "error":
                        error_msg = data.get("data", "Unknown error")
                        if on_error:
                            if asyncio.iscoroutinefunction(on_error):
                                await on_error(Exception(error_msg))
                            else:
                                on_error(Exception(error_msg))
                        break

                except websockets.exceptions.ConnectionClosed:
                    break

        return {
            "content": "".join(accumulated_content),
            "sessionId": final_session_id,
            "response": final_response,
            "progress": progress_messages
        }

    def stream_chat_generator(
        self,
        prompt: str,
        options: Optional[ChatOptions] = None,
        timeout: int = 300
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream a chat completion as a generator.

        Args:
            prompt: The user's prompt or question.
            options: Additional options for the chat request.
            timeout: Connection timeout in seconds.

        Yields:
            Dict with 'type' ('content', 'progress', 'complete', 'error') and 'data' keys.

        Example:
            >>> for chunk in client.chat.stream_chat_generator("Tell me a story"):
            ...     if chunk['type'] == 'content':
            ...         print(chunk['data'], end='', flush=True)
            ...     elif chunk['type'] == 'progress':
            ...         print(f"\\nProgress: {chunk['data'].get('percent')}%")
        """
        ws_url = f"{self.client.base_url.replace('http', 'ws', 1)}/wss?apiKey={self.client.api_key}"

        # Prepare options
        payload_options = {}
        if options:
            payload_options = options.model_dump(exclude_none=True) if hasattr(options, "model_dump") else options

        # Build request message
        request = {
            "type": "streamChat",
            "prompt": prompt,
            "options": payload_options
        }

        # Add sessionId if provided
        if isinstance(options, dict) and options.get("sessionId"):
            request["sessionId"] = options["sessionId"]
        elif hasattr(options, "sessionId") and options.sessionId:
            request["sessionId"] = options.sessionId

        # Queue to yield messages from the WebSocket thread
        import queue
        message_queue = queue.Queue()

        def on_message(ws_client, message):
            try:
                data = json.loads(message)
                # Normalize message types for consistency
                if data.get("type") == "stream_content":
                    data = {
                        "type": "content",
                        "data": data.get("content", ""),
                        "original_type": "stream_content"
                    }
                message_queue.put(data)
                # Close connection after receiving complete message
                if data.get("type") == "complete":
                    ws_client.close()
            except json.JSONDecodeError:
                message_queue.put({"type": "error", "data": f"Failed to parse message: {message}"})

        def on_error_ws(ws_client, error):
            message_queue.put({"type": "error", "data": str(error)})

        def on_close(ws_client, *args):
            message_queue.put(None)  # Signal end of stream

        def on_open(ws_client):
            ws_client.send(json.dumps(request))

        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error_ws,
            on_close=on_close
        )

        # Run WebSocket in a separate thread
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()

        # Yield messages as they arrive
        import time
        start_time = time.time()
        while True:
            # Check timeout
            if time.time() - start_time > timeout:
                break
            # Get message with timeout
            try:
                message = message_queue.get(timeout=1)
                if message is None:
                    break
                yield message
                # Exit after complete message
                if message.get("type") == "complete":
                    break
            except:
                # Queue.get timed out, check if we should continue
                continue