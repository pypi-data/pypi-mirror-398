from .pagination import Pagination


def test_pagination():
    per_page = 20

    pagination = Pagination(per_page=per_page)

    assert pagination.number_results is None
    assert pagination.offset == 0

    pagination.increment_offset(per_page)
    assert pagination.offset == per_page
    assert pagination.needs_increment

    pagination.increment_offset(per_page)
    assert pagination.offset == per_page * 2
    assert pagination.needs_increment

    pagination.increment_offset(5)
    assert pagination.offset == per_page * 2 + 5
    assert not pagination.needs_increment
