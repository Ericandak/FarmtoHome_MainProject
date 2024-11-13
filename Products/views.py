from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product,Category,Stock,Cart_table,CartItem_table,Review
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .utils import predict_fruit_disease
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
import json
from django.db.models import Q
from django.template.loader import render_to_string
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime,timedelta
import io
import imghdr
import re
from django.conf import settings
import os

def extract_date_from_filename(filename):
    # This pattern looks for date formats like YYYYMMDD_HHMMSS or YYYY-MM-DD_HH-MM-SS
    pattern = r'(\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2}[-_]?\d{2})'
    match = re.search(pattern, filename)
    if match:
        date_string = match.group(1)
        # Remove any separators
        date_string = date_string.replace('-', '').replace('_', '')
        try:
            return datetime.strptime(date_string, '%Y%m%d%H%M%S')
        except ValueError:
            return None
    return None
def get_image_creation_time(image):
    creation_time = None
    method_used = None

    filename_date = extract_date_from_filename(image.name)
    if filename_date:
        creation_time = filename_date
        method_used = "Filename"
        return creation_time, method_used

    # Method 1: EXIF Data (Most reliable for original photos)
    try:
        img = Image.open(image)
        exif_data = img._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    creation_time = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                    method_used = "EXIF DateTimeOriginal"
                    break
    except Exception as e:
        print(f"Error reading EXIF data: {str(e)}")

    # Method 2: File creation time (Fallback)
    if not creation_time:
        try:
            creation_time = datetime.fromtimestamp(os.path.getctime(image.temporary_file_path()))
            method_used = "File creation time"
        except Exception as e:
            print(f"Error getting file creation time: {str(e)}")

    return creation_time, method_used

def is_valid_image(image):
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(image.name)[1].lower()
    if ext not in valid_extensions:
        return False

    # Check file type using imghdr
    try:
        file_content = image.read()
        image.seek(0)  # Reset file pointer
        if imghdr.what(None, file_content) not in ['jpeg', 'png', 'gif']:
            return False
    except Exception as e:
        print(f"Error checking image type: {str(e)}")
        return False

    # Check MIME type using python-magic

    return True

@login_required
def add_product(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('product_name')
        category_id = request.POST.get('category')
        description = request.POST.get('description')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        image = request.FILES.get('image')
        is_active = request.POST.get('is_active') == 'on'  # Checkbox handling

        if not name:
            messages.error(request, 'Product name is required.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Product name is required'})
        if not quantity or not quantity.isdigit():
            messages.error(request, 'Valid quantity is required.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Valid quantity is required'})

        try:
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            messages.error(request, 'Invalid category selected.')
            return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Invalid category'})

        # Check image
        if image:
            if not is_valid_image(image):
                messages.error(request, 'Invalid image format. Please upload a valid image file (JPG, PNG, or GIF).')
                return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Invalid image format', 'username': request.user.username})

            creation_time, method_used = get_image_creation_time(image)
            if not creation_time:
                messages.warning(request, 'Unable to verify image creation time. Please ensure you are uploading a recent image.')
            else:
                cutoff_date = datetime.now() - timedelta(days=1)
                if creation_time < cutoff_date:
                    messages.error(request, f'Image is too old. Please upload an image taken within the last 24 hours. (Verification method: {method_used})')
                    return render(request, 'Products/SellerIndex.html', {'categories': categories, 'error': 'Image is too old', 'username': request.user.username})

            # Reset file pointer
            image.seek(0)

        product = Product(
            seller=request.user,
            name=name,
            category=category,
            description=description,
            price=price,
            image=image,
            is_active=is_active
        )

        try:
            product.save()
            stock = Stock(
                product=product,
                quantity=int(quantity)
            )
            stock.save()
            messages.success(request, 'Product added successfully.')
            return redirect('SellerHome')
        except Exception as e:
            messages.error(request, f'Error saving product: {str(e)}')
            return render(request, 'Products/Productlist.html', {'categories': categories, 'error': 'Error saving product'})

    return render(request, 'Products/SellerIndex.html', {'categories': categories, 'username': request.user.username})

