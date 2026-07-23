from django.shortcuts import redirect
from django.urls import reverse
from .models import UserSubscription, Plan
from django.utils import timezone

class SubscriptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            # First, check if the user has any subscription record.
            # If not, let's create a 1-day free trial.
            sub, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timezone.timedelta(days=1),
                    'is_active': True
                }
            )
            if created:
                free_plan, _ = Plan.objects.get_or_create(
                    name='free_trial', 
                    defaults={'price': 0, 'duration_days': 1, 'description': '1-Day Free Trial'}
                )
                sub.plan = free_plan
                sub.save()

            path = request.path
            
            # Define premium+ paths (₹99 or ₹999 required)
            premium_paths = ['/chat/', '/leaderboard/', '/data/']
            is_premium_path = any(path.startswith(p) for p in premium_paths)
            
            # Define basic paths (Any plan required)
            basic_paths = ['/time/', '/todo/', '/notes/', '/revision/', '/omr/', '/test/', '/diary/', '/password/']
            is_basic_path = any(path.startswith(p) for p in basic_paths)

            if is_premium_path or is_basic_path:
                is_valid = sub.is_valid()
                
                if not is_valid:
                    # Subscription expired
                    return redirect('pricing')

                if is_premium_path:
                    # Must be premium or yearly
                    if sub.plan.name not in ['premium', 'yearly']:
                        return redirect('pricing')

        response = self.get_response(request)
        return response
