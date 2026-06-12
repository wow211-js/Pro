from django.db import OperationalError

from .models import VisitorSession, hash_ip


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith('/static/'):
            return response

        if not request.user.is_authenticated:
            return response

        try:
            if not request.session.session_key:
                request.session.create()

            ip_hash = hash_ip(self._get_ip_address(request))

            VisitorSession.objects.update_or_create(
                session_key=request.session.session_key,
                defaults={
                    'user': request.user,
                    'ip_hash': ip_hash or '',
                },
            )
        except OperationalError:
            pass
        return response

    @staticmethod
    def _get_ip_address(request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
