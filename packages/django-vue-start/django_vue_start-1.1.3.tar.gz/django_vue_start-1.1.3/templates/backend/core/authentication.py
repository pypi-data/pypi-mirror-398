from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from allauth.account.models import EmailAddress

User = get_user_model()


class EmailVerificationBackend(ModelBackend):
    """
    Custom authentication backend that enforces email verification.
    Users must have at least one verified email address to login.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # First, use the default authentication
        user = super().authenticate(request, username=username, password=password, **kwargs)
        
        if user is None:
            return None
        
        # Check if user is a superuser (allow superusers to bypass)
        if user.is_superuser:
            return user
        
        # Check if the user has any email addresses in Allauth
        email_addresses = EmailAddress.objects.filter(user=user)
        
        if not email_addresses.exists():
            # No EmailAddress in Allauth - this user was created before Allauth setup
            # Block login to force them to register properly
            return None
        
        # Check if at least one email is verified
        has_verified_email = email_addresses.filter(verified=True).exists()
        
        if not has_verified_email:
            # No verified email - block login
            return None
        
        return user
