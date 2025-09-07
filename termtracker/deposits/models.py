from django.conf import settings
from django.db import models
from decimal import Decimal
from datetime import date
from django.utils import timezone


class Deposit(models.Model):
    SIMPLE = 'SIMPLE'
    MONTHLY = 'MONTHLY'
    ANNUAL = 'ANNUAL'
    COMPOUNDING_CHOICES = [
        (SIMPLE, 'Simple'),
        (MONTHLY, 'Monthly'),
        (ANNUAL, 'Annual')
    ]

    AUD = 'AUD'
    GBP = 'GBP'
    CURRENCY_CHOICES = [
        (AUD, 'AUD'),
        (GBP, 'GBP')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    annual_rate = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    compounding = models.CharField(max_length=10, choices=COMPOUNDING_CHOICES)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    fx_aud_to_gbp = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal('0.520000'))
    fx_gbp_to_aud = models.DecimalField(max_digits=12, decimal_places=6, default=Decimal('1.923077'))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"

    @property
    def days(self) -> int:
        return (self.end_date - self.start_date).days

    def _term_years(self) -> Decimal:
        return Decimal(self.days) / Decimal('365')

    def _rate_decimal(self) -> Decimal:
        return (self.annual_rate or Decimal('0')) / Decimal('100')

    def gross_interest_native(self) -> Decimal:
        P = self.principal
        r = self._rate_decimal()
        t = self._term_years()

        if self.compounding == self.SIMPLE:
            return (P * r * t).quantize(Decimal('0.01'))
        elif self.compounding == self.MONTHLY:
            n = Decimal('12')
            A = (P * (1 + r / n) ** (n * t))
            return (A - P).quantize(Decimal('0.01'))
        else:
            n = Decimal('1')
            A = (P * (1 + r / n) ** (n * t))
            return (A - P).quantize(Decimal('0.01'))

    def principal_in(self, target: str) -> Decimal:
        if target == self.currency:
            return self.principal
        if self.currency == self.GBP and target == self.AUD:
            return (self.principal * self.fx_gbp_to_aud).quantize(Decimal('0.01'))
        if self.currency == self.AUD and target == self.GBP:
            return (self.principal * self.fx_aud_to_gbp).quantize(Decimal('0.01'))
        return self.principal

    def interest_in(self, target: str) -> Decimal:
        gross = self.gross_interest_native()
        if target == self.currency:
            return gross
        if self.currency == self.GBP and target == self.AUD:
            return (gross * self.fx_gbp_to_aud).quantize(Decimal('0.01'))
        if self.currency == self.AUD and target == self.GBP:
            return (gross * self.fx_aud_to_gbp).quantize(Decimal('0.01'))
        return gross

    def estimated_tax(self, profile: 'TaxProfile') -> Decimal:
        interest = self.interest_in(self.AUD if profile.country == 'AU' else self.GBP)
        rate = (profile.marginal_rate or Decimal('0')) / Decimal('100')
        return (interest * rate).quantize(Decimal('0.01'))


class Pension(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tax_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    annual_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))  # if interest applies
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=3, choices=Deposit.CURRENCY_CHOICES)  # reuses Deposit choices
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.currency})"

    def annual_amount(self) -> Decimal:
        return (self.monthly_amount * 12).quantize(Decimal('0.01'))

    def annual_tax_paid(self) -> Decimal:
        return (self.tax_paid * 12).quantize(Decimal('0.01'))

    def estimated_tax(self, profile: 'TaxProfile') -> Decimal:
        amount = self.annual_amount()
        rate = (profile.marginal_rate or Decimal('0')) / Decimal('100')
        return (amount * rate).quantize(Decimal('0.01'))


class TaxProfile(models.Model):
    AU = 'AU'
    GB = 'GB'
    COUNTRY_CHOICES = [
        (AU, 'Australia'),
        (GB, 'United Kingdom'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default=AU)
    marginal_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # %
    tax_year_start_month = models.IntegerField(default=7)  # July for AU
    tax_year_start_day = models.IntegerField(default=1)
    tax_threshold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_threshold_currency = models.CharField(max_length=3, default='AUD')

    def save(self, *args, **kwargs):
        # Set default thresholds based on country
        if self.country == self.AU and self.tax_threshold == 0:
            self.tax_threshold = Decimal('18500')
            self.tax_threshold_currency = 'AUD'
        elif self.country == self.GB and self.tax_threshold == 0:
            self.tax_threshold = Decimal('12900')
            self.tax_threshold_currency = 'GBP'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.country}"
