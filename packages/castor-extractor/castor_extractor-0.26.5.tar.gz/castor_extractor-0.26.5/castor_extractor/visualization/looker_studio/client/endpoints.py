class LookerStudioAPIEndpoint:
    BASE_PATH = "https://datastudio.googleapis.com"

    @classmethod
    def search(cls) -> str:
        """
        Search a user's assets.
        See https://developers.google.com/looker-studio/integrate/api/reference/assets/search
        """
        return f"{cls.BASE_PATH}/v1/assets:search"

    @classmethod
    def permissions(cls, asset_name: str) -> str:
        """
        Get the permissions of an asset. The user must be the owner of the asset.
        See https://developers.google.com/looker-studio/integrate/api/reference/permissions/get
        """
        return f"{cls.BASE_PATH}/v1/assets/{asset_name}/permissions"
