"""TC3 Signature Generation for Tencent Cloud API."""

import hashlib
import hmac
import time
from datetime import datetime, timezone
from typing import Dict

TTS_SERVICE = "trtc"
TTS_VERSION = "2019-07-22"
TTS_ACTION_STREAM = "TextToSpeechSSE"
TTS_ACTION = "TextToSpeech"
TTS_HOST = "trtc.ai.tencentcloudapi.com"


def _sha256_hex(data: str) -> str:
    """Calculate SHA256 hash and return hex string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _hmac_sha256(key: bytes, msg: str) -> bytes:
    """Calculate HMAC-SHA256."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def generate_headers(
    secret_id: str,
    secret_key: str,
    payload: str,
    stream: bool = False,
) -> Dict[str, str]:
    """
    Generate authentication headers for Tencent Cloud API.

    Args:
        secret_id: Tencent Cloud Secret ID
        secret_key: Tencent Cloud Secret Key
        payload: Request payload as JSON string
        stream: Whether this is a streaming request

    Returns:
        Dictionary of HTTP headers
    """
    # Get current timestamp (use time.time() for correct UTC timestamp)
    timestamp = int(time.time())
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    # Choose action based on stream mode
    action = TTS_ACTION_STREAM if stream else TTS_ACTION

    # Step 1: Create canonical request
    http_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    canonical_headers = f"content-type:application/json\nhost:{TTS_HOST}\nx-tc-action:{action.lower()}\n"
    signed_headers = "content-type;host;x-tc-action"
    hashed_payload = _sha256_hex(payload)

    canonical_request = (
        f"{http_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{hashed_payload}"
    )

    # Step 2: Create string to sign
    algorithm = "TC3-HMAC-SHA256"
    credential_scope = f"{date}/{TTS_SERVICE}/tc3_request"
    hashed_canonical_request = _sha256_hex(canonical_request)
    string_to_sign = (
        f"{algorithm}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # Step 3: Calculate signature
    secret_date = _hmac_sha256(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, TTS_SERVICE)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # Step 4: Build authorization header
    authorization = (
        f"{algorithm} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    # Return headers
    return {
        "Authorization": authorization,
        "Content-Type": "application/json",
        "Host": TTS_HOST,
        "X-TC-Action": action,
        "X-TC-Version": TTS_VERSION,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Region": "ap-beijing",
    }
