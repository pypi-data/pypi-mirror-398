class SodaEndpointFactory:
    """Wrapper class around all endpoints we're using"""

    @classmethod
    def datasets(cls) -> str:
        return "datasets"

    @classmethod
    def checks(cls) -> str:
        return "checks"
