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

from django.core.mail import send_mail
from django.conf import settings

def send_password_reset_email(email, token, user_name="User"):
    subject = "Password Reset Request"
    plain_message = f"Hi {user_name},\n\nYour reset token is: {token}\n\nValid for 1 hour."
    html_message = f"""
    <div style="font-family:Arial,sans-serif;padding:24px;">
      <h2>Password Reset</h2>
      <p>Hi <strong>{user_name}</strong>,</p>
      <p>Your reset token is:</p>
      <pre style="background:#f0f0f0;padding:12px;border-radius:6px;">{token}</pre>
      <p>Valid for <strong>1 hour</strong>. If you didn't request this, ignore this email.</p>
    </div>
    """
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
        return False