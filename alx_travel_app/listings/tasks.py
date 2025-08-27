from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id, user_email, user_name, listing_title, start_date, end_date, total_price):
    """
    Send booking confirmation email asynchronously
    """
    try:
        subject = f'Booking Confirmation - {listing_title}'
        
        # Create email content
        html_message = f"""
        <html>
        <body>
            <h2>Booking Confirmation</h2>
            <p>Dear {user_name},</p>
            <p>Your booking has been confirmed! Here are the details:</p>
            <ul>
                <li><strong>Property:</strong> {listing_title}</li>
                <li><strong>Check-in:</strong> {start_date}</li>
                <li><strong>Check-out:</strong> {end_date}</li>
                <li><strong>Total Price:</strong> ${total_price}</li>
                <li><strong>Booking ID:</strong> {booking_id}</li>
            </ul>
            <p>Thank you for choosing ALX Travel App!</p>
            <p>Best regards,<br>ALX Travel Team</p>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f'Booking confirmation email sent successfully to {user_email} for booking {booking_id}')
        return f'Email sent successfully to {user_email}'
        
    except Exception as exc:
        logger.error(f'Failed to send booking confirmation email to {user_email}: {str(exc)}')
        # Retry the task
        raise self.retry(exc=exc, countdown=60, max_retries=3)