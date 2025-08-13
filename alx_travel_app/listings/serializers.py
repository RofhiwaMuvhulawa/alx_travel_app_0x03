from rest_framework import serializers
from .models import Listing, Booking, Payment

class ListingSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Listing
        fields = ['id', 'title', 'description', 'location', 'price_per_night', 'owner', 'created_at', 'updated_at', 'is_available']

class BookingSerializer(serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=Listing.objects.all())
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Booking
        fields = ['id', 'listing', 'user', 'start_date', 'end_date', 'total_price', 'status', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())
    
    class Meta:
        model = Payment
        fields = ['id', 'booking', 'transaction_id', 'chapa_tx_ref', 'amount', 'currency', 
                 'status', 'payment_method', 'chapa_reference', 'checkout_url', 
                 'created_at', 'updated_at', 'paid_at']
        read_only_fields = ['transaction_id', 'chapa_reference', 'checkout_url', 'paid_at']

class PaymentInitiationSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    return_url = serializers.URLField()
    callback_url = serializers.URLField(required=False)
