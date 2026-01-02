"""AgentBill Agents Resource - CRUD operations with signal type assignment"""

from typing import Any, Dict, List, Optional
import httpx


class AgentsResource:
    """
    Agents resource for CRUD operations and signal type management
    
    Example:
        >>> from agentbill import AgentBill
        >>> ab = AgentBill.init({"api_key": "agb_..."})
        >>> 
        >>> # Create agent
        >>> agent = ab.agents.create(name="Support Bot", description="Customer support agent")
        >>> print(f"API Key (save this!): {agent['api_key']}")
        >>> 
        >>> # Assign signal types (explicit assignment)
        >>> ab.agents.assign_signal_types(
        ...     agent_id=agent['id'],
        ...     signal_type_names=['ai_call', 'completion', 'embedding']
        ... )
        >>> 
        >>> # List agents
        >>> agents = ab.agents.list(status='active')
        >>> 
        >>> # Get signal types for agent
        >>> signal_types = ab.agents.get_signal_types(agent['id'])
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
    
    def list(self, status: Optional[str] = None) -> Dict[str, Any]:
        """
        List agents with optional status filter
        
        Args:
            status: Filter by status ('active', 'inactive', 'archived')
            
        Returns:
            Dict with 'data' (list of agents)
        """
        params = {}
        if status:
            params["status"] = status
        
        url = f"{self.base_url}/functions/v1/api-agents"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list agents"))
            
            return response.json()
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        external_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        signal_type_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new agent
        
        IMPORTANT: The response includes a one-time visible API key.
        Save this key securely - it cannot be retrieved again.
        
        Args:
            name: Agent name (required)
            description: Agent description
            agent_type: Type of agent (e.g., 'support', 'sales', 'assistant')
            model: Default model for this agent
            external_id: Your external ID for this agent
            metadata: Additional metadata
            signal_type_names: Signal types to auto-assign (e.g., ['ai_call', 'completion'])
            
        Returns:
            Created agent object with api_key (one-time visible)
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if agent_type:
            payload["agent_type"] = agent_type
        if model:
            payload["model"] = model
        if external_id:
            payload["external_id"] = external_id
        if metadata:
            payload["metadata"] = metadata
        if signal_type_names:
            payload["signal_type_names"] = signal_type_names
        
        url = f"{self.base_url}/functions/v1/api-agents"
        
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
                    # Include existing_agent info if duplicate
                    if error_data.get("existing_agent"):
                        error_msg += f" (existing: {error_data['existing_agent']})"
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response body'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def get(self, agent_id: str, by_external_id: bool = False) -> Dict[str, Any]:
        """
        Get an agent by ID or external_id
        
        Args:
            agent_id: Agent UUID or external_id
            by_external_id: If True, treat agent_id as external_id
            
        Returns:
            Agent object
        """
        params = {}
        if by_external_id:
            params["external_id"] = agent_id
        else:
            params["id"] = agent_id
        
        url = f"{self.base_url}/functions/v1/api-agents"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get agent"))
            
            result = response.json()
            if "data" in result and isinstance(result["data"], list):
                if len(result["data"]) == 0:
                    raise Exception("Agent not found")
                return result["data"][0]
            return result
    
    def update(
        self,
        agent_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        agent_type: Optional[str] = None,
        model: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an agent
        
        Args:
            agent_id: Agent UUID
            name: New name
            description: New description
            agent_type: New agent type
            model: New default model
            status: New status ('active', 'inactive', 'archived')
            metadata: New metadata (replaces existing)
            
        Returns:
            Updated agent object
        """
        payload = {"id": agent_id}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if agent_type:
            payload["agent_type"] = agent_type
        if model:
            payload["model"] = model
        if status:
            payload["status"] = status
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-agents"
        
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to update agent"))
            
            return response.json()
    
    def delete(self, agent_id: str) -> None:
        """
        Delete an agent
        
        Args:
            agent_id: Agent UUID to delete
        """
        url = f"{self.base_url}/functions/v1/api-agents"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": agent_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete agent"))
    
    def assign_signal_types(
        self,
        agent_id: Optional[str] = None,
        external_agent_id: Optional[str] = None,
        signal_type_ids: Optional[List[str]] = None,
        signal_type_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Assign signal types to an agent (explicit assignment)
        
        This method explicitly configures which signal types the agent can emit.
        Use this after creating an agent to define its capabilities.
        
        Args:
            agent_id: Agent UUID (provide this OR external_agent_id)
            external_agent_id: External agent ID (provide this OR agent_id)
            signal_type_ids: List of signal type UUIDs to assign
            signal_type_names: List of signal type names (e.g., ['ai_call', 'completion'])
            
        Returns:
            Dict with agent_id, signal_type_ids, and assigned_count
            
        Example:
            >>> ab.agents.assign_signal_types(
            ...     agent_id="agent-123",
            ...     signal_type_names=['ai_call', 'completion', 'embedding']
            ... )
        """
        if not agent_id and not external_agent_id:
            raise ValueError("Either agent_id or external_agent_id is required")
        if not signal_type_ids and not signal_type_names:
            raise ValueError("Either signal_type_ids or signal_type_names is required")
        
        payload = {}
        if agent_id:
            payload["agent_id"] = agent_id
        if external_agent_id:
            payload["external_agent_id"] = external_agent_id
        if signal_type_ids:
            payload["signal_type_ids"] = signal_type_ids
        if signal_type_names:
            payload["signal_type_names"] = signal_type_names
        
        url = f"{self.base_url}/functions/v1/api-agent-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to assign signal types"))
            
            return response.json()
    
    def get_signal_types(
        self,
        agent_id: str,
        by_external_id: bool = False
    ) -> Dict[str, Any]:
        """
        Get signal types assigned to an agent
        
        Args:
            agent_id: Agent UUID or external_id
            by_external_id: If True, treat agent_id as external_id
            
        Returns:
            Dict with agent_id and list of signal_types
        """
        params = {}
        if by_external_id:
            params["external_agent_id"] = agent_id
        else:
            params["agent_id"] = agent_id
        
        url = f"{self.base_url}/functions/v1/api-agent-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get signal types"))
            
            return response.json()
    
    def remove_signal_types(
        self,
        agent_id: str,
        signal_type_ids: Optional[List[str]] = None
    ) -> None:
        """
        Remove signal types from an agent
        
        Args:
            agent_id: Agent UUID
            signal_type_ids: Specific signal type IDs to remove. If None, removes all.
        """
        payload = {"agent_id": agent_id}
        if signal_type_ids:
            payload["signal_type_ids"] = signal_type_ids
        
        url = f"{self.base_url}/functions/v1/api-agent-signal-types"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json=payload
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to remove signal types"))
