from pyvoicing import Interval


def test_interval_add_subtract():
    i = Interval("M3")
    j = Interval(2)
    assert i.add(j).distance == 6
    assert i.subtract("m2").distance == 3
