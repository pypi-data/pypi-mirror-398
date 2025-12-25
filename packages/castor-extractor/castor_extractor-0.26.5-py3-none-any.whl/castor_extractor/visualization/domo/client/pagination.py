from dataclasses import dataclass

PER_PAGE = 50  # maximum value accepted by DOMO is 50


@dataclass
class Pagination:
    """Handles pagination within DOMO Api"""

    number_results: int | None = None
    offset: int = 0
    per_page: int = PER_PAGE
    should_stop: bool = False

    @property
    def needs_increment(self) -> bool:
        if self.number_results is None:
            return True  # first iteration

        if (self.number_results < self.per_page) or self.should_stop:
            return False

        return True

    @property
    def params(self) -> dict:
        return {"offset": self.offset, "limit": self.per_page}

    def increment_offset(self, number_results: int) -> None:
        self.offset += number_results
        self.number_results = number_results
