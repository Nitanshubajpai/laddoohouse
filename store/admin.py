from django.contrib import admin
from .models import Product, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'weight', 'tag', 'available', 'sort_order')
    list_editable = ('price', 'available', 'sort_order')
    list_filter = ('available', 'tag')
    search_fields = ('name',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'name', 'phone', 'total', 'pay_mode', 'status', 'created_at')
    list_filter = ('status', 'pay_mode')
    search_fields = ('order_id', 'name', 'phone', 'email')
    readonly_fields = ('order_id', 'created_at', 'updated_at')
    list_editable = ('status',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'order', 'quantity', 'unit_price', 'sweetener', 'subtotal')
    search_fields = ('product_name', 'order__order_id')
