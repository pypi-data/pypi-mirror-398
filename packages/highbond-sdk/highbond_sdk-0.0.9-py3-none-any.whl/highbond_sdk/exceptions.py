"""
Exceções personalizadas para o HighBond SDK.
"""


class HighBondAPIError(Exception):
    """Exceção base para erros da API HighBond."""

    def __init__(
        self, message: str, status_code: int = None, response: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class HighBondAuthError(HighBondAPIError):
    """Erro de autenticação (401).
    
    Ocorre quando o token é inválido ou expirado.
    """
    pass


class HighBondForbiddenError(HighBondAPIError):
    """Erro de permissão (403).
    
    Ocorre quando o usuário não tem permissão para acessar o recurso.
    """
    pass


class HighBondNotFoundError(HighBondAPIError):
    """Recurso não encontrado (404).
    
    Ocorre quando o recurso solicitado não existe.
    """
    pass


class HighBondValidationError(HighBondAPIError):
    """Erro de validação (422).
    
    Ocorre quando os dados enviados são inválidos.
    """
    pass


class HighBondRateLimitError(HighBondAPIError):
    """Erro de rate limit (429).
    
    Ocorre quando o limite de requisições é excedido.
    """
    pass


class HighBondConnectionError(HighBondAPIError):
    """Erro de conexão.
    
    Ocorre quando não é possível conectar à API.
    """
    pass
