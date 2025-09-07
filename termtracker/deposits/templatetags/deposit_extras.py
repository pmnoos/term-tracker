from django import template

register = template.Library()

@register.filter
def interest_in(deposit, currency):
    return deposit.interest_in(currency)

@register.filter
def estimated_tax(deposit, profile):
    return deposit.estimated_tax(profile)
