from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Payment
from .serializers import (
    PaymentSerializer, 
    PaymentCreateSerializer, 
    PaymentUpdateSerializer,
    PaymentStatusUpdateSerializer,
    RefundPaymentSerializer
)
from users.permissions import CanManagePayments
from registrations.models import Registration


class PaymentListCreateView(generics.ListCreateAPIView):
    """List all payments or create a new payment"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'currency', 'user', 'registration']
    search_fields = ['transaction_id', 'user__username', 'registration__event__title']
    ordering_fields = ['initiated_at', 'completed_at', 'amount']
    ordering = ['-initiated_at']
    
    def list(self, request, *args, **kwargs):
        """Override to return array directly instead of paginated response"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        queryset = Payment.objects.all()
        
        # Regular users can only see their own payments
        if not (self.request.user.is_admin() or self.request.user.is_superuser_role()):
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PaymentCreateSerializer
        return PaymentSerializer


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a payment"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PaymentUpdateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        queryset = Payment.objects.all()
        
        # Regular users can only access their own payments
        if not (self.request.user.is_admin() or self.request.user.is_superuser_role()):
            queryset = queryset.filter(user=self.request.user)
            
        return queryset
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        else:
            return [CanManagePayments()]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_payments(request):
    """Get current user's payments"""
    payments = Payment.objects.filter(user=request.user).order_by('-initiated_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """Initiate a new payment for a registration"""
    registration_id = request.data.get('registration_id')
    payment_method = request.data.get('payment_method')
    
    if not registration_id or not payment_method:
        return Response(
            {'error': 'registration_id and payment_method are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        registration = Registration.objects.get(id=registration_id)
    except Registration.DoesNotExist:
        return Response(
            {'error': 'Registration not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if user owns this registration
    if registration.user != request.user:
        return Response(
            {'error': 'You can only pay for your own registrations'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if registration already has a payment
    if hasattr(registration, 'payment'):
        return Response(
            {'error': 'Payment already exists for this registration'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create payment
    payment = Payment.objects.create(
        registration=registration,
        user=request.user,
        amount=registration.total_amount,
        currency='USD',
        payment_method=payment_method,
        status='pending'
    )
    
    serializer = PaymentSerializer(payment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([CanManagePayments])
def update_payment_status(request, pk):
    """Update payment status (admin only)"""
    payment = get_object_or_404(Payment, pk=pk)
    
    serializer = PaymentStatusUpdateSerializer(
        payment, 
        data=request.data, 
        partial=True
    )
    
    if serializer.is_valid():
        old_status = payment.status
        new_status = serializer.validated_data.get('status')
        
        # Business logic for status transitions
        if old_status == 'pending' and new_status == 'processing':
            payment.process_payment()
        elif old_status in ['pending', 'processing'] and new_status == 'completed':
            transaction_id = serializer.validated_data.get('transaction_id')
            gateway_response = serializer.validated_data.get('gateway_response')
            payment.complete_payment(transaction_id, gateway_response)
        elif old_status in ['pending', 'processing'] and new_status == 'failed':
            gateway_response = serializer.validated_data.get('gateway_response')
            payment.fail_payment(gateway_response=gateway_response)
        elif old_status == 'completed' and new_status == 'refunded':
            # Handle refund separately
            pass
        elif new_status == 'cancelled':
            payment.cancel_payment()
        else:
            return Response(
                {'error': f'Invalid status transition from {old_status} to {new_status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'message': 'Payment status updated successfully',
            'payment': PaymentSerializer(payment).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([CanManagePayments])
def refund_payment(request, pk):
    """Refund a payment"""
    payment = get_object_or_404(Payment, pk=pk)
    
    if payment.status != 'completed':
        return Response(
            {'error': 'Can only refund completed payments'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = RefundPaymentSerializer(data=request.data)
    if serializer.is_valid():
        amount = serializer.validated_data.get('amount')
        reason = serializer.validated_data.get('reason', '')
        
        # If no amount specified, refund full amount
        if amount is None:
            amount = payment.amount
            
        # Check if amount doesn't exceed payment amount
        if amount > payment.amount:
            return Response(
                {'error': 'Refund amount cannot exceed payment amount'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.refund_payment(amount, reason)
        
        return Response({
            'message': 'Payment refunded successfully',
            'payment': PaymentSerializer(payment).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)