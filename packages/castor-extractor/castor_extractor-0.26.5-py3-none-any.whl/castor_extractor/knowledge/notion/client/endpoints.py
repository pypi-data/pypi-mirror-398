class NotionEndpointFactory:
    """Wrapper class around all endpoints we're using"""

    BLOCKS = "blocks"
    SEARCH = "search"
    USERS = "users"

    @classmethod
    def users(cls) -> str:
        return cls.USERS

    @classmethod
    def blocks(cls, block_id: str) -> str:
        return f"{cls.BLOCKS}/{block_id}/children"

    @classmethod
    def search(cls) -> str:
        return cls.SEARCH
