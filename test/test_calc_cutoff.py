import falcon_kit.mains.calc_cutoff as mod
import helpers
import json
import os.path
import pytest


def test_help():
    try:
        mod.main(['prog', '--help'])
    except SystemExit:
        pass

# Note: genome_size==1 makes math easy.


def test_calc_cutoff(capsys):
    partial_capture_fn = os.path.join(
        helpers.get_test_data_dir(), 'calc_cutoff/partial_capture.txt')
    assert os.path.exists(partial_capture_fn)
    mod.main('prog --coverage 14 1 {}'.format(partial_capture_fn).split())
    out, err = capsys.readouterr()
    assert out == '2'
    assert err == ''


expected_err0 = """\
Not enough reads available for desired genome coverage (bases needed=23 > actual=22)
"""
expected_err1 = """\
User-provided genome_size: 1
Desired coverage: 23.0
"""


def test_calc_cutoff_err():
    partial_capture_fn = os.path.join(
        helpers.get_test_data_dir(), 'calc_cutoff/partial_capture.txt')
    assert os.path.exists(partial_capture_fn)
    with pytest.raises(Exception) as excinfo:
        mod.main('prog --coverage 23 1 {}'.format(partial_capture_fn).split())
    #assert expected_err0 in str(excinfo.value)
    assert expected_err1 in str(excinfo.value)


def test_calc_cutoff_errfile(monkeypatch, tmpdir):
    fn = str(tmpdir.mkdir('tmp').join('errfile'))
    monkeypatch.setenv('PBFALCON_ERRFILE', fn)
    partial_capture_fn = os.path.join(
        helpers.get_test_data_dir(), 'calc_cutoff/partial_capture.txt')
    assert os.path.exists(partial_capture_fn)
    with pytest.raises(Exception) as excinfo:
        mod.main('prog --coverage 23 1 {}'.format(partial_capture_fn).split())
    #assert expected_err0 in str(excinfo.value)
    assert expected_err1 in str(excinfo.value)
    assert expected_err0 in open(fn).read()
    assert expected_err1 in open(fn).read()

    # Also check new 'alarms.json'
    encoded0 = json.dumps(expected_err0)[1:-1]  # actually just escapes the newlines
    encoded1 = json.dumps(expected_err1)[1:-1]
    assert encoded0 in open('alarms.json').read()
    assert encoded1 in open('alarms.json').read()
