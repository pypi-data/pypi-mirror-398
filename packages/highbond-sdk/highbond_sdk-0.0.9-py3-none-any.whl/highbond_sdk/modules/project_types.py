"""
Módulo de Tipos de Projeto para o HighBond SDK.
"""
from typing import Optional, Dict, Any, List, Generator

from ..http_client import HighBondHTTPClient, PaginationMixin, ThreadingMixin
from ..config import PaginationConfig, ThreadingConfig, APIConfig
from ..utils import to_dataframe


class ProjectTypesModule(PaginationMixin, ThreadingMixin):
    """Módulo para gerenciamento de Tipos de Projeto no HighBond.
    
    Tipos de projeto definem categorias e configurações padrão para projetos.
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
        """Endpoint base para tipos de projeto."""
        return f"/orgs/{self._org_id}/project_types"
    
    def list_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None,
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista todos os tipos de projeto com paginação automática.
        
        Args:
            filters: Filtros adicionais.
            max_pages: Máximo de páginas a buscar (None = todas).
            return_pandas: Se True, retorna um DataFrame; se False, retorna uma lista.
            
        Returns:
            Lista de tipos de projeto ou DataFrame.
            
        Example:
            >>> for pt in client.project_types.list_all():
            ...     print(pt['attributes']['name'])
        """
        pagination = PaginationConfig(
            page_size=self._pagination_config.page_size,
            max_pages=max_pages or self._pagination_config.max_pages
        )
        
        params = {}
        if filters:
            for key, value in filters.items():
                params[f"filter[{key}]"] = value
        
        project_types = list(self._paginate(self._base_endpoint, pagination, params))
        
        if return_pandas:
            return to_dataframe(project_types)
        return project_types
    
    def get(self, project_type_id: int, return_pandas: bool = False) -> Dict[str, Any]:
        """Obtém um tipo de projeto específico por ID.
        
        Args:
            project_type_id: ID do tipo de projeto.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do tipo de projeto ou DataFrame.
            
        Example:
            >>> pt = client.project_types.get(123)
            >>> print(pt['data']['attributes']['name'])
        """
        endpoint = f"{self._base_endpoint}/{project_type_id}"
        response = self._http_client.get(endpoint, None)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def get_custom_attributes(
        self,
        project_type_id: int,
        fields: Optional[List[str]] = None,
        page_size: Optional[int] = None,
        page_number: Optional[str] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Obtém os atributos customizados de um tipo de projeto.
        
        Busca os custom_attributes via endpoint dedicado da API:
        GET /orgs/{org_id}/project_types/{project_type_id}/custom_attributes
        
        Args:
            project_type_id: ID do tipo de projeto.
            fields: Lista de campos específicos a retornar dos atributos customizados.
                   Exemplo: ['term', 'options', 'customizable_type', 'field_type', 'weight', 'required', 'default_values']
                   Se None, retorna todos os campos.
            page_size: Número de itens retornados por página (padrão: 50, máximo: 100).
            page_number: Número da página em formato Base64-encoded (para paginação).
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Resposta da API com os custom_attributes ou DataFrame.
            
        Example:
            >>> # Obter todos os custom_attributes
            >>> custom_attrs = client.project_types.get_custom_attributes(123)
            >>> print(custom_attrs)
            
            >>> # Obter apenas campos específicos dos custom_attributes
            >>> custom_attrs = client.project_types.get_custom_attributes(
            ...     project_type_id=123,
            ...     fields=['term', 'options', 'field_type', 'required']
            ... )
            
            >>> # Com paginação
            >>> custom_attrs = client.project_types.get_custom_attributes(
            ...     project_type_id=123,
            ...     fields=['term', 'options'],
            ...     page_size=25,
            ...     page_number="Mg=="
            ... )
        """
        # Endpoint correto para custom_attributes
        endpoint = f"{self._base_endpoint}/{project_type_id}/custom_attributes"
        params = {}
        
        # Adicionar campos customizados se especificados
        if fields and isinstance(fields, list):
            params['fields[custom_attributes]'] = ','.join(fields)
        
        # Adicionar paginação se especificada
        if page_size is not None:
            params['page[size]'] = str(page_size)
        
        if page_number is not None:
            params['page[number]'] = page_number
        
        # Fazer GET no endpoint de custom_attributes
        response = self._http_client.get(endpoint, params if params else None)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def get_many(
        self,
        project_type_ids: List[int],
        return_pandas: bool = False
    ) -> List[Dict[str, Any]]:
        """Obtém múltiplos tipos de projeto em paralelo.
        
        Args:
            project_type_ids: Lista de IDs de tipos de projeto.
            return_pandas: Se True, retorna um DataFrame; se False, retorna lista.
            
        Returns:
            Lista de dados de tipos de projeto ou DataFrame.
            
        Example:
            >>> types = client.project_types.get_many([1, 2, 3])
            >>> for pt in types:
            ...     print(pt['data']['attributes']['name'])
        """
        def fetch_type(pid):
            return self.get(pid, return_pandas=False)
        
        project_types = self._execute_parallel(
            fetch_type,
            project_type_ids,
            self._threading_config
        )
        
        if return_pandas:
            return to_dataframe(project_types)
        return project_types
    
    def create_custom_attribute(
        self,
        project_type_id: int,
        customizable_type: str,
        term: str,
        field_type: str,
        options: Optional[List[str]] = None,
        weight: Optional[int] = None,
        required: bool = False,
        default_values: Optional[List[str]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Cria um novo atributo customizado em um tipo de projeto.
        
        Este método permite criar um novo atributo customizado via API REST.
        Os atributos customizados são campos personalizáveis associados a objetos
        suportados em um tipo de projeto.
        
        Args:
            project_type_id: ID do tipo de projeto.
            customizable_type: Tipo do atributo customizado. Valores válidos:
                - CustomControlAttribute
                - CustomControlTestAttribute
                - CustomControlTestPlanAttribute
                - CustomFindingActionAttribute
                - CustomFindingAttribute
                - CustomObjectiveAttribute
                - CustomPlanningAttribute
                - CustomProjectPlanningAttribute
                - CustomResultsAttribute
                - CustomRiskAttribute
                - CustomRiskFactor
                - CustomWalkthroughAttribute
            term: Nome exibido do atributo customizado (máx 255 caracteres).
            field_type: Tipo do campo. Valores válidos:
                - "select": Seleção única
                - "multiselect": Múltiplas seleções
                - "date": Data
                - "text": Texto simples
                - "paragraph": Parágrafo (texto longo)
            options: Lista de opções (obrigatório se field_type é "select" ou "multiselect").
            weight: Peso do atributo (1-1000, obrigatório se customizable_type é CustomRiskFactor).
            required: Se o atributo é obrigatório (padrão: False).
            default_values: Valores padrão para o atributo.
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do atributo customizado criado ou DataFrame.
            
        Raises:
            HighBondValidationError: Se os dados forem inválidos.
            HighBondNotFoundError: Se o tipo de projeto não for encontrado.
            HighBondAuthError: Se houver erro de autenticação.
            ValueError: Se os parâmetros obrigatórios não forem fornecidos.
            
        Limits:
            - Máximo de 5 atributos customizados por tipo, exceto CustomRiskFactor (máximo 8).
            
        Example:
            >>> # Criar um atributo de seleção
            >>> attr = client.project_types.create_custom_attribute(
            ...     project_type_id=123,
            ...     customizable_type='CustomObjectiveAttribute',
            ...     term='Nível de Prioridade',
            ...     field_type='select',
            ...     options=['Baixa', 'Média', 'Alta'],
            ...     required=True,
            ...     default_values=['Média']
            ... )
            
            >>> # Criar um atributo CustomRiskFactor
            >>> attr = client.project_types.create_custom_attribute(
            ...     project_type_id=123,
            ...     customizable_type='CustomRiskFactor',
            ...     term='Fator de Risco',
            ...     field_type='select',
            ...     options=['Baixo', 'Médio', 'Alto'],
            ...     weight=50,
            ...     required=True
            ... )
        """
        # Validações
        if not term or not isinstance(term, str):
            raise ValueError("'term' é obrigatório e deve ser uma string.")
        
        if not customizable_type or not isinstance(customizable_type, str):
            raise ValueError("'customizable_type' é obrigatório e deve ser uma string.")
        
        if not field_type or not isinstance(field_type, str):
            raise ValueError("'field_type' é obrigatório e deve ser uma string.")
        
        if field_type in ['select', 'multiselect'] and not options:
            raise ValueError(
                f"'options' é obrigatório quando field_type é '{field_type}'."
            )
        
        if customizable_type == 'CustomRiskFactor' and weight is None:
            raise ValueError(
                "'weight' é obrigatório quando customizable_type é 'CustomRiskFactor'."
            )
        
        # Construir endpoint
        endpoint = f"{self._base_endpoint}/{project_type_id}/custom_attributes"
        
        # Construir payload
        payload = {
            "data": {
                "type": "custom_attributes",
                "attributes": {
                    "customizable_type": customizable_type,
                    "term": term,
                    "field_type": field_type,
                    "required": required,
                }
            }
        }
        
        # Adicionar campos opcionais se fornecidos
        if options is not None:
            payload["data"]["attributes"]["options"] = options
        
        if weight is not None:
            payload["data"]["attributes"]["weight"] = weight
        
        if default_values is not None:
            payload["data"]["attributes"]["default_values"] = default_values
        
        # Fazer requisição POST
        response = self._http_client.post(endpoint, payload)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def copy_project_type(
        self,
        source_project_type_id: int,
        name: str,
        description: Optional[str] = None,
        enable_creating_projects: bool = True,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Copia um tipo de projeto para a mesma organização.
        
        Cria um novo tipo de projeto baseado em um existente, herdando todas as
        suas configurações de termos e atributos customizáveis.
        
        Args:
            source_project_type_id: ID do tipo de projeto a ser copiado.
            name: Nome do novo tipo de projeto (máx 255 caracteres).
            description: Descrição do novo tipo de projeto (opcional, máx 255 caracteres).
            enable_creating_projects: Se True, permite criar projetos com este tipo;
                                     se False, mantém em modo rascunho (padrão: True).
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do novo tipo de projeto criado ou DataFrame.
            
        Raises:
            HighBondValidationError: Se o nome exceder 255 caracteres ou dados inválidos.
            HighBondNotFoundError: Se o tipo de projeto de origem não for encontrado.
            
        Example:
            >>> new_type = client.project_types.copy_project_type(
            ...     source_project_type_id=123,
            ...     name="My Custom Type",
            ...     description="Copy from original type"
            ... )
            >>> print(new_type['data']['id'])
        """
        payload = {
            "data": {
                "type": "project_types",
                "attributes": {
                    "name": name,
                    "enable_creating_projects": enable_creating_projects,
                    'description': description
                },
                "source_project_type_id": str(source_project_type_id),
            }
        }
        
        if description is not None:
            payload["data"]["attributes"]["description"] = description
        
        response = self._http_client.post(self._base_endpoint, payload)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    def copy_to_organization(
        self,
        source_project_type_id: int,
        target_org_id: int,
        name: str,
        description: Optional[str] = None,
        enable_creating_projects: bool = True,
        target_region: Optional[str] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Copia um tipo de projeto para outra organização com sincronização completa.
        
        Realiza uma cópia completa de um tipo de projeto:
        1. Coleta as informações do tipo de projeto original (incluindo workflow e atributos customizados)
        2. Cria um novo tipo de projeto na organização destino
        3. Sincroniza todos os atributos customizados (termos, toggles, opções) do tipo original
        
        Este processo garante que o novo tipo na org destino tenha exatamente as mesmas
        configurações do tipo original, incluindo todos os atributos customizados.
        
        Args:
            source_project_type_id: ID do tipo de projeto a ser copiado (da org atual).
            target_org_id: ID da organização destino.
            name: Nome do novo tipo de projeto na org destino (máx 255 caracteres).
            description: Descrição do novo tipo de projeto (opcional, máx 255 caracteres).
            enable_creating_projects: Se True, permite criar projetos com este tipo;
                                     se False, mantém em modo rascunho (padrão: True).
            target_region: Região da organização destino ("us", "eu", "au", "ca" ou "sa"). 
                          Se não fornecido, usa a região atual do cliente (opcional).
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do novo tipo de projeto criado na org destino ou DataFrame.
            
        Raises:
            HighBondValidationError: Se o nome exceder 255 caracteres ou dados inválidos.
            HighBondNotFoundError: Se o tipo de projeto de origem ou org destino não forem encontrados.
            HighBondForbiddenError: Se sem permissão para acessar a org destino.
            
        Warning:
            Este método faz múltiplas chamadas à API:
            1. GET do tipo original
            2. GET dos atributos customizados
            3. POST para criar novo tipo
            4. PATCH para sincronizar atributos customizados (se houver)
            
        Example:
            >>> new_type = client.project_types.copy_to_organization(
            ...     source_project_type_id=123,
            ...     target_org_id=456,
            ...     name="Copied Type in Other Org",
            ...     description="Copied from org 1",
            ...     target_region="eu"
            ... )
            >>> print(new_type['data']['id'])
        """
        # Passo 1: Coletar informações do tipo original
        original_type = self.get(source_project_type_id, return_pandas=False)
        original_attributes = original_type.get('data', {}).get('attributes', {})
        original_workflow = original_attributes.get('workflow', 'control')
        
        # Lista de atributos padrão que não são customizados
        standard_attributes = {
            'id', 'name', 'description', 'workflow', 'enable_creating_projects',
            'created_at', 'updated_at', 'type', 'created_by', 'updated_by'
        }
        
        # Extrair atributos customizados
        custom_attributes = {
            key: value for key, value in original_attributes.items()
            if key not in standard_attributes
        }
        
        print(f"ℹ Atributos customizados encontrados: {list(custom_attributes.keys())}")
        
        # Passo 2: Criar novo tipo de projeto na org destino com POST
        # Usar a região fornecida ou usar a região atual do cliente
        target_endpoint = f"/orgs/{target_org_id}/project_types"
        
        if target_region:
            # Criar um novo cliente HTTP com a região destino para fazer as chamadas
            target_api_config = APIConfig(
                token=self._http_client.config.token,
                org_id=target_org_id,
                region=target_region,
                timeout=self._http_client.config.timeout,
                max_retries=self._http_client.config.max_retries,
                retry_delay=self._http_client.config.retry_delay
            )
            target_http_client = HighBondHTTPClient(target_api_config)
        else:
            target_http_client = self._http_client
        
        # Truncar valores de strings para máximo de 60 caracteres (limite da API)
        def truncate_values(obj, max_length=60):
            """Trunca valores de strings recursivamente."""
            if isinstance(obj, dict):
                return {k: truncate_values(v, max_length) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [truncate_values(item, max_length) for item in obj]
            elif isinstance(obj, str) and len(obj) > max_length:
                return obj[:max_length]
            return obj
        
        # Preparar atributos customizados com truncagem
        truncated_custom_attrs = {
            key: truncate_values(value)
            for key, value in custom_attributes.items()
        }
        
        # Construir payload de criação SEM atributos customizados
        # (Atributos customizados só podem ser definidos APÓS a criação)
        create_payload = {
            "data": {
                "type": "project_types",
                "attributes": {
                    "name": name,
                    "workflow": original_workflow,
                    "enable_creating_projects": enable_creating_projects,
                },
            }
        }
        
        if description is not None:
            create_payload["data"]["attributes"]["description"] = description
        
        # Criar o novo tipo usando o cliente da região destino
        new_type = target_http_client.post(target_endpoint, create_payload)
        new_type_id = new_type.get('data', {}).get('id')
        
        if not new_type_id:
            return new_type
        
        print(f"✓ Novo tipo criado com ID: {new_type_id}")
        
        # Passo 3: Copiar atributos genéricos (project_terms, project_toggles, etc.) via PATCH
        if truncated_custom_attrs:
            try:
                print(f"📤 Atualizando {len(truncated_custom_attrs)} atributo(s) genérico(s)...")
                # Atualizar o tipo de projeto com os atributos genéricos via PATCH
                update_endpoint = f"/orgs/{target_org_id}/project_types/{new_type_id}"
                update_payload = {
                    "data": {
                        "id": new_type_id,
                        "type": "project_types",
                        "attributes": truncated_custom_attrs
                    }
                }
                new_type = target_http_client.patch(update_endpoint, update_payload)
                print(f"✓ Atributos genéricos atualizados com sucesso: {list(truncated_custom_attrs.keys())}")
            except Exception as e:
                print(f"⚠ Erro ao atualizar atributos genéricos: {str(e)}")
        
        # Passo 4: Copiar os custom_attributes via endpoint dedicado POST /custom_attributes
        try:
            print(f"📤 Buscando custom_attributes do tipo original...")
            # Buscar custom_attributes do tipo original
            original_custom_attrs = self.get_custom_attributes(
                project_type_id=source_project_type_id,
                return_pandas=False
            )
            
            if original_custom_attrs and isinstance(original_custom_attrs, dict):
                custom_attrs_list = original_custom_attrs.get('data', [])
                if custom_attrs_list:
                    print(f"ℹ Encontrados {len(custom_attrs_list)} custom_attribute(s)")
                    
                    # Criar uma instância do módulo para a organização destino
                    target_project_types_module = ProjectTypesModule(
                        http_client=target_http_client,
                        org_id=target_org_id,
                        pagination_config=self._pagination_config,
                        threading_config=self._threading_config
                    )
                    
                    # Criar cada custom_attribute via endpoint dedicado
                    for attr in custom_attrs_list:
                        try:
                            attr_data = attr.get('attributes', {})
                            customizable_type = attr_data.get('customizable_type')
                            term = attr_data.get('term')
                            field_type = attr_data.get('field_type')
                            options = attr_data.get('options')
                            weight = attr_data.get('weight')
                            required = attr_data.get('required', False)
                            default_values = attr_data.get('default_values')
                            
                            # Se required e não tem default_values, definir um fallback por tipo de campo
                            if required and not default_values:
                                if field_type in ['select', 'multiselect'] and options:
                                    default_values = [options[0]]  # Primeira opção disponível
                                elif field_type == 'text':
                                    default_values = ['N/A']  # Texto padrão
                                elif field_type == 'paragraph':
                                    default_values = ['N/A']  # Parágrafo padrão
                                elif field_type == 'date':
                                    default_values = ['2000-01-01']  # Data padrão
                            
                            print(f"  📝 Criando custom_attribute: {term} ({customizable_type})...")
                            
                            # Usar create_custom_attribute para criar o novo atributo
                            created_attr = target_project_types_module.create_custom_attribute(
                                project_type_id=new_type_id,
                                customizable_type=customizable_type,
                                term=term,
                                field_type=field_type,
                                options=options,
                                weight=weight,
                                required=required,
                                default_values=default_values
                            )
                            
                            created_id = created_attr.get('data', {}).get('id')
                            print(f"    ✓ Custom_attribute criado com ID: {created_id}")
                            
                        except Exception as e:
                            print(f"    ⚠ Erro ao criar custom_attribute '{term}': {str(e)}")
                    
                    # Fazer um GET final para obter o tipo de projeto completo com todos os atributos
                    new_type = target_project_types_module.get(new_type_id)
                    print(f"✓ Todos os custom_attributes copiados com sucesso")
                else:
                    print("ℹ Nenhum custom_attribute encontrado no tipo original")
        except Exception as e:
            print(f"⚠ Erro ao copiar custom_attributes: {str(e)}")
        
        if return_pandas:
            return to_dataframe(new_type)
        return new_type
    
    def update(
        self,
        project_type_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enable_creating_projects: Optional[bool] = None,
        attributes: Optional[Dict[str, Any]] = None,
        project_type_data: Optional[Dict[str, Any]] = None,
        return_pandas: bool = False
    ) -> Dict[str, Any]:
        """Atualiza um tipo de projeto existente.
        
        Permite atualizar configurações de um tipo de projeto existente, incluindo
        nome, descrição, habilitação de criação de projetos e atributos customizados
        como termos, toggles e opções.
        
        Args:
            project_type_id: ID do tipo de projeto a atualizar.
            name: Novo nome do tipo de projeto (opcional, máx 255 caracteres).
            description: Nova descrição do tipo de projeto (opcional, máx 255 caracteres).
            enable_creating_projects: Se True, permite criar projetos com este tipo;
                                     se False, desabilita (opcional).
            attributes: Dicionário com atributos customizados adicionais a atualizar
                       (como termos, toggles, etc.). Os atributos especificados serão
                       mesclados com os atributos obrigatórios (opcional).
            project_type_data: Dicionário completo retornado pela API (ex: resultado de get()).
                              Se fornecido, extrai automaticamente os attributes. Parâmetros
                              específicos (name, description, etc) sobrescrevem os valores
                              deste dicionário (opcional).
            return_pandas: Se True, retorna um DataFrame; se False, retorna resposta da API.
            
        Returns:
            Dados do tipo de projeto atualizado ou DataFrame.
            
        Raises:
            HighBondValidationError: Se os dados forem inválidos (ex: nome > 255 caracteres).
            HighBondNotFoundError: Se o tipo de projeto não for encontrado.
            HighBondAuthError: Se houver erro de autenticação.
            
        Warning:
            Ao atualizar atributos customizados (termos, toggles, etc.), certifique-se
            de fornecer valores válidos. Valores inválidos podem resultar em erro 422.
            
        Example:
            >>> # Atualizar nome e descrição
            >>> updated = client.project_types.update(
            ...     project_type_id=123,
            ...     name="Novo Nome",
            ...     description="Nova descrição"
            ... )
            
            >>> # Passar arquivo completo retornado pela API
            >>> tipo = client.project_types.get(123)
            >>> updated = client.project_types.update(
            ...     project_type_id=123,
            ...     project_type_data=tipo
            ... )
            
            >>> # Passar arquivo e sobrescrever alguns campos
            >>> tipo = client.project_types.get(123)
            >>> updated = client.project_types.update(
            ...     project_type_id=123,
            ...     project_type_data=tipo,
            ...     name="Novo Nome"  # Sobrescreve o nome do arquivo
            ... )
        """
        endpoint = f"{self._base_endpoint}/{project_type_id}"
        
        # Construir objeto de atributos
        payload_attributes = {}
        
        # Se um arquivo completo foi fornecido, extrair os attributes
        if project_type_data is not None:
            if isinstance(project_type_data, dict) and "data" in project_type_data:
                # Formato com 'data' wrapper
                extracted_attrs = project_type_data.get("data", {}).get("attributes", {})
            elif isinstance(project_type_data, dict) and "attributes" in project_type_data:
                # Formato direto com attributes
                extracted_attrs = project_type_data.get("attributes", {})
            else:
                extracted_attrs = project_type_data
            
            # Adicionar os atributos extraídos
            payload_attributes.update(extracted_attrs)
        
        # Adicionar parâmetros principais se fornecidos (sobrescrevem valores do arquivo)
        if name is not None:
            payload_attributes["name"] = name
        
        if description is not None:
            payload_attributes["description"] = description
        
        if enable_creating_projects is not None:
            payload_attributes["enable_creating_projects"] = enable_creating_projects
        
        # Mesclar com atributos customizados
        if attributes is not None:
            payload_attributes.update(attributes)
        
        # Validar que pelo menos um atributo foi fornecido
        if not payload_attributes:
            raise ValueError(
                "Nenhum atributo foi fornecido para atualizar. "
                "Forneça pelo menos um de: name, description, enable_creating_projects, attributes ou project_type_data."
            )
        
        payload = {
            "data": {
                'id': str(project_type_id),
                "type": "project_types",
                "attributes": payload_attributes,
            }
        }
        
        response = self._http_client.patch(endpoint, payload)
        
        if return_pandas:
            return to_dataframe(response)
        return response
    
    
    def delete(self, project_type_id: int) -> Dict[str, Any]:
        """Exclui um tipo de projeto.
        
        Args:
            project_type_id: ID do tipo de projeto a excluir.
            
        Returns:
            Resposta da API (geralmente vazia em sucesso).
            
        Warning:
            Esta ação é irreversível e pode afetar projetos existentes.
            
        Example:
            >>> client.project_types.delete(123)
        """
        endpoint = f"{self._base_endpoint}/{project_type_id}"
        return self._http_client.delete(endpoint)
    
