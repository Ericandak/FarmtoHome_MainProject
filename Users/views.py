
# Create your views here.
from django.shortcuts import render,redirect,reverse,get_object_or_404
from django.views.decorators.cache import never_cache
from django.contrib.auth import get_user_model
from django.db.models import Q,Sum
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
import pyotp
from django.core.mail import send_mail
from django.db.models import Exists, OuterRef
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_log,logout
from  django.contrib.auth.hashers import make_password
from .models import Address_table,State,Role,SellerDetails,ChatMessage
from Products.models import Category,Product,CartItem_table,Cart_table,Review
from django.db import IntegrityError
from django.views.decorators.http import require_GET
from allauth.account.utils import user_username
from django.templatetags.static import static
from django.db.models import Sum
from django.db.models.functions import TruncMonth,TruncDate
from orders.models import Order,OrderItem
from django.template.loader import render_to_string
import json
from django.conf import settings
from notifications.models import Notification
from django.utils.html import strip_tags
from django.utils import timezone
from .models import LicenseAuthenticationRequest
from datetime import timedelta
from django.db.models import Avg,Count
from django.contrib.auth.decorators import user_passes_test
from Delivery.models import JobApplication
from django.db import transaction



# Create your views here.
User = get_user_model()

def Registration(request):
    return render(request, 'Users/Login.html')

def UserRegistration(request):
    if request.method == 'POST':
        # Retrieve form data
        request.session['registration_data'] = {
            'first_name': request.POST.get('first-name'),
            'last_name': request.POST.get('last-name'),
            'email': request.POST.get('your_email'),
            'phone': request.POST.get('phone'),
            'password': request.POST.get('your_cpassword'),
        }
        reg=request.session.get('registration_data')
        email=reg['email']
        if User.objects.filter(email=email).exists():
            error_message = "Email is already registered."
            cont = {
                'background_image_url': static('assets/img/crops.jpg'),
                'error_message': error_message
                }
            return render(request, 'Users/Registration.html', cont)
        else:
        # Redirect to send OTP email
            return redirect('send_otp_email')
    context = {
        'background_image_url': static('assets/img/crops.jpg')
        }

    return render(request, 'Users/Registration.html',context)
    


def send_otp_email(request):
    # Retrieve registration data from session
    registration_data = request.session.get('registration_data')
    if not registration_data:
        return redirect('user_registration')  # Redirect to registration if session data is missing

    # Generate OTP using pyotp library
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()
    request.session['otp']=otp
    # Send OTP via email (example using Django's send_mail)
    subject = 'OTP Verification'
    message = f'Your OTP for registration is: {otp}'
    from_email = 'farmtohome584@gmail.com'  # Replace with your email
    to_email = registration_data['email']  # Use the email provided in registration form

    send_mail(subject, message, from_email, [to_email])

    # Pass OTP to template for verification
    context = {
        'otp': otp,
        'email': to_email,  # Passing email to pre-fill the form (optional)
    }

    return render(request, 'Users/send_otp_email.html', context)



def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_email = request.POST.get('email')  # Retrieve email from the form

        # Retrieve OTP from session
        stored_otp = request.session.get('otp')
        if stored_otp is None:
            messages.error(request, 'OTP expired. Please try again.')
            return redirect('user_registration')  # Redirect to registration page if OTP is expired

        # Validate OTP
        if user_otp == stored_otp:
            # Save registration data to database
            registration_data = request.session.get('registration_data')
            suffix = random.randint(1000, 9999)  # Adjust range as needed
            username = registration_data['first_name'] + str(suffix)
            while User.objects.filter(username=username).exists():
              suffix = random.randint(1000, 9999)  # Generate new suffix
              username = registration_data['first_name'] + str(suffix)
       # Check if the username already exists
            
            if registration_data:
                try:
                # Fetch the Role instance for 'Customer'
                    customer_role = Role.objects.get(name='Customer')
                except Role.DoesNotExist:
                    messages.error(request, 'Role "Customer" not found. Please contact support.')
                    return redirect('user_registration')

                hashed_password = make_password(registration_data['password'])
                # Assuming you have a model named `User` for user registration
                new_user = User.objects.create(
                    username=username,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone'],
                    password=hashed_password
                )
                new_user.role.set([customer_role])
                # Clear session data after registration
                del request.session['registration_data']
                del request.session['otp']
                
                messages.success(request, 'Registration successful!')
                return redirect('Login')  # Redirect to home or login page after successful registration
            else:
                messages.error(request, 'Registration data not found. Please try again.')
                return redirect('user_registration')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('user_registration')  # Redirect to registration page if OTP is incorrect

    return render(request, 'Users/verify_otp.html')
