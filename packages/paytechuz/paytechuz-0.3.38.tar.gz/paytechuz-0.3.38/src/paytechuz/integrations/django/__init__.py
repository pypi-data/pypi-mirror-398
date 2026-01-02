"""
Django integration for PayTechUZ.
"""

# Check if Django dependencies are available
try:
    from paytechuz.core.dependencies import check_dependencies
    check_dependencies('django', raise_error=False)
except ImportError:
    pass  # dependencies module not available yet during build

# Register the app configuration
default_app_config = 'paytechuz.integrations.django.apps.PaytechuzConfig'

# This is used to prevent Django from creating new migrations
# when the model changes. Instead, users should use the provided
# migration or create their own if needed.
PAYTECHUZ_PREVENT_MIGRATIONS = True


def get_payment_transaction_model():
    """
    Get the PaymentTransaction model lazily to avoid AppRegistryNotReady errors.
    
    Usage:
        PaymentTransaction = get_payment_transaction_model()
    """
    from paytechuz.integrations.django.models import PaymentTransaction
    return PaymentTransaction


__all__ = ['get_payment_transaction_model']

