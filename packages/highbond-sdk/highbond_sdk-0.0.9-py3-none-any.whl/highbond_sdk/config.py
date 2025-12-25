"""
Classes de configuração para o HighBond SDK.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .enums import Region


@dataclass
class APIConfig:
    """Configuração da API HighBond.
    
    Attributes:
        token: Token de autenticação Bearer.
        org_id: ID da organização.
        region: Região da API (us, eu, au, ca).
        timeout: Timeout das requisições em segundos.
        max_retries: Número máximo de tentativas.
        retry_delay: Delay inicial entre tentativas em segundos.
    """
    
    token: str
    org_id: int
    region: Region = Region.US
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Valida e normaliza os valores de configuração."""
        if isinstance(self.region, str):
            self.region = Region(self.region)
    
    @property
    def base_url(self) -> str:
        """Retorna a URL base da API."""
        return Region.get_base_url(self.region)
    
    @property
    def headers(self) -> Dict[str, str]:
        """Retorna os headers padrão para requisições."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }


@dataclass
class PaginationConfig:
    """Configuração de paginação.
    
    Attributes:
        page_size: Número de itens por página (máximo 100).
        max_pages: Número máximo de páginas a buscar (None = todas).
    """
    
    page_size: int = 50
    max_pages: Optional[int] = None
    
    def __post_init__(self):
        """Valida os valores de paginação."""
        if self.page_size < 1 or self.page_size > 100:
            raise ValueError("page_size deve estar entre 1 e 100")


@dataclass
class ThreadingConfig:
    """Configuração de threading.
    
    Attributes:
        max_workers: Número máximo de workers para operações paralelas.
        enabled: Se threading está habilitado.
    """
    
    max_workers: int = 5
    enabled: bool = True
    
    def __post_init__(self):
        """Valida os valores de threading."""
        if self.max_workers < 1:
            raise ValueError("max_workers deve ser pelo menos 1")


@dataclass
class ClientConfig:
    """Configuração completa do cliente HighBond.
    
    Attributes:
        api: Configuração da API.
        pagination: Configuração de paginação.
        threading: Configuração de threading.
    """
    
    api: APIConfig
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    threading: ThreadingConfig = field(default_factory=ThreadingConfig)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClientConfig":
        """Cria configuração a partir de dicionário."""
        api_config = APIConfig(**data.get("api", data))
        pagination_config = PaginationConfig(**data.get("pagination", {}))
        threading_config = ThreadingConfig(**data.get("threading", {}))
        
        return cls(
            api=api_config,
            pagination=pagination_config,
            threading=threading_config
        )
