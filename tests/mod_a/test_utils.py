from mod_a.utils import add


def test_work():
    """Tests the basic happy path."""
    assert add(4, 5) == 9
