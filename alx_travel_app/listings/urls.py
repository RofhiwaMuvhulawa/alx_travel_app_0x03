from django.urls import path
from .views import (
    listing_list_create, listing_detail, 
    booking_list_create, booking_detail,
    initiate_payment, verify_payment, payment_list, payment_detail
)

urlpatterns = [
    # Listings API
    path('listings/', listing_list_create, name='listing-list-create'),
    path('listings/<int:pk>/', listing_detail, name='listing-detail'),

    # Bookings API
    path('bookings/', booking_list_create, name='booking-list-create'),
    path('bookings/<int:pk>/', booking_detail, name='booking-detail'),
    
    # Payment API
    path('payments/initiate/', initiate_payment, name='initiate-payment'),
    path('payments/verify/<str:tx_ref>/', verify_payment, name='verify-payment'),
    path('payments/', payment_list, name='payment-list'),
    path('payments/<int:pk>/', payment_detail, name='payment-detail'),
]
