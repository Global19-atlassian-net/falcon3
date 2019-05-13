import falcon_kit.mains.zmw_collect as mod
import functools
import helpers
import pytest
import io
import falcon_kit.mains.fasta_filter as fasta_filter
import sys

test_data = [
    {   # Test empty input.
        'input_data': '',
        'exp_out': '',
    },
    {   # Test on an input with 2 subreads.
       'input_data': """\
>synthetic/1/500_1000
GATTACAGATTACAGATTACAGATTACA
>synthetic/2/0_4
ACTG
""",
        'exp_out': """\
synthetic/1\t28\t28\t1
synthetic/2\t4\t4\t1
"""
    },
    {   # Test a more complex input, and multiple subreads per ZMW.
       'input_data': """\
>synthetic/1/0_5
ACGTAACGTA
>synthetic/1/10_14
ACGTACGTA
>synthetic/1/14_15
ACGTA
>synthetic/2/0_500
GATTACAGATTACA
>synthetic/2/0_500
GATTACAGATTACAGATTACAGATTACA
>synthetic/2/0_500
GATTACAGATTACAGATTACA
>synthetic/2/500_1000
GATTACAGATTACAGATTACAGATTACA
>synthetic/2/0_500
GATTACA
>synthetic/3/0_8
ACGTACGTA
>synthetic/4/0_8
ACGTACGTAAAAAAA
>synthetic/5/0_8
ACGTACGTAAAAAAAAAAAA
""",
        'exp_out': """\
synthetic/1\t9\t24\t3
synthetic/2\t21\t98\t5
synthetic/3\t9\t9\t1
synthetic/4\t15\t15\t1
synthetic/5\t20\t20\t1
"""
    },
]

def check_run(capsys, input_data, exp_out):
    fp_in = io.StringIO(input_data)
    fp_out = io.StringIO()
    yield_zmw_tuple_func = fasta_filter.yield_zmwtuple(mod.yield_record(fp_in), whitelist_set=None, store_record=False)
    mod.run(fp_out, yield_zmw_tuple_func)
    assert fp_out.getvalue() == exp_out

def check_main(capsys, input_data, exp_out):
    mod.sys.stdin = io.StringIO(input_data)
    argv = ['prog']
    mod.main(argv)
    out, err = capsys.readouterr()
    assert(out == exp_out)

@pytest.mark.parametrize('test_data', test_data)
def test_run(capsys, test_data):
    check_run(capsys, **test_data)

@pytest.mark.parametrize('test_data', test_data)
def test_main(capsys, test_data):
    check_main(capsys, **test_data)

def test_help():
    try:
        mod.main(['prog', '--help'])
    except SystemExit:
        pass
