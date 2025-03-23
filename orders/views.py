from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction, OperationalError
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from payments.views import initiate_payment, payment_callback
from .models import Order, OrderItem
from Products.models import CartItem_table,Cart_table,Stock
from Users.models import ShippingAddress, Address_table, State
from django.core.serializers.json import DjangoJSONEncoder
import json
from notifications.utils import notify_admin
from django.shortcuts import render
from .models import Milestone, UserMilestone
from .utils import check_order_milestone
from django.conf import settings
import time


User = get_user_model()
@login_required
@transaction.atomic
def checkout(request):
    max_attempts = 3
    attempt = 0
    while attempt < max_attempts:
        try:
            with transaction.atomic():
                cart = Cart_table.objects.get(user=request.user)
                cart_items = CartItem_table.objects.filter(cart=cart)
                
                if not cart_items.exists():
                    messages.error(request, 'Your cart is empty')
                    return redirect('Products:usercart')
                
                # Calculate cart total first - do this before any other calculations
# Calculate cart total first - do this before any other calculations
                cart_total = sum(item.subtotal for item in cart_items)

                # Initialize total_after_discount with cart_total
                total_after_discount = cart_total

                # Get coupon and discount information from URL parameters
                coupon_code = request.GET.get('coupon')
                discount_amount = request.GET.get('discount', '0')
                final_total = request.GET.get('final_total')
                print(coupon_code)
                print(discount_amount)
                print(final_total)
                
                try:
                    discount = float(discount_amount)
                except (ValueError, TypeError):
                    discount = 0
                
                # Calculate discount if coupon is valid
                try:
                    if final_total:
                        print(final_total)
                        total_after_discount = float(final_total)
                        print(total_after_discount)
                    else:
                        total_after_discount = cart_total
                except (ValueError, TypeError):
                    total_after_discount = cart_total
                
                if coupon_code:
                    coupon = UserMilestone.objects.filter(
                        user=request.user,
                        coupon_code=coupon_code,
                        is_used=False,
                        expiry_date__gt=timezone.now()
                    ).first()
                    
                    if coupon:
                        if final_total:
                            # Convert final_total to Decimal to match cart_total type
                            from decimal import Decimal
                            total_after_discount = Decimal(final_total)
                            # Calculate what the discount must have been
                            discount = cart_total - total_after_discount
                            print(f"Using provided final_total: {total_after_discount}, calculated discount: {discount}")
                        else:
                            # Otherwise calculate the discount
                            print(coupon.milestone.discount_percentage)
                            # Convert percentage to Decimal before calculation
                            discount_percentage = Decimal(coupon.milestone.discount_percentage)
                            discount = (cart_total * discount_percentage) / Decimal('100')
                            total_after_discount = cart_total - discount
                            print(f"Cart total: {cart_total}, Discount: {discount}, Total after discount: {total_after_discount}")
                    print(f"After coupon processing: total_after_discount={total_after_discount}")
                if request.method == 'POST':
                    # Validate location data
                    latitude = request.POST.get('latitude')
                    longitude = request.POST.get('longitude')
                    discounted_total = request.POST.get('discounted_total')
                    coupon_code_post = request.POST.get('coupon_code')
                    print("discounted:",discounted_total)
                    if discounted_total:
                            from decimal import Decimal
                            total_after_discount = Decimal(discounted_total)
                            print(f"Using discounted_total from form: {total_after_discount}")
                    if coupon_code_post:
                        coupon_code = coupon_code_post
                    
                    if not (latitude and longitude):
                        messages.error(request, 'Please select a delivery location on the map')
                        return redirect('orders:checkout')

                    use_existing_address = request.POST.get('use_existing_address') == 'on'
                    
                    if use_existing_address:
                        existing_address = Address_table.objects.filter(user=request.user).first()
                        if existing_address:
                            shipping_data = {
                                'full_name': f"{request.user.first_name} {request.user.last_name}",
                                'address': existing_address.address,
                                'city': existing_address.city,
                                'zip_code': existing_address.zip_code,
                                'state_id': existing_address.state.id,
                                'latitude': latitude,
                                'longitude': longitude
                            }
                        else:
                            messages.error(request, 'No existing address found')
                            return redirect('orders:checkout')
                    else:
                        try:
                            print("total:",total_after_discount)
                            state = State.objects.get(id=request.POST.get('state'))
                            shipping_data = {
                                'full_name': request.POST.get('full_name'),
                                'address': request.POST.get('address'),
                                'city': request.POST.get('city'),
                                'zip_code': request.POST.get('zip_code'),
                                'state_id': state.id,
                                'latitude': latitude,
                                'longitude': longitude
                            }
                        except State.DoesNotExist:
                            messages.error(request, 'Invalid state selected')
                            return redirect('orders:checkout')
                    print("total before shiiping:",total_after_discount)
                    if all(shipping_data.values()):
                        # Pass coupon information to process_order
                        print(f"Before process_order: coupon_code={coupon_code}, total_after_discount={total_after_discount}")
                        order = process_order(request, shipping_data, coupon_code, total_after_discount)
                        if order:
                            return initiate_payment(request, order.id)
                        else:
                            messages.error(request, 'Error processing order')
                            return redirect('orders:checkout')
                    
                    messages.error(request, 'Please fill in all required fields')
                    return redirect('orders:checkout')

                # For GET requests, show the checkout page with discount applied
                context = {
                    'cart_items': cart_items,
                    'subtotal': cart_total,
                    'discount': discount,
                    'total': total_after_discount,
                    'coupon_code': coupon_code,
                    'existing_address': Address_table.objects.filter(user=request.user).first(),
                    'states': State.objects.all(),
                    'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY,
                }
                return render(request, 'orders/checkout.html', context)
                
        except OperationalError as e:
            if 'database is locked' in str(e):
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(0.5)  # Wait before retrying
                    continue
            messages.error(request, 'Transaction error. Please try again.')
            return redirect('Products:usercart')
            
        except Cart_table.DoesNotExist:
            messages.error(request, 'Your cart is empty')
            return redirect('Products:usercart')
            
    messages.error(request, 'Service temporarily unavailable. Please try again.')
    return redirect('Products:usercart')