def Login(request):
    if request.user.is_authenticated:
        # Check if the user just completed social login
        if 'socialaccount_login' in request.session:
            del request.session['socialaccount_login']

        if not request.user.role.exists():
            customer_role, created = Role.objects.get_or_create(name='Customer')
            request.user.role.add(customer_role)
            request.user.save()

        try:
            address = Address_table.objects.get(user=request.user)
            if address.state is None:
                return redirect('stateentry')
        except Address_table.DoesNotExist:
            return redirect('stateentry')
        return redirect('home')
    if request.method == 'POST':
        email = request.POST.get('your_email')
        password = request.POST.get('your_password')
        print(f"Attempting login with email: {email}")

        # Check if the user exists in the database
        try:
            user_obj = User.objects.get(email=email)
            print(f"User found: {user_obj.username}, Email: {user_obj.email}")
        except User.DoesNotExist:
            print(f"No user found with email: {email}")
            user_obj = None

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            print(f"Authentication successful for user: {user.username}")
            auth_log(request, user)
            request.session['username'] = user.username
            request.session.save()
            print(f"Session set in Login: {request.session.get('username')}")
            roles = user.role.all()
            role_names = list(roles.values_list('name', flat=True))
            print(f"User roles: {role_names}")

            if 'Admin' in role_names:
                return redirect('adminlog')
            elif 'delivery' in role_names:
                return redirect('Delivery:deliverindex')
            elif 'Customer' in role_names or 'Seller' in role_names:
                return handle_customer_seller_login(user, role_names)
            else:
                error_message = "User role not recognized."
                return render(request, 'Users/Login.html', {'error': error_message})
        else:
            print("Authentication failed")
            if user_obj:
                print("User exists but authentication failed. Possible password mismatch.")
            error_message = "Invalid email or password."
            return render(request, 'Users/Login.html', {'error': error_message})

    return render(request, 'Users/Login.html')

def handle_customer_seller_login(user, role_names):
    if 'Customer' in role_names:
        try:
            address = Address_table.objects.get(user=user)
            if address.state is None:
                return redirect('stateentry')
            elif not address.address or not address.city or not address.zip_code:
                return redirect('address_entry')
            elif 'Seller' in role_names:
                return handle_seller_part(user)
            else:
                return redirect('home')
        except Address_table.DoesNotExist:
            return redirect('stateentry')
    elif 'Seller' in role_names:
        return handle_seller_part(user)

def handle_seller_part(user):
    try:
        seller_details = SellerDetails.objects.get(user=user)
        if seller_details.state is None:
            return redirect('stateentry')
        elif not seller_details.FarmAddress or not seller_details.Farmcity or not seller_details.Farmzip_code:
            return redirect('SellerDetails')
        else:
            return redirect('SellerHome')
    except SellerDetails.DoesNotExist:
        return redirect('stateentry')

@never_cache
@login_required
def auth_logout(request):
    logout(request)
    return redirect('Login')
@login_required
def home(request):
    user = request.user
    cart_item_count = 0
    satisfied_customers = User.objects.count() 
    quality_of_service = Review.objects.aggregate(Avg('rating'))['rating__avg'] or 0 
    available_products = Product.objects.filter(is_active=True).count()  
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    categories_with_products = Category.objects.filter(
        Exists(Product.objects.filter(category=OuterRef('pk'), is_active=True))
    )
    
    try:
        cart = Cart_table.objects.get(user=user)
        cart_item_count = cart.items.count()
    except Cart_table.DoesNotExist:
        pass  # If the cart doesn't exist, count remains 0
    print(f"Number of products: {products.count()}")
    username = request.session.get('username') or user_username(user)
    if not username:
        username = user.email.split('@')[0] if user.email else 'User'
    best_selling_products = (
    OrderItem.objects
    .select_related('product')  # Use select_related to fetch related product data
    .values('product__id', 'product__name', 'product__image', 'product__price')  # Include image and price
    .annotate(total_quantity=Sum('quantity'))  # Sum the quantities sold
    .order_by('-total_quantity')[:5]  # Get top 5 best-selling products
    )

    context = {
        'username': username,
        'products': products,
        'categories': categories_with_products,
        'cart_item_count': cart_item_count,
        'best_selling_products': best_selling_products,
        'satisfied_customers': satisfied_customers,
        'quality_of_service': quality_of_service,
        'available_products': available_products
    }
    
    return render(request, 'Products/index.html', context)
