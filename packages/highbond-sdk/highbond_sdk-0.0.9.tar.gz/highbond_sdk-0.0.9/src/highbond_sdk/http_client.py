"""
Cliente HTTP para o HighBond SDK.
"""
import time
import base64
from typing import Optional, Dict, Any, Generator, List
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from .config import APIConfig, PaginationConfig, ThreadingConfig
from .exceptions import (
    HighBondAPIError,
    HighBondAuthError,
    HighBondForbiddenError,
    HighBondNotFoundError,
    HighBondValidationError,
    HighBondRateLimitError,
    HighBondConnectionError,
)


class HighBondHTTPClient:
    """Cliente HTTP de baixo nível para a API HighBond.
    
    Gerencia requisições HTTP, retry, tratamento de erros e sessão.
    """
    
    def __init__(self, config: APIConfig):
        """
        Args:
            config: Configuração da API.
        """
        self.config = config
        self._session = requests.Session()
        self._session.headers.update(config.headers)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Processa a resposta e lança exceções apropriadas.
        
        Args:
            response: Resposta da requisição.
            
        Returns:
            Dados JSON da resposta.
            
        Raises:
            HighBondAuthError: Para erros 401.
            HighBondForbiddenError: Para erros 403.
            HighBondNotFoundError: Para erros 404.
            HighBondValidationError: Para erros 422.
            HighBondRateLimitError: Para erros 429.
            HighBondAPIError: Para outros erros.
        """
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {}
        
        if response.status_code >= 400:
            error_message = self._extract_error_message(data, response)
            
            error_classes = {
                401: HighBondAuthError,
                403: HighBondForbiddenError,
                404: HighBondNotFoundError,
                422: HighBondValidationError,
                429: HighBondRateLimitError,
            }
            
            error_class = error_classes.get(response.status_code, HighBondAPIError)
            raise error_class(error_message, response.status_code, data)
        
        return data
    
    def _extract_error_message(
        self, data: Dict[str, Any], response: requests.Response
    ) -> str:
        """Extrai mensagem de erro da resposta.
        
        Args:
            data: Dados JSON da resposta.
            response: Resposta da requisição.
            
        Returns:
            Mensagem de erro formatada.
        """
        if "errors" in data and data["errors"]:
            errors = data["errors"]
            if isinstance(errors, list):
                messages = []
                for error in errors:
                    title = error.get("title", "")
                    detail = error.get("detail", "")
                    if title and detail:
                        messages.append(f"{title}: {detail}")
                    else:
                        messages.append(title or detail or str(error))
                return " | ".join(messages)
        
        return f"HTTP Error {response.status_code}: {response.reason}"
    
    def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> requests.Response:
        """Executa requisição com retry automático.
        
        Args:
            method: Método HTTP (GET, POST, etc).
            url: URL completa da requisição.
            **kwargs: Argumentos adicionais para requests.
            
        Returns:
            Resposta da requisição.
            
        Raises:
            HighBondConnectionError: Se todas as tentativas falharem.
        """
        kwargs.setdefault("timeout", self.config.timeout)
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._session.request(method, url, **kwargs)
                
                # Retry apenas em erros 5xx e 429
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    time.sleep(retry_after)
                    continue
                    
                if response.status_code >= 500:
                    delay = self.config.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                delay = self.config.retry_delay * (2 ** attempt)
                time.sleep(delay)
        
        raise HighBondConnectionError(
            f"Falha ao conectar após {self.config.max_retries} tentativas: {last_exception}"
        )
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa requisição GET.
        
        Args:
            endpoint: Endpoint da API (sem base URL).
            params: Parâmetros de query string.
            
        Returns:
            Dados JSON da resposta.
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._request_with_retry("GET", url, params=params)
        return self._handle_response(response)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa requisição POST.
        
        Args:
            endpoint: Endpoint da API (sem base URL).
            data: Dados JSON para enviar.
            
        Returns:
            Dados JSON da resposta.
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._request_with_retry("POST", url, json=data)
        return self._handle_response(response)
    
    def patch(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa requisição PATCH.
        
        Args:
            endpoint: Endpoint da API (sem base URL).
            data: Dados JSON para enviar.
            
        Returns:
            Dados JSON da resposta.
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._request_with_retry("PATCH", url, json=data)
        return self._handle_response(response)
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Executa requisição PUT.
        
        Args:
            endpoint: Endpoint da API (sem base URL).
            data: Dados JSON para enviar.
            
        Returns:
            Dados JSON da resposta.
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._request_with_retry("PUT", url, json=data)
        return self._handle_response(response)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        """Executa requisição DELETE.
        
        Args:
            endpoint: Endpoint da API (sem base URL).
            
        Returns:
            Dados JSON da resposta (pode ser vazio).
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._request_with_retry("DELETE", url)
        return self._handle_response(response)
    
    def close(self):
        """Fecha a sessão HTTP."""
        self._session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PaginationMixin:
    """Mixin para adicionar funcionalidade de paginação."""
    
    def _encode_page_number(self, page: int) -> str:
        """Codifica número da página em Base64 para a API.
        
        Args:
            page: Número da página (1-based).
            
        Returns:
            Número da página codificado em Base64.
        """
        return base64.b64encode(str(page).encode()).decode()
    
    def _paginate(
        self,
        endpoint: str,
        pagination_config: PaginationConfig,
        params: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Itera sobre todas as páginas de um endpoint.
        
        Args:
            endpoint: Endpoint da API.
            pagination_config: Configuração de paginação.
            params: Parâmetros adicionais de query string.
            
        Yields:
            Cada item da resposta paginada.
        """
        http_client: HighBondHTTPClient = self._http_client
        params = params or {}
        params["page[size]"] = pagination_config.page_size
        
        page = 1
        pages_fetched = 0
        
        while True:
            params["page[number]"] = self._encode_page_number(page)
            response = http_client.get(endpoint, params)
            
            data = response.get("data", [])
            if isinstance(data, list):
                for item in data:
                    yield item
            else:
                yield data
                return
            
            pages_fetched += 1
            
            # Verifica limite de páginas
            if pagination_config.max_pages and pages_fetched >= pagination_config.max_pages:
                return
            
            # Verifica se há próxima página
            links = response.get("links", {})
            if not links.get("next"):
                return
            
            page += 1


class ThreadingMixin:
    """Mixin para adicionar funcionalidade de threading."""
    
    def _execute_parallel(
        self,
        func,
        items: List[Any],
        threading_config: ThreadingConfig
    ) -> List[Any]:
        """Executa função em paralelo para múltiplos itens.
        
        Args:
            func: Função a ser executada para cada item.
            items: Lista de itens para processar.
            threading_config: Configuração de threading.
            
        Returns:
            Lista de resultados.
        """
        if not threading_config.enabled or len(items) <= 1:
            return [func(item) for item in items]
        
        results = []
        with ThreadPoolExecutor(max_workers=threading_config.max_workers) as executor:
            futures = {executor.submit(func, item): item for item in items}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "item": futures[future]})
        
        return results
