# truslyo/middleware.py
"""
Middleware for automatic fraud detection on protected routes

Supports:
- FastAPI (ASGI)
- Flask (WSGI)
- Django (WSGI)
- Starlette (ASGI)
"""

from typing import List, Optional, Callable, Any
import asyncio
from .client import TrusyloClient, FraudCheckResult
from .exceptions import FraudDetectedError, TrusyloError


class TrusyloMiddleware:
    """
    Middleware for automatic fraud detection on all protected routes
    
    Usage (FastAPI/Starlette):
        from truslyo import TruslyoMiddleware
        
        app.add_middleware(
            TruslyoMiddleware,
            api_key="sk_live_abc123",
            protected_routes=["/signup", "/checkout"]
        )
    
    Usage (Flask):
        from truslyo import TruslyoMiddleware
        
        app.wsgi_app = TruslyoMiddleware(
            app.wsgi_app,
            api_key="sk_live_abc123",
            protected_routes=["/signup", "/checkout"]
        )
    
    Usage (Django):
        # In settings.py MIDDLEWARE
        MIDDLEWARE = [
            'truslyo.middleware.DjangoTruslyoMiddleware',
            # ... other middleware
        ]
        
        # In settings.py
        TRUSLYO_API_KEY = "sk_live_abc123"
        TRUSLYO_PROTECTED_ROUTES = ["/signup", "/checkout"]
    """
    
    def __init__(
        self,
        app,
        api_key: str,
        protected_routes: Optional[List[str]] = None,
        block_on_fraud: bool = True,
        block_on_review: bool = False,
        fail_open: bool = True,
        custom_handler: Optional[Callable] = None
    ):
        """
        Initialize Truslyo middleware
        
        Args:
            app: ASGI or WSGI application
            api_key: Truslyo secret key (sk_...)
            protected_routes: List of route paths to protect (e.g., ["/signup"])
            block_on_fraud: Block when decision is "block" (default: True)
            block_on_review: Block when decision is "review" (default: False)
            fail_open: Continue if Truslyo API fails (default: True)
            custom_handler: Custom function to handle fraud results
        """
        self.app = app
        self.client = TrusyloClient(api_key=api_key)
        self.protected_routes = protected_routes or []
        self.block_on_fraud = block_on_fraud
        self.block_on_review = block_on_review
        self.fail_open = fail_open
        self.custom_handler = custom_handler
    
    async def __call__(self, scope, receive, send):
        """
        ASGI middleware entry point
        
        Used by FastAPI, Starlette, and other ASGI frameworks
        """
        # Only process HTTP requests
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        path = scope.get("path", "")
        method = scope.get("method", "")
        
        # Only protect POST requests to specified routes
        if method != "POST" or not self._should_protect(path):
            return await self.app(scope, receive, send)
        
        # Read the request body to extract token
        body_parts = []
        
        async def receive_with_buffer():
            """Receive and buffer the body so we can read it multiple times"""
            nonlocal body_parts
            message = await receive()
            
            if message["type"] == "http.request":
                body_parts.append(message.get("body", b""))
            
            return message
        
        # Collect the full body
        body = b""
        while True:
            message = await receive_with_buffer()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break
        
        # Parse form data to extract token
        token = None
        email = None
        
        try:
            # Try to parse as form data
            body_str = body.decode("utf-8")
            
            # Simple form parsing (for more complex cases, use a proper parser)
            if "truslyo_token=" in body_str:
                for part in body_str.split("&"):
                    if part.startswith("truslyo_token="):
                        token = part.split("=", 1)[1]
                    elif part.startswith("email="):
                        email = part.split("=", 1)[1]
        except:
            pass
        
        # Check fraud if token is present
        if token:
            try:
                # Get IP address from scope
                ip_address = self._get_ip_from_scope(scope)
                
                # Check fraud
                result = self.client.check(
                    token=token,
                    email=email,
                    ip_address=ip_address
                )
                
                # Store result in scope for access in endpoint
                scope["truslyo_result"] = result
                
                # Custom handler
                if self.custom_handler:
                    self.custom_handler(result, scope)
                
                # Block if needed
                if self.block_on_fraud and result.should_block():
                    return await self._send_blocked_response(send, result)
                
                if self.block_on_review and result.should_review():
                    return await self._send_review_response(send, result)
                    
            except TrusyloError as e:
                if not self.fail_open:
                    return await self._send_error_response(send, str(e))
                # Fail open - continue to app
        
        # Create a new receive that replays the buffered body
        body_index = 0
        
        async def replayed_receive():
            nonlocal body_index
            if body_index == 0:
                body_index += 1
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False
                }
            return await receive()
        
        # Continue to the app with replayed body
        return await self.app(scope, replayed_receive, send)
    
    def _should_protect(self, path: str) -> bool:
        """Check if path matches protected routes"""
        if not self.protected_routes:
            return False
        
        for route in self.protected_routes:
            if path.startswith(route):
                return True
        
        return False
    
    def _get_ip_from_scope(self, scope: dict) -> str:
        """Extract IP address from ASGI scope"""
        # Check headers first for proxy IPs
        headers = dict(scope.get("headers", []))
        
        # Try common proxy headers
        for header_name in [b"x-forwarded-for", b"x-real-ip", b"cf-connecting-ip"]:
            if header_name in headers:
                ip = headers[header_name].decode("utf-8")
                # X-Forwarded-For can have multiple IPs
                return ip.split(",")[0].strip()
        
        # Fallback to client IP
        client = scope.get("client")
        if client:
            return client[0]
        
        return "unknown"
    
    async def _send_blocked_response(self, send, result: FraudCheckResult):
        """Send fraud blocked response"""
        import json
        
        body = json.dumps({
            "error": "Fraud detected",
            "decision": "block",
            "risk_score": result.risk_score,
            "reasons": result.reasons,
            "fraud_patterns": result.fraud_patterns
        }).encode("utf-8")
        
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        
        await send({
            "type": "http.response.body",
            "body": body,
        })
    
    async def _send_review_response(self, send, result: FraudCheckResult):
        """Send review required response"""
        import json
        
        body = json.dumps({
            "error": "Manual review required",
            "decision": "review",
            "risk_score": result.risk_score,
            "reasons": result.reasons
        }).encode("utf-8")
        
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        
        await send({
            "type": "http.response.body",
            "body": body,
        })
    
    async def _send_error_response(self, send, error_msg: str):
        """Send error response"""
        import json
        
        body = json.dumps({
            "error": "Fraud check failed",
            "message": error_msg
        }).encode("utf-8")
        
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [
                [b"content-type", b"application/json"],
                [b"content-length", str(len(body)).encode()],
            ],
        })
        
        await send({
            "type": "http.response.body",
            "body": body,
        })


