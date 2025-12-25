"""
Módulo de Controles para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig
from ..utils import to_dataframe


class ControlsModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Controles no HighBond.
    
    Controles são mecanismos implementados para mitigar riscos
    e garantir conformidade com políticas e procedimentos.
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
        """Endpoint base para controles a nível de organização."""
        return f"/orgs/{self._org_id}/controls"
    
    def _objective_endpoint(self, objective_id: int) -> str:
        """Endpoint base para controles de um objetivo."""
        return f"/orgs/{self._org_id}/objectives/{objective_id}/controls"
    
    # ==================== LISTAGEM ====================
    
    def list_all(
        self,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todos os controles da organização com paginação automática.
        
        Args:
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            max_pages: Máximo de páginas a buscar.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de todos os controles ou DataFrame.
            
        Example:
            >>> for control in client.controls.list_all():
            ...     print(control['attributes']['title'])
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
        
        controles = list(self._paginate(self._org_endpoint, pagination, params))
        
        if return_pandas:
            return to_dataframe(controles)
        return controles
    
    
    def list_by_project(
        self,
        project_id: int,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todos os controles de um projeto (buscando todos os objetivos e seus controles).
        
        Args:
            project_id: ID do projeto.
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de controles do projeto ou DataFrame.
        """
        from .objectives import ObjectivesModule
        objectives_module = ObjectivesModule(
            self._http_client,
            self._org_id,
            self._pagination_config,
            self._threading_config
        )
        objetivos = list(objectives_module.list_by_project(project_id))
        controles = []
        for obj in objetivos:
            controles_obj = self.list_by_objective(
                objective_id=obj["id"],
                include=include
            )
            if isinstance(controles_obj, dict) and "data" in controles_obj:
                controles.extend(controles_obj["data"])
        if return_pandas:
            return to_dataframe(controles)
        return controles
    
    def list_by_objective(
        self,
        objective_id: int,
        page: int = 1,
        page_size: int = 50,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Lista controles de um objetivo específico.
        
        Args:
            objective_id: ID do objetivo.
            page: Número da página.
            page_size: Itens por página.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Resposta completa da API ou DataFrame.
        """
        params = {
            "page[number]": self._encode_page_number(page),
            "page[size]": min(page_size, 100)
        }
        
        if include:
            params["include"] = ",".join(include)
        
        endpoint = self._objective_endpoint(objective_id)
        response = self._http_client.get(endpoint, params)
        data = response["data"] if "data" in response else response
        
        # Adiciona informações do objetivo se necessário
        if return_pandas:
            return to_dataframe(data)
        return response
    
    # ==================== OBTENÇÃO ====================
    
    def get(
        self,
        control_id: int,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém um controle específico por ID.
        
        Args:
            control_id: ID do controle.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do controle ou DataFrame.
            
        Example:
            >>> control = client.controls.get(789)
            >>> print(control['data']['attributes']['title'])
        """
        endpoint = f"{self._org_endpoint}/{control_id}"
        params = {}
        
        if include:
            params["include"] = ",".join(include)
        
        response = self._http_client.get(endpoint, params if params else None)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def get_many(
        self,
        control_ids: List[int],
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtém múltiplos controles em paralelo.
        
        Args:
            control_ids: Lista de IDs de controles.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna lista.
            
        Returns:
            Lista de dados de controles ou DataFrame.
        """
        def fetch_control(cid):
            return self.get(cid, include, return_pandas=False)
        
        controls = self._execute_parallel(
            fetch_control,
            control_ids,
            self._threading_config
        )
        
        if return_pandas:
            return to_dataframe(controls)
        return controls
    
    # ==================== CRIAÇÃO ====================
    
    def create(
        self,
        objective_id: int,
        description: str,
        title: Optional[str] = None,
        control_id: Optional[str] = None,
        owner: Optional[str] = None,
        frequency: Optional[str] = None,
        method: Optional[str] = None,
        control_type: Optional[str] = None,
        prevent_detect: Optional[str] = None,
        status: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        owner_user_uid: Optional[str] = None,
        framework_origin_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Cria um novo controle em um objetivo.
        
        IMPORTANTE: Controles são criados dentro de Objectives, não diretamente em Projects.
        Endpoint: POST /orgs/{org_id}/objectives/{objective_id}/controls
        
        NOTA: Para projetos de workflow "Internal Control", os campos frequency, 
        control_type e prevent_detect são obrigatórios.
        
        Args:
            objective_id: ID do objetivo (obrigatório).
            description: Descrição detalhada do controle (obrigatório, max 524288 chars).
            title: Título do controle (opcional, max 255 chars).
            control_id: Código de referência do controle (max 255 chars).
            owner: Nome ou email do responsável (string, não envia notificação).
            frequency: Frequência do controle (ex: "Daily", "Weekly", "Monthly").
                Obrigatório para Internal Control workflow. Depende da config do project type.
            method: Método de teste/implementação (ex: "Management Review", "Observation").
            control_type: Tipo do controle (ex: "Application/System Control", "Manual Control").
                Obrigatório para Internal Control workflow. Depende da config do project type.
            prevent_detect: Preventivo ou detectivo (ex: "Prevent", "Detect", "N/A").
                Obrigatório para Internal Control workflow.
            status: Status do controle (ex: "Key Control", "Not Key Control").
            position: Ordem de exibição (1-2147483647).
            custom_attributes: Lista de atributos customizados.
                Formato: [{"id": "42", "term": "Nome", "value": ["valor"]}]
            owner_user_uid: UID do usuário responsável (sobrescreve owner, envia notificação).
            framework_origin_id: ID do controle equivalente em um framework associado.
            
        Returns:
            Dados do controle criado.
            
        Example:
            >>> # Para Internal Control workflow
            >>> control = client.controls.create(
            ...     objective_id=456,
            ...     description="Descrição detalhada do controle de aprovação",
            ...     title="Controle de Aprovação",
            ...     frequency="Daily",
            ...     control_type="Manual Control",
            ...     prevent_detect="Prevent",
            ...     owner="thomas@sodor.ca"
            ... )
            >>> 
            >>> # Para Workplan workflow
            >>> control = client.controls.create(
            ...     objective_id=456,
            ...     description="Descrição do procedimento",
            ...     title="Procedimento de Auditoria"
            ... )
        """
        attributes = {"description": description}
        
        optional_attrs = {
            "title": title,
            "control_id": control_id,
            "owner": owner,
            "frequency": frequency,
            "method": method,
            "control_type": control_type,
            "prevent_detect": prevent_detect,
            "status": status,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "controls",
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
                "data": {"type": "controls", "id": str(framework_origin_id)}
            }
        
        if relationships:
            payload["data"]["relationships"] = relationships
        
        endpoint = f"/orgs/{self._org_id}/objectives/{objective_id}/controls"
        return self._http_client.post(endpoint, payload)
    
    # ==================== ATUALIZAÇÃO ====================
    
    def update(
        self,
        control_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        control_id_ref: Optional[str] = None,
        owner: Optional[str] = None,
        frequency: Optional[str] = None,
        method: Optional[str] = None,
        control_type: Optional[str] = None,
        prevent_detect: Optional[str] = None,
        status: Optional[str] = None,
        position: Optional[int] = None,
        custom_attributes: Optional[List[Dict[str, Any]]] = None,
        owner_user_uid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Atualiza um controle existente.
        
        Endpoint: PATCH /orgs/{org_id}/controls/{control_id}
        
        Args:
            control_id: ID do controle a atualizar.
            title: Novo título (max 255 chars).
            description: Nova descrição (max 524288 chars).
            control_id_ref: Novo código de referência (campo control_id na API).
            owner: Nome ou email do responsável.
            frequency: Frequência do controle (ex: "Daily", "Weekly", "Monthly").
            method: Método de teste/implementação.
            control_type: Tipo do controle.
            prevent_detect: Preventivo ou detectivo.
            status: Status do controle.
            position: Nova ordem de exibição (1-2147483647).
            custom_attributes: Atributos customizados.
            owner_user_uid: UID do usuário responsável (sobrescreve owner).
            
        Returns:
            Dados do controle atualizado.
            
        Example:
            >>> control = client.controls.update(
            ...     control_id=789,
            ...     title="Novo título do controle",
            ...     status="Key Control"
            ... )
        """
        attributes = {}
        
        optional_attrs = {
            "title": title,
            "description": description,
            "control_id": control_id_ref,
            "owner": owner,
            "frequency": frequency,
            "method": method,
            "control_type": control_type,
            "prevent_detect": prevent_detect,
            "status": status,
            "position": position,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes is not None:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "controls",
                "id": str(control_id),
                "attributes": attributes
            }
        }
        
        if owner_user_uid:
            payload["data"]["relationships"] = {
                "owner_user": {
                    "data": {"type": "users", "id": str(owner_user_uid)}
                }
            }
        
        endpoint = f"{self._org_endpoint}/{control_id}"
        return self._http_client.patch(endpoint, payload)
    
    # ==================== EXCLUSÃO ====================
    
    def delete(self, control_id: int) -> Dict[str, Any]:
        """Exclui um controle.
        
        Args:
            control_id: ID do controle a excluir.
            
        Returns:
            Resposta da API.
            
        Warning:
            Esta ação é irreversível.
        """
        endpoint = f"{self._org_endpoint}/{control_id}"
        return self._http_client.delete(endpoint)
    

    


 