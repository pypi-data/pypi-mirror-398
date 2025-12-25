class ThoughtspotEndpointFactory:
    @classmethod
    def authentication(cls) -> str:
        return "api/rest/2.0/auth/token/full"

    @classmethod
    def metadata_search(cls) -> str:
        return "api/rest/2.0/metadata/search"

    @classmethod
    def liveboard_data(cls) -> str:
        return "api/rest/2.0/metadata/liveboard/data"
