import os
import requests
from typing import Optional, Dict, Any

class EconCausalClient:
    """
    Main client for the EconCausalAI platform.
    """
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        base_url: str = "http://localhost:8001/api/v1"
    ):
        self.api_key = api_key or os.environ.get('ECONCAUSAL_API_KEY')
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
            
        # Initialize sub-clients
        from .causal.discovery import CausalDiscoveryClient
        from .simulation.abm import SimulationClient
        from .optimization.optimizer import OptimizationClient
        from .data.catalog import DataClient
        
        self.causal = CausalDiscoveryClient(self)
        self.simulation = SimulationClient(self)
        self.optimization = OptimizationClient(self)
        self.data = DataClient(self)

    def _post(self, endpoint: str, json: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = self.session.post(f"{self.base_url}{endpoint}", json=json, timeout=300)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"API Error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('detail', str(e))}"
            except:
                error_msg += f" - {e.response.text[:200]}"
            raise Exception(error_msg) from e
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to {self.base_url}. Is the server running?")
        except requests.exceptions.Timeout:
            raise Exception(f"Request to {endpoint} timed out after 300s")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_msg = f"API Error: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail.get('detail', str(e))}"
            except:
                error_msg += f" - {e.response.text[:200]}"
            raise Exception(error_msg) from e
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to {self.base_url}. Is the server running?")
