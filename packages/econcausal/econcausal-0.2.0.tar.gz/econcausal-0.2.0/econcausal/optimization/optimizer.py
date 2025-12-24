from ..client import EconCausalClient

class OptimizationClient:
    def __init__(self, client: 'EconCausalClient'):
        self.client = client

    def optimize(
        self, 
        causal_graph,
        objectives,
        constraints = None,
        initial_conditions = None
    ):
        """
        Optimize policy parameters.
        """
        if initial_conditions is None:
            initial_conditions = {"inflation": 0.02, "gdp": 0.03}
            
        payload = {
            "causal_graph": causal_graph,
            "objectives": objectives,
            "constraints": constraints,
            "initial_conditions": initial_conditions
        }
        return self.client._post("/optimization/optimize_policy", payload)
