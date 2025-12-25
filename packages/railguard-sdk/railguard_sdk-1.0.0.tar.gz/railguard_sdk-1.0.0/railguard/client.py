import requests
from typing import Optional, Dict, List, Any


class RailGuardClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:3001"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        })

    def validate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/v1/validate",
            json=request
        )
        
        if not response.ok:
            error = response.json()
            raise Exception(f"RailGuard validation failed: {error}")
        
        return response.json()

    def get_rules(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if agent_id:
            params['agentId'] = agent_id
        
        response = self.session.get(
            f"{self.base_url}/v1/rules",
            params=params
        )
        
        if not response.ok:
            error = response.json()
            raise Exception(f"Failed to fetch rules: {error}")
        
        return response.json()

    def get_validations(
        self, 
        agent_id: Optional[str] = None, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if agent_id:
            params['agentId'] = agent_id
        if limit:
            params['limit'] = limit
        
        response = self.session.get(
            f"{self.base_url}/v1/validations",
            params=params
        )
        
        if not response.ok:
            error = response.json()
            raise Exception(f"Failed to fetch validations: {error}")
        
        return response.json()


def create_client(api_key: str, base_url: str = "http://localhost:3001") -> RailGuardClient:
    return RailGuardClient(api_key=api_key, base_url=base_url)
