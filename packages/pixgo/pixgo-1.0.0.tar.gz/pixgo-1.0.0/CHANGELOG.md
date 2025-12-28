# Changelog# PixGo Python Client


































[1.0.0]: https://github.com/DevWand/pixgo-python/releases/tag/v1.0.0- ✅ Tratamento de erros robusto- ✅ Type hints completo- ✅ Validação de CPF/CNPJ- ✅ Suporte a webhooks- ✅ Obtenção de detalhes completos- ✅ Consulta de status de pagamentos- ✅ Criação de pagamentos PIX instantâneos### Recursos Principais- Suporte para Python 3.7+- Testes unitários- Exemplos práticos de uso- Documentação completa em português- Context manager para gerenciamento de sessão- Validações de dados- Suporte a webhooks- Tratamento robusto de erros com exceções personalizadas- Modelos de dados: Payment, PaymentStatus, WebhookEvent- Obtenção de detalhes completos de pagamentos- Consulta de status de pagamentos- Suporte para criação de pagamentos PIX- Cliente Python completo para API do PixGo### Adicionado## [1.0.0] - 2025-12-26e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.
Cliente Python para a API do PixGo - Pagamentos PIX simplificados.

## Instalação

```bash
pip install pixgo
```

## Uso Rápido

```python
from pixgo import PixGoClient

client = PixGoClient(api_key="pk_sua_chave_aqui")

payment = client.create_payment(
    amount=25.50,
    description="Produto XYZ"
)

print(payment.qr_code)
```

## Documentação

Veja o [README.md](README.md) para documentação completa.

## Links

- Documentação: https://pixgo.org/api/v1/docs
- Site: https://pixgo.org