class FlaskTruslyoMiddleware:
    """
    Flask-specific middleware (WSGI)
    
    Usage:
        from truslyo import FlaskTruslyoMiddleware
        
        app.wsgi_app = FlaskTruslyoMiddleware(
            app.wsgi_app,
            api_key="sk_live_abc123",
            protected_routes=["/signup", "/checkout"]
        )
    """
    
    def __init__(
        self,
        app,
        api_key: str,
        protected_routes: Optional[List[str]] = None,
        block_on_fraud: bool = True,
        block_on_review: bool = False,
        fail_open: bool = True
    ):
        self.app = app
        self.client = TrusyloClient(api_key=api_key)
        self.protected_routes = protected_routes or []
        self.block_on_fraud = block_on_fraud
        self.block_on_review = block_on_review
        self.fail_open = fail_open
    
    def __call__(self, environ, start_response):
        """WSGI entry point"""
        from urllib.parse import parse_qs
        
        path = environ.get("PATH_INFO", "")
        method = environ.get("REQUEST_METHOD", "")
        
        # Only protect POST requests to specified routes
        if method != "POST" or not self._should_protect(path):
            return self.app(environ, start_response)
        
        # Read request body
        try:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            content_length = 0
        
        if content_length > 0:
            body = environ["wsgi.input"].read(content_length)
            
            # Parse form data
            try:
                body_str = body.decode("utf-8")
                params = parse_qs(body_str)
                
                token = params.get("truslyo_token", [None])[0]
                email = params.get("email", [None])[0]
                
                if token:
                    # Get IP address
                    ip_address = self._get_ip_from_environ(environ)
                    
                    # Check fraud
                    result = self.client.check(
                        token=token,
                        email=email,
                        ip_address=ip_address
                    )
                    
                    # Store result in environ
                    environ["truslyo_result"] = result
                    
                    # Block if needed
                    if self.block_on_fraud and result.should_block():
                        return self._blocked_response(start_response, result)
                    
                    if self.block_on_review and result.should_review():
                        return self._review_response(start_response, result)
                
            except TrusyloError as e:
                if not self.fail_open:
                    return self._error_response(start_response, str(e))
            
            # Reset input stream for the app to read
            from io import BytesIO
            environ["wsgi.input"] = BytesIO(body)
            environ["CONTENT_LENGTH"] = str(len(body))
        
        return self.app(environ, start_response)
    
    def _should_protect(self, path: str) -> bool:
        """Check if path matches protected routes"""
        if not self.protected_routes:
            return False
        
        for route in self.protected_routes:
            if path.startswith(route):
                return True
        
        return False
    
    def _get_ip_from_environ(self, environ: dict) -> str:
        """Extract IP from WSGI environ"""
        # Try proxy headers first
        for header in ["HTTP_X_FORWARDED_FOR", "HTTP_X_REAL_IP", "HTTP_CF_CONNECTING_IP"]:
            if header in environ:
                ip = environ[header]
                return ip.split(",")[0].strip()
        
        # Fallback to REMOTE_ADDR
        return environ.get("REMOTE_ADDR", "unknown")
    
    def _blocked_response(self, start_response, result: FraudCheckResult):
        """Return blocked response"""
        import json
        
        body = json.dumps({
            "error": "Fraud detected",
            "decision": "block",
            "risk_score": result.risk_score,
            "reasons": result.reasons,
            "fraud_patterns": result.fraud_patterns
        })
        
        start_response("403 Forbidden", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body)))
        ])
        
        return [body.encode("utf-8")]
    
    def _review_response(self, start_response, result: FraudCheckResult):
        """Return review required response"""
        import json
        
        body = json.dumps({
            "error": "Manual review required",
            "decision": "review",
            "risk_score": result.risk_score,
            "reasons": result.reasons
        })
        
        start_response("403 Forbidden", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body)))
        ])
        
        return [body.encode("utf-8")]
    
    def _error_response(self, start_response, error_msg: str):
        """Return error response"""
        import json
        
        body = json.dumps({
            "error": "Fraud check failed",
            "message": error_msg
        })
        
        start_response("500 Internal Server Error", [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body)))
        ])
        
        return [body.encode("utf-8")]


