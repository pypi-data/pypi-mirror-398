"""
FastAPI integration for PayTechUZ.
"""

try:
    from paytechuz.core.dependencies import check_dependencies
    check_dependencies('fastapi', raise_error=False)
except ImportError:
    pass


from .models import Base, PaymentTransaction  # noqa: F401
from .schemas import (  # noqa: F401
    PaymentTransactionBase,
    PaymentTransactionCreate,
    PaymentTransaction as PaymentTransactionSchema,
    PaymentTransactionList,
    PaymeWebhookRequest,
    PaymeWebhookResponse,
    PaymeWebhookErrorResponse,
    ClickWebhookRequest,
    ClickWebhookResponse
)
from .routes import (  # noqa: F401
    router,
    PaymeWebhookHandler,
    ClickWebhookHandler
)
