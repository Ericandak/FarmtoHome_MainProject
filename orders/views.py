from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
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


User = get_user_model()
@login_required
@transaction.atomic
def checkout(request):
    try:
        cart = Cart_table.objects.get(user=request.user)
        cart_items = CartItem_table.objects.filter(cart=cart)
    except Cart_table.DoesNotExist:
        return redirect('Products:usercart')

    if not cart_items.exists():
        return redirect('Products:usercart')

    try:
        existing_address = Address_table.objects.get(user=request.user)
    except Address_table.DoesNotExist:
        existing_address = None

    if request.method == 'POST':
        use_existing_address = request.POST.get('use_existing_address') == 'on'
        
        if use_existing_address and existing_address:
            shipping_data = {
                'full_name': f"{request.user.first_name} {request.user.last_name}",
                'address': existing_address.address,
                'city': existing_address.city,
                'zip_code': existing_address.zip_code,
                'state_id': existing_address.state.id,  # Store state ID instead of State object
            }
        else:
            state = State.objects.get(id=request.POST.get('state'))
            shipping_data = {
                'full_name': request.POST.get('full_name'),
                'address': request.POST.get('address'),
                'city': request.POST.get('city'),
                'zip_code': request.POST.get('zip_code'),
                'state_id': state.id,  # Store state ID instead of State object
            }

        if all(shipping_data.values()):
            # Store shipping data in session for later use
            request.session['shipping_data'] = shipping_data

            # Process the order
            order = process_order(request, shipping_data)
            if order:
                # Initiate payment
                return initiate_payment(request, order.id)
            else:
                return redirect('Products:usercart')
        else:
            messages.error(request, 'Please fill in all required fields.')

    states = State.objects.all()
    context = {
        'cart_items': cart_items,
        'total': sum(item.subtotal for item in cart_items),
        'existing_address': existing_address,
        'states': states,
    }
    return render(request, 'orders/checkout.html', context)


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

            return redirect('orders:order_confirmation', order_id=order.id)
        except Order.DoesNotExist:
            messages.error(request, 'Order not found. Please contact support.')
    else:
        # Payment failed
        messages.error(request, 'Payment failed. Please try again.')
    
    return redirect('orders:checkout')

@transaction.atomic
def process_order(request, shipping_data):
    cart = Cart_table.objects.get(user=request.user)
    cart_items = CartItem_table.objects.filter(cart=cart)
    
    # Check stock availability
    for cart_item in cart_items:
        stock = Stock.objects.get(product=cart_item.product)
        if stock.quantity < cart_item.quantity:
            messages.error(request, f'Not enough stock for {cart_item.product.name}. Please update your cart.')
            return None

    # Get the State object from the ID
    state = State.objects.get(id=shipping_data['state_id'])

    # Create shipping address
    shipping_address = ShippingAddress.objects.create(
        user=request.user,
        full_name=shipping_data['full_name'],
        address=shipping_data['address'],
        city=shipping_data['city'],
        zip_code=shipping_data['zip_code'],
        state=state  # Use the State object here
    )

    # Create the order
    order = Order.objects.create(
        consumer=request.user,
        shipping_address=shipping_address,
        total_amount=sum(item.subtotal for item in cart_items)
    )

    # Create order items
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            total_price=cart_item.subtotal
        )

    return order

def order_confirmation(request,order_id):
    order = Order.objects.get(id=order_id)
    notify_admin('order_success', f"New order #{order.id} placed for ${order.total_amount}")
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
