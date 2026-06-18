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


class IPRateLimitMiddleware:
    """Global rate limit for anonymous POST requests and login endpoints."""
    
    # Endpoints with stricter limits
    STRICT_PATHS = ['/accounts/login/', '/register/', '/api/keys/save/']
    STRICT_LIMIT = 10   # per 5 minutes
    STRICT_WINDOW = 300
    
    # General anonymous limit
    ANON_LIMIT = 30     # per minute
    ANON_WINDOW = 60
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if not request.user.is_authenticated and request.method == 'POST':
            ip = self._get_ip(request)
            path = request.path
            
            # Check strict paths first
            if any(path.startswith(p) for p in self.STRICT_PATHS):
                if not self._check_limit(ip, 'strict', self.STRICT_LIMIT, self.STRICT_WINDOW):
                    return HttpResponseForbidden(
                        'Слишком много попыток. Попробуйте позже.',
                        content_type='text/plain'
                    )
            else:
                if not self._check_limit(ip, 'anon', self.ANON_LIMIT, self.ANON_WINDOW):
                    return HttpResponseForbidden(
                        'Слишком много запросов. Попробуйте позже.',
                        content_type='text/plain'
                    )
        
        return self.get_response(request)
    
    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            return xff.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _check_limit(self, ip, prefix, limit, window):
        now = int(time.time())
        window_start = now - (now % window)
        cache_key = f"iprl:{prefix}:{ip}:{window_start}"
        count = cache.get(cache_key, 0)
        if count >= limit:
            return False
        cache.set(cache_key, count + 1, window)
        return True


class BlockCheckMiddleware:
    """Check if requester is blocked by recipient in direct message endpoints."""
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Only check for authenticated POST to conversation endpoints
        if request.user.is_authenticated and request.method == 'POST' and '/messages/' in request.path:
            from .models import UserBlock
            parts = request.path.strip('/').split('/')
            # Path: messages/<username>/
            if len(parts) >= 2 and parts[0] == 'messages':
                username = parts[1]
                if username and username != request.user.username:
                    is_blocked = UserBlock.objects.filter(
                        blocker__username=username, blocked=request.user
                    ).exists()
                    if is_blocked:
                        return HttpResponseForbidden(
                            'Пользователь ограничил возможность отправлять вам сообщения.',
                            content_type='text/plain'
                        )
        
        return self.get_response(request)
