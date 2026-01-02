"""OrdersResource for CrewAI Integration

Re-exports OrdersResource from the main AgentBill Python SDK for convenience.
"""

try:
    from agentbill.resources.orders import OrdersResource
except ImportError:
    # Standalone implementation if main SDK not installed
    import requests
    from typing import Any, Dict, List, Optional
    
    class OrdersResource:
        """Orders management resource for AgentBill API.
        
        Orders require agent association via agent_ids or agent_external_ids.
        """
        
        def __init__(self, config: Dict[str, Any]):
            self.api_key = config.get('api_key')
            self.base_url = config.get('base_url', 'https://bgwyprqxtdreuutzpbgw.supabase.co')
        
        def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
            url = f"{self.base_url}/functions/v1/{endpoint}"
            headers = {
                'X-API-Key': self.api_key,
                'Content-Type': 'application/json'
            }
            response = requests.request(method, url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        
        def create(
            self,
            status: str = 'draft',
            agent_ids: Optional[List[str]] = None,
            agent_external_ids: Optional[List[str]] = None,
            **kwargs
        ) -> Dict[str, Any]:
            """Create a new order.
            
            Args:
                status: Order status (draft, active, completed, cancelled)
                agent_ids: List of agent UUIDs (required if agent_external_ids not provided)
                agent_external_ids: List of agent external IDs (required if agent_ids not provided)
                **kwargs: Additional order fields (account_id, line_items, etc.)
            
            Returns:
                Created order data
            
            Raises:
                ValueError: If neither agent_ids nor agent_external_ids provided
            """
            if not agent_ids and not agent_external_ids:
                raise ValueError(
                    "Orders require agent association. Provide either 'agent_ids' or 'agent_external_ids'."
                )
            
            data = {'action': 'create', 'status': status, **kwargs}
            if agent_ids:
                data['agent_ids'] = agent_ids
            if agent_external_ids:
                data['agent_external_ids'] = agent_external_ids
            
            return self._request('POST', 'api-orders', data)
        
        def list(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
            """List orders."""
            return self._request('POST', 'api-orders', {
                'action': 'list',
                'limit': limit,
                'offset': offset
            })
        
        def get(self, order_id: str) -> Dict[str, Any]:
            """Get order by ID."""
            return self._request('POST', 'api-orders', {
                'action': 'get',
                'order_id': order_id
            })
        
        def update(self, order_id: str, **kwargs) -> Dict[str, Any]:
            """Update an order."""
            return self._request('POST', 'api-orders', {
                'action': 'update',
                'order_id': order_id,
                **kwargs
            })
        
        def delete(self, order_id: str) -> Dict[str, Any]:
            """Delete an order."""
            return self._request('POST', 'api-orders', {
                'action': 'delete',
                'order_id': order_id
            })
        
        def add_line_item(
            self,
            order_id: str,
            item_type: str,
            description: str,
            quantity: int = 1,
            unit_price: float = 0.0,
            **kwargs
        ) -> Dict[str, Any]:
            """Add a line item to an order.
            
            Valid item_type values: usage, platform_fee, setup_fee, base_fee, 
            overage, custom, product, service, subscription
            """
            return self._request('POST', 'api-orders', {
                'action': 'add_line_item',
                'order_id': order_id,
                'item_type': item_type,
                'description': description,
                'quantity': quantity,
                'unit_price': unit_price,
                **kwargs
            })

__all__ = ['OrdersResource']
