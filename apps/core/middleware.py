from importlib import import_module

from django.conf import settings
from django.utils.cache import patch_vary_headers
from django.utils.deprecation import MiddlewareMixin


class SplitSessionMiddleware(MiddlewareMixin):
    """Mantiene sesiones separadas para el admin y el sitio público.

    - Para rutas que inician con ADMIN_URL_PREFIX (por defecto '/admin/'),
      usa la cookie 'admin_sessionid' (configurable con ADMIN_SESSION_COOKIE_NAME).
    - Para el resto, usa la cookie estándar de settings.SESSION_COOKIE_NAME.

    Debe ubicarse antes de AuthenticationMiddleware.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        engine = import_module(settings.SESSION_ENGINE)
        self.SessionStore = engine.SessionStore

        self.admin_prefix = getattr(settings, 'ADMIN_URL_PREFIX', '/admin/')
        if not self.admin_prefix.endswith('/'):
            self.admin_prefix += '/'
        self.admin_cookie_name = getattr(settings, 'ADMIN_SESSION_COOKIE_NAME', 'admin_sessionid')

    def _cookie_name_for_request(self, request):
        path = request.path or ''
        if path.startswith(self.admin_prefix):
            return self.admin_cookie_name
        return settings.SESSION_COOKIE_NAME

    def process_request(self, request):
        cookie_name = self._cookie_name_for_request(request)
        session_key = request.COOKIES.get(cookie_name)
        request._session_cookie_name = cookie_name
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
            cookie_name = getattr(request, '_session_cookie_name', settings.SESSION_COOKIE_NAME)
        except AttributeError:
            return response


        if cookie_name in request.COOKIES and empty:
            response.delete_cookie(
                cookie_name,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            return response

        if accessed:
            patch_vary_headers(response, ('Cookie',))

        if not modified and not settings.SESSION_SAVE_EVERY_REQUEST:
            return response

        if empty:
            return response

        response.set_cookie(
            cookie_name,
            request.session.session_key,
            max_age=settings.SESSION_COOKIE_AGE,
            expires=None,
            domain=settings.SESSION_COOKIE_DOMAIN,
            path=settings.SESSION_COOKIE_PATH,
            secure=settings.SESSION_COOKIE_SECURE,
            httponly=settings.SESSION_COOKIE_HTTPONLY,
            samesite=settings.SESSION_COOKIE_SAMESITE,
        )
        return response
