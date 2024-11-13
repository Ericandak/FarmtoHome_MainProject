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

def jobs(request):
    cities = Address_table.objects.values_list('city', flat=True).distinct()
    pending_application = None
    if request.user.is_authenticated:
        user_application = JobApplication.objects.filter(user=request.user).order_by('-applied_at').first()

    print(user_application.status)
    
    context = {
        'cities': cities,
        'user_application': user_application,
        'user_application_status': user_application.status if user_application else None,
    }
    return render(request, 'Delivery/jobs.html',context)
@login_required
def apply_job(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        resume = request.FILES.get('resume')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        city = request.POST.get('city')
        
        
        # Save the application (you'll need to create a JobApplication model)
        JobApplication.objects.create(user=request.user, name=name, resume=resume, email=email, phone_number=phone_number, preferred_city=city,status='pending')
        
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
        assigned_city = job_application.preferred_city
    except JobApplication.DoesNotExist:
        print("No job application found")
        # Handle the case where no job application is found
        assigned_city = None
    if assigned_city:
        print("City is assigned")
        # Filter pending orders for the assigned city
        pending_orders = Order.objects.filter(
            Q(delivery_status='pending') & 
            Q(shipping_address__city=assigned_city)
        ).select_related('shipping_address', 'consumer')
        if pending_orders:
            print("Pending orders found")
        else:
            print("No pending orders found")
        active_orders = Order.objects.filter(
            Q(delivery_status__in=['shipped', 'in_transit']) &
            Q(delivery__delivery_person=request.user)
        ).select_related('shipping_address', 'consumer', 'delivery')
        active_orders_count = active_orders.count()
    else:
        print("No city is assigned")
        # If no city is assigned, don't show any orders
        pending_orders = Order.objects.none()
        active_orders = Order.objects.none()
        active_orders_count = 0
    context = {
        'pending_orders': pending_orders,
        'assigned_city': assigned_city,
        'active_orders': active_orders,
        'active_orders_count': active_orders_count,
    }
    return render(request, 'Delivery/DeliveryIndex.html', context)

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

