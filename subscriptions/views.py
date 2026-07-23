from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Payment, UserSubscription, Plan, PaymentSettings
from django.contrib.auth.models import User
from django.contrib import messages

# ----------------- BUSINESS DASHBOARD VIEWS -----------------

@user_passes_test(lambda u: u.is_superuser)
def business_overview(request):
    total_users = User.objects.count()
    active_subscriptions = UserSubscription.objects.filter(is_active=True, end_date__gte=timezone.now()).count()
    
    approved_payments = Payment.objects.filter(status='approved')
    total_revenue = sum(p.plan.price for p in approved_payments if p.plan)
    
    pending_payments = Payment.objects.filter(status='pending').count()
    
    recent_payments = Payment.objects.order_by('-created_at')[:5]
    
    if request.method == 'POST' and 'update_upi' in request.POST:
        new_upi = request.POST.get('upi_id')
        settings_obj, _ = PaymentSettings.objects.get_or_create(id=1)
        settings_obj.upi_id = new_upi
        settings_obj.save()
        messages.success(request, 'UPI ID updated successfully.')
        return redirect('business_overview')

    settings_obj = PaymentSettings.objects.first()
    current_upi_id = settings_obj.upi_id if settings_obj else "paytm.slax2x4@pty"

    context = {
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'recent_payments': recent_payments,
        'current_upi_id': current_upi_id,
        'active_tab': 'overview'
    }
    return render(request, 'subscriptions/business_overview.html', context)

@user_passes_test(lambda u: u.is_superuser)
def business_users(request):
    users = User.objects.select_related('subscription', 'subscription__plan').all().order_by('-date_joined')
    
    context = {
        'users': users,
        'active_tab': 'users'
    }
    return render(request, 'subscriptions/business_users.html', context)

@user_passes_test(lambda u: u.is_superuser)
def business_payments(request):
    status_filter = request.GET.get('status', 'all')
    
    payments = Payment.objects.all().order_by('-created_at')
    
    if status_filter != 'all':
        payments = payments.filter(status=status_filter)
        
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'active_tab': 'payments'
    }
    return render(request, 'subscriptions/business_payments.html', context)

@user_passes_test(lambda u: u.is_superuser)
def business_payment_review(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '')
        
        payment.admin_notes = admin_notes
        
        if action == 'approve':
            payment.status = 'approved'
            payment.save() # This triggers the signal to create/update UserSubscription
            messages.success(request, f'Payment from {payment.user.username} approved successfully.')
        elif action == 'reject':
            payment.status = 'rejected'
            payment.save()
            messages.error(request, f'Payment from {payment.user.username} rejected.')
            
        return redirect('business_payments')
        
    context = {
        'payment': payment,
        'active_tab': 'payments'
    }
    return render(request, 'subscriptions/business_payment_review.html', context)


# ----------------- PUBLIC FACING VIEWS -----------------

def pricing_view(request):
    Plan.objects.get_or_create(name='basic', defaults={'price': 49, 'duration_days': 30, 'description': 'Basic Plan (₹49/mo)'})
    Plan.objects.get_or_create(name='premium', defaults={'price': 99, 'duration_days': 30, 'description': 'Premium+ (₹99/mo)'})
    Plan.objects.get_or_create(name='yearly', defaults={'price': 999, 'duration_days': 365, 'description': 'Yearly All-Access (₹999/yr)'})
    
    plans = Plan.objects.exclude(name='free_trial').order_by('price')
    return render(request, 'subscriptions/pricing.html', {'plans': plans})

@login_required(login_url='/login')
def checkout_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    
    if request.method == 'POST':
        utr_id = request.POST.get('utr_id')
        screenshot = request.FILES.get('screenshot')
        
        if utr_id:
            Payment.objects.create(
                user=request.user,
                plan=plan,
                utr_id=utr_id,
                screenshot=screenshot,
                status='pending'
            )
            messages.success(request, 'Your payment has been submitted and is under review.')
            return redirect('/profile')
        else:
            messages.error(request, 'Please provide the UTR transaction ID.')

    settings_obj = PaymentSettings.objects.first()
    upi_id = settings_obj.upi_id if settings_obj else "paytm.slax2x4@pty"

    return render(request, 'subscriptions/checkout.html', {'plan': plan, 'upi_id': upi_id})

@login_required(login_url='/login')
def subscription_status(request):
    # Backward compatibility redirect to profile where we merged the UI
    return redirect('/profile')
