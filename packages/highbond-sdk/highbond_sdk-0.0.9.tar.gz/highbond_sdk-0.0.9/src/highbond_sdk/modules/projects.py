"""
Módulo de Projetos para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig
from ..enums import ProjectState, ProjectStatus

from ..utils import to_dataframe

class ProjectsModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Projetos no HighBond.
    
    Projetos são containers de alto nível que organizam objetivos,
    riscos, controles e issues.
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
    def _base_endpoint(self) -> str:
        """Endpoint base para projetos."""
        return f"/orgs/{self._org_id}/projects"
    
    def list(
        self,
        page: int = 1,
        page_size: int = 50,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Lista projetos com paginação manual.
        
        Args:
            page: Número da página (1-based).
            page_size: Itens por página (máximo 100).
            include: Relacionamentos para incluir (ex: ['objectives', 'owner']).
            filters: Filtros adicionais.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Resposta completa da API com data, meta e links, ou DataFrame.
            
        Example:
            >>> response = client.projects.list(page=1, page_size=25)
            >>> for project in response['data']:
            ...     print(project['attributes']['title'])
        """
        params = {
            "page[number]": self._encode_page_number(page),
            "page[size]": min(page_size, 100)
        }
        
        if include:
            params["include"] = ",".join(include)
        
        if filters:
            for key, value in filters.items():
                params[f"filter[{key}]"] = value
        
        response = self._http_client.get(self._base_endpoint, params)
        
        if return_pandas:
            data = response["data"] if "data" in response else response
            return to_dataframe(data)
        return response
    
    def list_all(
        self,
        include: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todos os projetos com paginação automática.
        
        Args:
            include: Relacionamentos para incluir.
            filters: Filtros adicionais.
            max_pages: Máximo de páginas a buscar (None = todas).
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de projetos ou DataFrame.
            
        Example:
            >>> for project in client.projects.list_all():
            ...     print(project['attributes']['title'])
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
        
        projetos = list(self._paginate(self._base_endpoint, pagination, params))
        
        if return_pandas:
            return to_dataframe(projetos)
        return projetos

    def list_project_types(self) -> List[Dict[str, Any]]:
        """Lista os tipos de projeto disponíveis na organização.

        Retorna a lista de `project_types` como fornecida pela API. Útil para
        sugerir IDs válidos quando a criação falha por tipo inválido.
        """
        endpoint = f"/orgs/{self._org_id}/project_types"
        resp = self._http_client.get(endpoint)
        if isinstance(resp, dict):
            data = resp.get("data", [])
            simplified = []
            for item in data:
                simplified.append({
                    "id": item.get("id"),
                    "name": (item.get("attributes") or {}).get("name")
                })
            return simplified
        return []


    def tipos_de_projetos(self) -> List[Dict[str, Any]]:
        """Alias em português para `list_project_types()`.

        Retorna a lista de tipos de projeto da organização.
        """
        return self.list_project_types()
    
    def get(
        self,
        project_id: int,
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém um projeto específico por ID.
        
        Args:
            project_id: ID do projeto.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do projeto ou DataFrame.
            
        Example:
            >>> project = client.projects.get(123)
            >>> print(project['data']['attributes']['title'])
        """
        endpoint = f"{self._base_endpoint}/{project_id}"
        params = {}
        
        if include:
            params["include"] = ",".join(include)
        
        response = self._http_client.get(endpoint, params if params else None)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def get_many(
        self,
        project_ids: List[int],
        include: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtém múltiplos projetos em paralelo.
        
        Args:
            project_ids: Lista de IDs de projetos.
            include: Relacionamentos para incluir.
            return_pandas: Se True, retorna um DataFrame; se False, retorna lista.
            
        Returns:
            Lista de dados de projetos ou DataFrame.
            
        Example:
            >>> projects = client.projects.get_many([123, 456, 789])
            >>> for p in projects:
            ...     print(p['data']['attributes']['title'])
        """
        def fetch_project(pid):
            return self.get(pid, include, return_pandas=False)
        
        projetos = self._execute_parallel(
            fetch_project,
            project_ids,
            self._threading_config
        )
        
        if return_pandas:
            return to_dataframe(projetos)
        return projetos
    
    def create(
        self,
        name: str,
        project_type_id: int,
        start_date: str,
        target_date: str,
        description: Optional[str] = None,
        state: Optional[ProjectState] = None,
        status: Optional[ProjectStatus] = None,
        background: Optional[str] = None,
        purpose: Optional[str] = None,
        scope: Optional[str] = None,
        budget: Optional[int] = None,
        opinion: Optional[str] = None,
        opinion_description: Optional[str] = None,
        management_response: Optional[str] = None,
        max_sample_size: Optional[int] = None,
        number_of_testing_rounds: Optional[int] = None,
        tag_list: Optional[List[str]] = None,
        planned_start_date: Optional[str] = None,
        planned_end_date: Optional[str] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Cria um novo projeto.
        
        Args:
            name: Nome do projeto (obrigatório, máx 120 caracteres).
            project_type_id: ID do tipo de projeto (obrigatório).
            start_date: Data de início (YYYY-MM-DD, obrigatório).
            target_date: Data alvo de conclusão (YYYY-MM-DD, obrigatório).
            description: Descrição do projeto (máx 524288 caracteres).
            state: Estado do projeto ("active" ou "archive", default: "active").
            status: Status do projeto ("draft", "proposed", "active", "completed").
            background: Background/contexto do projeto.
            purpose: Propósito/objetivos do projeto.
            scope: Escopo do projeto.
            budget: Orçamento em horas (0-2147483647).
            opinion: Opinião/rating final do projeto.
            opinion_description: Descrição da opinião.
            management_response: Resposta da gestão.
            max_sample_size: Tamanho máximo da amostra (0 para Workplan workflow).
            number_of_testing_rounds: Rodadas de teste (0, 1, 2 ou 4 para Internal Control).
            tag_list: Lista de tags.
            planned_start_date: Data de início planejada (YYYY-MM-DD).
            planned_end_date: Data de término planejada (YYYY-MM-DD).
            custom_attributes: Atributos customizados.
            
        Returns:
            Dados do projeto criado.
            
        Example:
            >>> project = client.projects.create(
            ...     name="Auditoria Q1 2024",
            ...     project_type_id=1,
            ...     start_date="2024-01-01",
            ...     target_date="2024-03-31",
            ...     status=ProjectStatus.ACTIVE
            ... )
        """
        # Campos obrigatórios
        attributes = {
            "name": name,
            "start_date": start_date,
            "target_date": target_date
        }
        
        # Campos opcionais
        optional_attrs = {
            "description": description,
            "state": state.value if isinstance(state, ProjectState) else state,
            "status": status.value if isinstance(status, ProjectStatus) else status,
            "background": background,
            "purpose": purpose,
            "scope": scope,
            "budget": budget,
            "opinion": opinion,
            "opinion_description": opinion_description,
            "management_response": management_response,
            "max_sample_size": max_sample_size,
            "number_of_testing_rounds": number_of_testing_rounds,
            "tag_list": tag_list,
            "planned_start_date": planned_start_date,
            "planned_end_date": planned_end_date,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes:
            attributes["custom_attributes"] = custom_attributes
        
        # Relacionamento obrigatório: project_type
        payload = {
            "data": {
                "type": "projects",
                "attributes": attributes,
                "relationships": {
                    "project_type": {
                        "data": {
                            "type": "project_types",
                            "id": str(project_type_id)
                        }
                    }
                }
            }
        }
        
        try:
            return self._http_client.post(self._base_endpoint, payload)
        except Exception as exc:
            from ..exceptions import HighBondValidationError

            if isinstance(exc, HighBondValidationError):
                resp = exc.response or {}
                errors = resp.get("errors", []) if isinstance(resp, dict) else []

                # Build detailed field_errors: field -> {message, pointer}
                field_errors: Dict[str, Dict[str, str]] = {}
                for err in errors:
                    src = err.get("source", {}) if isinstance(err, dict) else {}
                    pointer = str(src.get("pointer", "")) if src else ""
                    # normalize field name from pointer
                    field_name = None
                    if pointer.startswith("/data/attributes/"):
                        field_name = pointer.split("/data/attributes/")[-1]
                    elif pointer.startswith("/data/"):
                        field_name = pointer.split("/data/")[-1]
                    else:
                        field_name = pointer or None

                    if field_name:
                        field_errors[field_name] = {
                            "message": err.get("detail") if isinstance(err, dict) else "erro de validação",
                            "pointer": pointer,
                        }

                # Attach project_types suggestions (always try on validation error)
                try:
                    types_resp = self._http_client.get(f"/orgs/{self._org_id}/project_types")
                    raw_types = types_resp.get("data", []) if isinstance(types_resp, dict) else []
                    types = []
                    for item in raw_types:
                        types.append({
                            "id": item.get("id"),
                            "name": (item.get("attributes") or {}).get("name"),
                        })
                except Exception:
                    types = []

                if isinstance(resp, dict):
                    if types:
                        resp.setdefault("available_project_types", types)
                    if field_errors:
                        resp.setdefault("field_errors", {}).update(field_errors)

                    # Compose a readable message summarizing field errors
                    if field_errors:
                        summary = [f"{f}: {v.get('message')}" for f, v in field_errors.items()]
                        exc.message = " | ".join(summary)

                    # Add explanations per field to help the user fix the payload
                    explanations: Dict[str, str] = {}
                    for f, v in (resp.get("field_errors") or {}).items():
                        msg = v.get("message") if isinstance(v, dict) else str(v)
                        if "project_type" in f or "audit_type" in f:
                            explanations[f] = (
                                f"Campo 'project_type_id': {msg}. O `project_type_id` informado é inválido ou não existe. "
                                "Verifique `available_project_types` para IDs válidos e forneça um id pertencente à sua organização."
                            )
                        else:
                            explanations[f] = f"Campo '{f}': {msg}. Corrija esse campo conforme a mensagem de detalhe."

                    if explanations:
                        resp.setdefault("explanations", {}).update(explanations)

                    # Imprimir explicação amigável automaticamente
                    import json
                    print("\n[HighBondSDK] Erro de validação ao criar projeto:")
                    if resp.get("explanations"):
                        print("Explicações:")
                        for f, e in resp["explanations"].items():
                            print(f"- {e}")
                    if resp.get("available_project_types"):
                        print("\nTipos de projeto válidos:")
                        print(json.dumps(resp["available_project_types"], indent=2, ensure_ascii=False))
                    if resp.get("field_errors"):
                        print("\nDetalhes por campo:")
                        for f, v in resp["field_errors"].items():
                            print(f"- {f}: {v.get('message')} (pointer: {v.get('pointer')})")

                    exc.response = resp

            raise
    
    def update(
        self,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state: Optional[ProjectState] = None,
        status: Optional[ProjectStatus] = None,
        background: Optional[str] = None,
        purpose: Optional[str] = None,
        scope: Optional[str] = None,
        budget: Optional[int] = None,
        opinion: Optional[str] = None,
        opinion_description: Optional[str] = None,
        management_response: Optional[str] = None,
        certification: Optional[bool] = None,
        control_performance: Optional[bool] = None,
        risk_assurance: Optional[bool] = None,
        start_date: Optional[str] = None,
        target_date: Optional[str] = None,
        planned_start_date: Optional[str] = None,
        planned_end_date: Optional[str] = None,
        actual_start_date: Optional[str] = None,
        actual_end_date: Optional[str] = None,
        tag_list: Optional[List[str]] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Atualiza um projeto existente.
        
        Args:
            project_id: ID do projeto a atualizar.
            name: Novo nome.
            description: Nova descrição.
            state: Novo estado ("active", "archive", "delete").
            status: Novo status.
            background: Novo background.
            purpose: Novo propósito.
            scope: Novo escopo.
            budget: Novo orçamento.
            opinion: Nova opinião.
            opinion_description: Nova descrição da opinião.
            management_response: Nova resposta da gestão.
            certification: Habilitar certificações (requer System Admin + Professional).
            control_performance: Habilitar control performance.
            risk_assurance: Habilitar risk assurance.
            start_date: Nova data de início.
            target_date: Nova data alvo.
            planned_start_date: Nova data de início planejada.
            planned_end_date: Nova data de término planejada.
            actual_start_date: Nova data de início real.
            actual_end_date: Nova data de término real.
            tag_list: Nova lista de tags.
            custom_attributes: Novos atributos customizados.
            
        Returns:
            Dados do projeto atualizado.
            
        Example:
            >>> project = client.projects.update(
            ...     project_id=123,
            ...     status=ProjectStatus.COMPLETED
            ... )
        """
        attributes = {}
        
        optional_attrs = {
            "name": name,
            "description": description,
            "state": state.value if isinstance(state, ProjectState) else state,
            "status": status.value if isinstance(status, ProjectStatus) else status,
            "background": background,
            "purpose": purpose,
            "scope": scope,
            "budget": budget,
            "opinion": opinion,
            "opinion_description": opinion_description,
            "management_response": management_response,
            "certification": certification,
            "control_performance": control_performance,
            "risk_assurance": risk_assurance,
            "start_date": start_date,
            "target_date": target_date,
            "planned_start_date": planned_start_date,
            "planned_end_date": planned_end_date,
            "actual_start_date": actual_start_date,
            "actual_end_date": actual_end_date,
            "tag_list": tag_list,
        }
        
        for key, value in optional_attrs.items():
            if value is not None:
                attributes[key] = value
        
        if custom_attributes is not None:
            attributes["custom_attributes"] = custom_attributes
        
        payload = {
            "data": {
                "type": "projects",
                "id": str(project_id),
                "attributes": attributes
            }
        }
        
        endpoint = f"{self._base_endpoint}/{project_id}"
        return self._http_client.patch(endpoint, payload)
    
    def delete(self, project_id: int) -> Dict[str, Any]:
        """Exclui um projeto.
        
        Args:
            project_id: ID do projeto a excluir.
            
        Returns:
            Resposta da API (geralmente vazia em sucesso).
            
        Warning:
            Esta ação é irreversível e remove todos os dados associados.
            
        Example:
            >>> client.projects.delete(123)
        """
        endpoint = f"{self._base_endpoint}/{project_id}"
        return self._http_client.delete(endpoint)
    
    def delete_many(self, project_ids: List[int]) -> List[Dict[str, Any]]:
        """Exclui múltiplos projetos em paralelo.
        
        Args:
            project_ids: Lista de IDs de projetos a excluir.
            
        Returns:
            Lista de respostas da API.
            
        Warning:
            Esta ação é irreversível!
        """
        return self._execute_parallel(
            self.delete,
            project_ids,
            self._threading_config
        )
