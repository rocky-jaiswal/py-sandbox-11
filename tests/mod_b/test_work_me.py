from mod_b.work_me import work


def test_work():
    """Tests the basic happy path."""
    assert work(2, 5) == 7
