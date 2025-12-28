"""
PixGo - Cliente Python para API do PixGo
=========================================

Cliente Python para integração com a API de pagamentos PIX do PixGo.

Exemplo de uso:
    >>> from pixgo import PixGoClient
    >>> client = PixGoClient(api_key="pk_seu_token_aqui")
    >>> payment = client.create_payment(amount=25.50, description="Produto XYZ")
    >>> print(payment.qr_code)

"""

from .client import PixGoClient
from .models import Payment, PaymentStatus
from .exceptions import (
    PixGoException,
    PixGoAPIError,
    PixGoValidationError,
    PixGoAuthenticationError,
    PixGoRateLimitError,
)

__version__ = "1.0.0"
__author__ = "PixGo Python Client"
__all__ = [
    "PixGoClient",
    "Payment",
    "PaymentStatus",
    "PixGoException",
    "PixGoAPIError",
    "PixGoValidationError",
    "PixGoAuthenticationError",
    "PixGoRateLimitError",
]
