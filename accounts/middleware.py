import functools
import time
from django.core.cache import cache
from django.http import JsonResponse, HttpResponseForbidden


class SecurityHeadersMiddleware:
    """Add security headers per OWASP recommendations."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # CSP: allow self scripts, inline styles (for theme), no external scripts
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # inline JS needed for templates
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )

        # HSTS: force HTTPS for 1 year
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'accelerometer=(), gyroscope=(), magnetometer=(), '
            'payment=(), usb=(), vr=()'
        )

        # Prevent MIME sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Disable legacy XSS filter (CSP is primary defense)
        response['X-XSS-Protection'] = '0'

        return response


def rate_limit(key_prefix, max_requests=5, window=60):
    """Simple rate limiter using Django cache.
    
    Args:
        key_prefix: unique prefix for the endpoint (e.g., 'login', 'message')
        max_requests: max requests allowed in window
        window: time window in seconds
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Use username for authenticated, IP for anonymous
            if request.user.is_authenticated:
                client_key = f"{key_prefix}:u:{request.user.username}"
            else:
                client_key = f"{key_prefix}:ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
            
            now = int(time.time())
            window_start = now - (now % window)
            cache_key = f"rl:{client_key}:{window_start}"
            
            count = cache.get(cache_key, 0)
            if count >= max_requests:
                return HttpResponseForbidden(
                    f'Слишком много запросов. Попробуйте через {window} секунд.',
                    content_type='text/plain'
                )
            
            cache.set(cache_key, count + 1, window)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# JSON-friendly variant for API endpoints
def rate_limit_json(key_prefix, max_requests=5, window=60):
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                client_key = f"{key_prefix}:u:{request.user.username}"
            else:
                client_key = f"{key_prefix}:ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
            
            now = int(time.time())
            window_start = now - (now % window)
            cache_key = f"rl:{client_key}:{window_start}"
            
            count = cache.get(cache_key, 0)
            if count >= max_requests:
                return JsonResponse(
                    {'error': f'Rate limit exceeded. Retry after {window} seconds.'},
                    status=429
                )
            
            cache.set(cache_key, count + 1, window)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
