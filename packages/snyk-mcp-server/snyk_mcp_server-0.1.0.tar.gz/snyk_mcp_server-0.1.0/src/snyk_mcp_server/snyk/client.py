import asyncio
from typing import List, Optional, AsyncGenerator
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from .models import Vulnerability, PaginatedResponse


class SnykAPIError(Exception):
    """Snyk API specific error"""
    pass


class SnykClient:
    """Async Snyk API client with hardened security practices"""
    
    def __init__(self, api_token: str, api_version: str):
        if not api_token or not api_token.strip():
            raise ValueError("SNYK_API_TOKEN is required")
        if not api_version or not api_version.strip():
            raise ValueError("SNYK_API_VERSION is required")
            
        self.base_url = "https://api.snyk.io/rest"
        self.api_version = api_version
        self.headers = {
            "Authorization": f"token {api_token}",
            "Content-Type": "application/vnd.api+json",
            "User-Agent": "snyk-mcp/0.1.0"
        }
        
        # Configure httpx client with security settings
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            headers=self.headers
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _make_request(self, endpoint: str, params: Optional[dict] = None) -> PaginatedResponse:
        """Make authenticated request to Snyk API"""
        url = urljoin(self.base_url, endpoint)
        
        request_params = {"version": self.api_version}
        if params:
            request_params.update(params)
        
        try:
            response = await self.client.get(url, params=request_params)
            response.raise_for_status()
            
            data = response.json()
            return PaginatedResponse(
                data=data.get("data", []),
                links=data.get("links", {})
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("errors", [{}])[0].get("detail", "")
            except:
                error_detail = e.response.text
            
            raise SnykAPIError(f"API request failed: {e.response.status_code} - {error_detail}")
        except httpx.RequestError as e:
            raise SnykAPIError(f"Request error: {str(e)}")
    
    async def _paginate_all(self, endpoint: str, params: Optional[dict] = None) -> AsyncGenerator[Vulnerability, None]:
        """Paginate through all results and yield normalized vulnerabilities"""
        current_url = endpoint
        
        while current_url:
            # Extract params from URL if it's a full URL (for pagination)
            if current_url.startswith("http"):
                parsed = urlparse(current_url)
                current_url = parsed.path
                url_params = parse_qs(parsed.query)
                # Flatten single-item lists in query params
                url_params = {k: v[0] if len(v) == 1 else v for k, v in url_params.items()}
                if params:
                    url_params.update(params)
                params = url_params
            
            response = await self._make_request(current_url, params)
            
            # Yield normalized vulnerabilities
            for item in response.data:
                try:
                    yield Vulnerability.from_snyk_response(item)
                except Exception as e:
                    # Log and skip malformed responses
                    continue
            
            # Get next page URL
            current_url = response.next_url
            params = None  # Clear params for subsequent requests (they're in the URL)
    
    async def fetch_org_vulnerabilities(self, org_id: str) -> List[Vulnerability]:
        """Fetch all vulnerabilities for an organization"""
        if not org_id or not org_id.strip():
            raise ValueError("org_id is required")
        
        endpoint = f"/orgs/{org_id}/issues"
        params = {
            "scan_item.type": "package",
            "type": "package_vulnerability",
            "limit": "100"  # Max per page
        }
        
        vulnerabilities = []
        async for vuln in self._paginate_all(endpoint, params):
            vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    async def fetch_package_vulnerabilities(self, org_id: str, purl: str) -> List[Vulnerability]:
        """Fetch direct vulnerabilities for a specific package"""
        if not org_id or not org_id.strip():
            raise ValueError("org_id is required")
        if not purl or not purl.strip():
            raise ValueError("purl is required")
        
        endpoint = f"/orgs/{org_id}/packages/{purl}/issues"
        params = {
            "type": "package_vulnerability",
            "limit": "100"
        }
        
        vulnerabilities = []
        async for vuln in self._paginate_all(endpoint, params):
            vulnerabilities.append(vuln)
        
        return vulnerabilities