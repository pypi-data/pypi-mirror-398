class ConfluenceEndpointFactory:
    """
    Confluence rest api v2 endpoint factory.
    https://developer.atlassian.com/cloud/confluence/rest/v2/intro/#about
    """

    API = "wiki/api/v2/"
    DATABASE = "databases"
    FOLDERS = "folders"
    PAGES = "pages"
    SPACES = "spaces"
    USERS = "users-bulk"

    @classmethod
    def database(cls, database_id: str) -> str:
        """
        Endpoint to fetch a database by id.
        More: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-database/#api-databases-id-get
        """
        return f"{cls.API}{cls.DATABASE}/{database_id}"

    @classmethod
    def folder(cls, folder_id: str) -> str:
        """
        Endpoint to fetch a folder by id.
        More: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-folder/#api-folders-id-get
        """
        return f"{cls.API}{cls.FOLDERS}/{folder_id}"

    @classmethod
    def pages(cls, space_id: str) -> str:
        """
        Endpoint to fetch all pages in the given space.
        More: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-page/#api-spaces-id-pages-get
        """
        return f"{cls.API}{cls.SPACES}/{space_id}/{cls.PAGES}?body-format=atlas_doc_format"

    @classmethod
    def spaces(cls) -> str:
        """
        Endpoint to fetch all spaces.
        https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-space/#api-spaces-get
        """
        return f"{cls.API}{cls.SPACES}"

    @classmethod
    def users(cls) -> str:
        """
        Endpoint to fetch all user.
        More: https://developer.atlassian.com/cloud/confluence/rest/v2/api-group-user/#api-users-bulk-post
        """
        return f"{cls.API}{cls.USERS}"
