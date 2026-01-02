"""AgentBill Customers Resource - CRUD operations"""

from typing import Any, Dict, List, Optional
import httpx


class CustomersResource:
    """
    Customers resource for CRUD operations
    
    Example:
        >>> from agentbill import AgentBill
        >>> ab = AgentBill.init({"api_key": "agb_..."})
        >>> 
        >>> # List customers
        >>> customers = ab.customers.list(limit=10)
        >>> 
        >>> # Create customer
        >>> customer = ab.customers.create(name="Acme Corp", email="billing@acme.com")
        >>> 
        >>> # Get customer
        >>> customer = ab.customers.get("cust_123")
        >>> 
        >>> # Update customer
        >>> customer = ab.customers.update("cust_123", name="Acme Inc")
        >>> 
        >>> # Delete customer
        >>> ab.customers.delete("cust_123")
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get("base_url", "https://bgwyprqxtdreuutzpbgw.supabase.co")
        self.api_key = config["api_key"]
        self.debug = config.get("debug", False)
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List customers with pagination and search
        
        Args:
            limit: Number of customers to return (default: 50)
            offset: Offset for pagination (default: 0)
            search: Search term to filter by name or email
            
        Returns:
            Dict with 'data' (list of customers) and 'pagination' info
        """
        params = {"limit": str(limit), "offset": str(offset)}
        if search:
            params["search"] = search
        
        url = f"{self.base_url}/functions/v1/api-customers"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list customers"))
            
            return response.json()
    
    def create(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        external_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new customer
        
        Args:
            name: Customer name (required)
            email: Customer email (required)
            phone: Phone number
            website: Website URL
            external_id: Your external ID for this customer
            metadata: Additional metadata
            
        Returns:
            Created customer object
        """
        payload = {
            "name": name,
            "email": email
        }
        if phone:
            payload["phone"] = phone
        if website:
            payload["website"] = website
        if external_id:
            payload["external_id"] = external_id
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-customers"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] POST {url}")
                print(f"[AgentBill] Headers: X-API-Key={self.api_key[:12]}...")
                print(f"[AgentBill] Payload: {payload}")
            
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if self.debug:
                print(f"[AgentBill] Response: {response.status_code} - {response.text[:500] if response.text else 'empty'}")
            
            if response.status_code not in (200, 201):
                # Extract detailed error from API response
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}: {response.text[:200]}")
                    # Include existing_customer info if duplicate
                    if error_data.get("existing_customer"):
                        error_msg += f" (existing: {error_data['existing_customer']})"
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response body'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def get(self, customer_id: str, by_external_id: bool = False) -> Dict[str, Any]:
        """
        Get a customer by ID or external_id
        
        Args:
            customer_id: Customer UUID or external_id
            by_external_id: If True, treat customer_id as external_id
            
        Returns:
            Customer object
        """
        params = {}
        if by_external_id:
            params["external_id"] = customer_id
        else:
            params["id"] = customer_id
        
        url = f"{self.base_url}/functions/v1/api-customers"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get customer"))
            
            result = response.json()
            if "data" in result and isinstance(result["data"], list):
                if len(result["data"]) == 0:
                    raise Exception("Customer not found")
                return result["data"][0]
            return result
    
    def update(
        self,
        customer_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a customer
        
        Args:
            customer_id: Customer UUID
            name: New name
            email: New email
            phone: New phone
            website: New website
            metadata: New metadata (replaces existing)
            
        Returns:
            Updated customer object
        """
        payload = {"id": customer_id}
        if name:
            payload["name"] = name
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if website:
            payload["website"] = website
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-customers"
        
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to update customer"))
            
            return response.json()
    
    def delete(self, customer_id: str) -> None:
        """
        Delete a customer
        
        Args:
            customer_id: Customer UUID to delete
        """
        url = f"{self.base_url}/functions/v1/api-customers"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": customer_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete customer"))
