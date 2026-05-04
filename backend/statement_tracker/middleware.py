from django.contrib.auth import logout
from django.utils.timezone import now

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            current_time = now().timestamp()
            last_activity = request.session.get('last_activity')

            # 30 minutes inactivity limit
            timeout = 30 * 60

            if last_activity:
                if current_time - last_activity > timeout:
                    logout(request)
                    request.session.flush()

            request.session['last_activity'] = current_time

        return self.get_response(request)