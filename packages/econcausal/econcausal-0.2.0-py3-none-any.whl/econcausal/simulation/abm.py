from ..client import EconCausalClient

class SimulationClient:
    def __init__(self, client: 'EconCausalClient'):
        self.client = client

    def run(
        self, 
        causal_graph,
        policy,
        n_agents: int = 1000,
        time_steps: int = 20,
        initial_conditions = None
    ):
        """
        Run an economic simulation.
        """
        if initial_conditions is None:
            initial_conditions = {"inflation": 0.02, "gdp": 0.03}
            
        payload = {
            "causal_graph": causal_graph,
            "policy": policy,
            "n_agents": n_agents,
            "time_steps": time_steps,
            "initial_conditions": initial_conditions
        }
        return self.client._post("/simulation/run", payload)
