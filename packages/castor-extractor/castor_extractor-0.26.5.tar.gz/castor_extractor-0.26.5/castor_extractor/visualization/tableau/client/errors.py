class TableauApiError(ValueError):
    def __init__(self, error: str):
        super().__init__(f"Tableau API returned the following error: {error}")


class TableauApiTimeout(ValueError):
    def __init__(self, error: str):
        super().__init__(f"Tableau API returned a timeout error: {error}")
