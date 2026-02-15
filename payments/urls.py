from django.urls import path
from . import views

urlpatterns = [
    path('', views.PaymentListCreateView.as_view(), name='payment-list-create'),
    path('<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('my/', views.my_payments, name='my-payments'),
    path('initiate/', views.initiate_payment, name='initiate-payment'),
    path('<uuid:pk>/status/', views.update_payment_status, name='update-payment-status'),
    path('<uuid:pk>/refund/', views.refund_payment, name='refund-payment'),
]