"""
Testes unitários para o cliente PixGo
"""
import pytest
from unittest.mock import Mock, patch
from pixgo import (
    PixGoClient,
    Payment,
    PaymentStatus,
    PixGoValidationError,
    PixGoAuthenticationError,
    PixGoAPIError,
)


@pytest.fixture
def client():
    """Fixture que retorna um cliente PixGo configurado"""
    return PixGoClient(api_key="pk_test_key_12345")


@pytest.fixture
def mock_payment_data():
    """Fixture com dados de exemplo de um pagamento"""
    return {
        "payment_id": "dep_1234567890abcdef",
        "external_id": "pedido_123",
        "amount": 25.50,
        "status": "pending",
        "qr_code": "00020126580014BR.GOV.BCB.PIX...",
        "qr_image_url": "https://pixgo.org/qr/dep_1234567890abcdef.png",
        "expires_at": "2025-01-15T12:20:00",
        "created_at": "2025-01-15T12:00:00",
        "description": "Produto XYZ",
        "customer_name": "João Silva",
        "customer_cpf": "12345678901",
    }


class TestPixGoClient:
    """Testes para a classe PixGoClient"""
    
    def test_inicializacao_com_api_key_valida(self):
        """Testa inicialização com API key válida"""
        client = PixGoClient(api_key="pk_test_key")
        assert client.api_key == "pk_test_key"
        assert client.timeout == 30
    
    def test_inicializacao_sem_api_key(self):
        """Testa que levanta erro se API key não for fornecida"""
        with pytest.raises(PixGoValidationError):
            PixGoClient(api_key="")
    
    def test_inicializacao_com_api_key_invalida(self):
        """Testa que levanta erro se API key não começar com pk_"""
        with pytest.raises(PixGoValidationError):
            PixGoClient(api_key="invalid_key")
    
    def test_headers_configurados(self, client):
        """Testa se os headers estão configurados corretamente"""
        assert client._session.headers["X-API-Key"] == "pk_test_key_12345"
        assert client._session.headers["Content-Type"] == "application/json"
    
    @patch('pixgo.client.requests.Session.request')
    def test_create_payment_sucesso(self, mock_request, client, mock_payment_data):
        """Testa criação de pagamento com sucesso"""
        # Configurar mock
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "data": mock_payment_data
        }
        mock_request.return_value = mock_response
        
        # Criar pagamento
        payment = client.create_payment(
            amount=25.50,
            description="Produto XYZ",
            customer_name="João Silva"
        )
        
        # Verificações
        assert isinstance(payment, Payment)
        assert payment.payment_id == "dep_1234567890abcdef"
        assert payment.amount == 25.50
        assert payment.status == PaymentStatus.PENDING
    
    def test_create_payment_valor_minimo(self, client):
        """Testa validação de valor mínimo"""
        with pytest.raises(PixGoValidationError, match="Valor mínimo é R\\$ 10.00"):
            client.create_payment(amount=5.00)
    
    def test_create_payment_descricao_longa(self, client):
        """Testa validação de descrição muito longa"""
        descricao_longa = "x" * 201
        with pytest.raises(PixGoValidationError, match="máximo 200 caracteres"):
            client.create_payment(amount=10.00, description=descricao_longa)
    
    @patch('pixgo.client.requests.Session.request')
    def test_get_payment_status(self, mock_request, client):
        """Testa consulta de status de pagamento"""
        # Configurar mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"status": "completed"}
        }
        mock_request.return_value = mock_response
        
        # Consultar status
        status = client.get_payment_status("dep_1234567890abcdef")
        
        # Verificações
        assert status == PaymentStatus.COMPLETED
    
    @patch('pixgo.client.requests.Session.request')
    def test_autenticacao_falha(self, mock_request, client):
        """Testa erro de autenticação"""
        # Configurar mock
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "success": False,
            "error": "UNAUTHORIZED"
        }
        mock_request.return_value = mock_response
        
        # Tentar criar pagamento
        with pytest.raises(PixGoAuthenticationError):
            client.create_payment(amount=10.00)
    
    def test_context_manager(self):
        """Testa uso como context manager"""
        with PixGoClient(api_key="pk_test_key") as client:
            assert isinstance(client, PixGoClient)


class TestPayment:
    """Testes para a classe Payment"""
    
    def test_from_dict(self, mock_payment_data):
        """Testa criação de Payment a partir de dicionário"""
        payment = Payment.from_dict(mock_payment_data)
        
        assert payment.payment_id == "dep_1234567890abcdef"
        assert payment.amount == 25.50
        assert payment.status == PaymentStatus.PENDING
        assert payment.customer_name == "João Silva"
    
    def test_to_dict(self, mock_payment_data):
        """Testa conversão de Payment para dicionário"""
        payment = Payment.from_dict(mock_payment_data)
        data = payment.to_dict()
        
        assert data["payment_id"] == "dep_1234567890abcdef"
        assert data["amount"] == 25.50
        assert data["status"] == "pending"
    
    def test_is_paid(self):
        """Testa método is_paid()"""
        payment = Payment(
            payment_id="dep_123",
            amount=10.0,
            status=PaymentStatus.COMPLETED,
            qr_code="xxx",
            qr_image_url="xxx",
            created_at="2025-01-01",
            expires_at="2025-01-01"
        )
        assert payment.is_paid() is True
    
    def test_is_pending(self):
        """Testa método is_pending()"""
        payment = Payment(
            payment_id="dep_123",
            amount=10.0,
            status=PaymentStatus.PENDING,
            qr_code="xxx",
            qr_image_url="xxx",
            created_at="2025-01-01",
            expires_at="2025-01-01"
        )
        assert payment.is_pending() is True
    
    def test_is_expired(self):
        """Testa método is_expired()"""
        payment = Payment(
            payment_id="dep_123",
            amount=10.0,
            status=PaymentStatus.EXPIRED,
            qr_code="xxx",
            qr_image_url="xxx",
            created_at="2025-01-01",
            expires_at="2025-01-01"
        )
        assert payment.is_expired() is True


class TestPaymentStatus:
    """Testes para o enum PaymentStatus"""
    
    def test_valores(self):
        """Testa valores do enum"""
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.COMPLETED.value == "completed"
        assert PaymentStatus.EXPIRED.value == "expired"
        assert PaymentStatus.CANCELLED.value == "cancelled"
        assert PaymentStatus.REFUNDED.value == "refunded"
