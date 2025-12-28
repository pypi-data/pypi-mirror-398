"""
Exemplo de uso do pacote com configuração via arquivo .env
"""
import os
from pathlib import Path
from pixgo import PixGoClient

# Você pode usar python-dotenv para carregar variáveis de ambiente
# pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Variáveis de ambiente carregadas do arquivo .env")
except ImportError:
    print("⚠️  python-dotenv não instalado. Configure as variáveis manualmente.")


def get_client():
    """Cria cliente usando variáveis de ambiente"""
    api_key = os.getenv('PIXGO_API_KEY')
    
    if not api_key:
        raise ValueError(
            "PIXGO_API_KEY não configurada!\n"
            "1. Copie .env.example para .env\n"
            "2. Adicione sua API key no arquivo .env\n"
            "3. Ou defina a variável: export PIXGO_API_KEY=pk_sua_chave"
        )
    
    timeout = int(os.getenv('PIXGO_TIMEOUT', 30))
    
    return PixGoClient(api_key=api_key, timeout=timeout)


def exemplo_com_env():
    """Exemplo usando configuração de ambiente"""
    print("\n" + "=" * 60)
    print("EXEMPLO COM VARIÁVEIS DE AMBIENTE")
    print("=" * 60)
    
    try:
        # Criar cliente
        client = get_client()
        print("✓ Cliente criado com sucesso\n")
        
        # Criar pagamento
        payment = client.create_payment(
            amount=10.00,
            description="Teste com .env",
            customer_name="Cliente Teste"
        )
        
        print(f"✓ Pagamento criado!")
        print(f"  ID: {payment.payment_id}")
        print(f"  Valor: R$ {payment.amount}")
        print(f"  QR Code URL: {payment.qr_image_url}")
        
        # Verificar webhook URL configurada
        webhook_url = os.getenv('PIXGO_WEBHOOK_URL')
        if webhook_url:
            print(f"\n✓ Webhook configurado: {webhook_url}")
            print("  (Use webhook_url ao criar pagamentos)")
        
    except ValueError as e:
        print(f"\n✗ Erro de configuração:\n{e}")
        
    except Exception as e:
        print(f"\n✗ Erro: {e}")
    
    finally:
        if 'client' in locals():
            client.close()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    exemplo_com_env()