@login_required
def customer_dashboard_with_seller_link(request):
    print("Session keys:", request.session.keys())
    username = request.session.get('username')
    print(f"Session retrieved in dashboard: {username}")
    if not username:
        print("User object:", request.user)
        print("Is authenticated:", request.user.is_authenticated)
        return redirect('Login')

    return render(request, 'Products/index.html', {'has_seller_role': True,'username':username})


@login_required
def stateentry(request):
    user = request.user
    if request.method == 'POST':
        state_name = request.POST.get('state')
        country_name = request.POST.get('country')
        
        if state_name and country_name:
            state, created = State.objects.get_or_create(name=state_name, country=country_name)
            roles = user.role.all()
            role_names = set(roles.values_list('name', flat=True))

            # Check for Customer role
            if 'Customer' in role_names:
                try:
                    address = Address_table.objects.get(user=user)
                    if not address.address or not address.city or not address.zip_code:
                        return redirect('address_entry', state_id=state.id)
                except Address_table.DoesNotExist:
                    return redirect('address_entry', state_id=state.id)

            # Check for Seller role
            if 'Seller' in role_names:
                try:
                    seller_details = SellerDetails.objects.get(user=user)
                    if not seller_details.FarmAddress or not seller_details.Farmcity or not seller_details.Farmzip:
                        return redirect('SellerDetails', state_id=state.id)
                except SellerDetails.DoesNotExist:
                    return redirect('SellerDetails', state_id=state.id)

            # If all necessary details are filled, redirect to appropriate page
            if 'Seller' in role_names:
                return redirect('SellerHome')
            else:
                return redirect('home')

        else:
            error_message = "Both state and country are required."
            countries = State.objects.values_list('country', flat=True).distinct()
            return render(request, 'Users/Stateentry.html', {'error': error_message, 'countries': countries})

    countries = State.objects.values_list('country', flat=True).distinct()
    return render(request, 'Users/Stateentry.html', {'countries': countries})

@login_required
@require_GET
def load_states(request):
    country = request.GET.get('country')
    if not country:
        return JsonResponse([], safe=False)
    
    try:
        states = list(State.objects.filter(country=country)
                      .values('id', 'name')
                      .distinct()
                      .order_by('name'))
        return JsonResponse(states, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)



@login_required
def addressentry(request, state_id):
    if request.method == 'POST':
        street = request.POST.get('Landmark')
        city = request.POST.get('your_city')
        zipcode = request.POST.get('your_pin')
        state = get_object_or_404(State, id=state_id)
        
        if street and city and zipcode:
            Address_table.objects.create(
            user=request.user,
            address=street,
            city=city,
            zip_code=zipcode,
            state=state
        )
            try:
                return redirect('home')  # Redirect to the home page or another appropriate page
            except IntegrityError as e:
                # Catch and print any IntegrityErrors
                print(f"IntegrityError: {e}")
                error_message = "There was an error saving your address. Please try again."
                return render(request, 'Users/addressentry.html', {
                    'error': error_message,
                    'state': state_id,
                    'address': addresss
                })
        else:
            error_message = "All fields (street, city, and zipcode) are required."
            return render(request, 'Users/addressentry.html', {
                'error': error_message,
                'state': state_id,
                'address': addresss
            })

    return render(request, 'Users/addressentry.html', {
        'state': state_id
    })
