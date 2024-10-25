from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_email, user_field, user_username
from django.contrib.auth import get_user_model
from Users.models import Role

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # This hook is called before the social account is logged in
        # and before the pre-existing social account is connected.
        user = sociallogin.user
        if user.id:
            return
        try:
            # Check if a user with this email already exists
            existing_user = User.objects.get(email=user_email(user))
            # If we get here, the user exists, so connect this new social login to the existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        # Here you can add any additional user setup, like assigning roles
        #For example:
        if not user.username:
            user.username = user.email.split('@')[0]
        
        # Set session
        request.session['user_name'] = user.username
        request.session['socialaccount_login'] = True
        request.session.save()
        customer_role, created = Role.objects.get_or_create(name='Customer')
        user.role.add(customer_role)
        user.save()
        user.role.add(customer_role)
        return user
