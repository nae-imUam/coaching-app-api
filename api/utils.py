import random
import string
from django.core.mail import send_mail
from django.conf import settings


def generate_otp(length=6):
    """Generate a random OTP"""
    return ''.join(random.choices(string.digits, k=length))


def send_otp_sms(phone, otp):
    """
    Send OTP via SMS
    Note: Implement actual SMS gateway integration (Twilio, AWS SNS, etc.)
    """
    # TODO: Implement SMS gateway
    print(f"Sending OTP {otp} to {phone}")
    return True


def send_password_reset_sms(phone, token):
    """
    Send password reset token via SMS
    Note: Implement actual SMS gateway integration
    """
    # TODO: Implement SMS gateway
    print(f"Sending reset token {token} to {phone}")
    return True


def format_phone_number(phone):
    """Format phone number to standard format"""
    # Remove all non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Add country code if not present
    if not phone.startswith('91') and len(phone) == 10:
        phone = '91' + phone
    
    return phone


def calculate_percentage(obtained, total):
    """Calculate percentage"""
    if total == 0:
        return 0
    return round((obtained / total) * 100, 2)