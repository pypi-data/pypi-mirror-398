"""
InvoiceAI SDK Client
"""

from typing import Optional, Dict, Any
import requests

from .exceptions import InvoiceAIError, AuthenticationError, NotFoundError, TimeoutError
from .types import (
    Invoice,
    Client,
    Product,
    Quote,
    Profile,
    Stats,
    PaginatedInvoices,
    PaginatedClients,
    PaginatedProducts,
    PaginatedQuotes,
)

DEFAULT_BASE_URL = "https://urcvstsuqtlqhjgqudtn.supabase.co/functions/v1/api"
DEFAULT_TIMEOUT = 30


class InvoiceAI:
    """
    InvoiceAI API Client
    
    Usage:
        client = InvoiceAI(api_key="your_api_key")
        invoices = client.invoices.list()
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token is required")
        
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Initialize resources
        self.invoices = InvoicesResource(self)
        self.clients = ClientsResource(self)
        self.products = ProductsResource(self)
        self.quotes = QuotesResource(self)
        self.profile = ProfileResource(self)
        self.stats = StatsResource(self)
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["x-api-key"] = self.api_key
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        return headers
    
    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=self.timeout,
            )
            
            response_data = response.json()
            
            if not response.ok:
                error_message = response_data.get("error", "Request failed")
                error_code = response_data.get("code", "UNKNOWN_ERROR")
                
                if response.status_code == 401:
                    raise AuthenticationError(error_message)
                elif response.status_code == 404:
                    raise NotFoundError(error_message)
                else:
                    raise InvoiceAIError(error_message, response.status_code, error_code)
            
            return response_data
            
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timeout")
        except requests.exceptions.RequestException as e:
            raise InvoiceAIError(str(e), 500, "REQUEST_ERROR")


class InvoicesResource:
    """Invoices API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> PaginatedInvoices:
        """List all invoices."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._client.request("GET", "/invoices", params=params)
    
    def get(self, invoice_id: str) -> Invoice:
        """Get a single invoice by ID."""
        return self._client.request("GET", f"/invoices/{invoice_id}")
    
    def create(self, **data) -> Invoice:
        """Create a new invoice."""
        return self._client.request("POST", "/invoices", data=data)
    
    def update(self, invoice_id: str, **data) -> Invoice:
        """Update an existing invoice."""
        return self._client.request("PUT", f"/invoices/{invoice_id}", data=data)
    
    def delete(self, invoice_id: str) -> Dict[str, str]:
        """Delete an invoice."""
        return self._client.request("DELETE", f"/invoices/{invoice_id}")


class ClientsResource:
    """Clients API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def list(self, limit: int = 50, offset: int = 0) -> PaginatedClients:
        """List all clients."""
        params = {"limit": limit, "offset": offset}
        return self._client.request("GET", "/clients", params=params)
    
    def get(self, client_id: str) -> Client:
        """Get a single client by ID."""
        return self._client.request("GET", f"/clients/{client_id}")
    
    def create(self, **data) -> Client:
        """Create a new client."""
        return self._client.request("POST", "/clients", data=data)
    
    def update(self, client_id: str, **data) -> Client:
        """Update an existing client."""
        return self._client.request("PUT", f"/clients/{client_id}", data=data)
    
    def delete(self, client_id: str) -> Dict[str, str]:
        """Delete a client."""
        return self._client.request("DELETE", f"/clients/{client_id}")


class ProductsResource:
    """Products API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def list(self, limit: int = 50, offset: int = 0) -> PaginatedProducts:
        """List all products."""
        params = {"limit": limit, "offset": offset}
        return self._client.request("GET", "/products", params=params)
    
    def get(self, product_id: str) -> Product:
        """Get a single product by ID."""
        return self._client.request("GET", f"/products/{product_id}")
    
    def create(self, **data) -> Product:
        """Create a new product."""
        return self._client.request("POST", "/products", data=data)
    
    def update(self, product_id: str, **data) -> Product:
        """Update an existing product."""
        return self._client.request("PUT", f"/products/{product_id}", data=data)
    
    def delete(self, product_id: str) -> Dict[str, str]:
        """Delete a product."""
        return self._client.request("DELETE", f"/products/{product_id}")


class QuotesResource:
    """Quotes API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> PaginatedQuotes:
        """List all quotes."""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._client.request("GET", "/quotes", params=params)
    
    def get(self, quote_id: str) -> Quote:
        """Get a single quote by ID."""
        return self._client.request("GET", f"/quotes/{quote_id}")
    
    def create(self, **data) -> Quote:
        """Create a new quote."""
        return self._client.request("POST", "/quotes", data=data)
    
    def update(self, quote_id: str, **data) -> Quote:
        """Update an existing quote."""
        return self._client.request("PUT", f"/quotes/{quote_id}", data=data)
    
    def delete(self, quote_id: str) -> Dict[str, str]:
        """Delete a quote."""
        return self._client.request("DELETE", f"/quotes/{quote_id}")


class ProfileResource:
    """Profile API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def get(self) -> Profile:
        """Get the business profile."""
        return self._client.request("GET", "/profile")
    
    def update(self, **data) -> Profile:
        """Update the business profile."""
        return self._client.request("PUT", "/profile", data=data)


class StatsResource:
    """Stats API resource."""
    
    def __init__(self, client: InvoiceAI):
        self._client = client
    
    def get(self) -> Stats:
        """Get dashboard statistics."""
        return self._client.request("GET", "/stats")


# Async client (placeholder - requires aiohttp)
class AsyncInvoiceAI(InvoiceAI):
    """
    Async InvoiceAI API Client
    
    Usage:
        client = AsyncInvoiceAI(api_key="your_api_key")
        invoices = await client.invoices.list()
    """
    
    async def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async HTTP request to the API."""
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp is required for async support. Install with: pip install aiohttp")
        
        url = f"{self.base_url}{path}"
        headers = self._get_headers()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as response:
                    response_data = await response.json()
                    
                    if not response.ok:
                        error_message = response_data.get("error", "Request failed")
                        error_code = response_data.get("code", "UNKNOWN_ERROR")
                        
                        if response.status == 401:
                            raise AuthenticationError(error_message)
                        elif response.status == 404:
                            raise NotFoundError(error_message)
                        else:
                            raise InvoiceAIError(error_message, response.status, error_code)
                    
                    return response_data
                    
            except aiohttp.ClientTimeout:
                raise TimeoutError("Request timeout")
            except aiohttp.ClientError as e:
                raise InvoiceAIError(str(e), 500, "REQUEST_ERROR")
