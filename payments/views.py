from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from .razorpay_client import client
from .models import Payment, PaymentMethod
from django.contrib import messages
from .razorpay_client import client
from orders.models import Order
from django.db import transaction

def create_order(amount, currency='INR'):
    return client.order.create({
        'amount': int(float(amount )* 100),  # Razorpay expects amount in paise
        'currency': currency,
        'payment_capture': '1'
    })

@transaction.atomic
def initiate_payment(request, order_id):
    try:
        order = Order.objects.get(id=order_id, consumer=request.user)
        print(f"Order found: {order}")
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('orders:checkout')
    amount_in_paise = int(float(order.total_amount) * 100)
    print(f"Amount in paise: {amount_in_paise}")

    razorpay_order = create_order(order.total_amount)
        
    razorpay_method, _ = PaymentMethod.objects.get_or_create(name='Razorpay')
    
    payment = Payment.objects.create(
        order=order,
        payment_method=razorpay_method,
        amount=order.total_amount,
        status='pending',
        gateway_order_id=razorpay_order['id']
    )
    
    context = {
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': client.auth[0],
        'callback_url': request.build_absolute_uri(reverse('payments:callback')),
        'amount': order.total_amount,
        'amount_in_paise': int(float(order.total_amount) * 100),  # Add this line
        'currency': 'INR',
        'payment_id': payment.id,
    }
    return render(request, 'payments/payment.html', context)

@csrf_exempt
@transaction.atomic
def payment_callback(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')
        internal_payment_id = request.POST.get('payment_id', '')
        
        params_dict = {
            'razorpay_payment_id': payment_id,
            'razorpay_order_id': razorpay_order_id,
            'razorpay_signature': signature
        }
        
        try:
            client.utility.verify_payment_signature(params_dict)
            payment = Payment.objects.get(id=internal_payment_id)
            payment.status = 'completed'
            payment.gateway_payment_id = payment_id
            payment.gateway_signature = signature
            payment.save()

            # Update order status
            order = payment.order
            order.payment_status = 'completed'
            order.save()

            messages.success(request, 'Payment successful and order confirmed.')
            return redirect('orders:payment_callback')
        except Exception as e:
            payment = Payment.objects.get(id=internal_payment_id)
            payment.status = 'failed'
            payment.save()
            messages.error(request, f'Payment failed: {str(e)}. Please try again.')
            return redirect('orders:checkout')
    return redirect('orders:checkout')
