from .smart_pagination import SmartPagination


def test_smart_pagination():
    p = SmartPagination(initial_page_size=200)

    assert p.page_size == 200
    assert p._reduced_page_size is None
    assert p._counter is None
    assert p._slow_mode is False

    p.reduce_page_size()  # 200 → 20
    assert p.page_size == 20
    assert p._counter == 0
    assert p._slow_mode is True

    p.next()  # counter = 20
    assert p._counter == 20

    p.reduce_page_size()  # 20 → 2
    assert p.page_size == 2
    assert p._counter == 20  # stays 20 because we're already in slow mode
    assert p._slow_mode is True

    p.reset()

    # manual reset
    assert p._slow_mode is False
    assert p._counter is None
    assert p._reduced_page_size is None
    assert p.page_size == 200

    # running in full-speed mode
    p.next()
    p.next()
    p.next()

    assert p._slow_mode is False
    assert p._counter is None
    assert p._reduced_page_size is None
    assert p.page_size == 200

    # simulating a slow-mode once again
    p.reduce_page_size()
    assert p._slow_mode is True
    assert p._counter == 0
    assert p._reduced_page_size == 20
    assert p.page_size == 20

    for _ in range(9):
        p.next()

    # counter = 180 / 200 => still in slow mode
    assert p._slow_mode is True

    # counter reaches 200 / 200 => should get back to full speed
    p.next()
    assert p._slow_mode is False
    assert p._counter is None
    assert p._reduced_page_size is None
    assert p.page_size == 200
