"""
HighBond SDK - Cliente Python para a API HighBond.

Um SDK completo para interagir com a API HighBond, incluindo
suporte a paginação automática, multithreading e todas as
operações CRUD para Projects, Objectives, Risks, Controls e Issues.

Example:
    >>> from highbond_sdk import HighBondClient
    >>> 
    >>> client = HighBondClient(
    ...     token="seu-token",
    ...     org_id=12345,
    ...     region="us"
    ... )
    >>> 
    >>> # Listar todos os projetos
    >>> for project in client.projects.list_all():
    ...     print(project['attributes']['title'])
    >>> 
    >>> # Criar um risco
    >>> from highbond_sdk import Severity, RiskStatus
    >>> risk = client.risks.create(
    ...     project_id=123,
    ...     title="Risco de Compliance",
    ...     severity=Severity.HIGH,
    ...     status=RiskStatus.OPEN
    ... )
"""

__version__ = "0.0.2"
__author__ = "HighBond SDK Team"
__license__ = "MIT"

# Cliente principal
from .client import HighBondClient

# Configurações
from .config import (
    APIConfig,
    PaginationConfig,
    ThreadingConfig,
    ClientConfig,
)

# Exceções
from .exceptions import (
    HighBondAPIError,
    HighBondAuthError,
    HighBondForbiddenError,
    HighBondNotFoundError,
    HighBondValidationError,
    HighBondRateLimitError,
    HighBondConnectionError,
)

# Enums
from .enums import (
    Region,
    ProjectState,
    ProjectStatus,
    ObjectiveType,
    Severity,
    RiskStatus,
    ControlType,
    ControlStatus,
    ControlTestFrequency,
    ControlAutomation,
    IssueStatus,
    IssuePriority,
    SortOrder,
)

# Módulos (para acesso direto se necessário)
from .modules import (
    ProjectsModule,
    ObjectivesModule,
    RisksModule,
    ControlsModule,
    IssuesModule,
)

__all__ = [
    # Versão
    "__version__",
    
    # Cliente principal
    "HighBondClient",
    
    # Configurações
    "APIConfig",
    "PaginationConfig",
    "ThreadingConfig",
    "ClientConfig",
    
    # Exceções
    "HighBondAPIError",
    "HighBondAuthError",
    "HighBondForbiddenError",
    "HighBondNotFoundError",
    "HighBondValidationError",
    "HighBondRateLimitError",
    "HighBondConnectionError",
    
    # Enums
    "Region",
    "ProjectState",
    "ProjectStatus",
    "ObjectiveType",
    "Severity",
    "RiskStatus",
    "ControlType",
    "ControlStatus",
    "ControlTestFrequency",
    "ControlAutomation",
    "IssueStatus",
    "IssuePriority",
    "SortOrder",
    
    # Módulos
    "ProjectsModule",
    "ObjectivesModule",
    "RisksModule",
    "ControlsModule",
    "IssuesModule",
]
