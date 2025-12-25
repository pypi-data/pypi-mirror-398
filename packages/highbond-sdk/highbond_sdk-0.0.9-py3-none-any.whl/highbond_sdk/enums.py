
"""highbond_sdk.enums
======================

Enums usados pelo SDK. Muitos campos na API HighBond são configuráveis
por `project type`, portanto esses enums representam valores comuns
e são fornecidos apenas como conveniência/documentação.
"""

from enum import Enum


class ObjectiveType(str, Enum):
    """Tipos comuns de objetivo."""
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"


class ProjectState(str, Enum):
    """Estados possíveis de um projeto."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    CLOSED = "closed"


class ProjectStatus(str, Enum):
    """Status possíveis de um projeto."""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    OFF_TRACK = "off_track"
    COMPLETED = "completed"


class Region(str, Enum):
    """Regiões da API HighBond.

    Use esses valores para configurar a região apropriada.
    """

    US = "us"
    EU = "eu"
    AU = "au"
    CA = "ca"
    SA = "sa"

    @classmethod
    def get_base_url(cls, region: "Region") -> str:
        if region == cls.SA:
            return "https://apis-sa.diligentoneplatform.com/v1"
        return f"https://apis-{region.value}.highbond.com/v1"


class Severity(str, Enum):
    """Severidade típica para issues/risks (exemplos)."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RiskStatus(str, Enum):
    """Status comum de riscos."""
    OPEN = "Open"
    MONITORED = "Monitored"
    MITIGATED = "Mitigated"
    CLOSED = "Closed"


class ControlType(str, Enum):
    """Tipos de controles (exemplos)."""
    APPLICATION = "Application/System Control"
    MANUAL = "Manual Control"
    IT_DEPENDENT = "IT Dependent Manual Control"


class ControlStatus(str, Enum):
    """Status de controles."""
    KEY = "Key Control"
    NOT_KEY = "Not Key Control"


class ControlTestFrequency(str, Enum):
    """Frequência de teste de controles."""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"


class ControlAutomation(str, Enum):
    """Nível de automação do controle."""
    AUTOMATED = "Automated"
    MANUAL = "Manual"


class IssueStatus(str, Enum):
    """Status de issues."""
    OPEN = "Opened"
    IN_PROGRESS = "In Progress"
    CLOSED = "Closed"


class IssuePriority(str, Enum):
    """Prioridade de issues."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


__all__ = [
    "ObjectiveType",
    "ProjectState",
    "ProjectStatus",
    "Region",
    "Severity",
    "RiskStatus",
    "ControlType",
    "ControlStatus",
    "ControlTestFrequency",
    "ControlAutomation",
    "IssueStatus",
    "IssuePriority",
    "SortOrder",
]


#  Os valores abaixo são EXEMPLOS comuns que podem variar de acordo
# com a configuração da sua organização. Sempre verifique as opções disponíveis no
# seu project type específico.

# Adiciona enum faltante para documentação automática
# Exemplos de valores para campo 'scope' em Issues:
# - "Local"
# - "Regional"
# - "Enterprise"

# Exemplos de valores para campo 'escalation' em Issues:
# - "Owner"
# - "Manager"
# - "Director"
# - "Executive"
# - "Board"



