from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Listing, Booking, Payment
from .serializers import ListingSerializer, BookingSerializer, PaymentSerializer, PaymentInitiationSerializer
from .chapa_service import ChapaService
from .tasks import send_booking_confirmation_email
import uuid
import logging

logger = logging.getLogger(__name__)

### LISTINGS CRUD ###

@swagger_auto_schema(
    method='get',
    responses={200: ListingSerializer(many=True)}
)
@swagger_auto_schema(
    method='post',
    request_body=ListingSerializer,
    responses={201: ListingSerializer}
)
@api_view(['GET', 'POST'])
def listing_list_create(request):
    """Retrieve all listings or create a new listing"""
    if request.method == 'GET':
        listings = Listing.objects.all()
        serializer = ListingSerializer(listings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ListingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={200: ListingSerializer}
)
@swagger_auto_schema(
    method='put',
    request_body=ListingSerializer,
    responses={200: ListingSerializer}
)
@swagger_auto_schema(
    method='delete',
    responses={204: 'No Content'}
)
@api_view(['GET', 'PUT', 'DELETE'])
def listing_detail(request, pk):
    """Retrieve, update, or delete a listing by ID"""
    try:
        listing = Listing.objects.get(pk=pk)
    except Listing.DoesNotExist:
        return Response({"error": "Listing not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ListingSerializer(listing)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ListingSerializer(listing, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        listing.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


### BOOKINGS CRUD ###

@swagger_auto_schema(
    method='get',
    responses={200: BookingSerializer(many=True)}
)
@swagger_auto_schema(
    method='post',
    request_body=BookingSerializer,
    responses={201: BookingSerializer}
)
@api_view(['GET', 'POST'])
def booking_list_create(request):
    """List all bookings or create a new booking"""
    if request.method == 'GET':
        bookings = Booking.objects.all()
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = BookingSerializer(data=request.data)
        if serializer.is_valid():
            booking = serializer.save()
            
            # Trigger email notification asynchronously
            try:
                send_booking_confirmation_email.delay(
                    booking_id=booking.id,
                    user_email=booking.user_email,
                    user_name=booking.user_name,
                    listing_title=booking.listing.title,
                    start_date=str(booking.start_date),
                    end_date=str(booking.end_date),
                    total_price=str(booking.total_price)
                )
                logger.info(f'Email task queued for booking {booking.id}')
            except Exception as e:
                logger.error(f'Failed to queue email task for booking {booking.id}: {str(e)}')
                # Don't fail the booking creation if email task fails
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='get',
    responses={200: BookingSerializer}
)
@swagger_auto_schema(
    method='put',
    request_body=BookingSerializer,
    responses={200: BookingSerializer}
)
@swagger_auto_schema(
    method='delete',
    responses={204: 'No Content'}
)
@api_view(['GET', 'PUT', 'DELETE'])
def booking_detail(request, pk):
    """Retrieve, update, or delete a booking by ID"""
    try:
        booking = Booking.objects.get(pk=pk)
    except Booking.DoesNotExist:
        return Response({"error": "Booking not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = BookingSerializer(booking, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


### PAYMENT ENDPOINTS ###

@swagger_auto_schema(
    method='post',
    request_body=PaymentInitiationSerializer,
    responses={
        201: openapi.Response('Payment initiated successfully', PaymentSerializer),
        400: 'Bad Request',
        404: 'Booking not found'
    }
)
@api_view(['POST'])
def initiate_payment(request):
    """Initiate payment for a booking"""
    serializer = PaymentInitiationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    booking_id = serializer.validated_data['booking_id']
    return_url = serializer.validated_data['return_url']
    callback_url = serializer.validated_data.get('callback_url')
    
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check if payment already exists
    if hasattr(booking, 'payment'):
        if booking.payment.status == 'COMPLETED':
            return Response({'error': 'Payment already completed'}, status=status.HTTP_400_BAD_REQUEST)
        elif booking.payment.status == 'PENDING':
            return Response(PaymentSerializer(booking.payment).data, status=status.HTTP_200_OK)
    
    # Generate unique transaction reference
    tx_ref = f"ALX_TRAVEL_{booking.id}_{uuid.uuid4().hex[:8]}"
    
    # Initialize Chapa service
    chapa_service = ChapaService()
    
    # Initiate payment with Chapa
    chapa_response = chapa_service.initiate_payment(
        amount=booking.total_price,
        currency='ETB',
        email=booking.user.email,
        first_name=booking.user.first_name or booking.user.username,
        last_name=booking.user.last_name or '',
        tx_ref=tx_ref,
        callback_url=callback_url,
        return_url=return_url
    )
    
    if not chapa_response or chapa_response.get('status') != 'success':
        logger.error(f"Chapa payment initiation failed: {chapa_response}")
        return Response({'error': 'Payment initiation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Create or update payment record
    payment_data = chapa_response.get('data', {})
    payment, created = Payment.objects.get_or_create(
        booking=booking,
        defaults={
            'transaction_id': tx_ref,
            'chapa_tx_ref': tx_ref,
            'amount': booking.total_price,
            'currency': 'ETB',
            'status': 'PENDING',
            'checkout_url': payment_data.get('checkout_url')
        }
    )
    
    if not created:
        payment.checkout_url = payment_data.get('checkout_url')
        payment.save()
    
    return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('tx_ref', openapi.IN_PATH, description="Transaction reference", type=openapi.TYPE_STRING)
    ],
    responses={
        200: PaymentSerializer,
        404: 'Payment not found',
        500: 'Verification failed'
    }
)
@api_view(['POST'])
def verify_payment(request, tx_ref):
    """Verify payment status with Chapa"""
    try:
        payment = Payment.objects.get(chapa_tx_ref=tx_ref)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Initialize Chapa service
    chapa_service = ChapaService()
    
    # Verify payment with Chapa
    verification_response = chapa_service.verify_payment(tx_ref)
    
    if not verification_response:
        return Response({'error': 'Payment verification failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Update payment status based on Chapa response
    chapa_data = verification_response.get('data', {})
    chapa_status = chapa_data.get('status', '').lower()
    
    if chapa_status == 'success':
        payment.status = 'COMPLETED'
        payment.paid_at = timezone.now()
        payment.chapa_reference = chapa_data.get('reference')
        payment.payment_method = chapa_data.get('method')
        
        # Update booking status
        payment.booking.status = 'CONFIRMED'
        payment.booking.save()
        
        # TODO: Send confirmation email using Celery
        # send_booking_confirmation_email.delay(payment.booking.id)
        
    elif chapa_status in ['failed', 'cancelled']:
        payment.status = 'FAILED' if chapa_status == 'failed' else 'CANCELLED'
        payment.booking.status = 'CANCELLED'
        payment.booking.save()
    
    payment.save()
    
    return Response(PaymentSerializer(payment).data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method='get',
    responses={200: PaymentSerializer(many=True)}
)
@api_view(['GET'])
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.all()
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method='get',
    responses={200: PaymentSerializer}
)
@api_view(['GET'])
def payment_detail(request, pk):
    """Get payment details"""
    try:
        payment = Payment.objects.get(pk=pk)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = PaymentSerializer(payment)
    return Response(serializer.data)
