"""
Modelos de dados para o cliente PixGo
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PaymentStatus(str, Enum):
    """Status possíveis de um pagamento"""
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass
class Payment:
    """Representa um pagamento PIX no PixGo"""
    
    payment_id: str
    amount: float
    status: PaymentStatus
    qr_code: str
    qr_image_url: str
    created_at: str
    expires_at: str
    external_id: Optional[str] = None
    description: Optional[str] = None
    customer_name: Optional[str] = None
    customer_cpf: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None
    updated_at: Optional[str] = None
    payer_name: Optional[str] = None
    payer_cpf: Optional[str] = None
    payer_phone: Optional[str] = None
    completed_at: Optional[str] = None
    expired_at: Optional[str] = None
    refunded_at: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Payment':
        """Cria uma instância de Payment a partir de um dicionário"""
        # Converter status para enum
        status = data.get('status')
        if isinstance(status, str):
            status = PaymentStatus(status)
        
        return cls(
            payment_id=data.get('payment_id'),
            external_id=data.get('external_id'),
            amount=data.get('amount'),
            status=status,
            qr_code=data.get('qr_code'),
            qr_image_url=data.get('qr_image_url'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            expires_at=data.get('expires_at'),
            description=data.get('description'),
            customer_name=data.get('customer_name'),
            customer_cpf=data.get('customer_cpf'),
            customer_email=data.get('customer_email'),
            customer_phone=data.get('customer_phone'),
            customer_address=data.get('customer_address'),
            payer_name=data.get('payer_name'),
            payer_cpf=data.get('payer_cpf'),
            payer_phone=data.get('payer_phone'),
            completed_at=data.get('completed_at'),
            expired_at=data.get('expired_at'),
            refunded_at=data.get('refunded_at'),
        )
    
    def to_dict(self) -> dict:
        """Converte o pagamento para um dicionário"""
        result = {
            'payment_id': self.payment_id,
            'amount': self.amount,
            'status': self.status.value if isinstance(self.status, PaymentStatus) else self.status,
            'qr_code': self.qr_code,
            'qr_image_url': self.qr_image_url,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
        }
        
        # Adicionar campos opcionais se existirem
        optional_fields = [
            'external_id', 'description', 'customer_name', 'customer_cpf',
            'customer_email', 'customer_phone', 'customer_address', 'updated_at',
            'payer_name', 'payer_cpf', 'payer_phone', 'completed_at',
            'expired_at', 'refunded_at'
        ]
        
        for field in optional_fields:
            value = getattr(self, field, None)
            if value is not None:
                result[field] = value
        
        return result
    
    def is_paid(self) -> bool:
        """Retorna True se o pagamento foi confirmado"""
        return self.status == PaymentStatus.COMPLETED
    
    def is_pending(self) -> bool:
        """Retorna True se o pagamento está pendente"""
        return self.status == PaymentStatus.PENDING
    
    def is_expired(self) -> bool:
        """Retorna True se o pagamento expirou"""
        return self.status == PaymentStatus.EXPIRED


@dataclass
class WebhookEvent:
    """Representa um evento de webhook do PixGo"""
    
    event: str
    timestamp: str
    data: Payment
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WebhookEvent':
        """Cria uma instância de WebhookEvent a partir de um dicionário"""
        return cls(
            event=data.get('event'),
            timestamp=data.get('timestamp'),
            data=Payment.from_dict(data.get('data', {}))
        )
