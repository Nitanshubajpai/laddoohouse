from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Sum, Count
from store.models import Product, Order, OrderItem


def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('dashboard:home')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'dashboard/login.html')


def dashboard_logout(request):
    logout(request)
    return redirect('dashboard:login')


@login_required
def dashboard_home(request):
    orders = Order.objects.all()
    stats = {
        'total_orders': orders.count(),
        'revenue': orders.aggregate(r=Sum('total'))['r'] or 0,
        'pending': orders.exclude(status__in=['Shipped', 'Delivered']).count(),
        'delivered': orders.filter(status='Delivered').count(),
        'new_orders': orders.filter(status='New').count(),
    }
    recent_orders = orders[:8]
    return render(request, 'dashboard/home.html', {'stats': stats, 'recent_orders': recent_orders})


@login_required
def orders_list(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    stats = {
        'total': Order.objects.count(),
        'new': Order.objects.filter(status='New').count(),
        'making': Order.objects.filter(status='Making').count(),
        'packed': Order.objects.filter(status='Packed').count(),
        'shipped': Order.objects.filter(status='Shipped').count(),
        'delivered': Order.objects.filter(status='Delivered').count(),
    }
    return render(request, 'dashboard/orders.html', {
        'orders': orders, 'stats': stats,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    return render(request, 'dashboard/order_detail.html', {'order': order, 'status_choices': Order.STATUS_CHOICES})


@login_required
@require_POST
def update_status(request, pk):
    order = get_object_or_404(Order, pk=pk)
    new_status = request.POST.get('status')
    valid = [s[0] for s in Order.STATUS_CHOICES]
    if new_status in valid:
        order.status = new_status
        order.save()
        messages.success(request, f'Status updated to {new_status}.')
    return redirect('dashboard:order_detail', pk=pk)


@login_required
@require_POST
def update_tracking(request, pk):
    order = get_object_or_404(Order, pk=pk)
    order.tracking = request.POST.get('tracking', '')
    order.save()
    messages.success(request, 'Tracking number saved.')
    return redirect('dashboard:order_detail', pk=pk)


@login_required
def products_list(request):
    products = Product.objects.all()
    return render(request, 'dashboard/products.html', {'products': products})


@login_required
def product_add(request):
    if request.method == 'POST':
        product = Product.objects.create(
            name=request.POST['name'],
            description=request.POST['description'],
            price=int(request.POST['price']),
            weight=request.POST.get('weight', '400g'),
            emoji=request.POST.get('emoji', '🟤'),
            tag=request.POST.get('tag', ''),
            ingredients=request.POST.get('ingredients', ''),
            shelf_life=request.POST.get('shelf_life', ''),
            storage_instructions=request.POST.get('storage_instructions', ''),
            allergens=request.POST.get('allergens', ''),
            available=request.POST.get('available') == 'on',
            sort_order=int(request.POST.get('sort_order', 0)),
        )
        if request.FILES.get('image'):
            product.image = request.FILES['image']
            product.save()
        messages.success(request, 'Product added successfully!')
        return redirect('dashboard:products')
    return render(request, 'dashboard/product_form.html', {'action': 'Add', 'emojis': EMOJIS})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        product.price = int(request.POST['price'])
        product.weight = request.POST.get('weight', '400g')
        product.emoji = request.POST.get('emoji', '🟤')
        product.tag = request.POST.get('tag', '')
        product.ingredients = request.POST.get('ingredients', '')
        product.shelf_life = request.POST.get('shelf_life', '')
        product.storage_instructions = request.POST.get('storage_instructions', '')
        product.allergens = request.POST.get('allergens', '')
        product.available = request.POST.get('available') == 'on'
        product.sort_order = int(request.POST.get('sort_order', 0))
        if request.FILES.get('image'):
            product.image = request.FILES['image']
        elif request.POST.get('clear_image'):
            product.image = None
        product.save()
        messages.success(request, 'Product updated successfully!')
        return redirect('dashboard:products')
    return render(request, 'dashboard/product_form.html', {'action': 'Edit', 'product': product, 'emojis': EMOJIS})


@login_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, f'"{product.name}" deleted.')
    return redirect('dashboard:products')


@login_required
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.available = not product.available
    product.save()
    state = 'shown on' if product.available else 'hidden from'
    messages.success(request, f'"{product.name}" is now {state} the store.')
    return redirect('dashboard:products')


EMOJIS = ['🟤','🟡','⚫','🟢','🔶','🟣','⚪','🟠','🔴','🔵','🥥','🌾','🌰','🍯','🌿','💛','✨','🫐','🫚','🧆']
