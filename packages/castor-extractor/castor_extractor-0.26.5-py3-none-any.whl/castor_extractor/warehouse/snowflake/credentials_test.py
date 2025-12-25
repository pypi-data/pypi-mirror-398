import pytest

from .credentials import SnowflakeCredentials


def test_SnowflakeCredentials():
    assert SnowflakeCredentials(
        account="snowwhite",
        password="hammer",
        user="dwarf",
    )

    assert SnowflakeCredentials(
        account="snowwhite",
        private_key="pickaxe",
        user="dwarf",
    )

    with pytest.raises(ValueError):
        SnowflakeCredentials(
            account="snowwhite",
            password="hammer",
            private_key="pickaxe",
            user="dwarf",
        )

    with pytest.raises(ValueError):
        SnowflakeCredentials(
            account="snowwhite",
            user="dwarf",
        )
