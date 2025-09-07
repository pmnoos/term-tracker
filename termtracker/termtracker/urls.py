from django.contrib import admin
from django.urls import path, include
from deposits.views import register_view, home

urlpatterns = [
    path('', home, name='home'),  # root URL
    path('admin/', admin.site.urls),
    path('accounts/register/', register_view, name='register'),
    path('deposits/', include('deposits.urls')),
]
