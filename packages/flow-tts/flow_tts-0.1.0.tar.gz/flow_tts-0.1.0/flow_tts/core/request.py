"""HTTP Request Handler for Tencent Cloud API."""

import base64
import http.client
import json
from typing import Any, Callable, Dict, Iterator, Optional

from ..types import TTSError

TTS_HOST = "trtc.tencentcloudapi.com"


def make_request(headers: Dict[str, str], payload: str) -> Dict[str, Any]:
    """
    Make a regular HTTP POST request to Tencent Cloud API.

    Args:
        headers: Request headers (including Authorization)
        payload: Request payload as JSON string

    Returns:
        Parsed JSON response

    Raises:
        TTSError: If request fails
    """
    conn = http.client.HTTPSConnection(TTS_HOST, timeout=30)

    try:
        conn.request("POST", "/", payload.encode("utf-8"), headers)
        response = conn.getresponse()
        response_data = response.read().decode("utf-8")

        if response.status != 200:
            try:
                error_data = json.loads(response_data)
                error_msg = error_data.get("Response", {}).get("Error", {})
                raise TTSError(
                    message=error_msg.get("Message", f"HTTP {response.status}"),
                    code=error_msg.get("Code"),
                    request_id=error_data.get("Response", {}).get("RequestId"),
                )
            except json.JSONDecodeError:
                raise TTSError(
                    message=f"HTTP {response.status}: {response_data}",
                )

        result = json.loads(response_data)

        # Check for API errors
        if "Response" in result and "Error" in result["Response"]:
            error = result["Response"]["Error"]
            raise TTSError(
                message=error.get("Message", "Unknown error"),
                code=error.get("Code"),
                request_id=result["Response"].get("RequestId"),
            )

        return result

    finally:
        conn.close()


SSEChunk = Dict[str, Any]


def make_stream_request(
    headers: Dict[str, str],
    payload: str,
    on_chunk: Callable[[SSEChunk], None],
) -> None:
    """
    Make an SSE streaming request to Tencent Cloud API.

    Args:
        headers: Request headers (including Authorization)
        payload: Request payload as JSON string
        on_chunk: Callback for each SSE chunk

    Raises:
        TTSError: If request fails
    """
    conn = http.client.HTTPSConnection(TTS_HOST, timeout=60)

    try:
        conn.request("POST", "/", payload.encode("utf-8"), headers)
        response = conn.getresponse()

        if response.status != 200:
            response_data = response.read().decode("utf-8")
            try:
                error_data = json.loads(response_data)
                error_msg = error_data.get("Response", {}).get("Error", {})
                raise TTSError(
                    message=error_msg.get("Message", f"HTTP {response.status}"),
                    code=error_msg.get("Code"),
                    request_id=error_data.get("Response", {}).get("RequestId"),
                )
            except json.JSONDecodeError:
                raise TTSError(
                    message=f"HTTP {response.status}: {response_data}",
                )

        # Read SSE stream
        buffer = ""
        while True:
            chunk = response.read(8192)
            if not chunk:
                break

            buffer += chunk.decode("utf-8")

            # Process complete lines
            lines = buffer.split("\n")
            buffer = lines.pop()  # Keep incomplete line in buffer

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Parse SSE data field
                if line.startswith("data: "):
                    data_str = line[6:]  # Remove "data: " prefix
                    try:
                        data = json.loads(data_str)
                        on_chunk(data)
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        pass

    finally:
        conn.close()
