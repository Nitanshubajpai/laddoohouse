from django.db import models

class Product(models.Model):
    TAG_CHOICES = [('', 'None'), ('ayurvedic', 'Ayurvedic'), ('popular', 'Popular')]

    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.PositiveIntegerField()
    weight = models.CharField(max_length=20, default='400g')
    emoji = models.CharField(max_length=10, default='🟤')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    tag = models.CharField(max_length=20, choices=TAG_CHOICES, blank=True, default='')
    ingredients = models.TextField(blank=True, default='')
    shelf_life = models.CharField(max_length=60, blank=True, default='', help_text='e.g. 30 days at room temperature')
    storage_instructions = models.TextField(blank=True, default='')
    allergens = models.CharField(max_length=200, blank=True, default='', help_text='e.g. Contains nuts, dairy')
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Making', 'Making'),
        ('Packed', 'Packed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]
    PAY_CHOICES = [('upi', 'Paid via UPI'), ('later', 'Pay Later')]

    order_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    total = models.PositiveIntegerField()
    pay_mode = models.CharField(max_length=10, choices=PAY_CHOICES, default='upi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    tracking = models.CharField(max_length=100, blank=True, default='')
    payment_screenshot = models.ImageField(upload_to='screenshots/', blank=True, null=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order_id} — {self.name}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f'{self.product_name} x{self.quantity}'
