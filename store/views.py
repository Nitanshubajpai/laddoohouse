import json, random, string, re, threading
import requests as http_requests
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from .models import Product, Order, OrderItem


def _send_whatsapp(to_number, body):
    """Send a WhatsApp message via Twilio REST API. Silently skips if not configured."""
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_wa = getattr(settings, 'TWILIO_WHATSAPP_FROM', '')
    if not all([sid, token, from_wa]):
        return
    try:
        http_requests.post(
            f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
            data={'From': from_wa, 'To': f'whatsapp:+{to_number}', 'Body': body},
            auth=(sid, token),
            timeout=10,
        )
    except Exception:
        pass


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

    # --- WhatsApp to owner ---
    owner_wa = (
        f'🛒 *New Order — {order.order_id}*\n\n'
        f'Customer: {order.name}\n'
        f'Phone: +91{order.phone}\n'
        f'Payment: {pay_label}\n\n'
        f'{items_text}\n\n'
        f'*Total: ₹{order.total}*'
    )
    _send_whatsapp(settings.WHATSAPP_NUMBER, owner_wa)

    # --- WhatsApp to customer ---
    customer_wa = (
        f'🏡 *The Laddoo House — Order Confirmed!*\n\n'
        f'Hi {order.name}! Your order *{order.order_id}* has been placed.\n\n'
        f'{items_text}\n\n'
        f'*Total: ₹{order.total}*\n'
        f'Payment: {pay_label}\n\n'
        f'We\'ll dispatch within 2 days. Thank you! 🙏'
    )
    _send_whatsapp(f'91{order.phone}', customer_wa)


def home(request):
    products = Product.objects.filter(available=True)
    return render(request, 'store/home.html', {
        'products': products,
        'upi_id': settings.UPI_ID,
        'upi_discount': settings.UPI_DISCOUNT,
        'whatsapp': settings.WHATSAPP_NUMBER,
        'shipping_charge': settings.SHIPPING_CHARGE,
        'kanpur_pincodes': list(settings.KANPUR_PINCODES),
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
        pincode = request.POST.get('pincode', '').strip()
        pay_mode = request.POST.get('pay_mode', 'upi')
        cart_json = request.POST.get('cart', '[]')
        screenshot = request.FILES.get('screenshot')

        if not all([name, phone, email, address, pincode]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)
        if not re.fullmatch(r'\d{10}', phone):
            return JsonResponse({'error': 'Phone number must be exactly 10 digits.'}, status=400)
        if not re.fullmatch(r'\d{6}', pincode):
            return JsonResponse({'error': 'Please enter a valid 6-digit pincode.'}, status=400)

        cart = json.loads(cart_json)
        if not cart:
            return JsonResponse({'error': 'Cart is empty.'}, status=400)

        raw_total = sum(item['price'] * item['qty'] for item in cart)
        discount = settings.UPI_DISCOUNT if pay_mode == 'upi' else 0
        shipping = 0 if pincode in settings.KANPUR_PINCODES else settings.SHIPPING_CHARGE
        final_total = raw_total - discount + shipping

        order_id = 'TLH-' + ''.join(random.choices(string.digits, k=4))
        while Order.objects.filter(order_id=order_id).exists():
            order_id = 'TLH-' + ''.join(random.choices(string.digits, k=4))

        order = Order.objects.create(
            order_id=order_id, name=name, phone=phone, email=email,
            address=address, pincode=pincode, total=final_total,
            pay_mode=pay_mode, shipping_charge=shipping,
            payment_screenshot=screenshot if screenshot else None,
        )
        valid_sweeteners = {'sugar', 'brown_sugar', 'unsweetened'}
        for item in cart:
            sweetener = item.get('sweetener', 'sugar')
            if sweetener not in valid_sweeteners:
                sweetener = 'sugar'
            OrderItem.objects.create(
                order=order,
                product_name=item['name'],
                quantity=item['qty'],
                unit_price=item['price'],
                sweetener=sweetener,
            )
        threading.Thread(target=_send_order_notifications, args=(order,), daemon=True).start()
        return JsonResponse({'success': True, 'order_id': order_id, 'total': final_total, 'shipping': shipping})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


STATUS_ORDER = ['New', 'Making', 'Packed', 'Shipped', 'Delivered']

def order_track(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    current_index = STATUS_ORDER.index(order.status) if order.status in STATUS_ORDER else 0
    steps = []
    for i, label in enumerate(STATUS_ORDER):
        if i < current_index:
            state = 'done'
        elif i == current_index:
            state = 'active'
        else:
            state = ''
        steps.append({'label': label, 'state': state})
    return render(request, 'store/order_track.html', {
        'order': order,
        'steps': steps,
        'whatsapp': settings.WHATSAPP_NUMBER,
    })

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
