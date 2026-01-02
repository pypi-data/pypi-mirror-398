"""
Internal Django webhook handlers for PayTechUZ.
"""
from .payme import PaymeWebhook
from .click import ClickWebhook
from .uzum import UzumWebhook
from .paynet import PaynetWebhook

__all__ = [
    'PaymeWebhook',
    'ClickWebhook',
    'UzumWebhook',
    'PaynetWebhook'
]
