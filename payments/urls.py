# payments/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    path('', views.create_transaction, name='home'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/approve/<int:tx_id>/', views.approve_transaction, name='approve_transaction'),
    path('admin/reject/<int:tx_id>/', views.reject_transaction, name='reject_transaction'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('freeze_account/', views.freeze_account, name='freeze_account'),
    path('unfreeze_account/', views.unfreeze_account, name='unfreeze_account'),
    path('sent/', views.sent_transactions, name='sent_transactions'),
    path('received/', views.received_transactions, name='received_transactions'),
    path('qr_code_image/<uuid:code>/', views.qr_code_image, name='qr_code_image'),
    path('scan_qr/', views.scan_qr_code, name='scan_qr'),
    # например, для обработки QR-кода:
    path('process_qr/<uuid:code>/', views.process_qr_code, name='process_qr'),
    path('transfer_qr/<uuid:code>/', views.transfer_via_qr, name='transfer_qr'),
    path('create_open_qr/', views.create_open_qr, name='create_open_qr'),
    path('create_fixed_qr/', views.create_fixed_qr, name='create_fixed_qr'),
    path('qr_history/', views.qr_history, name='qr_history'),
    path('top_up_balance/', views.top_up_balance, name='top_up_balance'),
    path('view_qr/<uuid:code>/', views.view_qr_page, name='view_qr_page'),
]

