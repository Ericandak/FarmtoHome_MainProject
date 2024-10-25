from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class EmailBackend(ModelBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        print(f"EmailBackend: Attempting authentication for email: {email}")
        try:
            user = User.objects.get(email=email)
            print(f"EmailBackend: User found: {user.username}")
            if user.check_password(password) and self.user_can_authenticate(user):
                print("EmailBackend: Password check passed")
                return user
            else:
                print("EmailBackend: Password check failed or user cannot be authenticated")
        except User.DoesNotExist:
            print(f"EmailBackend: No user found with email: {email}")
        return None