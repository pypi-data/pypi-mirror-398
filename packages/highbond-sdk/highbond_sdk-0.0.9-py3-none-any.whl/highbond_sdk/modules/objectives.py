"""
Módulo de Objetivos para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig
from ..enums import ObjectiveType
from ..utils import to_dataframe


class ObjectivesModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Objetivos no HighBond.
    
    Objetivos são unidades de trabalho dentro de projetos que definem
    escopo e metas específicas.
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
    
    def _base_endpoint(self, project_id: int) -> str:
        """Endpoint base para objetivos de um projeto."""
        return f"/orgs/{self._org_id}/projects/{project_id}/objectives"
    
    
    def list_by_project(
        self,
        project_id: int,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todos os objetivos de um projeto com paginação automática.
        
        Args:
            project_id: ID do projeto.
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            max_pages: Máximo de páginas.
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de objetivos ou DataFrame.
            
        Example:
            >>> for obj in client.objectives.list_all_by_project(123):
            ...     print(obj['attributes']['title'])
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
        
        objetivos = list(self._paginate(
            self._base_endpoint(project_id), pagination, params
        ))
        
        if return_pandas:
            return to_dataframe(objetivos)
        return objetivos
    
    def get(
        self,
        project_id: int,
        objective_id: int,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém um objetivo específico.
        
        Args:
            project_id: ID do projeto.
            objective_id: ID do objetivo.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna um dict.
            
        Returns:
            Dados do objetivo ou DataFrame.
            
        Example:
            >>> obj = client.objectives.get(123, 456)
            >>> print(obj['data']['attributes']['title'])
        """
        endpoint = f"{self._base_endpoint(project_id)}/{objective_id}"
        params = {}
        
        if include:
            params["include"] = ",".join(include)
        
        response = self._http_client.get(endpoint, params if params else None)
        
        if return_pandas:
            data = response.get('data', {})
            return to_dataframe([data] if isinstance(data, dict) else data)
        return response
    
    def create(
        self,
        project_id: int,
        title: str,
        description: Optional[str] = None,
        objective_type: Optional[ObjectiveType] = None,
        reference: Optional[str] = None,
        position: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        planned_start_date: Optional[str] = None,
        planned_end_date: Optional[str] = None,
        owner_id: Optional[int] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Cria um novo objetivo em um projeto.
        
        Args:
            project_id: ID do projeto.
            title: Título do objetivo (obrigatório).
            description: Descrição do objetivo.
            objective_type: Tipo do objetivo.
            reference: Referência externa.
            position: Posição na lista de objetivos.
            start_date: Data de início real.
            end_date: Data de término real.
            planned_start_date: Data de início planejada.
            planned_end_date: Data de término planejada.
            owner_id: ID do proprietário.
            custom_attributes: Atributos customizados.
            
        Returns:
            Dados do objetivo criado.
            
        Example:
            >>> obj = client.objectives.create(
            ...     project_id=123,
            ...     title="Revisão de Controles",
            ...     objective_type=ObjectiveType.WALKTHROUGH
            ... )
        """
        attributes = {"title": title}
        
        optional_attrs = {
            "description": description,
            "objective_type": (
                objective_type.value 
                if isinstance(objective_type, ObjectiveType) 
                else objective_type
            ),
            "reference": reference,
            "position": position,
            "start_date": start_date,
            "end_date": end_date,
            "planned_start_date": planned_start_date,
            "planned_end_date": planned_end_date,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "objectives",
                "attributes": attributes
            }
        }
        
        if owner_id:
            payload["data"]["relationships"] = {
                "owner": {
                    "data": {"type": "users", "id": str(owner_id)}
                }
            }
        
        return self._http_client.post(self._base_endpoint(project_id), payload)
    
    def update(
        self,
        project_id: int,
        objective_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        objective_type: Optional[ObjectiveType] = None,
        reference: Optional[str] = None,
        position: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        planned_start_date: Optional[str] = None,
        planned_end_date: Optional[str] = None,
        owner_id: Optional[int] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Atualiza um objetivo existente.
        
        Args:
            project_id: ID do projeto.
            objective_id: ID do objetivo.
            title: Novo título.
            description: Nova descrição.
            objective_type: Novo tipo.
            reference: Nova referência.
            position: Nova posição.
            start_date: Nova data de início.
            end_date: Nova data de término.
            planned_start_date: Nova data de início planejada.
            planned_end_date: Nova data de término planejada.
            owner_id: Novo proprietário.
            custom_attributes: Novos atributos customizados.
            
        Returns:
            Dados do objetivo atualizado.
            
        Example:
            >>> obj = client.objectives.update(
            ...     project_id=123,
            ...     objective_id=456,
            ...     title="Revisão de Controles - Atualizado"
            ... )
        """
        attributes = {}
        
        optional_attrs = {
            "title": title,
            "description": description,
            "objective_type": (
                objective_type.value 
                if isinstance(objective_type, ObjectiveType) 
                else objective_type
            ),
            "reference": reference,
            "position": position,
            "start_date": start_date,
            "end_date": end_date,
            "planned_start_date": planned_start_date,
            "planned_end_date": planned_end_date,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes is not None:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "objectives",
                "id": str(objective_id),
                "attributes": attributes
            }
        }
        
        if owner_id:
            payload["data"]["relationships"] = {
                "owner": {
                    "data": {"type": "users", "id": str(owner_id)}
                }
            }
        
        endpoint = f"{self._base_endpoint(project_id)}/{objective_id}"
        return self._http_client.patch(endpoint, payload)
    
    def delete(self, project_id: int, objective_id: int) -> Dict[str, Any]:
        """Exclui um objetivo.
        
        Args:
            project_id: ID do projeto.
            objective_id: ID do objetivo a excluir.
            
        Returns:
            Resposta da API.
            
        Warning:
            Esta ação é irreversível.
        """
        endpoint = f"{self._base_endpoint(project_id)}/{objective_id}"
        return self._http_client.delete(endpoint)
