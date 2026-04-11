from django.urls import path
from .api_views import RegisterAPI, LoginAPI, UserAPI, ProfileUpdateAPI

urlpatterns = [
    path('auth/register/', RegisterAPI.as_view(), name='api-register'),
    path('auth/login/', LoginAPI.as_view(), name='api-login'),
    path('auth/user/', UserAPI.as_view(), name='api-user'),
    path('auth/profile/update/', ProfileUpdateAPI.as_view(), name='api-profile-update'),
]
