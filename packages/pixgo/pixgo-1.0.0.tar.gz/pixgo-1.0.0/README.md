# PixGo - Cliente Python

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Cliente Python para integração com a [API de pagamentos PIX do PixGo](https://pixgo.org/api/v1/docs).

## 📋 Sobre

O PixGo permite que você integre pagamentos PIX em sua aplicação de forma rápida e segura. Este pacote Python oferece uma interface simples e intuitiva para consumir a API do PixGo.

### Recursos

- ✅ Criação de pagamentos PIX instantâneos
- ✅ Consulta de status de pagamentos
- ✅ Obtenção de detalhes completos de pagamentos
- ✅ Suporte a webhooks para notificações em tempo real
- ✅ Validação de CPF/CNPJ
- ✅ Tratamento de erros robusto
- ✅ Suporte a context managers
- ✅ Type hints completo

## 🚀 Instalação

```bash
pip install pixgo
```

Ou instale a partir do código-fonte:

```bash
git clone https://github.com/DevWand/pixgo-python.git
cd pixgo-python
pip install -e .
```

## 📖 Uso Básico

### Configuração Inicial

Primeiro, obtenha sua API key:
1. Crie uma conta em [pixgo.org](https://pixgo.org)
2. Valide suas informações de carteira Liquid
3. Navegue até a seção "Checkouts"
4. Gere sua API key de produção

### Criar um Pagamento

```python
from pixgo import PixGoClient

# Inicializar o cliente
client = PixGoClient(api_key="pk_sua_chave_aqui")

# Criar um pagamento
payment = client.create_payment(
    amount=25.50,
    description="Produto XYZ",
    customer_name="João Silva",
    customer_cpf="12345678901",
    customer_email="joao@exemplo.com",
    customer_phone="(11) 99999-9999",
    external_id="pedido_123"
)

print(f"Pagamento criado: {payment.payment_id}")
print(f"QR Code: {payment.qr_code}")
print(f"URL da imagem QR: {payment.qr_image_url}")
print(f"Expira em: {payment.expires_at}")
```

### Consultar Status de um Pagamento

```python
from pixgo import PixGoClient, PaymentStatus

client = PixGoClient(api_key="pk_sua_chave_aqui")

# Consultar apenas o status
status = client.get_payment_status("dep_1234567890abcdef")

if status == PaymentStatus.COMPLETED:
    print("Pagamento confirmado!")
elif status == PaymentStatus.PENDING:
    print("Aguardando pagamento...")
elif status == PaymentStatus.EXPIRED:
    print("Pagamento expirou")

# Ou verificar diretamente se foi pago
if client.check_payment("dep_1234567890abcdef"):
    print("Pagamento confirmado!")
```

### Obter Detalhes Completos

```python
client = PixGoClient(api_key="pk_sua_chave_aqui")

# Obter todos os dados do pagamento
payment = client.get_payment("dep_1234567890abcdef")

print(f"Status: {payment.status}")
print(f"Valor: R$ {payment.amount}")
print(f"Cliente: {payment.customer_name}")
print(f"CPF: {payment.customer_cpf}")

# Verificar se foi pago
if payment.is_paid():
    print("Pagamento confirmado!")
```

### Usando Context Manager

```python
from pixgo import PixGoClient

# A conexão será fechada automaticamente
with PixGoClient(api_key="pk_sua_chave_aqui") as client:
    payment = client.create_payment(
        amount=100.00,
        description="Serviço ABC"
    )
    print(f"QR Code: {payment.qr_code}")
```

## 🔔 Webhooks

Configure webhooks para receber notificações automáticas quando o status de um pagamento mudar:

```python
from pixgo import PixGoClient

client = PixGoClient(api_key="pk_sua_chave_aqui")

payment = client.create_payment(
    amount=50.00,
    description="Produto com webhook",
    webhook_url="https://seu-site.com/webhook/pixgo"
)
```

### Processando Webhooks em Flask

```python
from flask import Flask, request, jsonify
from pixgo import WebhookEvent

app = Flask(__name__)

@app.route('/webhook/pixgo', methods=['POST'])
def pixgo_webhook():
    # Receber dados do webhook
    data = request.get_json()
    
    # Converter para objeto WebhookEvent
    event = WebhookEvent.from_dict(data)
    
    # Processar evento
    if event.event == 'payment.completed':
        payment = event.data
        print(f"Pagamento {payment.payment_id} confirmado!")
        print(f"Valor: R$ {payment.amount}")
        print(f"Pagador: {payment.payer_name}")
        
        # Atualizar seu banco de dados
        # marcar_pedido_como_pago(payment.external_id)
        
    elif event.event == 'payment.expired':
        payment = event.data
        print(f"Pagamento {payment.payment_id} expirou")
        # cancelar_pedido(payment.external_id)
    
    # Responder com sucesso
    return jsonify({'received': True}), 200

if __name__ == '__main__':
    app.run(port=5000)
```

## 📊 Modelos de Dados

### Payment

Representa um pagamento PIX:

```python
@dataclass
class Payment:
    payment_id: str           # ID do pagamento (dep_...)
    amount: float             # Valor em reais
    status: PaymentStatus     # Status do pagamento
    qr_code: str             # Código PIX Copia e Cola
    qr_image_url: str        # URL da imagem QR Code
    created_at: str          # Data de criação
    expires_at: str          # Data de expiração
    external_id: str         # ID externo (opcional)
    description: str         # Descrição (opcional)
    customer_name: str       # Nome do cliente (opcional)
    customer_cpf: str        # CPF/CNPJ (opcional)
    # ... outros campos opcionais
```

### PaymentStatus

Enum com os possíveis status:

```python
class PaymentStatus(Enum):
    PENDING = "pending"       # Aguardando pagamento
    COMPLETED = "completed"   # Pagamento confirmado
    EXPIRED = "expired"       # Pagamento expirou
    CANCELLED = "cancelled"   # Pagamento cancelado
    REFUNDED = "refunded"     # Pagamento estornado
```

## ⚠️ Tratamento de Erros

O pacote oferece exceções específicas para diferentes tipos de erro:

```python
from pixgo import (
    PixGoClient,
    PixGoAPIError,
    PixGoValidationError,
    PixGoAuthenticationError,
    PixGoRateLimitError
)

client = PixGoClient(api_key="pk_sua_chave_aqui")

try:
    payment = client.create_payment(amount=25.50)
    
except PixGoValidationError as e:
    # Erro de validação (ex: valor mínimo não atingido)
    print(f"Erro de validação: {e}")
    
except PixGoAuthenticationError as e:
    # API key inválida
    print(f"Erro de autenticação: {e}")
    
except PixGoRateLimitError as e:
    # Limite de requisições excedido
    print(f"Rate limit excedido: {e}")
    
except PixGoAPIError as e:
    # Outros erros da API
    print(f"Erro da API: {e}")
    print(f"Código: {e.error_code}")
    print(f"Status HTTP: {e.status_code}")
```

## 📝 Validações

O cliente realiza validações automáticas:

- **amount**: Mínimo R$ 10.00
- **description**: Máximo 200 caracteres
- **customer_name**: Máximo 100 caracteres
- **customer_email**: Máximo 255 caracteres (formato válido)
- **external_id**: Máximo 50 caracteres
- **customer_cpf**: 11 dígitos (CPF) ou 14 dígitos (CNPJ)

## 📈 Limites

### Sistema de Progressão (7 Níveis)

A API do PixGo utiliza um sistema de níveis baseado no histórico de transações confirmadas:

- **Nível 1 - Iniciante** (R$ 0 a R$ 299,99): Limite de R$ 300,00 por QR Code
- **Nível 2 - Bronze** (R$ 300 a R$ 499,99): Limite de R$ 500,00 por QR Code
- **Nível 3 - Prata** (R$ 500 a R$ 999,99): Limite de R$ 1.000,00 por QR Code
- **Nível 4 - Ouro** (R$ 1.000 a R$ 2.999,99): Limite de R$ 1.500,00 por QR Code
- **Nível 5 - Platina** (R$ 3.000 a R$ 4.999,99): Limite de R$ 2.000,00 por QR Code
- **Nível 6 - Diamante** (R$ 5.000 a R$ 5.999,99): Limite de R$ 2.500,00 por QR Code
- **Nível Máximo - Elite** (R$ 6.000+): Limite de R$ 3.000,00 por QR Code

### Outros Limites

- **Limite diário por CPF/CNPJ do pagador**: R$ 6.000,00
- **Expiração de pagamentos**: 20 minutos
- **Rate limit (consulta de status)**: 1.000 requisições por 24 horas
- **QR Codes por dia**: Ilimitado

## 🔧 Desenvolvimento

### Instalação para Desenvolvimento

```bash
git clone https://github.com/DevWand/pixgo-python.git
cd pixgo-python
pip install -e ".[dev]"
```

### Executar Testes

```bash
pytest
```

### Formatação de Código

```bash
black pixgo/
```

### Linting

```bash
flake8 pixgo/
```

## 📚 Exemplos Completos

### Exemplo: E-commerce Simples

```python
from pixgo import PixGoClient, PaymentStatus
import time

def processar_pedido(valor, descricao, cliente_info):
    client = PixGoClient(api_key="pk_sua_chave_aqui")
    
    # Criar pagamento
    payment = client.create_payment(
        amount=valor,
        description=descricao,
        customer_name=cliente_info['nome'],
        customer_cpf=cliente_info['cpf'],
        customer_email=cliente_info['email'],
        external_id=cliente_info['pedido_id'],
        webhook_url="https://seu-site.com/webhook"
    )
    
    print(f"Pagamento criado: {payment.payment_id}")
    print(f"Mostre este QR Code ao cliente: {payment.qr_image_url}")
    
    # Aguardar pagamento (exemplo simplificado)
    print("Aguardando pagamento...")
    for i in range(40):  # 40 tentativas x 30 segundos = 20 minutos
        time.sleep(30)
        
        status = client.get_payment_status(payment.payment_id)
        
        if status == PaymentStatus.COMPLETED:
            print("Pagamento confirmado! Processando pedido...")
            return True
        elif status == PaymentStatus.EXPIRED:
            print("Pagamento expirou")
            return False
    
    return False

# Usar
cliente = {
    'nome': 'Maria Silva',
    'cpf': '12345678901',
    'email': 'maria@exemplo.com',
    'pedido_id': 'PED-001'
}

if processar_pedido(150.00, "Kit de produtos", cliente):
    print("Pedido processado com sucesso!")
else:
    print("Pedido cancelado")
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🔗 Links Úteis

- [Documentação da API PixGo](https://pixgo.org/api/v1/docs)
- [Site do PixGo](https://pixgo.org)
- [Guia do PixGo](https://pixgo.org/guia_pixgo.php)
- [FAQ](https://pixgo.org/faq.php)

## 📧 Suporte

- Email: [contato@pixgo.org](mailto:contato@pixgo.org)
- Telegram: Grupo de suporte disponível no dashboard do PixGo
- Documentação: Sempre atualizada em [https://pixgo.org/api/v1/docs](https://pixgo.org/api/v1/docs)

---

**Nota**: Este é um cliente não oficial desenvolvido para facilitar a integração com a API do PixGo. Todas as operações são realizadas em ambiente de produção real.
