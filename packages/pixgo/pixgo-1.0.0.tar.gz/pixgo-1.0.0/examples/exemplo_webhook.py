"""
Exemplo de servidor Flask com webhooks do PixGo
"""
from flask import Flask, request, jsonify
from pixgo import PixGoClient, WebhookEvent, PaymentStatus

app = Flask(__name__)

# Configuração
PIXGO_API_KEY = "pk_sua_chave_aqui"
client = PixGoClient(api_key=PIXGO_API_KEY)


@app.route('/criar-pagamento', methods=['POST'])
def criar_pagamento():
    """Endpoint para criar um novo pagamento"""
    try:
        data = request.get_json()
        
        # Criar pagamento com webhook
        payment = client.create_payment(
            amount=data.get('amount'),
            description=data.get('description'),
            customer_name=data.get('customer_name'),
            customer_cpf=data.get('customer_cpf'),
            customer_email=data.get('customer_email'),
            external_id=data.get('external_id'),
            webhook_url=request.url_root + 'webhook/pixgo'  # URL do webhook
        )
        
        return jsonify({
            'success': True,
            'payment_id': payment.payment_id,
            'qr_code': payment.qr_code,
            'qr_image_url': payment.qr_image_url,
            'amount': payment.amount,
            'expires_at': payment.expires_at
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/pagamento/<payment_id>', methods=['GET'])
def consultar_pagamento(payment_id):
    """Endpoint para consultar um pagamento"""
    try:
        payment = client.get_payment(payment_id)
        
        return jsonify({
            'success': True,
            'payment': {
                'payment_id': payment.payment_id,
                'amount': payment.amount,
                'status': payment.status.value,
                'customer_name': payment.customer_name,
                'created_at': payment.created_at,
                'is_paid': payment.is_paid()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/webhook/pixgo', methods=['POST'])
def webhook_pixgo():
    """Endpoint para receber webhooks do PixGo"""
    try:
        # Receber dados do webhook
        data = request.get_json()
        
        # Log dos headers (útil para debug)
        print("\n=== Webhook Recebido ===")
        print(f"Event: {request.headers.get('X-Webhook-Event')}")
        print(f"Timestamp: {request.headers.get('X-Webhook-Timestamp')}")
        
        # Converter para objeto WebhookEvent
        event = WebhookEvent.from_dict(data)
        
        # Processar evento
        if event.event == 'payment.completed':
            processar_pagamento_confirmado(event.data)
            
        elif event.event == 'payment.expired':
            processar_pagamento_expirado(event.data)
            
        elif event.event == 'payment.refunded':
            processar_pagamento_estornado(event.data)
        
        # Responder com sucesso
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        return jsonify({'error': str(e)}), 400


def processar_pagamento_confirmado(payment):
    """Processa um pagamento confirmado"""
    print(f"\n✓ Pagamento Confirmado!")
    print(f"  ID: {payment.payment_id}")
    print(f"  Valor: R$ {payment.amount}")
    print(f"  Pagador: {payment.payer_name}")
    print(f"  CPF: {payment.payer_cpf}")
    
    # IMPORTANTE: Validar o pagamento consultando a API
    # Não confie apenas no webhook
    try:
        payment_validated = client.get_payment(payment.payment_id)
        
        if payment_validated.is_paid():
            print(f"  ✓ Pagamento validado pela API")
            
            # Aqui você deve:
            # 1. Atualizar seu banco de dados
            # 2. Marcar o pedido como pago
            # 3. Enviar email de confirmação
            # 4. Liberar o produto/serviço
            
            if payment.external_id:
                print(f"  Processando pedido: {payment.external_id}")
                # marcar_pedido_como_pago(payment.external_id)
                # enviar_email_confirmacao(payment)
                # liberar_produto(payment.external_id)
        else:
            print(f"  ✗ AVISO: Status divergente na API: {payment_validated.status}")
            
    except Exception as e:
        print(f"  ✗ Erro ao validar pagamento: {e}")


def processar_pagamento_expirado(payment):
    """Processa um pagamento expirado"""
    print(f"\n⏰ Pagamento Expirado")
    print(f"  ID: {payment.payment_id}")
    print(f"  Valor: R$ {payment.amount}")
    
    # Aqui você deve:
    # 1. Cancelar o pedido
    # 2. Liberar o estoque
    # 3. Notificar o cliente
    
    if payment.external_id:
        print(f"  Cancelando pedido: {payment.external_id}")
        # cancelar_pedido(payment.external_id)
        # liberar_estoque(payment.external_id)
        # notificar_cliente_expiracao(payment)


def processar_pagamento_estornado(payment):
    """Processa um pagamento estornado"""
    print(f"\n↩️  Pagamento Estornado")
    print(f"  ID: {payment.payment_id}")
    print(f"  Valor: R$ {payment.amount}")
    
    # Aqui você deve:
    # 1. Reverter o pedido
    # 2. Atualizar o banco de dados
    # 3. Notificar o cliente
    
    if payment.external_id:
        print(f"  Revertendo pedido: {payment.external_id}")
        # reverter_pedido(payment.external_id)
        # notificar_cliente_estorno(payment)


@app.route('/')
def index():
    """Página inicial com exemplos"""
    return """
    <h1>Servidor de Exemplo - PixGo Webhooks</h1>
    
    <h2>Endpoints Disponíveis:</h2>
    <ul>
        <li><strong>POST /criar-pagamento</strong> - Criar novo pagamento</li>
        <li><strong>GET /pagamento/{id}</strong> - Consultar pagamento</li>
        <li><strong>POST /webhook/pixgo</strong> - Receber webhooks</li>
    </ul>
    
    <h2>Exemplo de Criação de Pagamento:</h2>
    <pre>
POST /criar-pagamento
Content-Type: application/json

{
    "amount": 25.50,
    "description": "Produto XYZ",
    "customer_name": "João Silva",
    "customer_cpf": "12345678901",
    "customer_email": "joao@exemplo.com",
    "external_id": "pedido_123"
}
    </pre>
    """


if __name__ == '__main__':
    print("=" * 50)
    print("Servidor Flask com Webhooks do PixGo")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST /criar-pagamento")
    print("  GET  /pagamento/<id>")
    print("  POST /webhook/pixgo")
    print("\n" + "=" * 50)
    
    # Iniciar servidor
    app.run(debug=True, port=5000)
