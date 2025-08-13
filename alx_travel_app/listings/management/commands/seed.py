from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from listings.models import Listing
import random

class Command(BaseCommand):
    help = 'Seeds the database with sample listings'

    def handle(self, *args, **kwargs):
        # Ensure at least one user exists
        if not User.objects.filter(username='testuser').exists():
            User.objects.create_user(username='testuser', password='testpass123')

        user = User.objects.get(username='testuser')

        # Sample data for listings
        sample_listings = [
            {
                'title': 'Cozy Beachfront Villa',
                'description': 'A beautiful villa by the sea with stunning views.',
                'location': 'Cape Town, South Africa',
                'price_per_night': 150.00,
            },
            {
                'title': 'Mountain Retreat Cabin',
                'description': 'A serene cabin in the mountains, perfect for hiking.',
                'location': 'Drakensberg, South Africa',
                'price_per_night': 100.00,
            },
            {
                'title': 'City Loft Apartment',
                'description': 'Modern loft in the heart of the city.',
                'location': 'Johannesburg, South Africa',
                'price_per_night': 80.00,
            },
        ]

        # Create listings
        for listing_data in sample_listings:
            Listing.objects.get_or_create(
                title=listing_data['title'],
                defaults={
                    'description': listing_data['description'],
                    'location': listing_data['location'],
                    'price_per_night': listing_data['price_per_night'],
                    'owner': user,
                    'is_available': random.choice([True, False]),
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database with sample listings'))
      
