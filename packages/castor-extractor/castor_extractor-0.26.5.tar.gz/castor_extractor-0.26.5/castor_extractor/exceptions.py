class NoDatabaseProvidedException(Exception):
    def __init__(self):
        super().__init__("""No database eligible for extraction.
If you are using the db_allow/db_block options, please make sure to use the correct case.
        """)


class TestConnectionException(Exception):
    def __init__(self, caused_by: Exception):
        super().__init__(f"Connection could not be verified: {caused_by}")
