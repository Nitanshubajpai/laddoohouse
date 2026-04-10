import json, random, string
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from .models import Product, Order, OrderItem


def _send_order_notifications(order):
    items_text = '\n'.join(
        f'  {item.product_name} x{item.quantity}  —  ₹{item.subtotal}'
        for item in order.items.all()
    )
    pay_label = 'Paid via UPI' if order.pay_mode == 'upi' else 'Pay Later'

    # --- email to owner ---
    owner_body = (
        f'New order received!\n\n'
        f'Order ID : {order.order_id}\n'
        f'Customer : {order.name}\n'
        f'Phone    : {order.phone}\n'
        f'Email    : {order.email}\n'
        f'Address  :\n{order.address}\n\n'
        f'Items:\n{items_text}\n\n'
        f'Total    : ₹{order.total}\n'
        f'Payment  : {pay_label}\n'
    )
    try:
        send_mail(
            subject=f'[Laddoo House] New Order {order.order_id} — {order.name}',
            message=owner_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.OWNER_EMAIL],
            fail_silently=True,
        )
    except BadHeaderError:
        pass

    # --- confirmation email to customer ---
    customer_body = (
        f'Hi {order.name},\n\n'
        f'Thank you for your order! Here\'s a summary:\n\n'
        f'Order ID : {order.order_id}\n\n'
        f'Items:\n{items_text}\n\n'
        f'Total    : ₹{order.total}\n'
        f'Payment  : {pay_label}\n\n'
        f'We\'ll reach out on WhatsApp to confirm and provide delivery updates.\n\n'
        f'— The Laddoo House'
    )
    try:
        send_mail(
            subject=f'Your Laddoo House Order {order.order_id} is Confirmed!',
            message=customer_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            fail_silently=True,
        )
    except BadHeaderError:
        pass


def home(request):
    products = Product.objects.filter(available=True)
    return render(request, 'store/home.html', {
        'products': products,
        'upi_id': settings.UPI_ID,
        'upi_discount': settings.UPI_DISCOUNT,
        'whatsapp': settings.WHATSAPP_NUMBER,
    })


def menu(request):
    products = Product.objects.filter(available=True)
    return render(request, 'store/menu.html', {'products': products})


@require_POST
def place_order(request):
    try:
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        address = request.POST.get('address', '').strip()
        pay_mode = request.POST.get('pay_mode', 'upi')
        cart_json = request.POST.get('cart', '[]')
        screenshot = request.FILES.get('screenshot')

        if not all([name, phone, email, address]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)
        if pay_mode == 'upi' and not screenshot:
            return JsonResponse({'error': 'Payment screenshot is required for UPI orders.'}, status=400)

        cart = json.loads(cart_json)
        if not cart:
            return JsonResponse({'error': 'Cart is empty.'}, status=400)

        raw_total = sum(item['price'] * item['qty'] for item in cart)
        discount = settings.UPI_DISCOUNT if pay_mode == 'upi' else 0
        final_total = raw_total - discount

        order_id = 'TLH-' + ''.join(random.choices(string.digits, k=4))
        while Order.objects.filter(order_id=order_id).exists():
            order_id = 'TLH-' + ''.join(random.choices(string.digits, k=4))

        order = Order.objects.create(
            order_id=order_id, name=name, phone=phone, email=email,
            address=address, total=final_total, pay_mode=pay_mode,
            payment_screenshot=screenshot if screenshot else None,
        )
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                quantity=item['qty'],
                unit_price=item['price'],
            )
        _send_order_notifications(order)
        return JsonResponse({'success': True, 'order_id': order_id, 'total': final_total})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, 'store/order_success.html', {'order': order, 'whatsapp': settings.WHATSAPP_NUMBER})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    other_products = Product.objects.filter(available=True).exclude(pk=pk)[:4]
    return render(request, 'store/product_detail.html', {
        'product': product,
        'other_products': other_products,
        'upi_discount': settings.UPI_DISCOUNT,
    })
