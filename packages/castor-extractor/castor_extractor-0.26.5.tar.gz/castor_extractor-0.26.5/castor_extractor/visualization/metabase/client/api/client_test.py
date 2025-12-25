from .client import CARDS_KEY, CARDS_KEY_DEPRECATED, ApiClient


def test__dashboard_cards():
    for key in (CARDS_KEY, CARDS_KEY_DEPRECATED):
        dashboards = [
            {
                "name": "dash_1",
                key: ["card_1", "card_2"],
            },
            {
                "name": "dash_2",
                key: ["card_3"],
            },
            {
                "name": "dash_3",
            },
        ]

        cards = list(ApiClient._dashboard_cards(dashboards))
        assert cards == ["card_1", "card_2", "card_3"]
