"""
Paralegal SDK - Multi-tenant LLM Observability
"""
import os
from typing import Optional

try:
    from traceloop.sdk import Traceloop as TraceloopSDK
except ImportError:
    raise ImportError(
        "traceloop-sdk is required. Install it with: pip install traceloop-sdk"
    )

class Paralegal:
    @staticmethod
    def init(
        api_key: Optional[str] = None,
        app_name: Optional[str] = None,
        disable_batch: bool = False,
        exporter_endpoint: Optional[str] = None,
        **kwargs
    ):
        api_key = api_key or os.environ.get("PARALEGAL_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Paralegal API key not found. "
                "Set PARALEGAL_API_KEY environment variable or pass api_key parameter."
            )
        
        if not exporter_endpoint:
            exporter_endpoint = os.environ.get(
                "PARALEGAL_ENDPOINT", 
                "https://infra-1-gl4c.onrender.com"
            )
        
        headers = {
            "x-paralegal-api-key": api_key,
        }
        
        if app_name:
            headers["x-paralegal-app-name"] = app_name
        
        TraceloopSDK.init(
            api_endpoint=exporter_endpoint,
            disable_batch=disable_batch,
            headers=headers,
            **kwargs
        )
        
        print(f"✅ Paralegal tracing initialized")

# Make init available at module level
init = Paralegal.init

__version__ = "0.1.0"
__all__ = ["Paralegal", "init"]
