"""
Exemplo de sistema de e-commerce simples com PixGo
"""
import time
from datetime import datetime
from pixgo import PixGoClient, PaymentStatus


class PedidoEcommerce:
    """Simula um pedido de e-commerce"""
    
    def __init__(self, pedido_id: str, valor: float, produtos: list):
        self.pedido_id = pedido_id
        self.valor = valor
        self.produtos = produtos
        self.status = "pendente"
        self.payment_id = None
        self.criado_em = datetime.now()
    
    def __repr__(self):
        return f"Pedido({self.pedido_id}, R$ {self.valor}, {self.status})"


def criar_pedido_com_pix(client: PixGoClient, pedido: PedidoEcommerce, cliente_info: dict):
    """Cria um pedido e gera o pagamento PIX"""
    
    print(f"\n{'=' * 60}")
    print(f"NOVO PEDIDO - {pedido.pedido_id}")
    print(f"{'=' * 60}")
    print(f"Produtos: {', '.join(pedido.produtos)}")
    print(f"Valor Total: R$ {pedido.valor:.2f}")
    print(f"Cliente: {cliente_info['nome']}")
    print(f"{'=' * 60}\n")
    
    try:
        # Criar pagamento PIX
        print("⏳ Gerando QR Code PIX...")
        payment = client.create_payment(
            amount=pedido.valor,
            description=f"Pedido {pedido.pedido_id} - {len(pedido.produtos)} item(ns)",
            customer_name=cliente_info['nome'],
            customer_cpf=cliente_info['cpf'],
            customer_email=cliente_info['email'],
            customer_phone=cliente_info.get('telefone'),
            external_id=pedido.pedido_id
        )
        
        pedido.payment_id = payment.payment_id
        
        print(f"✓ QR Code gerado com sucesso!\n")
        print(f"ID do Pagamento: {payment.payment_id}")
        print(f"Valor: R$ {payment.amount:.2f}")
        print(f"Expira em: {payment.expires_at}")
        print(f"\nURL do QR Code: {payment.qr_image_url}")
        print(f"\nPIX Copia e Cola:")
        print(f"{payment.qr_code[:50]}...")
        
        return payment
        
    except Exception as e:
        print(f"✗ Erro ao criar pagamento: {e}")
        return None


def aguardar_pagamento(client: PixGoClient, pedido: PedidoEcommerce, timeout_minutos: int = 20):
    """Aguarda a confirmação do pagamento"""
    
    print(f"\n{'=' * 60}")
    print(f"AGUARDANDO PAGAMENTO - {pedido.pedido_id}")
    print(f"{'=' * 60}")
    print(f"Consultando status a cada 10 segundos...")
    print(f"Timeout: {timeout_minutos} minutos\n")
    
    tentativas = (timeout_minutos * 60) // 10  # Consultar a cada 10 segundos
    
    for i in range(tentativas):
        try:
            # Consultar status
            status = client.get_payment_status(pedido.payment_id)
            
            tempo_decorrido = (i + 1) * 10
            minutos = tempo_decorrido // 60
            segundos = tempo_decorrido % 60
            
            print(f"[{minutos:02d}:{segundos:02d}] Status: {status.value}", end="")
            
            if status == PaymentStatus.COMPLETED:
                print(" ✓ PAGO!")
                pedido.status = "pago"
                return True
                
            elif status == PaymentStatus.EXPIRED:
                print(" ⏰ EXPIRADO")
                pedido.status = "expirado"
                return False
            
            else:
                print(" ⏳ Aguardando...")
            
            # Aguardar 10 segundos antes da próxima consulta
            time.sleep(10)
            
        except Exception as e:
            print(f"\n✗ Erro ao consultar status: {e}")
            time.sleep(10)
    
    print(f"\n⏰ Timeout atingido")
    pedido.status = "timeout"
    return False


