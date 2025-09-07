from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.views.decorators.http import require_POST
from .forms import DepositForm, PensionForm, RegisterForm
from .models import Deposit, Pension, TaxProfile


def register_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('deposit_list')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def deposit_list(request):
    """Display a list of deposits for the current user."""
    deposits = Deposit.objects.filter(user=request.user)
    return render(request, 'deposits/deposit_list.html', {'deposits': deposits})


@login_required
def deposit_create(request):
    """Create a new deposit."""
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                deposit = form.save(commit=False)
                deposit.user = request.user
                deposit.save()
            messages.success(request, 'Deposit created successfully!')
            return redirect('deposit_list')
    else:
        form = DepositForm()
    return render(request, 'deposits/deposit_form.html', {'form': form})


@login_required
def deposit_edit(request, pk):
    """Edit an existing deposit."""
    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DepositForm(request.POST, instance=deposit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Deposit updated successfully!')
            return redirect('deposit_list')
    else:
        form = DepositForm(instance=deposit)
    return render(request, 'deposits/deposit_form.html', {'form': form, 'edit_mode': True})


@login_required
@require_POST
def deposit_delete(request, pk):
    """Delete a deposit."""
    deposit = get_object_or_404(Deposit, pk=pk, user=request.user)
    deposit.delete()
    messages.success(request, 'Deposit deleted successfully!')
    return redirect('deposit_list')


@login_required
def pension_list(request):
    """Display a list of pensions for the current user."""
    pensions = Pension.objects.filter(user=request.user)
    return render(request, 'pensions/pension_list.html', {'pensions': pensions})


@login_required
def pension_create(request):
    """Create a new pension."""
    if request.method == 'POST':
        form = PensionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                pension = form.save(commit=False)
                pension.user = request.user
                pension.save()
            messages.success(request, 'Pension created successfully!')
            return redirect('pension_list')
    else:
        form = PensionForm()
    return render(request, 'pensions/pension_form_custom.html', {'form': form})


@login_required
def pension_edit(request, pk):
    """Edit an existing pension."""
    pension = get_object_or_404(Pension, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PensionForm(request.POST, instance=pension)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pension updated successfully!')
            return redirect('pension_list')
    else:
        form = PensionForm(instance=pension)
    return render(request, 'pensions/pension_form_custom.html', {'form': form, 'edit_mode': True})


@login_required
@require_POST
def pension_delete(request, pk):
    """Delete a pension."""
    pension = get_object_or_404(Pension, pk=pk, user=request.user)
    pension.delete()
    messages.success(request, 'Pension deleted successfully!')
    return redirect('pension_list')


def home(request):
    """Display the home page."""
    return render(request, 'home.html')


@login_required
def dashboard(request):
    """Display the user dashboard with deposits and tax profiles."""
    deposits = Deposit.objects.filter(user=request.user)
    
    # Get or create tax profiles for the user
    profile_au, _ = TaxProfile.objects.get_or_create(
        user=request.user,
        country=TaxProfile.AU,
        defaults={'marginal_rate': 30}
    )
    profile_uk, _ = TaxProfile.objects.get_or_create(
        user=request.user,
        country=TaxProfile.GB,
        defaults={'marginal_rate': 20}
    )
    
    # Calculate summary statistics
    total_deposits = deposits.count()
    
    # Calculate total principal by currency
    total_principal_aud = sum(
        deposit.principal_in('AUD') for deposit in deposits if deposit.currency == 'AUD'
    )
    total_principal_gbp = sum(
        deposit.principal_in('GBP') for deposit in deposits if deposit.currency == 'GBP'
    )
    
    # Calculate total interest by currency
    total_interest_native = sum(deposit.gross_interest_native() for deposit in deposits)
    total_interest_aud = sum(deposit.interest_in('AUD') for deposit in deposits)
    total_interest_gbp = sum(deposit.interest_in('GBP') for deposit in deposits)
    
    # Calculate total estimated tax
    total_tax_au = sum(deposit.estimated_tax(profile_au) for deposit in deposits)
    total_tax_uk = sum(deposit.estimated_tax(profile_uk) for deposit in deposits)
    
    return render(request, 'dashboard.html', {
        'deposits': deposits,
        'profile_au': profile_au,
        'profile_uk': profile_uk,
        'total_deposits': total_deposits,
        'total_principal_aud': total_principal_aud,
        'total_principal_gbp': total_principal_gbp,
        'total_interest_native': total_interest_native,
        'total_interest_aud': total_interest_aud,
        'total_interest_gbp': total_interest_gbp,
        'total_tax_au': total_tax_au,
        'total_tax_uk': total_tax_uk,
    })


@login_required
def tax_obligations(request):
    """Display tax obligations for the user's deposits."""
    from django.utils import timezone
    from .utils import calculate_tax_obligations
    
    # Get user's deposits and pensions
    deposits = Deposit.objects.filter(user=request.user)
    pensions = Pension.objects.filter(user=request.user)
    
    # Get or create tax profiles
    profile_au, _ = TaxProfile.objects.get_or_create(
        user=request.user,
        country=TaxProfile.AU,
        defaults={'marginal_rate': 30, 'tax_threshold': 18500}
    )
    profile_uk, _ = TaxProfile.objects.get_or_create(
        user=request.user,
        country=TaxProfile.GB,
        defaults={'marginal_rate': 20, 'tax_threshold': 12900}
    )
    
    # Handle year selection
    current_year = timezone.now().year
    available_years = list(range(current_year - 2, current_year + 3))  # prev 2 + current + next 2
    
    selected_year = int(request.GET.get('year', current_year))
    
    # Calculate tax obligations for each year
    tax_data = calculate_tax_obligations(deposits, selected_year, profile_au, profile_uk)
    
    return render(request, 'tax_obligations.html', {
        'tax_data': tax_data,
        'pensions': pensions,
        'available_years': available_years,
        'selected_year': selected_year,
        'profile_au': profile_au,
        'profile_uk': profile_uk,
    })


def logout_view(request):
    """Handle user logout."""
    logout(request)
    return redirect('home')
