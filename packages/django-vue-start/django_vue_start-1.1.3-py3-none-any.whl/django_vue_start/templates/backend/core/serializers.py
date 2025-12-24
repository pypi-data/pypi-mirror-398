from dj_rest_auth.serializers import LoginSerializer
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from django.contrib.auth import authenticate
from rest_framework import serializers


class EmailVerifiedLoginSerializer(LoginSerializer):
    """
    Custom login serializer that checks email verification before allowing login
    and resends verification email if needed
    """
    def validate(self, attrs):
        # Call parent validation first  
        attrs = super().validate(attrs)
        
        user = attrs.get('user')
        
        if user:
            # Allow superusers to bypass
            if user.is_superuser:
                return attrs
            
            # Check email verification
            email_addresses = EmailAddress.objects.filter(user=user)
            
            if not email_addresses.exists():
                raise serializers.ValidationError(
                    "Please register with a valid email address."
                )
            
            if not email_addresses.filter(verified=True).exists():
                # Get primary or first email
                primary_email = email_addresses.filter(primary=True).first()
                if not primary_email:
                    primary_email = email_addresses.first()
                
                # Send verification email
                try:
                    confirmation = EmailConfirmationHMAC(primary_email)
                    confirmation.send(request=self.context.get('request'))
                except Exception as e:
                    # If sending fails, just show the error without sending
                    pass
                
                raise serializers.ValidationError(
                    "E-mail is not verified. A new verification email has been sent to your inbox. Please check your email."
                )
        
        return attrs