class DjangoTruslyoMiddleware:
    """
    Django-specific middleware
    
    Usage:
        # In settings.py MIDDLEWARE
        MIDDLEWARE = [
            'truslyo.middleware.DjangoTruslyoMiddleware',
            # ... other middleware
        ]
        
        # In settings.py
        TRUSLYO_API_KEY = "sk_live_abc123"
        TRUSLYO_PROTECTED_ROUTES = ["/signup", "/checkout"]
        TRUSLYO_BLOCK_ON_FRAUD = True
        TRUSLYO_BLOCK_ON_REVIEW = False
        TRUSLYO_FAIL_OPEN = True
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Import Django settings
        from django.conf import settings
        
        api_key = getattr(settings, "TRUSLYO_API_KEY", None)
        if not api_key:
            raise ValueError(
                "TRUSLYO_API_KEY not found in Django settings. "
                "Add TRUSLYO_API_KEY = 'sk_live_abc123' to settings.py"
            )
        
        self.client = TrusyloClient(api_key=api_key)
        self.protected_routes = getattr(settings, "TRUSLYO_PROTECTED_ROUTES", [])
        self.block_on_fraud = getattr(settings, "TRUSLYO_BLOCK_ON_FRAUD", True)
        self.block_on_review = getattr(settings, "TRUSLYO_BLOCK_ON_REVIEW", False)
        self.fail_open = getattr(settings, "TRUSLYO_FAIL_OPEN", True)
    
    def __call__(self, request):
        """Django middleware entry point"""
        from django.http import JsonResponse
        
        # Only protect POST requests to specified routes
        if request.method == "POST" and self._should_protect(request.path):
            token = request.POST.get("truslyo_token")
            
            if token:
                try:
                    email = request.POST.get("email")
                    ip_address = self._get_client_ip(request)
                    
                    # Check fraud
                    result = self.client.check(
                        token=token,
                        email=email,
                        ip_address=ip_address
                    )
                    
                    # Attach result to request
                    request.truslyo_result = result
                    
                    # Block if needed
                    if self.block_on_fraud and result.should_block():
                        return JsonResponse({
                            "error": "Fraud detected",
                            "decision": "block",
                            "risk_score": result.risk_score,
                            "reasons": result.reasons,
                            "fraud_patterns": result.fraud_patterns
                        }, status=403)
                    
                    if self.block_on_review and result.should_review():
                        return JsonResponse({
                            "error": "Manual review required",
                            "decision": "review",
                            "risk_score": result.risk_score,
                            "reasons": result.reasons
                        }, status=403)
                    
                except TrusyloError as e:
                    if not self.fail_open:
                        return JsonResponse({
                            "error": "Fraud check failed",
                            "message": str(e)
                        }, status=500)
        
        # Continue to view
        response = self.get_response(request)
        return response
    
    def _should_protect(self, path: str) -> bool:
        """Check if path matches protected routes"""
        if not self.protected_routes:
            return False
        
        for route in self.protected_routes:
            if path.startswith(route):
                return True
        
        return False
    
    def _get_client_ip(self, request) -> str:
        """Get client IP from Django request"""
        # Try proxy headers first
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        
        x_real_ip = request.META.get("HTTP_X_REAL_IP")
        if x_real_ip:
            return x_real_ip
        
        cf_connecting_ip = request.META.get("HTTP_CF_CONNECTING_IP")
        if cf_connecting_ip:
            return cf_connecting_ip
        
        # Fallback to REMOTE_ADDR
        return request.META.get("REMOTE_ADDR", "unknown")