@login_required
def profile_update(request):
    user=request.user
    username = user.username
    user = None
    address = None
    state = None
    countries = []

    if username:
        try:
            user = get_object_or_404(User, username=username)
            address = get_object_or_404(Address_table, user=user)
            state = address.state if address else None
        except (User.DoesNotExist, Address_table.DoesNotExist):
            user = None
            address = None

        if request.method == 'POST':
            if user:
                user.email = request.POST.get('email', user.email)
                user.first_name = request.POST.get('first_name', user.first_name)
                user.last_name = request.POST.get('last_name', user.last_name)
                user.phone_number = request.POST.get('phone_number', user.phone_number)
                user.save()

            if address:
                address.address = request.POST.get('street', address.address)
                address.city = request.POST.get('city', address.city)
                address.zip_code = request.POST.get('zip_code', address.zip_code)
                new_state = request.POST.get('state')
                new_country = request.POST.get('country')
                if new_state and new_country:
                    state, created = State.objects.get_or_create(name=new_state, country=new_country)
                    address.state = state
                address.save()

            messages.success(request, "Profile updated successfully.")
            return redirect('profile_edit')

        if state:
            countries = State.objects.values_list('country', flat=True).distinct()
    else:
        messages.error(request, "User not found in session.")
        return redirect('Login')  # Redirect to login page if username is not in session

    context = {
        'user': user,
        'address': address,
        'state': state,
        'countries': countries
    }
    return render(request, 'Users/User_profile.html', context)


@login_required
def SellerProfile(request):
    user = request.user
    print(user.username)
    categories=Category.objects.all()
    users_with_chats = User.objects.filter(
    Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
    ).distinct().exclude(id=user.id)
    print(f"User: {user.username}")
    license_status=LicenseAuthenticationRequest.objects.filter(seller=user).order_by('-created_at').first()
    if license_status:
        license_status=license_status.status
    else:
        license_status='none'
    context = {
        'username': user.username,
        'categories':categories,
        'users_with_chats': users_with_chats,
        'license_status': license_status

        # Add any other user details you want to pass to the template
    }
    return render(request,'Products/SellerIndex.html',context)
def SellerRegister(request):
    if request.method == 'POST':
        # Retrieve form data
        request.session['seller_data'] = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'password': request.POST.get('cpassword'),
        }
        reg=request.session.get('seller_data')
        email=reg['email']
        try:
            existing_user = User.objects.get(email=email)
            existing_roles = existing_user.role.values_list('name', flat=True)
            if 'Seller' in existing_roles:
                # User is already registered as Seller
                messages.info(request, 'Email is already registered as a Seller.')
                return redirect('Login')  # or handle accordingly
            else:
                # Handle case for users with other roles
                context = {
                    'update_roles': True,
                    'background_image_url': static('assets/img/crops.jpg'),
                    'existing_user': existing_user
                }
                return render(request, 'Users/SellerReg.html', context)

        except User.DoesNotExist:
            return redirect('seller_send_otp_email')

            
    context = {
        'background_image_url': static('assets/img/crops.jpg')
        }
    return render(request,'Users/SellerReg.html',context)
