from ..client import EconCausalClient

class DataClient:
    def __init__(self, client: 'EconCausalClient'):
        self.client = client

    def list_datasets(self, limit: int = 100):
        """
        List available curated datasets.
        """
        return self.client._get("/datasets", params={"limit": limit})
