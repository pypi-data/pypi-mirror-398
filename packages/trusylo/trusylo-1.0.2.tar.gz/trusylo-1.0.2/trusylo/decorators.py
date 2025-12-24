"""
Decorator for protecting endpoints with fraud detection
"""

from functools import wraps
from typing import Optional, Callable, Any
from .client import TrusyloClient
from .exceptions import FraudDetectedError, TrusyloError


def trusylo_protect(
    api_key: str,
    block_on_fraud: bool = True,
    block_on_review: bool = False,
    fail_open: bool = True,
    custom_handler: Optional[Callable] = None
):
    """
    Decorator to protect endpoints with Truslyo fraud detection
    
    Usage:
        @app.post("/signup")
        @truslyo_protect(api_key="sk_live_abc123")
        async def signup(request):
            # Your code here
            return {"success": True}
    
    Args:
        api_key: Your Truslyo secret key (starts with sk_)
        block_on_fraud: Block when decision is "block" (default: True)
        block_on_review: Block when decision is "review" (default: False)
        fail_open: Continue if Truslyo API fails (default: True)
        custom_handler: Custom function to handle fraud results
    
    Raises:
        FraudDetectedError: When fraud is detected and block_on_fraud=True
    """
    
    client = TrusyloClient(api_key=api_key)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(request, *args, **kwargs):
            try:
                # Extract token from request
                token = _extract_token(request)
                
                if not token:
                    if fail_open:
                        # No token found, continue without check
                        return await func(request, *args, **kwargs)
                    else:
                        raise TrusyloError("Missing Truslyo token")
                
                # Extract email and IP from request
                email = _extract_email(request)
                ip_address = _get_client_ip(request)
                
                # Check fraud
                result = client.check(
                    token=token,
                    email=email,
                    ip_address=ip_address
                )
                
                # Attach result to request for logging
                request.truslyo_result = result
                
                # Custom handler
                if custom_handler:
                    custom_handler(result, request)
                
                # Block if needed
                if block_on_fraud and result.should_block():
                    raise FraudDetectedError(
                        f"Fraud detected: {result.get_summary()}",
                        result=result
                    )
                
                if block_on_review and result.should_review():
                    raise FraudDetectedError(
                        f"Manual review required: {result.get_summary()}",
                        result=result
                    )
                
            except TrusyloError:
                if not fail_open:
                    raise
                # Fail open - continue without check
            
            # Continue to original function
            return await func(request, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(request, *args, **kwargs):
            try:
                token = _extract_token(request)
                
                if not token:
                    if fail_open:
                        return func(request, *args, **kwargs)
                    else:
                        raise TrusyloError("Missing Truslyo token")
                
                email = _extract_email(request)
                ip_address = _get_client_ip(request)
                
                result = client.check(
                    token=token,
                    email=email,
                    ip_address=ip_address
                )
                
                request.truslyo_result = result
                
                if custom_handler:
                    custom_handler(result, request)
                
                if block_on_fraud and result.should_block():
                    raise FraudDetectedError(
                        f"Fraud detected: {result.get_summary()}",
                        result=result
                    )
                
                if block_on_review and result.should_review():
                    raise FraudDetectedError(
                        f"Manual review required: {result.get_summary()}",
                        result=result
                    )
                
            except TrusyloError:
                if not fail_open:
                    raise
            
            return func(request, *args, **kwargs)
        
        # Return async or sync wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _extract_token(request) -> Optional[str]:
    """Extract truslyo_token from form data or JSON body"""
    # FastAPI
    if hasattr(request, 'form'):
        try:
            form = request.form()
            if hasattr(form, '__await__'):
                import asyncio
                form = asyncio.run(form)
            return form.get('truslyo_token')
        except:
            pass
    
    # Flask
    if hasattr(request, 'form') and hasattr(request.form, 'get'):
        token = request.form.get('truslyo_token')
        if token:
            return token
    
    # Django
    if hasattr(request, 'POST'):
        token = request.POST.get('truslyo_token')
        if token:
            return token
    
    # JSON body
    if hasattr(request, 'json'):
        try:
            json_data = request.json() if callable(request.json) else request.json
            if isinstance(json_data, dict):
                return json_data.get('truslyo_token')
        except:
            pass
    
    return None


def _extract_email(request) -> Optional[str]:
    """Try to find email in common form fields"""
    fields = ['email', 'username', 'user_email', 'email_address']
    
    for field in fields:
        # FastAPI/Flask form
        if hasattr(request, 'form'):
            try:
                form = request.form()
                if hasattr(form, '__await__'):
                    import asyncio
                    form = asyncio.run(form)
                email = form.get(field)
                if email:
                    return email
            except:
                pass
        
        # Django POST
        if hasattr(request, 'POST'):
            email = request.POST.get(field)
            if email:
                return email
        
        # JSON body
        if hasattr(request, 'json'):
            try:
                json_data = request.json() if callable(request.json) else request.json
                if isinstance(json_data, dict):
                    email = json_data.get(field)
                    if email:
                        return email
            except:
                pass
    
    return None


def _get_client_ip(request) -> str:
    """Get real IP address, handling proxies"""
    # Check proxy headers first
    if hasattr(request, 'headers'):
        headers = request.headers
        
        # Try common proxy headers
        for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
            ip = headers.get(header)
            if ip:
                # X-Forwarded-For can have multiple IPs
                return ip.split(',')[0].strip()
    
    # FastAPI
    if hasattr(request, 'client') and hasattr(request.client, 'host'):
        return request.client.host
    
    # Flask
    if hasattr(request, 'remote_addr'):
        return request.remote_addr
    
    # Django
    if hasattr(request, 'META'):
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    return 'unknown'

