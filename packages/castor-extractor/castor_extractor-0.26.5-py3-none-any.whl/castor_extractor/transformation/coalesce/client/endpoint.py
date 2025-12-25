class CoalesceEndpointFactory:
    """Provide endpoints to hit Coalesce API"""

    @classmethod
    def environments(cls, environment_id: int | None = None) -> str:
        """
        When specified, concatenate environment_id at the end to fetch details.
        Otherwise, list existing environments.
        """
        base = "api/v1/environments"
        if environment_id:
            return base + f"/{environment_id}"
        return base

    @classmethod
    def nodes(cls, environment_id: int, node_id: str | None = None) -> str:
        """
        When specified, concatenate node_id at the end to fetch details.
        Otherwise, list existing nodes in the given environment.
        """
        base = f"api/v1/environments/{environment_id}/nodes"
        if node_id:
            return base + f"/{node_id}"
        return base

    @classmethod
    def runs(cls) -> str:
        """
        Get runs (additional filtering can be done in the body)
        """
        base = "api/v1/runs"
        return base

    @classmethod
    def run_results(cls, run_id: str) -> str:
        """
        get run results (including success/fail for tests), given a run id
        """
        return f"api/v1/runs/{run_id}/results"
