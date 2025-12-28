"""
Exceções personalizadas para o cliente PixGo
"""


class PixGoException(Exception):
    """Classe base para todas as exceções do PixGo"""
    pass


class PixGoAPIError(PixGoException):
    """Erro retornado pela API do PixGo"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = None, response_data: dict = None):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class PixGoValidationError(PixGoException):
    """Erro de validação de dados"""
    pass


class PixGoAuthenticationError(PixGoException):
    """Erro de autenticação (API key inválida)"""
    pass


class PixGoRateLimitError(PixGoException):
    """Erro de limite de requisições excedido"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)
