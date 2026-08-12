from rest_framework import generics, permissions

from .models import User
from .serializers import RegisterSerializer, UserProfileSerializer


class RegisterView(generics.CreateAPIView):
    """Public endpoint to create a new account."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/accounts/profile/  -> view own profile
    PUT/PATCH /api/accounts/profile/ -> update own profile
    Always operates on the currently authenticated user -- there is no
    pk in the URL, so users can never view/edit someone else's profile.
    """

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
