"""
Exemplo de uso básico do cliente PixGo
"""
from pixgo import PixGoClient, PaymentStatus

def exemplo_criar_pagamento():
    """Exemplo: Criar um pagamento PIX"""
    print("=== Criar Pagamento ===")
    
    # Inicializar cliente
    client = PixGoClient(api_key="pk_sua_chave_aqui")
    
    try:
        # Criar pagamento
        payment = client.create_payment(
            amount=25.50,
            description="Produto XYZ",
            customer_name="João Silva",
            customer_cpf="12345678901",
            customer_email="joao@exemplo.com",
            customer_phone="(11) 99999-9999",
            external_id="pedido_123"
        )
        
        print(f"✓ Pagamento criado com sucesso!")
        print(f"  ID: {payment.payment_id}")
        print(f"  Valor: R$ {payment.amount}")
        print(f"  Status: {payment.status.value}")
        print(f"  QR Code URL: {payment.qr_image_url}")
        print(f"  Expira em: {payment.expires_at}")
        
        return payment.payment_id
        
    except Exception as e:
        print(f"✗ Erro ao criar pagamento: {e}")
        return None
    finally:
        client.close()


def exemplo_consultar_status(payment_id: str):
    """Exemplo: Consultar status de um pagamento"""
    print(f"\n=== Consultar Status ===")
    
    client = PixGoClient(api_key="pk_sua_chave_aqui")
    
    try:
        # Consultar status
        status = client.get_payment_status(payment_id)
        
        print(f"✓ Status do pagamento {payment_id}:")
        print(f"  Status: {status.value}")
        
        # Verificar status específico
        if status == PaymentStatus.COMPLETED:
            print(f"  ✓ Pagamento confirmado!")
        elif status == PaymentStatus.PENDING:
            print(f"  ⏳ Aguardando pagamento...")
        elif status == PaymentStatus.EXPIRED:
            print(f"  ⏰ Pagamento expirou")
            
    except Exception as e:
        print(f"✗ Erro ao consultar status: {e}")
    finally:
        client.close()


def exemplo_obter_detalhes(payment_id: str):
    """Exemplo: Obter detalhes completos de um pagamento"""
    print(f"\n=== Obter Detalhes ===")
    
    client = PixGoClient(api_key="pk_sua_chave_aqui")
    
    try:
        # Obter detalhes
        payment = client.get_payment(payment_id)
        
        print(f"✓ Detalhes do pagamento:")
        print(f"  ID: {payment.payment_id}")
        print(f"  Valor: R$ {payment.amount}")
        print(f"  Status: {payment.status.value}")
        print(f"  Cliente: {payment.customer_name}")
        print(f"  CPF: {payment.customer_cpf}")
        print(f"  Descrição: {payment.description}")
        print(f"  Criado em: {payment.created_at}")
        
        # Usar métodos de conveniência
        if payment.is_paid():
            print(f"  ✓ Pagamento confirmado!")
        elif payment.is_pending():
            print(f"  ⏳ Aguardando pagamento...")
        elif payment.is_expired():
            print(f"  ⏰ Pagamento expirou")
            
    except Exception as e:
        print(f"✗ Erro ao obter detalhes: {e}")
    finally:
        client.close()


def exemplo_context_manager():
    """Exemplo: Usar context manager"""
    print(f"\n=== Context Manager ===")
    
    try:
        # Usar context manager (fecha a conexão automaticamente)
        with PixGoClient(api_key="pk_sua_chave_aqui") as client:
            payment = client.create_payment(
                amount=100.00,
                description="Teste com context manager"
            )
            
            print(f"✓ Pagamento criado: {payment.payment_id}")
            
            # Verificar se foi pago
            if client.check_payment(payment.payment_id):
                print(f"  ✓ Pagamento confirmado!")
            else:
                print(f"  ⏳ Aguardando pagamento...")
        
        print(f"✓ Conexão fechada automaticamente")
        
    except Exception as e:
        print(f"✗ Erro: {e}")


def exemplo_tratamento_erros():
    """Exemplo: Tratamento de erros"""
    print(f"\n=== Tratamento de Erros ===")
    
    from pixgo import (
        PixGoAPIError,
        PixGoValidationError,
        PixGoAuthenticationError,
        PixGoRateLimitError
    )
    
    client = PixGoClient(api_key="pk_sua_chave_aqui")
    
    try:
        # Tentar criar pagamento com valor inválido
        payment = client.create_payment(amount=5.00)  # Mínimo é R$ 10.00
        
    except PixGoValidationError as e:
        print(f"✗ Erro de validação: {e}")
        
    except PixGoAuthenticationError as e:
        print(f"✗ Erro de autenticação: {e}")
        
    except PixGoRateLimitError as e:
        print(f"✗ Rate limit excedido: {e}")
        
    except PixGoAPIError as e:
        print(f"✗ Erro da API: {e}")
        if e.error_code:
            print(f"  Código: {e.error_code}")
        if e.status_code:
            print(f"  Status HTTP: {e.status_code}")
            
    finally:
        client.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Exemplos de uso do PixGo Python Client")
    print("=" * 50)
    
    # Exemplo 1: Criar pagamento
    payment_id = exemplo_criar_pagamento()
    
    if payment_id:
        # Exemplo 2: Consultar status
        exemplo_consultar_status(payment_id)
        
        # Exemplo 3: Obter detalhes
        exemplo_obter_detalhes(payment_id)
    
    # Exemplo 4: Context manager
    exemplo_context_manager()
    
    # Exemplo 5: Tratamento de erros
    exemplo_tratamento_erros()
    
    print("\n" + "=" * 50)
    print("Exemplos concluídos!")
    print("=" * 50)
