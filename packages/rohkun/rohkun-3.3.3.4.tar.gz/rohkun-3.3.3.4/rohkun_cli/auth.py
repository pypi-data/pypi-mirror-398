"""
Authorization with Rohkun API
"""
import requests
import uuid
from typing import Optional
from dataclasses import dataclass

from .config import API_BASE_URL, API_TIMEOUT


@dataclass
class AuthResult:
    """Result of authorization check"""
    authorized: bool
    user_id: Optional[str] = None
    request_id: Optional[str] = None  # Store request_id for usage tracking
    credits_remaining: Optional[int] = None
    tier: Optional[str] = None
    reason: Optional[str] = None
    message: str = ""
    cli_display: Optional[dict] = None


def authorize_scan(
    api_key: str,
    project_name: Optional[str] = None,
    estimated_files: Optional[int] = None
) -> AuthResult:
    """
    Check with server if scan is authorized
    
    Args:
        api_key: User's API key
        project_name: Optional project name
        estimated_files: Optional file count estimate
        
    Returns:
        AuthResult with authorization status
    """
    request_id = str(uuid.uuid4())
    
    from . import __version__
    
    payload = {
        "api_key": api_key,
        "request_id": request_id,
        "cli_version": __version__,
        "scan_metadata": {
            "project_name": project_name,
            "estimated_files": estimated_files
        }
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/authorize-scan",
            json=payload,
            timeout=API_TIMEOUT
        )
        
        data = response.json()
        
        return AuthResult(
            authorized=data.get("authorized", False),
            user_id=data.get("user_id"),
            request_id=request_id,  # Store the request_id we created
            credits_remaining=data.get("credits_remaining"),
            tier=data.get("tier"),
            reason=data.get("reason"),
            message=data.get("message", ""),
            cli_display=data.get("cli_display")
        )
        
    except requests.exceptions.Timeout:
        return AuthResult(
            authorized=False,
            reason="timeout",
            message="Authorization request timed out. Please check your internet connection."
        )
    except requests.exceptions.ConnectionError:
        return AuthResult(
            authorized=False,
            reason="connection_error",
            message="Could not connect to Rohkun API. Please check your internet connection."
        )
    except Exception as e:
        return AuthResult(
            authorized=False,
            reason="error",
            message=f"Authorization failed: {str(e)}"
        )


def report_usage(
    api_key: str,
    request_id: str,
    success: bool,
    credits_consumed: int = 1
):
    """
    Report usage to server (fire-and-forget)
    
    This is non-blocking and won't fail the CLI if it errors
    """
    try:
        requests.post(
            f"{API_BASE_URL}/api/v1/usage",
            json={
                "api_key": api_key,
                "request_id": request_id,
                "success": success,
                "credits_consumed": credits_consumed
            },
            timeout=5
        )
    except:
        # Silently fail - don't block CLI
        pass
