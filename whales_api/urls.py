from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

from whales_api.views import GoogleLogin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/', include('api.urls')),
    path('rest-auth/', include('rest_auth.urls')),
    path('rest-auth/google/', GoogleLogin.as_view(), name="google_login"),
    url(r'^accounts/', include('allauth.urls')),
]
