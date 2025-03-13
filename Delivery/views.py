from django.shortcuts import render
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from Products.models import Product,Category,Stock,Cart_table,CartItem_table,Review
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from Users.models import Address_table,User
from .models import Delivery
from orders.models import Order
from .models import JobApplication
from Users.models import ShippingAddress
from django.db.models import Q
from .models import DeliveryPerson
from django.conf import settings

def jobs(request):
    # Get unique pincodes from addresses
    pincodes = Address_table.objects.values_list('zip_code', flat=True).distinct()
    pending_application = None
    if request.user.is_authenticated:
        user_application = JobApplication.objects.filter(user=request.user).order_by('-applied_at').first()
    
    context = {
        'pincodes': pincodes,
        'user_application': user_application,
        'user_application_status': user_application.status if user_application else None,
    }
    return render(request, 'Delivery/jobs.html', context)

@login_required
def apply_job(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        resume = request.FILES.get('resume')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        pincode = request.POST.get('pincode')  # Changed from city
        
        JobApplication.objects.create(
            user=request.user,
            name=name,
            resume=resume,
            email=email,
            phone_number=phone_number,
            preferred_pincode=pincode,  # Changed from preferred_city
            status='pending'
        )
        
        messages.success(request, 'Your application has been submitted successfully and is pending review.')
        return redirect('Delivery:jobs')
    
    return redirect('Delivery:jobs')

def job_requests(request):
    job_applications = JobApplication.objects.all().order_by('-applied_at')
    print(f"Number of applications: {job_applications.count()}")
    for app in job_applications:
        print(f"Application: {app.name} - {app.status}")
    return render(request, 'admin/job_requests.html', {'job_applications': job_applications})

@login_required
def deliverindex(request):
    user_email = request.user.email
    try:
        job_application = JobApplication.objects.get(email=user_email, status='approved')
        delivery_person, created = DeliveryPerson.objects.get_or_create(
            user=request.user,
            defaults={'primary_pincode': job_application.preferred_pincode}
        )
        
        # Get orders for both pincodes
        pincode_filter = Q(shipping_address__zip_code=delivery_person.primary_pincode)
        if delivery_person.secondary_pincode:
            pincode_filter |= Q(shipping_address__zip_code=delivery_person.secondary_pincode)

        pending_orders = Order.objects.filter(
            Q(delivery_status='pending') & pincode_filter
        ).select_related('shipping_address', 'consumer')

        active_orders = Order.objects.filter(
            Q(delivery_status__in=['shipped', 'in_transit']) &
            Q(delivery__delivery_person=request.user)
        ).select_related('shipping_address', 'consumer', 'delivery')

        # Get available pincodes from ShippingAddress
        available_pincodes = ShippingAddress.objects.values_list('zip_code', flat=True).distinct()

        context = {
            'pending_orders': pending_orders,
            'active_orders': active_orders,
            'delivery_person': delivery_person,
            'available_pincodes': available_pincodes,
            'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
        }
        return render(request, 'Delivery/DeliveryIndex.html', context)
    except JobApplication.DoesNotExist:
        messages.error(request, 'No approved job application found.')
        return redirect('home')

@login_required
def update_delivery_pincodes(request):
    if request.method == 'POST':
        primary_pincode = request.POST.get('primary_pincode')
        secondary_pincode = request.POST.get('secondary_pincode')
        
        if primary_pincode:
            delivery_person = DeliveryPerson.objects.get(user=request.user)
            delivery_person.primary_pincode = primary_pincode
            if secondary_pincode and secondary_pincode != primary_pincode:
                delivery_person.secondary_pincode = secondary_pincode
            else:
                delivery_person.secondary_pincode = None
            delivery_person.save()
            messages.success(request, 'Delivery areas updated successfully')
        else:
            messages.error(request, 'Please select at least one pincode')
    return redirect('Delivery:deliverindex')

@login_required
def start_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    delivery, created = Delivery.objects.get_or_create(order=order, delivery_person=request.user)
    
    if delivery.status == 'assigned':
        delivery.start_delivery()
        order.delivery_status = 'shipped'
        order.save()
    messages.success(request, 'Delivery started successfully')
    return redirect('Delivery:deliverindex')  # Redirect back to the delivery index page

@login_required
def complete_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    delivery = get_object_or_404(Delivery, order=order, delivery_person=request.user)
    delivery.complete_delivery()
    messages.success(request, 'Delivery completed successfully')
    return redirect('Delivery:deliverindex')

@login_required
def fail_delivery(request, delivery_id):
    if request.method == 'POST':
        delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
        reason = request.POST.get('reason', '')
        delivery.fail_delivery(reason)
    return redirect('Delivery:deliverindex')

def order_history(request):
    completed_deliveries = Delivery.objects.filter(
        delivery_person=request.user,
        status='delivered'
    ).order_by('-completed_at')
    
    context = {
        'completed_deliveries': completed_deliveries
    }
    return render(request, 'Delivery/order_history.html', context)

@login_required
def update_location(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        delivery_person = DeliveryPerson.objects.get(user=request.user)
        delivery_person.update_location(latitude, longitude)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

