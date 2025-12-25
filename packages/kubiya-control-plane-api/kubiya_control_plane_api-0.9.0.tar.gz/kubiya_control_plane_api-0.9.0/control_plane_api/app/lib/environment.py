"""
Environment detection utilities for API deployment context.

Provides functions to detect serverless environments and determine
whether WebSocket connections should be used.

Serverless environments detected:
- AWS Lambda
- Vercel Functions
- Google Cloud Functions
- Azure Functions
"""

from typing import Literal
import os


def detect_environment() -> Literal["standard", "serverless"]:
    """
    Detect if running in a serverless environment.

    Returns:
        "serverless" if running in a serverless environment (Lambda, Vercel, GCF, Azure Functions)
        "standard" for traditional server environments
    """
    # AWS Lambda
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "serverless"

    # Vercel Functions
    if os.environ.get("VERCEL"):
        return "serverless"

    # Google Cloud Functions
    if os.environ.get("FUNCTION_TARGET") or os.environ.get("K_SERVICE"):
        return "serverless"

    # Azure Functions
    if os.environ.get("AZURE_FUNCTIONS_ENVIRONMENT"):
        return "serverless"

    return "standard"


def should_use_websocket() -> bool:
    """
    Determine if WebSocket should be used based on environment.

    WebSocket is disabled in serverless environments due to limitations:
    - Short-lived execution contexts
    - No persistent connections
    - Function timeout constraints

    Returns:
        True if WebSocket should be used, False otherwise
    """
    # Never use WebSocket in serverless
    if detect_environment() == "serverless":
        return False

    # Check explicit disable
    if os.environ.get("WEBSOCKET_ENABLED", "true").lower() == "false":
        return False

    return True
