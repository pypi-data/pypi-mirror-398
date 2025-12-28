"""
Cliente principal para a API do PixGo
"""
import requests
from typing import Optional, Dict, Any
from .models import Payment, PaymentStatus
from .exceptions import (
    PixGoAPIError,
    PixGoValidationError,
    PixGoAuthenticationError,
    PixGoRateLimitError,
)


class PixGoClient:
    """Cliente para interagir com a API do PixGo"""
    
    BASE_URL = "https://pixgo.org/api/v1"
    
    def __init__(self, api_key: str, timeout: int = 30):
        """
        Inicializa o cliente PixGo
        
        Args:
            api_key: Sua chave de API do PixGo (formato: pk_...)
            timeout: Timeout em segundos para as requisições (padrão: 30)
        
        Raises:
            PixGoValidationError: Se a API key não for fornecida
        """
        if not api_key:
            raise PixGoValidationError("API key é obrigatória")
        
        if not api_key.startswith("pk_"):
            raise PixGoValidationError("API key deve começar com 'pk_'")
        
        self.api_key = api_key
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "PixGo-Python-Client/1.0.0"
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Faz uma requisição à API do PixGo
        
        Args:
            method: Método HTTP (GET, POST, etc)
            endpoint: Endpoint da API (sem a base URL)
            data: Dados para enviar no corpo da requisição
            params: Parâmetros de query string
        
        Returns:
            Resposta da API em formato de dicionário
        
        Raises:
            PixGoAuthenticationError: Erro de autenticação
            PixGoRateLimitError: Limite de requisições excedido
            PixGoAPIError: Outros erros da API
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            
            # Tentar fazer parse do JSON
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"message": response.text}
            
            # Verificar erros HTTP
            if response.status_code == 401:
                raise PixGoAuthenticationError("API key inválida ou não autorizada")
            
            elif response.status_code == 429:
                raise PixGoRateLimitError("Limite de requisições excedido")
            
            elif response.status_code >= 400:
                error_message = response_data.get('message', 'Erro desconhecido')
                error_code = response_data.get('error', None)
                raise PixGoAPIError(
                    message=error_message,
                    error_code=error_code,
                    status_code=response.status_code,
                    response_data=response_data
                )
            
            return response_data
        
        except requests.exceptions.Timeout:
            raise PixGoAPIError(f"Timeout após {self.timeout} segundos")
        
        except requests.exceptions.ConnectionError as e:
            raise PixGoAPIError(f"Erro de conexão: {str(e)}")
        
        except (PixGoAuthenticationError, PixGoRateLimitError, PixGoAPIError):
            # Re-lançar exceções personalizadas
            raise
        
        except Exception as e:
            raise PixGoAPIError(f"Erro inesperado: {str(e)}")
    
    def create_payment(
        self,
        amount: float,
        description: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_cpf: Optional[str] = None,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_address: Optional[str] = None,
        external_id: Optional[str] = None,
        webhook_url: Optional[str] = None
    ) -> Payment:
        """
        Cria um novo pagamento PIX
        
        Args:
            amount: Valor do pagamento em reais (mínimo R$ 10.00)
            description: Descrição do pagamento (máx 200 caracteres)
            customer_name: Nome do cliente (máx 100 caracteres)
            customer_cpf: CPF ou CNPJ do cliente (11 ou 14 dígitos)
            customer_email: Email do cliente (máx 255 caracteres)
            customer_phone: Telefone do cliente (máx 20 caracteres)
            customer_address: Endereço completo do cliente (máx 500 caracteres)
            external_id: ID externo para identificação (máx 50 caracteres)
            webhook_url: URL para receber notificações de webhook
        
        Returns:
            Objeto Payment com os dados do pagamento criado
        
        Raises:
            PixGoValidationError: Erro de validação dos dados
            PixGoAPIError: Erro ao criar o pagamento
        
        Example:
            >>> client = PixGoClient(api_key="pk_seu_token")
            >>> payment = client.create_payment(
            ...     amount=25.50,
            ...     description="Produto XYZ",
            ...     customer_name="João Silva",
            ...     customer_cpf="12345678901"
            ... )
            >>> print(payment.qr_code)
        """
        # Validações básicas
        if amount < 10.0:
            raise PixGoValidationError("Valor mínimo é R$ 10.00")
        
        if description and len(description) > 200:
            raise PixGoValidationError("Descrição deve ter no máximo 200 caracteres")
        
        if customer_name and len(customer_name) > 100:
            raise PixGoValidationError("Nome do cliente deve ter no máximo 100 caracteres")
        
        if customer_email and len(customer_email) > 255:
            raise PixGoValidationError("Email deve ter no máximo 255 caracteres")
        
        if external_id and len(external_id) > 50:
            raise PixGoValidationError("external_id deve ter no máximo 50 caracteres")
        
        # Montar payload
        payload = {"amount": amount}
        
        if description:
            payload["description"] = description
        if customer_name:
            payload["customer_name"] = customer_name
        if customer_cpf:
            payload["customer_cpf"] = customer_cpf
        if customer_email:
            payload["customer_email"] = customer_email
        if customer_phone:
            payload["customer_phone"] = customer_phone
        if customer_address:
            payload["customer_address"] = customer_address
        if external_id:
            payload["external_id"] = external_id
        if webhook_url:
            payload["webhook_url"] = webhook_url
        
        # Fazer requisição
        response = self._make_request("POST", "payment/create", data=payload)
        
        # Retornar objeto Payment
        if response.get('success') and 'data' in response:
            return Payment.from_dict(response['data'])
        else:
            raise PixGoAPIError("Resposta da API não contém dados do pagamento")
    
    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Consulta o status de um pagamento
        
        Args:
            payment_id: ID do pagamento (formato: dep_...)
        
        Returns:
            Status atual do pagamento
        
        Raises:
            PixGoValidationError: Se o payment_id não for fornecido
            PixGoAPIError: Erro ao consultar o status
        
        Note:
            Este endpoint tem limite de 1.000 requisições por 24 horas
        
        Example:
            >>> status = client.get_payment_status("dep_1234567890abcdef")
            >>> if status == PaymentStatus.COMPLETED:
            ...     print("Pagamento confirmado!")
        """
        if not payment_id:
            raise PixGoValidationError("payment_id é obrigatório")
        
        response = self._make_request("GET", f"payment/{payment_id}/status")
        
        if response.get('success') and 'data' in response:
            status = response['data'].get('status')
            return PaymentStatus(status)
        else:
            raise PixGoAPIError("Resposta da API não contém status do pagamento")
    
    def get_payment(self, payment_id: str) -> Payment:
        """
        Obtém detalhes completos de um pagamento
        
        Args:
            payment_id: ID do pagamento (formato: dep_...)
        
        Returns:
            Objeto Payment com todos os dados do pagamento
        
        Raises:
            PixGoValidationError: Se o payment_id não for fornecido
            PixGoAPIError: Erro ao consultar o pagamento
        
        Example:
            >>> payment = client.get_payment("dep_1234567890abcdef")
            >>> print(f"Status: {payment.status}")
            >>> print(f"QR Code: {payment.qr_code}")
        """
        if not payment_id:
            raise PixGoValidationError("payment_id é obrigatório")
        
        response = self._make_request("GET", f"payment/{payment_id}")
        
        if response.get('success') and 'data' in response:
            return Payment.from_dict(response['data'])
        else:
            raise PixGoAPIError("Resposta da API não contém dados do pagamento")
    
    def check_payment(self, payment_id: str) -> bool:
        """
        Verifica se um pagamento foi confirmado
        
        Args:
            payment_id: ID do pagamento (formato: dep_...)
        
        Returns:
            True se o pagamento foi confirmado, False caso contrário
        
        Example:
            >>> if client.check_payment("dep_1234567890abcdef"):
            ...     print("Pagamento confirmado!")
        """
        try:
            status = self.get_payment_status(payment_id)
            return status == PaymentStatus.COMPLETED
        except PixGoAPIError:
            return False
    
    def close(self):
        """Fecha a sessão HTTP"""
        self._session.close()
    
    def __enter__(self):
        """Suporte para context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Suporte para context manager"""
        self.close()