def processar_pedido(client: PixGoClient, pedido: PedidoEcommerce):
    """Processa o pedido após confirmação do pagamento"""
    
    print(f"\n{'=' * 60}")
    print(f"PROCESSANDO PEDIDO - {pedido.pedido_id}")
    print(f"{'=' * 60}")
    
    try:
        # Obter detalhes completos do pagamento
        payment = client.get_payment(pedido.payment_id)
        
        print(f"✓ Pagamento confirmado!")
        print(f"  Valor recebido: R$ {payment.amount:.2f}")
        print(f"  Pagador: {payment.payer_name or payment.customer_name}")
        print(f"  CPF: {payment.payer_cpf or payment.customer_cpf}")
        print(f"  Confirmado em: {payment.completed_at or payment.updated_at}")
        
        # Simular processamento
        print(f"\n⏳ Separando produtos...")
        time.sleep(1)
        for produto in pedido.produtos:
            print(f"  ✓ {produto}")
        
        print(f"\n⏳ Gerando nota fiscal...")
        time.sleep(1)
        print(f"  ✓ NF-e: 123456")
        
        print(f"\n⏳ Enviando email de confirmação...")
        time.sleep(1)
        print(f"  ✓ Email enviado para {payment.customer_email}")
        
        print(f"\n✓ Pedido processado com sucesso!")
        pedido.status = "processado"
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao processar pedido: {e}")
        return False


def cancelar_pedido(pedido: PedidoEcommerce):
    """Cancela um pedido"""
    
    print(f"\n{'=' * 60}")
    print(f"CANCELANDO PEDIDO - {pedido.pedido_id}")
    print(f"{'=' * 60}")
    print(f"✓ Pedido cancelado")
    print(f"✓ Estoque liberado")
    pedido.status = "cancelado"


# Exemplo de uso
def main():
    """Função principal - demonstração completa"""
    
    print(f"\n{'#' * 60}")
    print(f"{'SISTEMA DE E-COMMERCE COM PIXGO':^60}")
    print(f"{'#' * 60}\n")
    
    # Configurar cliente
    API_KEY = "pk_sua_chave_aqui"  # Substitua pela sua API key
    client = PixGoClient(api_key=API_KEY)
    
    # Simular dados do cliente
    cliente_info = {
        'nome': 'Maria Silva',
        'cpf': '12345678901',
        'email': 'maria.silva@exemplo.com',
        'telefone': '(11) 98765-4321'
    }
    
    # Criar pedido
    pedido = PedidoEcommerce(
        pedido_id='PED-2025-001',
        valor=150.00,
        produtos=[
            'Camiseta Básica Branca (R$ 50,00)',
            'Calça Jeans Slim (R$ 80,00)',
            'Frete Expresso (R$ 20,00)'
        ]
    )
    
    try:
        # 1. Criar pagamento PIX
        payment = criar_pedido_com_pix(client, pedido, cliente_info)
        
        if not payment:
            print("\n✗ Falha ao criar pagamento")
            return
        
        # 2. Aguardar confirmação (com timeout reduzido para demonstração)
        # Em produção, use o timeout padrão de 20 minutos
        print("\n⚠️  DEMONSTRAÇÃO: Usando timeout de 2 minutos")
        print("⚠️  Em produção, o timeout seria de 20 minutos\n")
        
        input("Pressione ENTER para começar a monitorar o pagamento...")
        
        pagamento_confirmado = aguardar_pagamento(
            client, 
            pedido, 
            timeout_minutos=2  # Reduzido para demonstração
        )
        
        # 3. Processar ou cancelar
        if pagamento_confirmado:
            processar_pedido(client, pedido)
        else:
            cancelar_pedido(pedido)
        
        # Status final
        print(f"\n{'=' * 60}")
        print(f"STATUS FINAL")
        print(f"{'=' * 60}")
        print(f"Pedido: {pedido.pedido_id}")
        print(f"Status: {pedido.status.upper()}")
        print(f"Valor: R$ {pedido.valor:.2f}")
        print(f"{'=' * 60}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Operação interrompida pelo usuário")
        cancelar_pedido(pedido)
        
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        
    finally:
        client.close()
        print("\n✓ Conexão encerrada")


if __name__ == "__main__":
    main()
