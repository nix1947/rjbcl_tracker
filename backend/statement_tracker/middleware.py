from django.contrib.auth import logout
from django.utils.timezone import now


class SecureSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = now().timestamp()
            last_activity = request.session.get('last_activity')

            # 1. Check for Inactivity (Session Life Cycle Management)
            timeout = 30 * 60
            if last_activity and (current_time - last_activity > timeout):
                logout(request)
                return self.get_response(request)

            # 2. Bind Session to Identity (User-Session Association)
            current_user_agent = request.META.get('HTTP_USER_AGENT', '')
            current_ip = self.get_client_ip(request)

            stored_user_agent = request.session.get('initial_user_agent')
            stored_ip = request.session.get('initial_ip')

            if stored_user_agent is None:
                # First time: store the browser and IP profile
                request.session['initial_user_agent'] = current_user_agent
                request.session['initial_ip'] = current_ip
            elif stored_user_agent != current_user_agent or stored_ip != current_ip:
                # Potential Session Hijacking detected
                logout(request)
                request.session.flush()
                return self.get_response(request)

            request.session['last_activity'] = current_time

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')