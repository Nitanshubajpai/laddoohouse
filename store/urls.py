from django.urls import path
from . import views

app_name = 'store'
urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu, name='menu'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-success/<str:order_id>/', views.order_success, name='order_success'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
]