def update_roles(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            seller_role, created = Role.objects.get_or_create(name='Seller')
            
            # Update the user's roles
            if not user.role.filter(name='Seller').exists():
                user.role.add(seller_role)
                messages.success(request, 'Role added successfully.')
            else:
                messages.info(request, 'Role already exists for this user.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        except Role.DoesNotExist:
            messages.error(request, 'Role not found.')

        return redirect('Login')

    return redirect('SellerReg')
def seller_send_otp_email(request):
    # Retrieve registration data from session
    registration_data = request.session.get('seller_data')
    if not registration_data:
        return redirect('SellerReg')  # Redirect to registration if session data is missing

    # Generate OTP using pyotp library
    otp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(otp_secret)
    otp = totp.now()
    request.session['otp']=otp
    # Send OTP via email (example using Django's send_mail)
    subject = 'OTP Verification'
    message = f'Your OTP for registration for the seller account is: {otp}'
    from_email = 'farmtohome584@gmail.com'  # your email
    to_email = registration_data['email']  # email provided in registration form

    send_mail(subject, message, from_email, [to_email])

    # Pass OTP to template for verification
    context = {
        'otp': otp,
        'email': to_email,  # Passing email to pre-fill the form
    }

    return render(request, 'Users/seller_send_otp_email.html', context)
def verify_otp_seller(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_email = request.POST.get('email')  # Retrieve email from the form

        # Retrieve OTP from session
        stored_otp = request.session.get('otp')
        if stored_otp is None:
            messages.error(request, 'OTP expired. Please try again.')
            return redirect('SellerReg')  # Redirect to registration page if OTP is expired

        # Validate OTP
        if user_otp == stored_otp:
            # Save registration data to database
            registration_data = request.session.get('seller_data')
            suffix = random.randint(1000, 9999)  # Adjust range as needed
            username = registration_data['first_name'] + str(suffix)
            while User.objects.filter(username=username).exists():
              suffix = random.randint(1000, 9999)  # Generate new suffix
              username = registration_data['first_name'] + str(suffix)
       # Check if the username already exists
            
            if registration_data:
                seller_role = Role.objects.get(name='Seller')
                hashed_password = make_password(registration_data['password'])
                # Assuming you have a model named `User` for user registration
                new_user = User.objects.create(
                    username=username,
                    first_name=registration_data['first_name'],
                    last_name=registration_data['last_name'],
                    email=registration_data['email'],
                    phone_number=registration_data['phone'],
                    password=hashed_password,
                )
                new_user.role.set([seller_role])
                # Clear session data after registration
                del request.session['seller_data']
                del request.session['otp']
                
                messages.success(request, 'Registration successful!')
                return redirect('Login')  # Redirect to home or login page after successful registration
            else:
                messages.error(request, 'Registration data not found. Please try again.')
                return redirect('SellerReg')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('SellerReg')  # Redirect to registration page if OTP is incorrect

    return render(request, 'Users/seller_send_otp_email.html')
@login_required
def Seller_Details(request, state_id):
    state = get_object_or_404(State, id=state_id)
    if request.method == 'POST':
        farmname = request.POST.get('farm_name')
        street = request.POST.get('landmark')  
        city = request.POST.get('Your_city')
        zipcode = request.POST.get('your_pin')
        print(farmname)
        print(street)
        print(city)
        print(zipcode)
        if farmname and street and city and zipcode:
            print('success')
            try:
                SellerDetails.objects.create(
                    user=request.user,
                    FarmName=farmname,
                    FarmAddress=street,
                    Farmcity=city,
                    Farmzip_code=zipcode,
                    state=state
                )
                return redirect('SellerHome')
            except IntegrityError as e:
                print(f"IntegrityError: {e}")
                error_message = "There was an error saving your address. Please try again."
        else:
            error_message = "All fields (farm name, street, city, and zipcode) are required."
        
        context={
            'error': error_message,
            'state_id': state_id,
            'state':state,
            
        }
    else:
        context={
            'state_id': state_id,
            'state':state
        }

    return render(request, 'Users/Sellerentry.html', context)
@never_cache
def adminlog(request):
    if request.user.is_authenticated and request.user.is_staff:
        username = request.user.username
        end_date = timezone.now().date()
        start_date = end_date - timezone.timedelta(days=30)
        
        # Data for the new sales chart (last 30 days)
        sales_data = Order.objects.filter(order_date__date__range=[start_date, end_date])\
            .annotate(date=TruncDate('order_date'))\
            .values('date')\
            .annotate(total_sales=Sum('total_amount'))\
            .order_by('date')

        dates = [item['date'].strftime('%Y-%m-%d') for item in sales_data]
        sales = [float(item['total_sales']) for item in sales_data]
        
        # Data for the existing chart (monthly data for the current year)
        current_year = timezone.now().year
        monthly_data = Order.objects.filter(order_date__year=current_year)\
            .annotate(month=TruncMonth('order_date'))\
            .values('month')\
            .annotate(total_sales=Sum('total_amount'))\
            .order_by('month')
        
        three_days_ago = timezone.now() - timedelta(days=3)
        recent_orders = Order.objects.filter(
        order_date__gte=three_days_ago
    ).select_related('consumer').order_by('-order_date')[:5]  # Limit to 5 most recent orders

        recent_users = User.objects.filter(
        date_joined__gte=timezone.now() - timedelta(days=30)
        ).order_by('-date_joined')[:5]  # Limit to 5 most recent users

        chart_data = [0] * 12
        for entry in monthly_data:
            month_index = entry['month'].month - 1
            chart_data[month_index] = float(entry['total_sales'])
        
        context = {
            'username': username,
            'sales_dates': json.dumps(dates),
            'sales_amounts': json.dumps(sales),
            'chart_data': json.dumps(chart_data),
            'recent_orders': recent_orders,
            'recent_users':recent_users,
        }
        
        return render(request, 'admin/dashboard.html', context)
    else:
        return redirect('Login')



@login_required
def adminupdate(request):
    user = request.user
    if request.method == 'POST':
        try:

            user.username = request.POST.get('username', user.username)
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.phone_number = request.POST.get('phone_number', user.phone_number)
            user.save()
            messages.success(request, "Admin details updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to update admin details. Error: {str(e)}")
        return redirect('adminupdate')

    context = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'phone_number': user.phone_number,
    }
    return render(request, 'admin/user.html', context)
@login_required
def userslist(request):
    users = User.objects.all()
    return render(request, 'admin/tables.html', {'users': users, 'username': request.user.username})



@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'admin/notifications.html', {'notifications': notifications})

@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notification_list')
@login_required
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f"User {user.username} has been deactivated successfully.")
        return redirect('adminuserslist')
    users = User.objects.all()
    return render(request, 'admin/tables.html', {'users': users, 'username': request.user.username})



