"""AgentBill Orders Resource - CRUD operations with line items"""

from typing import Any, Dict, List, Optional
import httpx


class OrdersResource:
    """
    Orders resource for CRUD operations
    
    Orders belong to Accounts (customers) and can have line items for billing.
    
    IMPORTANT: At least one agent must be associated with an order via 
    agent_ids or agent_external_ids. Orders cannot be created without agents.
    
    Example:
        >>> from agentbill import AgentBill
        >>> ab = AgentBill.init({"api_key": "agb_..."})
        >>> 
        >>> # List orders for an account
        >>> orders = ab.orders.list(account_id="acct_123")
        >>> 
        >>> # Create order (agent_ids or agent_external_ids REQUIRED)
        >>> order = ab.orders.create(
        ...     account_id="acct_123",
        ...     name="Enterprise License Q1 2024",
        ...     external_id="ORD-2024-001",
        ...     agent_ids=["agent-uuid-1", "agent-uuid-2"]  # REQUIRED
        ... )
        >>> 
        >>> # Alternative: use agent external IDs
        >>> order = ab.orders.create(
        ...     account_id="acct_123",
        ...     name="Enterprise License Q1 2024",
        ...     agent_external_ids=["my-chatbot", "my-assistant"]  # REQUIRED
        ... )
        >>> 
        >>> # Add line items
        >>> ab.orders.add_line_item(
        ...     order_id=order["id"],
        ...     description="AI API Usage - January",
        ...     quantity=1000,
        ...     unit_price=0.05,
        ...     item_type="usage"  # Valid: usage, platform_fee, setup_fee, base_fee, overage, custom, product, service, subscription
        ... )
        >>> 
        >>> # Get order with line items
        >>> order = ab.orders.get("order_123")
        >>> 
        >>> # Get order by external_id
        >>> order = ab.orders.get("ORD-2024-001", by_external_id=True)
        >>> 
        >>> # Update order status
        >>> order = ab.orders.update("order_123", status="active")
        >>> 
        >>> # Delete order
        >>> ab.orders.delete("order_123")
        
    Valid item_type values for add_line_item:
        - usage: Usage-based charges
        - platform_fee: Platform fees
        - setup_fee: One-time setup fees
        - base_fee: Recurring base fees
        - overage: Overage charges
        - custom: Custom charges
        - product: Product purchases
        - service: Service charges
        - subscription: Subscription fees
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
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List orders with pagination and filtering
        
        Args:
            account_id: Filter by account ID
            status: Filter by status (draft, active, completed, cancelled)
            limit: Number of orders to return (default: 50)
            offset: Offset for pagination (default: 0)
            search: Search term to filter by name or external_id
            
        Returns:
            Dict with 'data' (list of orders) and 'pagination' info
        """
        params = {"limit": str(limit), "offset": str(offset)}
        if search:
            params["search"] = search
        if account_id:
            params["account_id"] = account_id
        if status:
            params["status"] = status
        
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list orders"))
            
            return response.json()
    
    def create(
        self,
        account_id: str,
        name: str,
        agent_ids: Optional[List[str]] = None,
        agent_external_ids: Optional[List[str]] = None,
        external_id: Optional[str] = None,
        account_external_id: Optional[str] = None,
        billing_contact_id: Optional[str] = None,
        billing_contact_external_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new order
        
        IMPORTANT: At least one agent must be specified via agent_ids or agent_external_ids.
        Orders cannot be created without agent association for proper billing attribution.
        
        Args:
            account_id: Account (customer) UUID this order belongs to (required unless account_external_id provided)
            name: Order name (required)
            agent_ids: List of agent UUIDs to associate with this order (required if agent_external_ids not provided)
            agent_external_ids: List of agent external IDs (required if agent_ids not provided)
            external_id: Your external ID for this order
            account_external_id: External ID of the account (alternative to account_id)
            billing_contact_id: Contact UUID for billing
            billing_contact_external_id: External ID of billing contact (alternative to billing_contact_id)
            start_date: Order start date (ISO format)
            end_date: Order end date (ISO format)
            status: Order status (draft, active, completed, cancelled)
            currency: Currency code (default: USD)
            metadata: Additional metadata
            
        Returns:
            Created order object
            
        Raises:
            Exception: If neither agent_ids nor agent_external_ids provided
            
        Example:
            >>> order = ab.orders.create(
            ...     account_id="acct-uuid",
            ...     name="Enterprise Q1",
            ...     agent_ids=["agent-uuid-1"]  # At least one agent required
            ... )
        """
        # Validate agent requirement
        if not agent_ids and not agent_external_ids:
            raise ValueError(
                "At least one agent must be specified via agent_ids or agent_external_ids. "
                "Orders cannot be created without agent association for billing attribution."
            )
        
        payload = {
            "account_id": account_id,
            "name": name
        }
        if agent_ids:
            payload["agent_ids"] = agent_ids
        if agent_external_ids:
            payload["agent_external_ids"] = agent_external_ids
        if external_id:
            payload["external_id"] = external_id
        if account_external_id:
            payload["account_external_id"] = account_external_id
        if billing_contact_id:
            payload["billing_contact_id"] = billing_contact_id
        if billing_contact_external_id:
            payload["billing_contact_external_id"] = billing_contact_external_id
        if start_date:
            payload["start_date"] = start_date
        if end_date:
            payload["end_date"] = end_date
        if status:
            payload["status"] = status
        if currency:
            payload["currency"] = currency
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] POST {url}")
                print(f"[AgentBill] Payload: {payload}")
            
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if response.status_code not in (200, 201):
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                    if error_data.get("existing_order"):
                        error_msg += f" (existing: {error_data['existing_order']})"
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def get(self, order_id: str, by_external_id: bool = False) -> Dict[str, Any]:
        """
        Get an order by ID or external_id (includes line items)
        
        Args:
            order_id: Order UUID or external_id
            by_external_id: If True, treat order_id as external_id
            
        Returns:
            Order object with order_line_items
        """
        params = {}
        if by_external_id:
            params["external_id"] = order_id
        else:
            params["id"] = order_id
        
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to get order"))
            
            return response.json()
    
    def update(
        self,
        order_id: str,
        name: Optional[str] = None,
        billing_contact_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        currency: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update an order
        
        Args:
            order_id: Order UUID
            name: New name
            billing_contact_id: New billing contact ID
            start_date: New start date
            end_date: New end date
            status: New status
            currency: New currency
            metadata: New metadata (replaces existing)
            
        Returns:
            Updated order object
        """
        payload = {"id": order_id}
        if name is not None:
            payload["name"] = name
        if billing_contact_id is not None:
            payload["billing_contact_id"] = billing_contact_id
        if start_date is not None:
            payload["start_date"] = start_date
        if end_date is not None:
            payload["end_date"] = end_date
        if status is not None:
            payload["status"] = status
        if currency is not None:
            payload["currency"] = currency
        if metadata is not None:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            response = client.patch(url, headers=self._get_headers(), json=payload)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to update order"))
            
            return response.json()
    
    def delete(self, order_id: str) -> None:
        """
        Delete an order and its line items
        
        Args:
            order_id: Order UUID to delete
        """
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": order_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete order"))
    
    # Line Items methods
    def list_line_items(self, order_id: str) -> Dict[str, Any]:
        """
        List line items for an order
        
        Args:
            order_id: Order UUID
            
        Returns:
            Dict with 'data' (list of line items)
        """
        params = {"order_id": order_id, "action": "line-items"}
        url = f"{self.base_url}/functions/v1/api-orders"
        
        with httpx.Client(timeout=30) as client:
            response = client.get(url, headers=self._get_headers(), params=params)
            
            if response.status_code != 200:
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to list line items"))
            
            return response.json()
    
    def add_line_item(
        self,
        order_id: str,
        description: str,
        quantity: float,
        unit_price: float,
        product_id: Optional[str] = None,
        product_name: Optional[str] = None,
        product_sku: Optional[str] = None,
        usage_metric: Optional[str] = None,
        usage_quantity: Optional[float] = None,
        discount_type: Optional[str] = None,
        discount_value: Optional[float] = None,
        tax_rate: Optional[float] = None,
        notes: Optional[str] = None,
        sort_order: Optional[int] = None,
        agent_id: Optional[str] = None,
        item_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a line item to an order
        
        Args:
            order_id: Order UUID (required)
            description: Line item description (required)
            quantity: Quantity (required)
            unit_price: Price per unit (required)
            product_id: Product reference ID
            product_name: Product name
            product_sku: Product SKU
            usage_metric: Usage metric name (e.g., "api_calls", "tokens")
            usage_quantity: Usage quantity for this metric
            discount_type: "percentage" or "fixed"
            discount_value: Discount amount/percentage
            tax_rate: Tax rate percentage
            notes: Additional notes
            sort_order: Display order
            agent_id: Associated agent ID
            item_type: Type of item (product, usage, etc.)
            metadata: Additional metadata
            
        Returns:
            Created line item object
        """
        payload = {
            "order_id": order_id,
            "description": description,
            "quantity": quantity,
            "unit_price": unit_price
        }
        if product_id:
            payload["product_id"] = product_id
        if product_name:
            payload["product_name"] = product_name
        if product_sku:
            payload["product_sku"] = product_sku
        if usage_metric:
            payload["usage_metric"] = usage_metric
        if usage_quantity is not None:
            payload["usage_quantity"] = usage_quantity
        if discount_type:
            payload["discount_type"] = discount_type
        if discount_value is not None:
            payload["discount_value"] = discount_value
        if tax_rate is not None:
            payload["tax_rate"] = tax_rate
        if notes:
            payload["notes"] = notes
        if sort_order is not None:
            payload["sort_order"] = sort_order
        if agent_id:
            payload["agent_id"] = agent_id
        if item_type:
            payload["item_type"] = item_type
        if metadata:
            payload["metadata"] = metadata
        
        url = f"{self.base_url}/functions/v1/api-orders?action=line-items"
        
        with httpx.Client(timeout=30) as client:
            if self.debug:
                print(f"[AgentBill] POST {url}")
                print(f"[AgentBill] Payload: {payload}")
            
            response = client.post(url, headers=self._get_headers(), json=payload)
            
            if response.status_code not in (200, 201):
                try:
                    error_data = response.json() if response.text else {}
                    error_msg = error_data.get("error", f"HTTP {response.status_code}")
                except Exception:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200] if response.text else 'No response'}"
                raise Exception(error_msg)
            
            return response.json()
    
    def remove_line_item(self, line_item_id: str) -> None:
        """
        Remove a line item from an order
        
        Args:
            line_item_id: Line item UUID to delete
        """
        url = f"{self.base_url}/functions/v1/api-orders?action=line-items"
        
        with httpx.Client(timeout=30) as client:
            response = client.request(
                "DELETE",
                url,
                headers=self._get_headers(),
                json={"id": line_item_id}
            )
            
            if response.status_code not in (200, 204):
                error = response.json() if response.text else {"error": "Request failed"}
                raise Exception(error.get("error", "Failed to delete line item"))
