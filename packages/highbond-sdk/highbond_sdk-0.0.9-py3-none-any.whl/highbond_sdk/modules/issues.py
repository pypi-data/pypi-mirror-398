"""
Módulo de Issues para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig
from ..utils import to_dataframe


class IssuesModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Issues no HighBond.
    
    Issues representam problemas identificados, deficiências ou
    achados de auditoria que requerem acompanhamento e remediação.
    """
    
    def __init__(
        self,
        http_client: HighBondHTTPClient,
        org_id: int,
        pagination_config: PaginationConfig,
        threading_config: ThreadingConfig
    ):
        """
        Args:
            http_client: Cliente HTTP configurado.
            org_id: ID da organização.
            pagination_config: Configuração de paginação.
            threading_config: Configuração de threading.
        """
        self._http_client = http_client
        self._org_id = org_id
        self._pagination_config = pagination_config
        self._threading_config = threading_config
    
    @property
    def _org_endpoint(self) -> str:
        """Endpoint base para issues a nível de organização."""
        return f"/orgs/{self._org_id}/issues"
    
    def _project_endpoint(self, project_id: int) -> str:
        """Endpoint base para issues de um projeto."""
        return f"/orgs/{self._org_id}/projects/{project_id}/issues"
    

    
    # ==================== LISTAGEM ====================
    
    def list_all(
        self,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todas as issues da organização com paginação automática.
        
        Args:
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            max_pages: Máximo de páginas a buscar.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de issues ou DataFrame.
            
        Example:
            >>> for issue in client.issues.list_all():
            ...     print(issue['attributes']['title'])
        """
        pagination = PaginationConfig(
            page_size=self._pagination_config.page_size,
            max_pages=max_pages or self._pagination_config.max_pages
        )
        
        params = {}
        if include:
            params["include"] = ",".join(include)
        if filters:
            for key, value in filters.items():
                params[f"filter[{key}]"] = value
        
        issues = list(self._paginate(self._org_endpoint, pagination, params))
        
        if return_pandas:
            return to_dataframe(issues)
        return issues
    
    
    def list_by_project(
        self,
        project_id: int,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todas as issues de um projeto com paginação automática.
        
        Args:
            project_id: ID do projeto.
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            max_pages: Máximo de páginas.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de issues ou DataFrame.
        """
        pagination = PaginationConfig(
            page_size=self._pagination_config.page_size,
            max_pages=max_pages or self._pagination_config.max_pages
        )
        
        params = {}
        if include:
            params["include"] = ",".join(include)
        if filters:
            for key, value in filters.items():
                params[f"filter[{key}]"] = value
        
        issues = list(self._paginate(
            self._project_endpoint(project_id), pagination, params
        ))
        
        if return_pandas:
            return to_dataframe(issues)
        return issues

    
    def list_open(
        self,
        include: Optional[List[str]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        """Lista todas as issues abertas (status = open).
        
        Args:
            include: Relacionamentos para incluir.
            max_pages: Máximo de páginas.
            
        Yields:
            Cada issue aberta.
            
        Example:
            >>> open_issues = list(client.issues.list_open())
            >>> print(f"Issues abertas: {len(open_issues)}")
        """

        if return_pandas:
            return to_dataframe(self.list_all(include=include,filters={"closed": "false"}))
        
        return self.list_all(
            include=include,
            filters={"closed": "false"},
            max_pages=max_pages
        )
    
    # ==================== OBTENÇÃO ====================
    
    def get(
        self,
        issue_id: int,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém uma issue específica por ID.
        
        Args:
            issue_id: ID da issue.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna um dict.
            
        Returns:
            Dados da issue ou DataFrame.
            
        Example:
            >>> issue = client.issues.get(999)
            >>> print(issue['data']['attributes']['title'])
        """
        endpoint = f"{self._org_endpoint}/{issue_id}"
        params = {}
        
        if include:
            params["include"] = ",".join(include)
        
        response = self._http_client.get(endpoint, params if params else None)
        
        if return_pandas:
            data = response.get('data', {})
            return to_dataframe([data] if isinstance(data, dict) else data)
        return response
    
    def get_many(
        self,
        issue_ids: List[int],
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtém múltiplas issues em paralelo.
        
        Args:
            issue_ids: Lista de IDs de issues.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de dados de issues ou DataFrame.
        """
        def fetch_issue(iid):
            response = self.get(iid, include)
            return response.get('data', response)
        
        issues = self._execute_parallel(
            fetch_issue,
            issue_ids,
            self._threading_config
        )
        
        if return_pandas:
            return to_dataframe(issues)
        return issues
    
    # ==================== CRIAÇÃO ====================
    
    def create(
        self,
        project_id: int,
        description: str,
        deficiency_type: str,
        owner: Optional[str] = None,
        owner_user_uid: Optional[str] = None,
        title: Optional[str] = None,
        recommendation: Optional[str] = None,
        severity: Optional[str] = None,
        published: Optional[bool] = None,
        identified_at: Optional[str] = None,
        reference: Optional[str] = None,
        risk: Optional[str] = None,
        scope: Optional[str] = None,
        escalation: Optional[str] = None,
        cause: Optional[str] = None,
        effect: Optional[str] = None,
        cost_impact: Optional[float] = None,
        executive_summary: Optional[str] = None,
        executive_owner: Optional[str] = None,
        project_owner: Optional[str] = None,
        closed: Optional[bool] = None,
        remediation_status: Optional[str] = None,
        remediation_plan: Optional[str] = None,
        remediation_date: Optional[str] = None,
        actual_remediation_date: Optional[str] = None,
        retest_deadline_date: Optional[str] = None,
        actual_retest_date: Optional[str] = None,
        retesting_results_overview: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        target_id: Optional[int] = None,
        target_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Cria uma nova issue em um projeto.
        
        IMPORTANTE: Issues são criadas em Projects, não em Objectives diretamente.
        Endpoint: POST /orgs/{org_id}/projects/{project_id}/issues
        
        NOTA: Você deve fornecer `owner` (string) OU `owner_user_uid` (UID do usuário).
        Pelo menos um deles é obrigatório.
        
        Args:
            project_id: ID do projeto (obrigatório).
            description: Descrição detalhada da issue (obrigatório, max 524288 chars).
            deficiency_type: Tipo de deficiência (obrigatório, ex: "Deficiency", "Significant Deficiency").
                Opções dependem da configuração do project type.
            owner: Nome ou email do responsável (obrigatório se owner_user_uid não for fornecido).
            owner_user_uid: UID do usuário responsável (sobrescreve owner se fornecido).
            title: Título da issue (max 255 chars).
            recommendation: Descrição das ações recomendadas (max 524288 chars).
            severity: Severidade (ex: "High", "Medium", "Low"). Depende da config do project type.
            published: Se a issue é visível para todos (True) ou oculta de certos roles (False).
            identified_at: Timestamp de quando foi identificada (formato ISO 8601).
            reference: ID/referência da issue (max 255 chars).
            risk: Descrição do risco/impacto (max 524288 chars).
            scope: Escopo (ex: "Local", "Regional", "Enterprise"). Depende da config do project type.
            escalation: Para quem escalar (ex: "Owner", "Manager"). Depende da config do project type.
            cause: Descrição da causa (max 524288 chars).
            effect: Descrição do efeito (max 524288 chars).
            cost_impact: Custo monetário estimado/real.
            executive_summary: Resumo executivo (max 524288 chars).
            executive_owner: Nome/email do owner executivo.
            project_owner: Nome/email do owner do projeto.
            closed: Se a issue está fechada (True) ou aberta (False, padrão).
            remediation_status: Status de remediação (ex: "Opened", "In Progress", "Closed").
            remediation_plan: Descrição do plano de remediação (max 524288 chars).
            remediation_date: Data limite para remediação (YYYY-MM-DD).
            actual_remediation_date: Data real de remediação (YYYY-MM-DD).
            retest_deadline_date: Data limite para reteste (YYYY-MM-DD).
            actual_retest_date: Data real de reteste (YYYY-MM-DD).
            retesting_results_overview: Resumo dos resultados de reteste (max 524288 chars).
            position: Ordem de exibição (1-2147483647).
            custom_attributes: Atributos customizados.
                Formato: [{"id": "42", "term": "Nome", "value": ["valor"]}]
            target_id: ID do recurso relacionado à issue (se não fornecido, vincula ao projeto).
            target_type: Tipo do recurso relacionado. Valores possíveis:
                "projects", "narratives", "objectives", "walkthrough_summaries",
                "project_plannings", "walkthroughs", "control_tests", "control_test_plans",
                "project_results", "project_files", "risk_control_matrices",
                "testing_rounds", "risks", "controls"
            
        Returns:
            Dados da issue criada.
            
        Raises:
            ValueError: Se nem owner nem owner_user_uid forem fornecidos.
            
        Example:
            >>> issue = client.issues.create(
            ...     project_id=123,
            ...     description="<p>Descrição detalhada da deficiência</p>",
            ...     deficiency_type="Deficiency",
            ...     owner="thomas@sodor.ca",
            ...     title="Deficiência de Controle",
            ...     severity="High",
            ...     recommendation="<p>Recomendação de ação</p>"
            ... )
            >>> 
            >>> # Ou usando owner_user_uid
            >>> issue = client.issues.create(
            ...     project_id=123,
            ...     description="Descrição da issue",
            ...     deficiency_type="Significant Deficiency",
            ...     owner_user_uid="3NQ6XzAUxqJMnAQ7n4KF",
            ...     severity="Critical"
            ... )
        """
        # Validação: pelo menos owner ou owner_user_uid deve ser fornecido
        if owner is None and owner_user_uid is None:
            raise ValueError(
                "Você deve fornecer 'owner' (string) ou 'owner_user_uid' (UID do usuário). "
                "Pelo menos um deles é obrigatório."
            )
        
        attributes = {
            "description": description,
            "deficiency_type": deficiency_type
        }
        
        optional_attrs = {
            "owner": owner,
            "title": title,
            "recommendation": recommendation,
            "severity": severity,
            "published": published,
            "identified_at": identified_at,
            "reference": reference,
            "risk": risk,
            "scope": scope,
            "escalation": escalation,
            "cause": cause,
            "effect": effect,
            "cost_impact": cost_impact,
            "executive_summary": executive_summary,
            "executive_owner": executive_owner,
            "project_owner": project_owner,
            "closed": closed,
            "remediation_status": remediation_status,
            "remediation_plan": remediation_plan,
            "remediation_date": remediation_date,
            "actual_remediation_date": actual_remediation_date,
            "retest_deadline_date": retest_deadline_date,
            "actual_retest_date": actual_retest_date,
            "retesting_results_overview": retesting_results_overview,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "issues",
                "attributes": attributes
            }
        }
        
        relationships = {}
        
        if owner_user_uid:
            relationships["owner_user"] = {
                "data": {"type": "users", "id": str(owner_user_uid)}
            }
        
        if target_id and target_type:
            relationships["target"] = {
                "data": {"type": target_type, "id": str(target_id)}
            }
        
        if relationships:
            payload["data"]["relationships"] = relationships
        
        return self._http_client.post(self._project_endpoint(project_id), payload)
    
    # ==================== ATUALIZAÇÃO ====================
    
    def update(
        self,
        issue_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        deficiency_type: Optional[str] = None,
        owner: Optional[str] = None,
        recommendation: Optional[str] = None,
        severity: Optional[str] = None,
        published: Optional[bool] = None,
        identified_at: Optional[str] = None,
        reference: Optional[str] = None,
        risk: Optional[str] = None,
        scope: Optional[str] = None,
        escalation: Optional[str] = None,
        cause: Optional[str] = None,
        effect: Optional[str] = None,
        cost_impact: Optional[float] = None,
        executive_summary: Optional[str] = None,
        executive_owner: Optional[str] = None,
        project_owner: Optional[str] = None,
        closed: Optional[bool] = None,
        remediation_status: Optional[str] = None,
        remediation_plan: Optional[str] = None,
        remediation_date: Optional[str] = None,
        actual_remediation_date: Optional[str] = None,
        retest_deadline_date: Optional[str] = None,
        actual_retest_date: Optional[str] = None,
        retesting_results_overview: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        owner_user_uid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atualiza uma issue existente.
        
        Endpoint: PATCH /orgs/{org_id}/issues/{issue_id}
        
        Args:
            issue_id: ID da issue a atualizar.
            title: Novo título (max 255 chars).
            description: Nova descrição (max 524288 chars).
            deficiency_type: Tipo de deficiência.
            owner: Nome ou email do responsável.
            recommendation: Descrição das ações recomendadas.
            severity: Severidade.
            published: Se a issue é visível para todos.
            identified_at: Timestamp de quando foi identificada.
            reference: ID/referência da issue.
            risk: Descrição do risco/impacto.
            scope: Escopo.
            escalation: Para quem escalar.
            cause: Descrição da causa.
            effect: Descrição do efeito.
            cost_impact: Custo monetário estimado/real.
            executive_summary: Resumo executivo.
            executive_owner: Nome/email do owner executivo.
            project_owner: Nome/email do owner do projeto.
            closed: Se a issue está fechada.
            remediation_status: Status de remediação.
            remediation_plan: Descrição do plano de remediação.
            remediation_date: Data limite para remediação (YYYY-MM-DD).
            actual_remediation_date: Data real de remediação (YYYY-MM-DD).
            retest_deadline_date: Data limite para reteste (YYYY-MM-DD).
            actual_retest_date: Data real de reteste (YYYY-MM-DD).
            retesting_results_overview: Resumo dos resultados de reteste.
            position: Ordem de exibição (1-2147483647).
            custom_attributes: Atributos customizados.
            owner_user_uid: UID do usuário responsável (sobrescreve owner).
            
        Returns:
            Dados da issue atualizada.
            
        Example:
            >>> issue = client.issues.update(
            ...     issue_id=999,
            ...     closed=True,
            ...     actual_remediation_date="2024-06-15"
            ... )
        """
        attributes = {}
        
        optional_attrs = {
            "title": title,
            "description": description,
            "deficiency_type": deficiency_type,
            "owner": owner,
            "recommendation": recommendation,
            "severity": severity,
            "published": published,
            "identified_at": identified_at,
            "reference": reference,
            "risk": risk,
            "scope": scope,
            "escalation": escalation,
            "cause": cause,
            "effect": effect,
            "cost_impact": cost_impact,
            "executive_summary": executive_summary,
            "executive_owner": executive_owner,
            "project_owner": project_owner,
            "closed": closed,
            "remediation_status": remediation_status,
            "remediation_plan": remediation_plan,
            "remediation_date": remediation_date,
            "actual_remediation_date": actual_remediation_date,
            "retest_deadline_date": retest_deadline_date,
            "actual_retest_date": actual_retest_date,
            "retesting_results_overview": retesting_results_overview,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes is not None:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "issues",
                "id": str(issue_id),
                "attributes": attributes
            }
        }
        
        if owner_user_uid:
            payload["data"]["relationships"] = {
                "owner_user": {
                    "data": {"type": "users", "id": str(owner_user_uid)}
                }
            }
        
        endpoint = f"{self._org_endpoint}/{issue_id}"
        return self._http_client.patch(endpoint, payload)

    
    # ==================== EXCLUSÃO ====================
    
    def delete(self, issue_id: int) -> Dict[str, Any]:
        """Exclui uma issue.
        
        Args:
            issue_id: ID da issue a excluir.
            
        Returns:
            Resposta da API.
            
        Warning:
            Esta ação é irreversível.
        """
        endpoint = f"{self._org_endpoint}/{issue_id}"
        return self._http_client.delete(endpoint)
    
    

