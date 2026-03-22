from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
import secrets

from ..models import User
from ..serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
)
from ..utils import send_password_reset_email


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    Register a new user
    POST /api/auth/register/
    Body: {
        "phone": "1234567890",
        "password": "securepassword",
        "name": "John Doe",
        "institute_name": "ABC Institute",
        "email": "john@example.com"  (optional)
    }
    """
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'User registered successfully',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

    return Response({
        'success': False,
        'message': 'Registration failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login user with phone and password
    POST /api/auth/login/
    Body: {
        "phone": "1234567890",
        "password": "securepassword"
    }
    """
    serializer = LoginSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'message': 'Login successful',
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

    return Response({
        'success': False,
        'message': 'Login failed',
        'errors': serializer.errors
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout user (client should delete tokens)
    POST /api/auth/logout/
    Headers: Authorization: Bearer <access_token>
    Body: { "refresh_token": "..." }  (optional — blacklists the token)
    """
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        return Response({
            'success': True,
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile_view(request):
    """
    Get current user profile
    GET /api/auth/profile/
    Headers: Authorization: Bearer <access_token>
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    Update user profile
    PUT/PATCH /api/auth/profile/update/
    Headers: Authorization: Bearer <access_token>
    Body: { "name": "...", "institute_name": "...", "email": "..." }
    """
    serializer = UserSerializer(request.user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            'success': True,
            'message': 'Profile updated successfully',
            'user': serializer.data
        }, status=status.HTTP_200_OK)

    return Response({
        'success': False,
        'message': 'Update failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    Change password for a logged-in user
    POST /api/auth/change-password/
    Headers: Authorization: Bearer <access_token>
    Body: {
        "old_password": "currentpassword",
        "new_password": "newpassword"
    }
    """
    serializer = ChangePasswordSerializer(data=request.data)

    if serializer.is_valid():
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'success': False,
                'message': 'Old password is incorrect'
            }, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)

    return Response({
        'success': False,
        'message': 'Password change failed',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
#  PASSWORD RESET  (no login required)
# ─────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """
    Step 1 — Request a password reset token.
    POST /api/auth/password-reset/request/
    Body: {
        "phone": "1234567890",
        "institute_name": "My Academy"   ← security verification field
    }

    Behaviour:
    • institute_name must match the account's institute_name (case-insensitive).
      This acts as a second factor so random people can't spam reset tokens.
    • If the phone exists AND has an email, the token is emailed.
    • If the phone exists but has NO email, we return a specific error
      so the frontend can tell the user to contact support.
    • If the phone does NOT exist we still return a generic success
      (prevents user enumeration).
    • In DEBUG mode only, the token is also included in the response
      so developers can test without a mail server.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid request',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    institute_name = request.data.get('institute_name', '').strip()

    if not institute_name:
        return Response({
            'success': False,
            'message': 'Institute name is required for verification.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generic response used when user is not found (anti-enumeration)
    generic_ok = Response({
        'success': True,
        'message': 'If the phone number is registered, a reset token has been sent to the associated email.'
    }, status=status.HTTP_200_OK)

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        return generic_ok

    # ── Security check: verify institute_name matches ──────────────────
    if user.institute_name.strip().lower() != institute_name.lower():
        # Return the same generic error as "user not found" to avoid
        # leaking whether the phone exists but institute_name was wrong.
        return Response({
            'success': False,
            'message': 'Institute name does not match our records. Please check and try again.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # User exists and institute matches — check they have an email
    if not user.email:
        return Response({
            'success': False,
            'message': (
                'No email address is linked to this account. '
                'Please contact support to reset your password.'
            )
        }, status=status.HTTP_400_BAD_REQUEST)

    # Generate a secure token and persist it
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_created = timezone.now()
    user.save(update_fields=['reset_token', 'reset_token_created'])

    # Send the token by email
    email_sent = send_password_reset_email(
        email=user.email,
        token=reset_token,
        user_name=user.name,
    )

    if not email_sent:
        # Wipe the token so a stale one is never left behind
        user.reset_token = None
        user.reset_token_created = None
        user.save(update_fields=['reset_token', 'reset_token_created'])

        return Response({
            'success': False,
            'message': (
                'We could not send the reset email right now. '
                'Please try again later or contact support.'
            )
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    response_data = {
        'success': True,
        'message': f'A password reset token has been sent to {_mask_email(user.email)}.',
        'email': _mask_email(user.email),   # Frontend uses this to show "sent to j***@gmail.com"
    }

    # ⚠️  Include raw token ONLY during development so you can test
    #    without a real mail server. Remove / guard this in production.
    from django.conf import settings
    if getattr(settings, 'DEBUG', False):
        response_data['debug_token'] = reset_token
        response_data['debug_note'] = (
            'debug_token is visible because DEBUG=True. '
            'Remove this in production.'
        )

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """
    Step 2 — Confirm the reset using the token and set a new password.
    POST /api/auth/password-reset/confirm/
    Body: {
        "phone": "1234567890",
        "token": "<token from email>",
        "new_password": "mynewpassword"
    }

    Token is valid for 1 hour. After use it is immediately invalidated.
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'message': 'Invalid request',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']

    try:
        user = User.objects.get(phone=phone, reset_token=token)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Invalid phone number or token.'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Check token age (1 hour expiry)
    if user.reset_token_created:
        age = timezone.now() - user.reset_token_created
        if age > timedelta(hours=1):
            # Clear the expired token
            user.reset_token = None
            user.reset_token_created = None
            user.save(update_fields=['reset_token', 'reset_token_created'])

            return Response({
                'success': False,
                'message': 'Reset token has expired. Please request a new one.'
            }, status=status.HTTP_400_BAD_REQUEST)

    # All good — update password and invalidate the token
    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_created = None
    user.save()

    return Response({
        'success': True,
        'message': 'Password has been reset successfully. You can now log in.'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token_view(request):
    """
    Verify if a JWT access token is still valid.
    POST /api/auth/verify-token/
    Body: { "token": "<access_token>" }
    """
    from rest_framework_simplejwt.tokens import AccessToken

    token = request.data.get('token')

    if not token:
        return Response({
            'success': False,
            'message': 'Token is required'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        AccessToken(token)
        return Response({
            'success': True,
            'message': 'Token is valid'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({
            'success': False,
            'message': 'Invalid or expired token'
        }, status=status.HTTP_401_UNAUTHORIZED)


# ── helpers ──────────────────────────────────

def _mask_email(email: str) -> str:
    """Return a masked email like  j***@gmail.com for display in responses."""
    try:
        local, domain = email.split('@', 1)
        masked_local = local[0] + '***' if len(local) > 1 else '***'
        return f"{masked_local}@{domain}"
    except Exception:
        return '***@***.***'
    



    