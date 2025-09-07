from datetime import date, datetime
from decimal import Decimal
from .models import Deposit, Pension


def get_tax_year_period(year, country):
    """Get the start and end dates for a tax year in a specific country."""
    if country == 'AU':
        # Australian tax year: July 1 - June 30
        start = date(year, 7, 1)
        end = date(year + 1, 6, 30)
    else:  # UK
        # UK tax year: April 6 - April 5
        start = date(year, 4, 6)
        end = date(year + 1, 4, 5)
    return start, end


def calculate_interest_in_period(deposit, period_start, period_end):
    """Calculate interest earned by a deposit within a specific period.
    
    Returns the interest amount earned during the period.
    """
    # If deposit doesn't overlap with period, return 0
    if deposit.end_date < period_start or deposit.start_date > period_end:
        return Decimal('0.00')
    
    # Calculate the overlapping period
    overlap_start = max(deposit.start_date, period_start)
    overlap_end = min(deposit.end_date, period_end)
    
    # Calculate days in overlap period
    overlap_days = (overlap_end - overlap_start).days
    
    # If no overlap, return 0
    if overlap_days <= 0:
        return Decimal('0.00')
    
    # Calculate total days in deposit period
    total_deposit_days = (deposit.end_date - deposit.start_date).days
    
    # Calculate prorated interest
    if total_deposit_days > 0:
        total_interest = deposit.gross_interest_native()
        prorated_interest = (Decimal(overlap_days) / Decimal(total_deposit_days)) * total_interest
        return prorated_interest.quantize(Decimal('0.01'))
    
    return Decimal('0.00')


def calculate_tax_obligations(deposits, year, profile_au, profile_uk):
    """Calculate tax obligations for a specific year for both countries."""
    # Get user's pensions
    pensions = Pension.objects.filter(user=profile_au.user)
    
    # Calculate UK tax obligations
    uk_start, uk_end = get_tax_year_period(year, 'GB')
    uk_total_interest = Decimal('0.00')
    
    # Calculate interest for UK tax year from deposits
    for deposit in deposits:
        if deposit.currency == Deposit.GBP:
            uk_total_interest += calculate_interest_in_period(deposit, uk_start, uk_end)
    
    # Calculate pension amounts for UK tax year
    uk_total_pension = Decimal('0.00')
    uk_total_tax_paid = Decimal('0.00')
    for pension in pensions:
        if pension.currency == 'GBP':
            # For pensions, we add the annual amount (12 months of monthly payments)
            uk_total_pension += pension.annual_amount()
            # Add up the annual tax paid
            uk_total_tax_paid += pension.annual_tax_paid()
    
    # Total UK income is interest + pension
    uk_total_income = uk_total_interest + uk_total_pension
    
    # Apply UK tax threshold
    uk_taxable_income = max(Decimal('0.00'), uk_total_income - profile_uk.tax_threshold)
    uk_tax_owed = (uk_taxable_income * profile_uk.marginal_rate / 100).quantize(Decimal('0.01'))
    # Subtract already paid tax
    uk_tax_owed = max(Decimal('0.00'), uk_tax_owed - uk_total_tax_paid)
    
    # Calculate Australian tax obligations
    au_start, au_end = get_tax_year_period(year, 'AU')
    au_total_interest = Decimal('0.00')
    
    # Calculate interest for Australian tax year
    for deposit in deposits:
        if deposit.currency == Deposit.AUD:
            au_total_interest += calculate_interest_in_period(deposit, au_start, au_end)
    
    # Calculate pension amounts for Australian tax year
    au_total_pension = Decimal('0.00')
    au_total_tax_paid = Decimal('0.00')
    for pension in pensions:
        if pension.currency == 'AUD':
            # For pensions, we add the annual amount (12 months of monthly payments)
            au_total_pension += pension.annual_amount()
            # Add up the annual tax paid
            au_total_tax_paid += pension.annual_tax_paid()
    
    # Total Australian income is interest + pension
    au_total_income = au_total_interest + au_total_pension
    
    # Apply Australian tax threshold
    au_taxable_income = max(Decimal('0.00'), au_total_income - profile_au.tax_threshold)
    au_tax_owed = (au_taxable_income * profile_au.marginal_rate / 100).quantize(Decimal('0.01'))
    # Subtract already paid tax
    au_tax_owed = max(Decimal('0.00'), au_tax_owed - au_total_tax_paid)
    
    return {
        'uk': {
            'tax_year_start': uk_start.strftime('%d/%m/%Y'),
            'tax_year_end': uk_end.strftime('%d/%m/%Y'),
            'total_interest': uk_total_interest,
            'total_pension': uk_total_pension,
            'total_tax_paid': uk_total_tax_paid,
            'total_income': uk_total_income,
            'threshold': profile_uk.tax_threshold,
            'taxable_income': uk_taxable_income,
            'tax_owed': uk_tax_owed,
        },
        'au': {
            'tax_year_start': au_start.strftime('%d/%m/%Y'),
            'tax_year_end': au_end.strftime('%d/%m/%Y'),
            'total_interest': au_total_interest,
            'total_pension': au_total_pension,
            'total_tax_paid': au_total_tax_paid,
            'total_income': au_total_income,
            'threshold': profile_au.tax_threshold,
            'taxable_income': au_taxable_income,
            'tax_owed': au_tax_owed,
        }
    }