@login_required
def chat_view(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)
    if request.method == 'POST':
        message = request.POST.get('message')
        chat_message = ChatMessage.objects.create(sender=request.user, receiver=receiver, message=message)
        return JsonResponse({
            'status': 'success',
            'message': {
                'sender': request.user.username,
                'message': chat_message.message,
                'timestamp': chat_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@login_required
def get_messages(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)
    messages = ChatMessage.objects.filter(
        (Q(sender=request.user, receiver=receiver) | Q(sender=receiver, receiver=request.user))
    ).order_by('timestamp')
    return JsonResponse([{
        'sender': msg.sender.username,
        'message': msg.message,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages], safe=False)

@login_required
def seller_chat_list(request):
    # Get all unique users who have sent messages to this seller
    chat_users = User.objects.filter(
        Q(sent_messages__receiver=request.user) | Q(received_messages__sender=request.user)
    ).distinct()

    context = {
        'chat_users': chat_users,
    }
    return render(request, 'Users/seller_chat_list.html', context)

@login_required
def get_chat_users(request):
       try:
           user = request.user
           print(f"Current user: {user.username}")  # Debugging line

           chat_users = User.objects.filter(
               Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
           ).distinct().exclude(id=user.id)

           print(f"Chat users query: {chat_users.query}")  # Debugging line
           print(f"Number of chat users: {chat_users.count()}")  # Debugging line

           user_data = []
           for chat_user in chat_users:
               unread_count = ChatMessage.objects.filter(sender=chat_user, receiver=user, is_read=False).count()
               user_data.append({
                   'id': chat_user.id,
                   'username': chat_user.username,
                   'unread_count': unread_count
               })# Debugging line
           return JsonResponse(user_data, safe=False)
       except Exception as e:
           print(f"Error in get_chat_users: {str(e)}")  # Debugging line
           return JsonResponse({'error': 'An error occurred'}, status=500)





@login_required
def license_authentication(request):
    existing_request = LicenseAuthenticationRequest.objects.filter(
        seller=request.user, 
        status__in=['pending', 'approved']
    ).first()

    if existing_request:
        # User has already submitted a license that's pending or approved
        return render(request, 'Products/SellerLicense.html', {'existing_request': existing_request})
    if request.method == 'POST':
        license_file = request.FILES.get('license_file')
        comments = request.POST.get('comments', '')

        if license_file:
            # Check file extension
            file_extension = license_file.name.split('.')[-1].lower()
            if file_extension not in ['pdf', 'jpg', 'jpeg', 'png']:
                messages.error(request, 'Only PDF and image files (jpg, jpeg, png) are allowed.')
            else:
                # Create and save the license request
                license_request = LicenseAuthenticationRequest(
                    seller=request.user,
                    license_file=license_file,
                    status='pending'
                )
                license_request.save()
                messages.success(request, 'Your license has been submitted for authentication. We will review it shortly.')
                return redirect('license_authentication')  # or wherever you want to redirect after submission
        else:
            messages.error(request, 'Please upload a license file.')

    return render(request, 'Products/SellerLicense.html')



@user_passes_test(lambda u: u.is_staff)
def license_requests(request):
    license_requests = LicenseAuthenticationRequest.objects.all().order_by('-created_at')
    return render(request, 'admin/license_requests.html', {'license_requests': license_requests})

@user_passes_test(lambda u: u.is_staff)
def approve_license(request, request_id):
    if request.method == 'POST':
        license_request = LicenseAuthenticationRequest.objects.get(id=request_id)
        license_request.status = 'approved'
        license_request.save()
    return redirect('license_requests')

@user_passes_test(lambda u: u.is_staff)
def reject_license(request, request_id):
    if request.method == 'POST':
        license_request = LicenseAuthenticationRequest.objects.get(id=request_id)
        license_request.status = 'rejected'
        license_request.save()
    return redirect('license_requests')

def seller_view(request, seller_id):
    user=request.user
    seller = get_object_or_404(User, id=seller_id)
    seller_products = Product.objects.filter(seller=seller)
    rating_distribution = Review.objects.filter(product__seller=seller).values('rating').annotate(count=Count('rating')).order_by('rating')
    avg_rating = Review.objects.filter(product__seller=seller).aggregate(Avg('rating'))['rating__avg'] or 0

    # Get stock information for each product
    products_with_stock = []
    for product in seller_products:
        stock_info = product.stock if hasattr(product, 'stock') else None
        products_with_stock.append({
            'product': product,
            'stock': stock_info,
        })
    latest_license_request = LicenseAuthenticationRequest.objects.filter(seller=seller).order_by('-created_at').first()
    context = {
        'seller': seller,
        'products_with_stock': products_with_stock,
        'avg_rating': avg_rating,
        'rating_distribution': list(rating_distribution),
        'username': user.username,
        'license_request': latest_license_request,
    }
    return render(request, 'Products/UserSellerview.html', context)
@transaction.atomic
def approve_job(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    if application.status != 'pending':
        messages.error(request, "This application has already been processed.")
        return redirect('Delivery:job_requests')

    try:
        # Check if user already exists
        user, created = User.objects.get_or_create(email=application.email)
        
        if created:
            # Set up new user
            user.username = f"delivery_{application.name.lower().replace(' ', '_')}"
            user.set_password(User.objects.make_random_password())
            user.first_name = application.name.split()[0]
            user.last_name = ' '.join(application.name.split()[1:]) if len(application.name.split()) > 1 else ''
            user.phone_number = application.phone_number
            user.save()

        # Add delivery role
        delivery_role, _ = Role.objects.get_or_create(name='delivery')
        user.role.add(delivery_role)

        # Update application status
        application.status = 'approved'
        application.save()

    # Send email
        subject = 'Your Delivery Job Application has been Approved'
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Congratulations {user.first_name}!</h1>
            <p>Your application to join our delivery team has been approved.</p>
            
            {'<p>A new account has been created for you. Your temporary password is: ' + password_message + '</p>'
            '<p>Please change your password upon first login.</p>'
            if created else
            '<p>The delivery role has been added to your existing account.</p>'}
            
            <p>You can log in using your email: {user.email}</p>
            <p>Login here: [Your login URL]</p>
            
            <p>Welcome to the team!</p>
            <p>Best regards,<br>The Management Team</p>
        </body>
        </html>
        """
        plain_message = f"""
        Congratulations {user.first_name}!

        Your application to join our delivery team has been approved.

        {'A new account has been created for you. Your temporary password is: ' + password_message + 'Please change your password upon first login.'
        if created else
        'The delivery role has been added to your existing account.'}

        You can log in using your email: {user.email}
        Login here: http://127.0.0.1:8000/login/

        Welcome to the team!

        Best regards,
        The Management Team
        """

        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = user.email

        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)

        if created:
            messages.success(request, f'New delivery user account created for {user.email} and notified via email.')
        else:
            messages.success(request, f'Delivery role added to existing user {user.email} and notified via email.')
        
        # Redirect to process_approved_application in Delivery app
        return redirect(reverse('Delivery:job_requests'))
    except Exception as e:
        messages.error(request, f"An error occurred while processing the application: {str(e)}")
        return redirect('Delivery:job_requests')


def reject_job(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    application.status = 'rejected'
    application.save()
    messages.success(request, 'Job application rejected successfully!')
    return redirect('Delivery:job_requests')