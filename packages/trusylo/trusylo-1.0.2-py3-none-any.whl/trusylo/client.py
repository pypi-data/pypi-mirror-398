"""
Core API client for Truslyo fraud detection
"""

import requests
from typing import Dict, Optional, Any
from .exceptions import (
    TruslyoError,
    FraudDetectedError,
    InvalidTokenError,
    APIError,
    RateLimitError
)

__version__ = "1.0.2"
class TruslyoClient:
    """
    Truslyo API Client
    
    Usage:
        client = TruslyoClient(api_key="sk_live_abc123")
        result = client.check(token="eyJ...", email="user@example.com")
        
        if result.should_block():
            raise FraudDetectedError("Signup blocked")
    """
    
    def __init__(
        self, 
        api_key: str,
        base_url: str = "https://trusylo.com",
        timeout: int = 5
    ):
        if not api_key:
            raise ValueError("API key is required")
        
        if not api_key.startswith("sk_"):
            raise ValueError(
                "Invalid API key format. Must start with 'sk_'. "
                "Use your secret key, not publishable key."
            )
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
    def check(
        self,
        token: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'FraudCheckResult':
        """
        Check if a signup/transaction is fraudulent
        
        Args:
            token: Token from frontend (created by Truslyo.js SDK)
            email: User's email address (optional, overrides token data)
            ip_address: User's IP address (optional, overrides token data)
            user_id: Your internal user ID (optional)
            metadata: Additional data to include (optional)
        
        Returns:
            FraudCheckResult object with decision, risk score, reasons
        
        Raises:
            InvalidTokenError: Token is invalid or expired
            APIError: API request failed
            RateLimitError: Rate limit exceeded
        """
        
        payload = {
            "token": token,
            "email": email,
            "ip_address": ip_address,
            "user_id": user_id,
            "metadata": metadata
        }
        
        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/check",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": f"truslyo-python/{__version__}"
                },
                timeout=self.timeout
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded. Upgrade your plan or wait before retrying."
                )
            
            # Handle invalid token
            if response.status_code == 400:
                error_data = response.json()
                if "token" in error_data.get("detail", "").lower():
                    raise InvalidTokenError(
                        f"Invalid token: {error_data.get('detail', 'Unknown error')}"
                    )
            
            # Handle other errors
            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", error_msg)
                except:
                    pass
                
                raise APIError(
                    f"API request failed ({response.status_code}): {error_msg}"
                )
            
            data = response.json()
            return FraudCheckResult(data)
            
        except requests.exceptions.Timeout:
            raise APIError(
                f"Request timed out after {self.timeout} seconds. "
                "Try increasing timeout or check your network."
            )
        except requests.exceptions.RequestException as e:
            raise APIError(f"Network error: {str(e)}")


class FraudCheckResult:
    """
    Result from fraud detection check
    
    Attributes:
        decision: "approve", "block", or "review"
        risk_score: Float between 0.0 and 1.0
        session_id: Session identifier
        reasons: List of reasons for the decision
        fraud_patterns: List of detected fraud patterns
        processing_time_ms: Time taken for check
        raw: Full raw response from API
    """
    
    def __init__(self, data: Dict[str, Any]):
        self.decision = data.get("decision", "approve")
        self.risk_score = data.get("risk_score", 0.0)
        self.session_id = data.get("session_id", "")
        self.reasons = data.get("reasons", [])
        self.fraud_patterns = data.get("fraud_patterns", [])
        self.processing_time_ms = data.get("processing_time_ms", 0)
        self.raw = data
    
    def should_block(self) -> bool:
        """Returns True if signup should be blocked"""
        return self.decision == "block"
    
    def should_review(self) -> bool:
        """Returns True if signup needs manual review"""
        return self.decision == "review"
    
    def is_approved(self) -> bool:
        """Returns True if signup is approved"""
        return self.decision == "approve"
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if self.should_block():
            return f"Blocked: {', '.join(self.reasons)}"
        elif self.should_review():
            return f"Review required: {', '.join(self.reasons)}"
        else:
            return "Approved"
    
    def __repr__(self):
        return (
            f"FraudCheckResult(decision='{self.decision}', "
            f"risk_score={self.risk_score:.2f})"
        )

