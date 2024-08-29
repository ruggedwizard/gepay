from . import views
from django.urls import path

urlpatterns = [
    path('', views.landing, name='landing_page'),
    path('index', views.index, name='index'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('transfer/', views.transfer, name='transfer'),
    path('deposit/', views.deposit, name='deposit'),
    path('history/', views.history, name='history'),
    path('recipient/<str:username>/', views.recipient, name='recipient'),
    path('fetch_users/', views.fetch_users, name='fetch_users'),
    path('transaction/success/', views.transaction_success, name='transaction_success'),
    path('settings/', views.settings, name='settings'),
    path('profile/', views.profile, name='profile'),
    # path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('verify_pin/', views.verify_pin, name='verify_pin'),
]