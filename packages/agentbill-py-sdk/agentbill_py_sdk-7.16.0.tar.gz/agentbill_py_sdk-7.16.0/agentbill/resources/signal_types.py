"""AgentBill Signal Types Resource - CRUD operations for signal type management"""

from typing import Any, Dict, List, Optional
import httpx


class SignalTypesResource:
    """
    Signal Types resource for CRUD operations
    
    Example:
        >>> from agentbill import AgentBill
        >>> ab = AgentBill.init({"api_key": "agb_..."})
        >>> 
        >>> # Create signal type
        >>> st = ab.signal_types.create(
        ...     name="ai_completion",
        ...     category="activity",
        ...     description="Tracks AI completion events"
        ... )
        >>> 
        >>> # List all signal types
        >>> signal_types = ab.signal_types.list()
        >>> 
        >>> # Get specific signal type
        >>> st = ab.signal_types.get(signal_type_id)
        >>> 
        >>> # Update signal type
        >>> ab.signal_types.update(signal_type_id, description="Updated description")
        >>> 
        >>> # Delete signal type
        >>> ab.signal_types.delete(signal_type_id)
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
        category: Optional[str] = None,
        include_global: bool = True
    ) -> Dict[str, Any]:
        """
        List signal types with optional filters
        
        Args:
            category: Filter by category ('activity' or 'outcome')
            include_global: Include global (system) signal types (default: True)
            
        Returns:
            Dict with 'data' (list of signal types) and 'summary'
        """
        params = {}
        if category:
            params["category"] = category
        if not include_global:
            params["include_global"] = "false"
        
        url = f"{self.base_url}/functions/v1/api-signal-types"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] GET {url}")
            
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list signal types"))
            
            return response.json()
    
    def create(
        self,
        name: str,
        category: str = "activity",
        description: Optional[str] = None,
        unit: Optional[str] = None,
        default_value: Optional[float] = None,
        external_id: Optional[str] = None,
        expected_metrics: Optional[Dict[str, Any]] = None,
        revenue_formula: Optional[str] = None,
        validation_rules: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new signal type
        
        Args:
            name: Signal type name (required, e.g., 'ai_completion', 'chat_message')
            category: Category - 'activity' or 'outcome' (default: 'activity')
            description: Human-readable description
            unit: Unit of measurement (e.g., 'call', 'token', 'message')
            default_value: Default value for this signal type
            external_id: Your external ID for this signal type
            expected_metrics: Expected metrics configuration
            revenue_formula: Formula for revenue calculation
            validation_rules: Validation rules for signals of this type
            
        Returns:
            Created signal type object
        """
        payload: Dict[str, Any] = {
            "name": name,
            "category": category
        }
        if description:
            payload["description"] = description
        if unit:
            payload["unit"] = unit
        if default_value is not None:
            payload["default_value"] = default_value
        if external_id:
            payload["external_id"] = external_id
        if expected_metrics:
            payload["expected_metrics"] = expected_metrics
        if revenue_formula:
            payload["revenue_formula"] = revenue_formula
        if validation_rules:
            payload["validation_rules"] = validation_rules
        
        url = f"{self.base_url}/functions/v1/api-signal-types"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] POST {url}")
                print(f"[AgentBill] Payload: {payload}")
            
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if response.status_code not in (200, 201):
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    if error_data.get("existing_id"):
                        error_msg += f" (existing_id: {error_data['existing_id']})"
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def get(
        self,
        signal_type_id: str,
        by_external_id: bool = False
    ) -> Dict[str, Any]:
        """
        Get a signal type by ID or external_id
        
        Args:
            signal_type_id: Signal type UUID or external_id
            by_external_id: If True, treat signal_type_id as external_id
            
        Returns:
            Signal type object
        """
        params = {}
        if by_external_id:
            params["external_id"] = signal_type_id
        else:
            params["id"] = signal_type_id
        
        url = f"{self.base_url}/functions/v1/api-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get signal type"))
            
            return response.json()
    
    def update(
        self,
        signal_type_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        unit: Optional[str] = None,
        default_value: Optional[float] = None,
        external_id: Optional[str] = None,
        expected_metrics: Optional[Dict[str, Any]] = None,
        revenue_formula: Optional[str] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update a signal type
        
        Args:
            signal_type_id: Signal type UUID
            name: New name
            description: New description
            category: New category
            unit: New unit
            default_value: New default value
            external_id: New external ID
            expected_metrics: New expected metrics
            revenue_formula: New revenue formula
            validation_rules: New validation rules
            is_active: Active status
            
        Returns:
            Updated signal type object
        """
        payload: Dict[str, Any] = {"id": signal_type_id}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if category is not None:
            payload["category"] = category
        if unit is not None:
            payload["unit"] = unit
        if default_value is not None:
            payload["default_value"] = default_value
        if external_id is not None:
            payload["external_id"] = external_id
        if expected_metrics is not None:
            payload["expected_metrics"] = expected_metrics
        if revenue_formula is not None:
            payload["revenue_formula"] = revenue_formula
        if validation_rules is not None:
            payload["validation_rules"] = validation_rules
        if is_active is not None:
            payload["is_active"] = is_active
        
        url = f"{self.base_url}/functions/v1/api-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to update signal type"))
            
            return response.json()
    
    def delete(self, signal_type_id: str) -> None:
        """
        Delete a signal type
        
        Args:
            signal_type_id: Signal type UUID to delete
            
        Note: Cannot delete global (system) signal types
        """
        url = f"{self.base_url}/functions/v1/api-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": signal_type_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete signal type"))
