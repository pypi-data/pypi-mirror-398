"""
Cliente principal do HighBond SDK.
"""
from typing import Optional, Union

from .config import APIConfig, PaginationConfig, ThreadingConfig, ClientConfig
from .enums import Region
from .http_client import HighBondHTTPClient
from .modules import (
    ProjectsModule,
    ProjectTypesModule,
    ObjectivesModule,
    RisksModule,
    ControlsModule,
    IssuesModule,
)


class HighBondClient:
    """Cliente principal para a API HighBond.
    
    Fornece acesso a todos os módulos da API através de uma interface unificada.
    
    Attributes:
        projects: Módulo para gerenciamento de projetos.
        project_types: Módulo para gerenciamento de tipos de projeto.
        objectives: Módulo para gerenciamento de objetivos.
        risks: Módulo para gerenciamento de riscos.
        controls: Módulo para gerenciamento de controles.
        issues: Módulo para gerenciamento de issues.
    
    Example:
        >>> from highbond_sdk import HighBondClient
        >>> 
        >>> # Inicialização simples
        >>> client = HighBondClient(
        ...     token="seu-token",
        ...     org_id=12345,
        ...     region="us"
        ... )
        >>> 
        >>> # Listar projetos
        >>> for project in client.projects.list_all():
        ...     print(project['attributes']['title'])
        >>> 
        >>> # Criar um risco
        >>> risk = client.risks.create(
        ...     project_id=123,
        ...     title="Novo Risco",
        ...     severity="high"
        ... )
    """
     
    def __init__(
        self,
        token: str,
        org_id: int,
        region: Union[str, Region] = Region.US,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        page_size: int = 50,
        max_pages: Optional[int] = None,
        max_workers: int = 5,
        threading_enabled: bool = True,
        config: Optional[ClientConfig] = None
    ):
        """Inicializa o cliente HighBond.
        
        Args:
            token: Token de autenticação Bearer da API.
            org_id: ID da organização no HighBond.
            region: Região da API (us, eu, au, ca).
            timeout: Timeout das requisições em segundos.
            max_retries: Número máximo de tentativas em caso de erro.
            retry_delay: Delay inicial entre tentativas em segundos.
            page_size: Número de itens por página na paginação.
            max_pages: Máximo de páginas a buscar (None = todas).
            max_workers: Número máximo de workers para operações paralelas.
            threading_enabled: Se threading está habilitado.
            config: Configuração completa (sobrescreve outros parâmetros).
        
        Example:
            >>> # Usando parâmetros individuais
            >>> client = HighBondClient(
            ...     token="seu-token",
            ...     org_id=12345,
            ...     region="us"
            ... )
            >>> 
            >>> # Usando configuração completa
            >>> from highbond_sdk import ClientConfig, APIConfig
            >>> config = ClientConfig(
            ...     api=APIConfig(token="seu-token", org_id=12345)
            ... )
            >>> client = HighBondClient(config=config)
        """
        if config:
            self._config = config
        else:
            api_config = APIConfig(
                token=token,
                org_id=org_id,
                region=Region(region) if isinstance(region, str) else region,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            pagination_config = PaginationConfig(
                page_size=page_size,
                max_pages=max_pages
            )
            threading_config = ThreadingConfig(
                max_workers=max_workers,
                enabled=threading_enabled
            )
            self._config = ClientConfig(
                api=api_config,
                pagination=pagination_config,
                threading=threading_config
            )
        
        # Inicializa cliente HTTP
        self._http_client = HighBondHTTPClient(self._config.api)
        
        # Inicializa módulos
        self._projects = ProjectsModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
        self._project_types = ProjectTypesModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
        self._objectives = ObjectivesModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
        self._risks = RisksModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
        self._controls = ControlsModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
        self._issues = IssuesModule(
            self._http_client,
            self._config.api.org_id,
            self._config.pagination,
            self._config.threading
        )
    
    @property
    def projects(self) -> ProjectsModule:
        """Módulo de Projetos."""
        return self._projects
    
    @property
    def project_types(self) -> ProjectTypesModule:
        """Módulo de Tipos de Projeto."""
        return self._project_types
    
    @property
    def objectives(self) -> ObjectivesModule:
        """Módulo de Objetivos."""
        return self._objectives
    
    @property
    def risks(self) -> RisksModule:
        """Módulo de Riscos."""
        return self._risks
    
    @property
    def controls(self) -> ControlsModule:
        """Módulo de Controles."""
        return self._controls
    
    @property
    def issues(self) -> IssuesModule:
        """Módulo de Issues."""
        return self._issues
    
    @property
    def config(self) -> ClientConfig:
        """Configuração do cliente."""
        return self._config
    
    def close(self):
        """Fecha conexões e libera recursos."""
        self._http_client.close()
    
    def __enter__(self):
        """Suporte a context manager."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fecha cliente ao sair do context manager."""
        self.close()
    
    def __repr__(self) -> str:
        return (
            f"HighBondClient(org_id={self._config.api.org_id}, "
            f"region={self._config.api.region.value})"
        )