@login_required
@transaction.atomic
def order_payment_callback(request):
    payment_callback(request)
    if any(message.tags == 'success' for message in messages.get_messages(request)):
        try:
            # Get the latest order for the user
            order = Order.objects.filter(consumer=request.user).latest('order_date')
            
            # Update stock
            for order_item in order.items.all():
                stock = Stock.objects.get(product=order_item.product)
                stock.quantity -= order_item.quantity
                stock.save()

            # Clear the user's cart
            cart = Cart_table.objects.get(user=request.user)
            CartItem_table.objects.filter(cart=cart).delete()
            cart.delete()
            
            # Check for milestone achievements
            if order.payment_status == 'completed':
                user_milestone = check_order_milestone(request.user)
                if user_milestone:
                    messages.success(
                        request,
                        f"🎉 Congratulations! You've unlocked a {user_milestone.milestone.discount_percentage}% discount! "
                        f"Use code: {user_milestone.coupon_code}"
                    )

            return redirect('orders:order_confirmation', order_id=order.id)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found. Please contact support.')
    else:
        # Payment failed
        messages.error(request, 'Payment failed. Please try again.')
    
    return redirect('orders:checkout')

@transaction.atomic
def process_order(request, shipping_data, coupon_code=None, discounted_total=None):
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        try:
            with transaction.atomic():
                # Create shipping address
                shipping_address = ShippingAddress.objects.create(
                    user=request.user,
                    **shipping_data
                )

                cart = Cart_table.objects.select_for_update().get(user=request.user)
                cart_items = CartItem_table.objects.select_for_update().filter(cart=cart)
                
                # Verify stock availability
                for cart_item in cart_items:
                    stock = Stock.objects.select_for_update().get(product=cart_item.product)
                    if stock.quantity < cart_item.quantity:
                        raise ValueError(f'Not enough stock for {cart_item.product.name}')

                # Create order with discounted total if provided
                if discounted_total is not None:
                    try:
                        total_amount = float(discounted_total)
                        print(f"Using discounted total: {total_amount}")
                    except (ValueError, TypeError):
                        total_amount = sum(item.subtotal for item in cart_items)
                        print(f"Failed to convert discounted total, using original: {total_amount}")
                else:
                    total_amount = sum(item.subtotal for item in cart_items)
                    print(f"No discount provided, using original total: {total_amount}")
                
                
                order = Order.objects.create(
                    consumer=request.user,
                    shipping_address=shipping_address,
                    total_amount=total_amount
                )
                print(f"Created order with total_amount: {order.total_amount}")
                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        total_price=cart_item.subtotal
                    )
                
                # Mark coupon as used if provided
                if coupon_code:
                    coupon = UserMilestone.objects.filter(
                        user=request.user,
                        coupon_code=coupon_code,
                        is_used=False
                    ).first()
                    
                    if coupon:
                        coupon.is_used = True
                        coupon.save()

                return order

        except OperationalError as e:
            if 'database is locked' in str(e):
                attempt += 1
                if attempt < max_attempts:
                    time.sleep(0.5)
                    continue
            raise
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return None

    return None

