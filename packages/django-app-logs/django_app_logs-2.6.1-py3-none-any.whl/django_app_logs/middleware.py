from threading import local

_request_context = local()


class RequestContextMiddleware:
    """
    Middleware qui capture et stocke les informations de contexte de la requête
    (user, IP, User-Agent) dans un thread-local pour utilisation par les signaux.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Stocker les informations dans le thread-local
        _request_context.user = getattr(request, 'user', None)
        _request_context.ip_address = self.get_client_ip(request)
        _request_context.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]

        response = self.get_response(request)

        return response

    @staticmethod
    def get_client_ip(request):
        """Récupère l'IP client, gérant les proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def get_current_user():
        """Récupère l'utilisateur courant."""
        user = getattr(_request_context, 'user', None)
        if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
            return user
        return None

    @staticmethod
    def get_ip_address():
        """Récupère l'adresse IP."""
        return getattr(_request_context, 'ip_address', None)

    @staticmethod
    def get_user_agent():
        """Récupère le User-Agent."""
        return getattr(_request_context, 'user_agent', '')
