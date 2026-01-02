"""AgentBill Contacts Resource - CRUD operations"""

from typing import Any, Dict, List, Optional
import httpx


class ContactsResource:
    """
    Contacts resource for CRUD operations
    
    Contacts belong to Accounts (customers) and contain billing address information.
    
    Example:
        >>> from agentbill import AgentBill
        >>> ab = AgentBill.init({"api_key": "agb_..."})
        >>> 
        >>> # List contacts for an account
        >>> contacts = ab.contacts.list(account_id="acct_123")
        >>> 
        >>> # Create contact with billing address
        >>> contact = ab.contacts.create(
        ...     account_id="acct_123",
        ...     name="John Doe",
        ...     email="john@acme.com",
        ...     billing_address_line1="123 Main St",
        ...     billing_city="San Francisco",
        ...     billing_state="CA",
        ...     billing_postal_code="94102",
        ...     billing_country="US"
        ... )
        >>> 
        >>> # Get contact
        >>> contact = ab.contacts.get("contact_123")
        >>> 
        >>> # Update contact
        >>> contact = ab.contacts.update("contact_123", phone="+1-555-1234")
        >>> 
        >>> # Delete contact
        >>> ab.contacts.delete("contact_123")
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
        account_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List contacts with pagination and filtering
        
        Args:
            account_id: Filter by account ID
            limit: Number of contacts to return (default: 50)
            offset: Offset for pagination (default: 0)
            search: Search term to filter by name or email
            
        Returns:
            Dict with 'data' (list of contacts) and 'pagination' info
        """
        params = {"limit": str(limit), "offset": str(offset)}
        if search:
            params["search"] = search
        if account_id:
            params["account_id"] = account_id
        
        url = f"{self.base_url}/functions/v1/api-contacts"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list contacts"))
            
            return response.json()
    
    def create(
        self,
        account_id: str,
        name: str,
        email: str,
        phone: Optional[str] = None,
        billing_address_line1: Optional[str] = None,
        billing_address_line2: Optional[str] = None,
        billing_city: Optional[str] = None,
        billing_state: Optional[str] = None,
        billing_postal_code: Optional[str] = None,
        billing_country: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new contact
        
        Args:
            account_id: Account (customer) ID this contact belongs to (required)
            name: Contact name (required)
            email: Contact email (required)
            phone: Phone number
            billing_address_line1: Street address line 1
            billing_address_line2: Street address line 2
            billing_city: City
            billing_state: State/Province
            billing_postal_code: Postal/ZIP code
            billing_country: Country code (e.g., "US", "GB")
            metadata: Additional metadata
            
        Returns:
            Created contact object
        """
        payload = {
            "account_id": account_id,
            "name": name,
            "email": email
        }
        if phone:
            payload["phone"] = phone
        if billing_address_line1:
            payload["billing_address_line1"] = billing_address_line1
        if billing_address_line2:
            payload["billing_address_line2"] = billing_address_line2
        if billing_city:
            payload["billing_city"] = billing_city
        if billing_state:
            payload["billing_state"] = billing_state
        if billing_postal_code:
            payload["billing_postal_code"] = billing_postal_code
        if billing_country:
            payload["billing_country"] = billing_country
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-contacts"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] POST {url}")
                print(f"[AgentBill] Payload: {payload}")
            
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if response.status_code not in (200, 201):
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    if error_data.get("existing_contact"):
                        error_msg += f" (existing: {error_data['existing_contact']})"
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def get(self, contact_id: str) -> Dict[str, Any]:
        """
        Get a contact by ID
        
        Args:
            contact_id: Contact UUID
            
        Returns:
            Contact object
        """
        params = {"id": contact_id}
        url = f"{self.base_url}/functions/v1/api-contacts"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get contact"))
            
            return response.json()
    
    def update(
        self,
        contact_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        billing_address_line1: Optional[str] = None,
        billing_address_line2: Optional[str] = None,
        billing_city: Optional[str] = None,
        billing_state: Optional[str] = None,
        billing_postal_code: Optional[str] = None,
        billing_country: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a contact
        
        Args:
            contact_id: Contact UUID
            name: New name
            email: New email
            phone: New phone
            billing_address_line1: New street address line 1
            billing_address_line2: New street address line 2
            billing_city: New city
            billing_state: New state/province
            billing_postal_code: New postal/ZIP code
            billing_country: New country code
            metadata: New metadata (replaces existing)
            
        Returns:
            Updated contact object
        """
        payload = {"id": contact_id}
        if name is not None:
            payload["name"] = name
        if email is not None:
            payload["email"] = email
        if phone is not None:
            payload["phone"] = phone
        if billing_address_line1 is not None:
            payload["billing_address_line1"] = billing_address_line1
        if billing_address_line2 is not None:
            payload["billing_address_line2"] = billing_address_line2
        if billing_city is not None:
            payload["billing_city"] = billing_city
        if billing_state is not None:
            payload["billing_state"] = billing_state
        if billing_postal_code is not None:
            payload["billing_postal_code"] = billing_postal_code
        if billing_country is not None:
            payload["billing_country"] = billing_country
        if metadata is not None:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-contacts"
        
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to update contact"))
            
            return response.json()
    
    def delete(self, contact_id: str) -> None:
        """
        Delete a contact
        
        Args:
            contact_id: Contact UUID to delete
        """
        url = f"{self.base_url}/functions/v1/api-contacts"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": contact_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete contact"))
