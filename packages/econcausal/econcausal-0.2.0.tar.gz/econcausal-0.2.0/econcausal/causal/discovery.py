from ..client import EconCausalClient
from typing import Dict, Any

class CausalDiscoveryClient:
    def __init__(self, client: 'EconCausalClient'):
        self.client = client

    def discover(
        self,
        data, # List[Dict] or DataFrame
        algorithm: str = "pc_algorithm",
        theory_constraints = None,
        use_bootstrap: bool = False,
        n_bootstrap: int = 50
    ) -> Dict[str, Any]:
        """
        Discover causal structure from data.

        Args:
            data: Input data (DataFrame or list of dicts)
            algorithm: Algorithm to use ("pc_algorithm" or "notears")
            theory_constraints: Optional list of theory constraints
            use_bootstrap: Enable bootstrap uncertainty quantification
            n_bootstrap: Number of bootstrap iterations (default: 50)

        Returns:
            Dict with:
                - graph: Causal graph with nodes and edges
                - explanation: Text explanation
                - validation_results: Bootstrap statistics (if enabled)

        Example:
            >>> result = client.causal.discover(
            ...     data=my_df,
            ...     algorithm="pc_algorithm",
            ...     use_bootstrap=True,
            ...     n_bootstrap=50
            ... )
            >>> for edge in result['graph']['edges']:
            ...     print(f"{edge['source']} → {edge['target']}")
            ...     print(f"  Confidence: {edge.get('bootstrap_frequency', 'N/A')}")
        """
        # Auto-convert pandas DataFrame
        if hasattr(data, 'to_dict'):
            data = data.to_dict(orient='records')

        payload = {
            "data": data,
            "algorithm": algorithm,
            "theory_constraints": theory_constraints,
            "use_bootstrap": use_bootstrap,
            "n_bootstrap": n_bootstrap
        }

        endpoint = "/causal/discover_bootstrap" if use_bootstrap else "/causal/discover"
        return self.client._post(endpoint, payload)

    def validate_data(self, data) -> Dict[str, Any]:
        """
        Validate data quality before analysis.

        Args:
            data: Input data (DataFrame or list of dicts)

        Returns:
            Dict with validation results:
                - is_valid: Boolean
                - errors: List of errors
                - warnings: List of warnings
                - statistics: Data quality metrics
        """
        if hasattr(data, 'to_dict'):
            data = data.to_dict(orient='records')

        return self.client._post("/causal/validate", {"data": data})
