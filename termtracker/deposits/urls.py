from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Deposits
    path('deposits/', views.deposit_list, name='deposit_list'),
    path('deposits/new/', views.deposit_create, name='deposit_create'),
    path('deposits/<int:pk>/edit/', views.deposit_edit, name='deposit_edit'),
    path('deposits/<int:pk>/delete/', views.deposit_delete, name='deposit_delete'),

    # Pensions
    path('pensions/', views.pension_list, name='pension_list'),
    path('pensions/new/', views.pension_create, name='pension_create'),
    path('pensions/<int:pk>/edit/', views.pension_edit, name='pension_edit'),
    path('pensions/<int:pk>/delete/', views.pension_delete, name='pension_delete'),

    # Registration
    path('accounts/register/', views.register_view, name='register'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Tax Obligations
    path('tax-obligations/', views.tax_obligations, name='tax_obligations'),

    # Logout
    path('logout/', views.logout_view, name='logout'),

    # Login
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
]