def order_confirmation(request,order_id):
    order = Order.objects.get(id=order_id)
    notify_admin('order_success', f"New order #{order.id} placed for ${order.total_amount}")
    if order.payment_status == 'completed':
                    user_milestone=check_order_milestone(request.user)
                    if user_milestone:
                        messages.success(
                        request,
                        f"🎉 Congratulations! You've unlocked a {user_milestone.milestone.discount_percentage}% discount! "
                        f"Use code: {user_milestone.coupon_code}"
                    )
    context = {
        'order': order,
        'order_id': order_id
    }
    return render(request, 'orders/order_processing.html', context)



@login_required
def user_orders(request):
    cons = request.user
    orders = Order.objects.filter(consumer=request.user).order_by('-order_date')
    
    # Prefetch related order items to optimize database queries
    orders = orders.prefetch_related('items')
    
    return render(request, 'orders/user_orders.html', {'orders': orders, 'username': cons})

@login_required
def cancel_order(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id, consumer=request.user)
        if order.can_be_cancelled():
            order.delivery_status = 'cancelled'
            order.save()
            messages.success(request, f'Order #{order.id} has been cancelled successfully.')
        else:
            messages.error(request, 'This order cannot be cancelled.')
    return redirect('orders:user_orders')

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import Product, Order, OrderItem

@login_required
def seller_dashboard(request):
    seller = request.user
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)  # Last 30 days

    # Total sales
    total_sales = OrderItem.objects.filter(
        product__seller=seller,
        order__order_date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_price'))['total'] or 0

    # Total orders
    total_orders = Order.objects.filter(
        items__product__seller=seller,
        order_date__range=(start_date, end_date)
    ).distinct().count()

    # Top selling products
    top_products = Product.objects.filter(seller=seller).annotate(
        total_sales=Sum('orderitem__quantity')
    ).order_by('-total_sales')[:5]

    # Recent orders
    recent_orders = Order.objects.filter(
        items__product__seller=seller
    ).distinct().order_by('-order_date')[:10]

    # Sales chart data
    sales_data = []
    sales_dates = []
    for i in range(30):
        date = end_date - timedelta(days=i)
        sales = OrderItem.objects.filter(
            product__seller=seller,
            order__order_date__date=date
        ).aggregate(total=Sum('total_price'))['total'] or 0
        sales_data.append(sales)
        sales_dates.append(date.strftime('%Y-%m-%d'))

    # Orders chart data
    order_data = []
    order_dates = []
    for i in range(30):
        date = end_date - timedelta(days=i)
        orders = Order.objects.filter(
            items__product__seller=seller,
            order_date__date=date
        ).distinct().count()
        order_data.append(orders)
        order_dates.append(date.strftime('%Y-%m-%d'))

    context = {
        'seller': seller,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'top_products': top_products,
        'recent_orders': recent_orders,
        'sales_data_json': json.dumps(sales_data, cls=DjangoJSONEncoder),
        'sales_dates_json': json.dumps(sales_dates, cls=DjangoJSONEncoder),
        'order_data_json': json.dumps(order_data, cls=DjangoJSONEncoder),
        'order_dates_json': json.dumps(order_dates, cls=DjangoJSONEncoder),
    }

    return render(request, 'orders/sellerdashboard.html', context)

def milestone_progress(request):
    user = request.user
    order_count = user.orders.filter(payment_status='completed').count()
    milestones = Milestone.objects.all()
    achieved_milestones = UserMilestone.objects.filter(user=user)
    
    # Get active (unused) coupons
    active_coupons = UserMilestone.objects.filter(
        user=user,
        is_used=False,
        expiry_date__gt=timezone.now()
    )

    context = {
        'order_count': order_count,
        'milestones': milestones,
        'achieved_milestones': achieved_milestones,
        'active_coupons': active_coupons
    }
    return render(request, 'Orders/milestone_progress.html', context)
