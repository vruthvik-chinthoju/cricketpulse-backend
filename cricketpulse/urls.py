from django.urls import path, include
from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from core.views import GoogleLogin,GithubLogin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/login/', TokenObtainPairView.as_view()),
    path('api/refresh/', TokenRefreshView.as_view()),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('api/auth/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('api/auth/github/', GithubLogin.as_view(), name='github_login'),
]

