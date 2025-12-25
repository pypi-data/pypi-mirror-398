import datetime

from .time_filter import TimeFilter


def test__time_filter(freezer):
    tf = TimeFilter(day=datetime.date(1992, 5, 13))

    assert tf.to_dict() == {
        "day": datetime.date(1992, 5, 13),
        "hour_min": None,
        "hour_max": None,
    }

    freezer.move_to("1989-02-02")

    assert TimeFilter.default().to_dict() == {
        "day": datetime.date(1989, 2, 1),
        "hour_min": 0,
        "hour_max": 23,
    }
