
import falcon_kit.mains.ovlp_filter as mod


def assert_equal(expected, got):
    assert expected == got


def test_help():
    """Can be called 'pytest' or something, but reports
    proper help message otherwise.
    """
    try:
        mod.main(['prog', '--help'])
    except SystemExit:
        pass


def test_several():
    expected = {"ignore": set(['000000001', '000000002', '000000017', '000000028',  '001052514', '001071196']),
        "contained": set([('000797987')])}
    data = """\
000000000 000000001 -1807 100.00 0 181 1988 1988 0 0 1807 1989 overlap
000000000 000000002 -823 99.88 0 0 823 1988 0 1166 1989 1989 overlap
000000000 000000003 -50 99.94 0 0 50 1988 0 0 50 50 overlap
000000000 000000017 -61 98.36 0 0 61 1988 0 1928 1989 1989 overlap
000000000 000000028 -1952 79.95 0 0 1952 1988 0 37 1989 1989 overlap
000000001 000000000 -1807 100.00 0 0 1807 1989 0 181 1988 1988 overlap
000000001 000000002 -642 99.84 0 0 642 1989 0 1347 1989 1989 overlap
000000002 000000000 -823 99.88 0 1166 1989 1989 0 0 823 1988 overlap
000000002 000000001 -642 99.84 0 1347 1989 1989 0 0 642 1989 overlap
000000003 000000000 -50 99.94 0 0 50 50 0 0 50 1988 overlap
000000017 000000000 -61 98.36 0 1928 1989 1989 0 0 61 1988 overlap
000000028 000000000 -1952 79.95 0 37 1989 1989 0 0 1952 1988 overlap
000019569 000797987 -9661 99.658 0 333 9967 9984 1 0 9661 9661 contains
000019569 001052514 -1340 99.702 0 0 1341 9984 1 0 1340 10656 overlap
000019569 001071196 -6060 99.160 0 3897 9984 9984 0 0 6060 9472 overlap
000797987 000019569 -9634 99.658 0 0 9661 9661 1 333 9967 9984 contained
001052514 000019569 -1341 99.702 0 0 1340 10656 1 0 1341 9984 overlap
001071196 000019569 -6060 99.160 0 6060 9472 0 0 3897 9984 9984 overlap
"""
    readlines = data.strip().splitlines
    max_diff, max_ovlp, min_ovlp, min_len = 1000, 1000, 1, 1
    got = mod.filter_stage1(readlines, max_diff, max_ovlp, min_ovlp, min_len)
    assert_equal(expected, got)


def test_one_not_ignored():
    """This is the same as a line dropped in the earlier test.
    """
    expected = {"ignore": set(), "contained": set()}
    data = """\
000000003 000000000 -50 99.94 0 0 50 50 0 0 50 1988 overlap
"""
    readlines = data.strip().splitlines
    max_diff, max_ovlp, min_ovlp, min_len = 1000, 1000, 1, 1
    got = mod.filter_stage1(readlines, max_diff, max_ovlp, min_ovlp, min_len)
    assert_equal(expected, got)


def test_one_line_ignored():
    """This is the same as a line kept in the earlier test.
    """
    expected = {"ignore": set(['000000017']), "contained": set()}
    data = """\
000000017 000000000 -61 98.36 0 1928 1989 1989 0 0 61 1988 overlap
"""
    readlines = data.strip().splitlines
    max_diff, max_ovlp, min_ovlp, min_len = 1000, 1000, 1, 1
    got = mod.filter_stage1(readlines, max_diff, max_ovlp, min_ovlp, min_len)
    assert_equal(expected, got)


def test_empty():
    expected = {"ignore": set(), "contained": set()}
    data = """\
"""
    readlines = data.strip().splitlines
    max_diff, max_ovlp, min_ovlp, min_len = 1000, 1000, 1, 1
    got = mod.filter_stage1(readlines, max_diff, max_ovlp, min_ovlp, min_len)
    assert_equal(expected, got)
