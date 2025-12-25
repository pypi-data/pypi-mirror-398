"""
Módulo de Riscos para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig

from ..utils import to_dataframe

class RisksModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Riscos no HighBond.
    
    Riscos representam ameaças potenciais aos objetivos da organização.
    Podem ser vinculados a projetos, objetivos e controles.
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
        """Endpoint base para riscos a nível de organização."""
        return f"/orgs/{self._org_id}/risks"
    
    def _objective_endpoint(self, objective_id: int) -> str:
        """Endpoint base para riscos de um objetivo."""
        return (
            f"/orgs/{self._org_id}/objectives/{objective_id}/risks"
        )
    
    # ==================== LISTAGEM ====================
    
    
    def list_all(
        self,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Lista todos os riscos da organização: busca todos os projetos, depois todos os objetivos de cada projeto (em paralelo), e então todos os riscos de cada objetivo (em paralelo).
        """
        from .projects import ProjectsModule
        from .objectives import ObjectivesModule
        # 1. Buscar todos os projetos
        projects_module = ProjectsModule(
            self._http_client,
            self._org_id,
            self._pagination_config,
            self._threading_config
        )
        all_projects = list(projects_module.list_all())

        # Criar um mapa de objetivo_id para project_id
        objective_to_project = {}

        # 2. Buscar todos os objetivos de todos os projetos em paralelo
        objectives_module = ObjectivesModule(
            self._http_client,
            self._org_id,
            self._pagination_config,
            self._threading_config
        )
        def fetch_objectives(proj):
            objetivos = list(objectives_module.list_by_project(proj["id"]))
            for obj in objetivos:
                objective_to_project[obj["id"]] = proj["id"]
            return objetivos
        all_objectives_nested = self._execute_parallel(
            fetch_objectives,
            all_projects,
            self._threading_config
        )
        all_objectives = [obj for sublist in all_objectives_nested for obj in sublist]

        # 3. Buscar todos os riscos de todos os objetivos em paralelo
        def fetch_risks(obj):
            riscos_obj = self.list_by_objective(
                objective_id=obj["id"],
                include=include
            )
            if isinstance(riscos_obj, dict) and "data" in riscos_obj:
                for risco in riscos_obj["data"]:
                    risco["project_id"] = objective_to_project.get(obj["id"])
                return riscos_obj["data"]
            return []
        all_risks_nested = self._execute_parallel(
            fetch_risks,
            all_objectives,
            self._threading_config
        )
        all_risks = [r for sublist in all_risks_nested for r in sublist]

        if return_pandas:
            return to_dataframe(all_risks)
        return all_risks
    

    
    def list_by_project(
        self,
        project_id: int,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Lista todos os riscos de um projeto (buscando todos os objetivos e seus riscos).
        """
        from .objectives import ObjectivesModule
        objectives_module = ObjectivesModule(
            self._http_client,
            self._org_id,
            self._pagination_config,
            self._threading_config
        )
        objetivos = list(objectives_module.list_by_project(project_id))
        riscos = []
        for obj in objetivos:
            riscos_obj = self.list_by_objective(
                objective_id=obj["id"],
                include=include
            )
            if isinstance(riscos_obj, dict) and "data" in riscos_obj:
                riscos.extend(riscos_obj["data"])
        if return_pandas:
            return to_dataframe(riscos)
        return riscos
    
    # ==================== LISTAGEM POR OBJETIVO ====================
    
    def list_by_objective(
        self,
        objective_id: int,
        page: int = 1,
        page_size: int = 50,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Lista riscos de um objetivo específico.
        
        Args:
            objective_id: ID do objetivo.
            page: Número da página.
            page_size: Itens por página.
            include: Relacionamentos para incluir.
            
        Returns:
            Resposta completa da API.
        """
        params = {
            "page[number]": self._encode_page_number(page),
            "page[size]": min(page_size, 100)
        }
        
        if include:
            params["include"] = ",".join(include)
        
        endpoint = self._objective_endpoint(objective_id)
        if return_pandas:
            response = self._http_client.get(endpoint, params)
            return to_dataframe(response)
        return self._http_client.get(endpoint, params)
    
    # ==================== OBTENÇÃO ====================
    
    def get(
        self,
        risk_id: int,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém um risco específico por ID.
        
        Args:
            risk_id: ID do risco.
            include: Relacionamentos para incluir.
            
        Returns:
            Dados do risco.
            
        Example:
            >>> risk = client.risks.get(456)
            >>> print(risk['data']['attributes']['title'])
        """
        endpoint = f"{self._org_endpoint}/{risk_id}"
        params = {}
        
        if include:
            params["include"] = ",".join(include)
        if return_pandas:
            response = self._http_client.get(endpoint, params)
            return to_dataframe(response)
        
        return self._http_client.get(endpoint, params if params else None)
    
    def get_many(
        self,
        risk_ids: List[int],
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtém múltiplos riscos em paralelo.
        
        Args:
            risk_ids: Lista de IDs de riscos.
            include: Relacionamentos para incluir.
            
        Returns:
            Lista de dados de riscos.
        """
        def fetch_risk(rid):
            return self.get(rid, include)
        
        if return_pandas:
            risks = self._execute_parallel(
                fetch_risk,
                risk_ids,
                self._threading_config
            )
            return to_dataframe(risks)
        
        return self._execute_parallel(
            fetch_risk,
            risk_ids,
            self._threading_config
        )
    
    # ==================== CRIAÇÃO ====================
    
    def create(
        self,
        objective_id: int,
        description: str,
        title: Optional[str] = None,
        risk_id: Optional[str] = None,
        owner: Optional[str] = None,
        impact: Optional[str] = None,
        likelihood: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        custom_factors: Optional[List[Dict[str, Any]]] = None,
        owner_user_uid: Optional[str] = None,
        framework_origin_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cria um novo risco em um objetivo.
        
        IMPORTANTE: Riscos são criados dentro de Objectives, não diretamente em Projects.
        Endpoint: POST /orgs/{org_id}/objectives/{objective_id}/risks
        
        Args:
            objective_id: ID do objetivo (obrigatório).
            description: Descrição detalhada do risco (obrigatório, max 524288 chars).
            title: Título do risco (opcional, max 255 chars).
            risk_id: Código de referência do risco (max 255 chars).
            owner: Nome ou email do responsável (string, não envia notificação).
            impact: Classificação de impacto (ex: "High", "Medium", "Low" - depende da config do project type).
            likelihood: Probabilidade (ex: "High", "Medium", "Low" - depende da config do project type).
            position: Ordem de exibição (1-2147483647).
            custom_attributes: Lista de atributos customizados.
                Formato: [{"id": "42", "term": "Nome", "value": ["valor"]}]
            custom_factors: Lista de fatores de risco customizados.
                Formato: [{"id": "42", "term": "Fator", "value": ["valor"]}]
            owner_user_uid: UID do usuário responsável (sobrescreve owner, envia notificação).
            framework_origin_id: ID do risco equivalente em um framework associado.
            
        Returns:
            Dados do risco criado.
            
        Example:
            >>> risk = client.risks.create(
            ...     objective_id=456,
            ...     description="Descrição detalhada do risco de compliance",
            ...     title="Risco de Compliance",
            ...     impact="High",
            ...     likelihood="Medium",
            ...     owner="thomas@sodor.ca"
            ... )
        """
        attributes = {"description": description}
        
        optional_attrs = {
            "title": title,
            "risk_id": risk_id,
            "owner": owner,
            "impact": impact,
            "likelihood": likelihood,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes:
            attributes["custom_attributes"] = custom_attributes
        
        if custom_factors:
            attributes["custom_factors"] = custom_factors
        
        payload = {
            "data": {
                "type": "risks",
                "attributes": attributes
            }
        }
        
        relationships = {}
        
        if owner_user_uid:
            relationships["owner_user"] = {
                "data": {"type": "users", "id": str(owner_user_uid)}
            }
        
        if framework_origin_id:
            relationships["framework_origin"] = {
                "data": {"type": "risks", "id": str(framework_origin_id)}
            }
        
        if relationships:
            payload["data"]["relationships"] = relationships
        
        endpoint = f"/orgs/{self._org_id}/objectives/{objective_id}/risks"
        return self._http_client.post(endpoint, payload)
    
    # ==================== ATUALIZAÇÃO ====================
    
    def update(
        self,
        risk_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        risk_id_ref: Optional[str] = None,
        owner: Optional[str] = None,
        impact: Optional[str] = None,
        likelihood: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        custom_factors: Optional[List[Dict[str, Any]]] = None,
        owner_user_uid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atualiza um risco existente.
        
        Endpoint: PATCH /orgs/{org_id}/risks/{risk_id}
        
        Args:
            risk_id: ID do risco a atualizar.
            title: Novo título (max 255 chars).
            description: Nova descrição (max 524288 chars).
            risk_id_ref: Novo código de referência (campo risk_id na API).
            owner: Nome ou email do responsável.
            impact: Classificação de impacto (ex: "High", "Medium", "Low").
            likelihood: Probabilidade (ex: "High", "Medium", "Low").
            position: Nova ordem de exibição (1-2147483647).
            custom_attributes: Atributos customizados, formato [{ "term": "Fator", "value": ["valor"]}].
            custom_factors: Fatores de risco customizados, formato [{ "term": "Fator", "value": ["valor"]}].
            owner_user_uid: UID do usuário responsável (sobrescreve owner).
            
        Returns:
            Dados do risco atualizado.
            
        Example:
            >>> risk = client.risks.update(
            ...     risk_id=456,
            ...     title="Novo título do risco",
            ...     impact="Low"
            ... )
        """
        attributes = {}
        
        optional_attrs = {
            "title": title,
            "description": description,
            "risk_id": risk_id_ref,
            "owner": owner,
            "impact": impact,
            "likelihood": likelihood,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes is not None:
            attributes["custom_attributes"] = custom_attributes
        
        if custom_factors is not None:
            attributes["custom_factors"] = custom_factors
        
        payload = {
            "data": {
                "type": "risks",
                "id": str(risk_id),
                "attributes": attributes
            }
        }
        
        if owner_user_uid:
            payload["data"]["relationships"] = {
                "owner_user": {
                    "data": {"type": "users", "id": str(owner_user_uid)}
                }
            }
        
        endpoint = f"{self._org_endpoint}/{risk_id}"
        return self._http_client.patch(endpoint, payload)
    
    # ==================== EXCLUSÃO ====================
    
    def delete(self, risk_id: int) -> Dict[str, Any]:
        """Exclui um risco.
        
        Args:
            risk_id: ID do risco a excluir.
            
        Returns:
            Resposta da API.
            
        Warning:
            Esta ação é irreversível.
        """
        endpoint = f"{self._org_endpoint}/{risk_id}"
        return self._http_client.delete(endpoint)
    
