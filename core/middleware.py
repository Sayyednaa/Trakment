from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import logout

class BlockMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user, 'userprofile'):
            blocked_until = request.user.userprofile.blocked_until
            if blocked_until and blocked_until > timezone.now():
                logout(request)
                return render(request, 'blocked.html', {'blocked_until': blocked_until}, status=403)
                
        return self.get_response(request)
