from django.urls import path
from . import views

urlpatterns = [
    path('payments/', views.PaymentListCreateView.as_view(), name='payment-list-create'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/my/', views.my_payments, name='my-payments'),
    path('payments/initiate/', views.initiate_payment, name='initiate-payment'),
    path('payments/<uuid:pk>/status/', views.update_payment_status, name='update-payment-status'),
    path('payments/<uuid:pk>/refund/', views.refund_payment, name='refund-payment'),
]