@login_required
def seller_home(request):
    categories = Category.objects.all()
    return render(request, 'Products/SellerIndex.html', {'categories': categories, 'username': request.user.username})
@login_required
def productlist(request):
    products = Product.objects.filter(seller=request.user)
    prediction_result = request.session.pop('prediction_result', None)
    context = {
        'products': products,
        'username': request.user.username,
        'prediction_result': prediction_result
    }
    return render(request, 'Products/Productlist.html', context)

@login_required
def productedit(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        product.name = request.POST.get('product_name')
        product.category_id = request.POST.get('category')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.is_active = request.POST.get('is_active') == 'on'  
        
        if 'image' in request.FILES:
            product.image = request.FILES['image']
        
        product.save()

        stock = Stock.objects.get(product=product)
        stock.quantity = request.POST.get('quantity')
        stock.save()

        messages.success(request, 'Product updated successfully.')
        return redirect('sellerproductlist')

    return render(request, 'Products/productedit.html', {
        'product': product,
        'categories': categories,
        'username': request.user.username
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart_table.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem_table.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1
    cart_item.save()
    
    messages.success(request, f"{product.name} has been added to your cart.")
    return redirect(reverse('home'))
@login_required
def cartview(request):
    user = request.user
    try:
        cart = Cart_table.objects.get(user=user)
        cart_items = cart.items.all()
        cart_item_count = cart_items.count()
        total = cart.total 
    except Cart_table.DoesNotExist:
        cart_items = []
        cart_item_count = 0
        total = 0

    context = {
        'username': user.username,
        'cart_items': cart_items,
        'cart_item_count': cart_item_count,
        'total': total,
    }
    return render(request, 'Products/cart.html', context)
@require_POST
@login_required
def update_cart_item(request):
    data = json.loads(request.body)
    item_id = data.get('item_id')
    action = data.get('action')
    try:
        cart_item = CartItem_table.objects.select_related('product').get(id=item_id, cart__user=request.user)
        stock = Stock.objects.get(product=cart_item.product)
        if action == 'increase':
            if cart_item.quantity < stock.quantity:
                cart_item.quantity += 1
            else:
                return JsonResponse({'status': 'error', 'message': 'Not enough stock available'})
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart_item.delete()
                return JsonResponse({
                    'status': 'success',
                    'quantity': 0,
                    'subtotal': 0,
                    'total': cart_item.cart.total,
                })
        
        cart_item.save()
        cart_item.cart.refresh_from_db()
        return JsonResponse({
            'status': 'success',
            'quantity': cart_item.quantity,
            'subtotal': cart_item.subtotal,
            'total': cart_item.cart.total,
            'can_increase': cart_item.quantity < stock.quantity
        })

    except CartItem_table.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
    except Stock.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Stock information not found'}, status=404)

@login_required
@require_POST
def deletecart(request):
    try:
        print("hi")
        data = json.loads(request.body)
        item_id = data.get('item_id')

        if not item_id:
            return JsonResponse({'status': 'error', 'message': 'Item ID is required'}, status=400)

        cart_item = CartItem_table.objects.get(id=item_id, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()
        cart.refresh_from_db()

        return JsonResponse({
            'status': 'success',
            'total': cart.total,
            'is_cart_empty': cart.items.count() == 0  # Changed to boolean
        })
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    except CartItem_table.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Cart item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def product_detail(request, product_id):
    user=request.user
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:6]
    try:
        cart = Cart_table.objects.get(user=user)
        cart_item_count = cart.items.count()
    except Cart_table.DoesNotExist:
        cart_item_count = 0
    context = {
        'product': product,
        'related_products': related_products,
        'username':user.username,
        'cart_item_count': cart_item_count
    }
    return render(request, 'Products/shop-detail.html', context)


@login_required
def search_results(request):
    user=request.user
    query = request.GET.get('q')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', 'name')
    results=Product.objects.all()
    if query:
        results = Product.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()
    if category:
        results = results.filter(category_id=category)

    if min_price:
        results = results.filter(price__gte=min_price)

    if max_price:
        results = results.filter(price__lte=max_price)
    if sort == 'name':
        results = results.order_by('name')
    elif sort == '-name':
        results = results.order_by('-name')
    elif sort == 'price':
        results = results.order_by('price')
    elif sort == '-price':
        results = results.order_by('-price')
    results = results.order_by(sort)

    categories = Category.objects.all()
    try:
        cart = Cart_table.objects.get(user=user)
        cart_item_count = cart.items.count()
    except Cart_table.DoesNotExist:
        cart_item_count = 0

    context = {
        'results': results,
        'query': query,
        'categories': categories,
        'sort': sort, 
        'username':user.username,
        'cart_item_count': cart_item_count # Add this line to pass the current sort to the template

    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('Products/search_results_partial.html', context)
        return JsonResponse({'html': html, 'query': query})
    return render(request, 'Products/search_results.html', context)

def live_search(request):
    query = request.GET.get('q', '')
    print(f"Live search query: {query}")
    products = Product.objects.filter(name__icontains=query)[:3]  # Limit to 3 results
    categories = Category.objects.filter(name__icontains=query)[:2]  # Limit to 2 results
    results = []
    
    for product in products:
        results.append({
            'name': product.name,
            'image': product.image.url if product.image else '',
            'url': reverse('product_detail', args=[product.id]),
            'type': 'product'
        })
    
    for category in categories:
        results.append({
            'name': category.name,
            'image': category.image.url if category.image else '',
            'url': reverse('category_detail', args=[category.id]),
            'type': 'category'
        })
    return JsonResponse({'results': results})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully.')
        return redirect('sellerproductlist')  # Redirect to the product list page
    return redirect('sellerproductlist')


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            messages.error(request, 'Both rating and comment are required.')
            return redirect('product_detail', product_id=product.id)
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            messages.error(request, 'Invalid rating. Please provide a rating between 1 and 5.')
            return redirect('product_detail', product_id=product.id)
        
        try:
            review = Review(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
            review.full_clean()  # This will call the clean method and raise ValidationError if limit exceeded
            review.save()
            messages.success(request, 'Your review has been added successfully.')
        except ValidationError as e:
            messages.error(request, str(e))
        
        return redirect('product_detail', product_id=product.id)
    return redirect('product_detail', product_id=product.id)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all().order_by('-created_at')
    avg_rating = round(product.average_rating * 2) / 2
    # ... other context data ...
    return render(request, 'Products/shop-detail.html', {
        'product': product,
        'reviews': reviews,
        'username':request.user,
        'avg_rating': avg_rating,
    })


# from Products.utils import predict_fruit_disease
import logging

logger = logging.getLogger(__name__)

def process_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        image_path = os.path.join(temp_dir, 'temp_image.jpg')

        try:
            # Save the image temporarily
            with open(image_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            
            logger.info(f"Processing image: {image.name}")
            predicted_class, confidence, is_defected, condition = predict_fruit_disease(image_path)
            
            prediction_result = {
                'predicted_class': predicted_class,
                'confidence': round(confidence * 100, 2),  # Convert to percentage and round to 2 decimal places
                'is_defected': is_defected,
                'condition': condition
            }
            request.session['prediction_result'] = prediction_result
            logger.info(f"Prediction result: {prediction_result}")
            messages.success(request, 'Image processed successfully!')

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            messages.error(request, f'Error processing image: {str(e)}')

        finally:
            # Clean up: remove the temporary image file
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Temporary image removed: {image_path}")

        return redirect('sellerproductlist')

    messages.error(request, 'No image file received.')
    return redirect('sellerproductlist')

def product_detailforuser(request, slug):
       product = get_object_or_404(Product, slug=slug)
       context = {
           'product': product,
       }
       return render(request, 'Products/shop-detail.html', context)