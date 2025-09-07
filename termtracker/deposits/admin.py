from django.contrib import admin
from .models import Deposit, Pension, TaxProfile  # <-- include Pension if you want to manage it too

@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'principal', 'currency', 'start_date', 'end_date', 'annual_rate')

@admin.register(Pension)
class PensionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'monthly_amount', 'currency', 'start_date', 'end_date')

@admin.register(TaxProfile)
class TaxProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'country', 'marginal_rate')
