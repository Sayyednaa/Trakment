from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Payment, UserSubscription, Plan, PaymentSettings
from todo.models import SyllabusPreset
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


@user_passes_test(lambda u: u.is_superuser)
def business_syllabuses(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        csv_file = request.FILES.get('csv_file')
        csv_link = request.POST.get('csv_link', '')

        if title and (csv_file or csv_link):
            SyllabusPreset.objects.create(
                title=title,
                description=description,
                csv_file=csv_file,
                csv_link=csv_link
            )
            messages.success(request, f'Syllabus preset "{title}" added successfully.')
            return redirect('business_syllabuses')
        else:
            messages.error(request, 'Please provide a title and either a CSV file or CSV link.')

    presets = SyllabusPreset.objects.all()
    context = {
        'presets': presets,
        'active_tab': 'syllabuses'
    }
    return render(request, 'subscriptions/business_syllabuses.html', context)

@user_passes_test(lambda u: u.is_superuser)
def business_syllabus_delete(request, preset_id):
    preset = get_object_or_404(SyllabusPreset, id=preset_id)
    title = preset.title
    preset.delete()
    messages.success(request, f'Syllabus preset "{title}" deleted successfully.')
    return redirect('business_syllabuses')


@user_passes_test(lambda u: u.is_superuser)
def business_plans(request):
    Plan.objects.get_or_create(name='free_trial', defaults={'price': 0, 'duration_days': 1, 'description': '1-Day Free Trial'})
    Plan.objects.get_or_create(name='basic', defaults={'price': 49, 'duration_days': 30, 'description': 'Basic Plan (₹49/mo)'})
    Plan.objects.get_or_create(name='premium', defaults={'price': 99, 'duration_days': 30, 'description': 'Premium+ (₹99/mo)'})
    Plan.objects.get_or_create(name='yearly', defaults={'price': 999, 'duration_days': 365, 'description': 'Yearly All-Access (₹999/yr)'})

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        plan = get_object_or_404(Plan, id=plan_id)
        price = request.POST.get('price')
        duration_days = request.POST.get('duration_days')
        description = request.POST.get('description', '')

        if price is not None and duration_days:
            plan.price = price
            plan.duration_days = duration_days
            plan.description = description
            plan.save()
            messages.success(request, f'Plan "{plan.get_name_display()}" updated successfully.')
            return redirect('business_plans')
        else:
            messages.error(request, 'Please provide valid price and duration.')

    plans = Plan.objects.all().order_by('price')
    context = {
        'plans': plans,
        'active_tab': 'plans'
    }
    return render(request, 'subscriptions/business_plans.html', context)



# ----------------- PUBLIC FACING VIEWS -----------------


def pricing_view(request):
    Plan.objects.get_or_create(name='basic', defaults={'price': 49, 'duration_days': 30, 'description': 'Basic Plan (₹49/mo)'})
    Plan.objects.get_or_create(name='premium', defaults={'price': 99, 'duration_days': 30, 'description': 'Premium+ (₹99/mo)'})
    Plan.objects.get_or_create(name='yearly', defaults={'price': 999, 'duration_days': 365, 'description': 'Yearly All-Access (₹999/yr)'})
    
    plans = Plan.objects.exclude(name='free_trial').order_by('price')
    
    current_user_plan_price = Decimal('0.00')
    if request.user.is_authenticated and hasattr(request.user, 'subscription') and request.user.subscription.is_valid() and request.user.subscription.plan:
        current_user_plan_price = Decimal(str(request.user.subscription.plan.price))

    return render(request, 'subscriptions/pricing.html', {
        'plans': plans,
        'current_user_plan_price': current_user_plan_price
    })


from decimal import Decimal

@login_required(login_url='/login')
def checkout_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id)
    
    # Calculate prorated upgrade discount if user has active subscription
    has_active_sub = hasattr(request.user, 'subscription') and request.user.subscription.is_valid() and request.user.subscription.plan
    unused_credit = Decimal('0.00')
    days_remaining = 0
    current_plan_name = ''

    if has_active_sub:
        current_sub = request.user.subscription
        current_plan_name = current_sub.plan.get_name_display()
        
        # Prevent purchasing lower tier plans if user already has a higher tier plan
        if plan.price < current_sub.plan.price:
            messages.warning(request, f"You currently have '{current_plan_name}' (₹{current_sub.plan.price}) active. You cannot downgrade to a lower-priced plan.")
            return redirect('pricing')

        now = timezone.now()
        if current_sub.end_date > now:
            days_remaining = (current_sub.end_date - now).days
            total_days = (current_sub.end_date - current_sub.start_date).days or current_sub.plan.duration_days or 30
            if days_remaining > 0 and total_days > 0:
                daily_rate = Decimal(str(current_sub.plan.price)) / Decimal(str(total_days))
                unused_credit = round(daily_rate * Decimal(str(days_remaining)), 2)


    target_price = Decimal(str(plan.price))
    payable_amount = max(Decimal('0.00'), target_price - unused_credit)
    
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

    context = {
        'plan': plan,
        'upi_id': upi_id,
        'payable_amount': payable_amount,
        'unused_credit': unused_credit,
        'days_remaining': days_remaining,
        'current_plan_name': current_plan_name,
        'target_price': target_price,
    }
    return render(request, 'subscriptions/checkout.html', context)

@login_required(login_url='/login')
def subscription_status(request):
    # Backward compatibility redirect to profile where we merged the UI
    return redirect('/profile')

