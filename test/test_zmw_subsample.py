import falcon_kit.mains.zmw_subsample as mod
import functools
import helpers
import pytest
import os
import io
import json

import random

RANDOM_SEED = 12345

tests_strategy_random = [
    {   # Test empty input.
        'input_data': '',
        'coverage': 1,
        'genome_size': 1,
        'strategy': mod.STRATEGY_RANDOM,

        'exp_success': True,
        'exp_whitelist': '[]',
        'exp_throw': '',
    },
    {   # Test on an input with 1 subreads.
       'input_data': """\
synthetic/1\t28\t28\t1
""",
        'coverage': 1,
        'genome_size': 2,
        'strategy': mod.STRATEGY_RANDOM,

        'exp_success': True,
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': '',
    },
    {   # Test on the same input with 2 subreads, but with an empty line to skip.
       'input_data': """\
synthetic/1\t28\t28\t1
synthetic/2\t4\t4\t1
""",
        'coverage': 1,
        'genome_size': 2,
        'strategy': mod.STRATEGY_RANDOM,

        'exp_success': True,
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': '',
    },
    {   # Test on duplicate input sequences. This should throw.
       'input_data': """\
synthetic/1\t28\t28\t1
synthetic/2\t4\t4\t1
synthetic/1\t28\t28\t1
""",
        'coverage': 1,
        'genome_size': 2,
        'strategy': mod.STRATEGY_RANDOM,

        'exp_success': False,
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': '',
    },
    {   # Test a more complex input of several files, and multiple subreads per ZMW.
       'input_data': """\
synthetic/1\t9\t24\t3
synthetic/2\t21\t98\t5
synthetic/3\t9\t9\t1
synthetic/4\t15\t15\t1
synthetic/5\t20\t20\t1
""",
        'coverage': 3,
        'genome_size': 10,
        'strategy': mod.STRATEGY_RANDOM,

        'exp_success': True,
        'exp_whitelist': '["synthetic/2", "synthetic/3", "synthetic/5"]',
        'exp_throw': '',
    },
]

tests_strategy_longest = [
    {
        'input_data': tests_strategy_random[0]['input_data'],
        'coverage': tests_strategy_random[0]['coverage'],
        'genome_size': tests_strategy_random[0]['genome_size'],
        'strategy': mod.STRATEGY_LONGEST,
        'exp_success': tests_strategy_random[0]['exp_success'],
        'exp_whitelist': '[]',
        'exp_throw': tests_strategy_random[0]['exp_throw'],
    },
    {
        'input_data': tests_strategy_random[1]['input_data'],
        'coverage': tests_strategy_random[1]['coverage'],
        'genome_size': tests_strategy_random[1]['genome_size'],
        'strategy': mod.STRATEGY_LONGEST,
        'exp_success': tests_strategy_random[1]['exp_success'],
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': tests_strategy_random[1]['exp_throw'],
    },
    {
        'input_data': tests_strategy_random[2]['input_data'],
        'coverage': tests_strategy_random[2]['coverage'],
        'genome_size': tests_strategy_random[2]['genome_size'],
        'strategy': mod.STRATEGY_LONGEST,
        'exp_success': tests_strategy_random[2]['exp_success'],
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': tests_strategy_random[2]['exp_throw'],
    },
    {
        'input_data': tests_strategy_random[3]['input_data'],
        'coverage': tests_strategy_random[3]['coverage'],
        'genome_size': tests_strategy_random[3]['genome_size'],
        'strategy': mod.STRATEGY_LONGEST,
        'exp_success': tests_strategy_random[3]['exp_success'],
        'exp_whitelist': '["synthetic/1"]',
        'exp_throw': tests_strategy_random[3]['exp_throw'],
    },
    {
        'input_data': tests_strategy_random[4]['input_data'],
        'coverage': tests_strategy_random[4]['coverage'],
        'genome_size': tests_strategy_random[4]['genome_size'],
        'strategy': mod.STRATEGY_LONGEST,
        'exp_success': tests_strategy_random[4]['exp_success'],
        'exp_whitelist': '["synthetic/2", "synthetic/5"]',
        'exp_throw': tests_strategy_random[4]['exp_throw'],
    },
]

def check_run(tmpdir, input_data, coverage, genome_size, strategy, exp_success, exp_whitelist, exp_throw):
    strategy_func = mod.STRATEGY_TYPE_TO_FUNC[strategy]
    random.seed(RANDOM_SEED)

    fp_in = io.StringIO(input_data)
    if exp_success:
        zmws_whitelist, _, _ = mod.run(fp_in, coverage, genome_size, strategy_func)
        assert sorted(json.loads(exp_whitelist)) == sorted(zmws_whitelist)
    else:
        with pytest.raises(Exception):
            zmws_whitelist, _, _ = mod.run(fp_in, coverage, genome_size, strategy_func)


def check_main(tmpdir, input_data, coverage, genome_size, strategy, exp_success, exp_whitelist, exp_throw):
    mod.sys.stdin = io.StringIO(input_data)

    out_fn = tmpdir.join('out.whitelist.json')
    random.seed(RANDOM_SEED)

    argv = ['prog', '--strategy', strategy,
            '--coverage', str(coverage),
            '--genome-size', str(genome_size),
            '--random-seed', str(RANDOM_SEED),
            str(out_fn)
            ]

    if exp_success:
        mod.main(argv)
        result_whitelist = open(str(out_fn)).read()
        assert sorted(json.loads(exp_whitelist)) == sorted(json.loads(result_whitelist))
    else:
        with pytest.raises(Exception):
            mod.main(argv)

@pytest.mark.parametrize('test_data', tests_strategy_random)
def test_run_strategy_random(tmpdir, test_data):
    check_run(tmpdir, **test_data)

@pytest.mark.parametrize('test_data', tests_strategy_longest)
def test_run_strategy_longest(tmpdir, test_data):
    check_run(tmpdir, **test_data)

@pytest.mark.parametrize('test_data', tests_strategy_random)
def test_main_random(tmpdir, test_data):
    check_main(tmpdir, **test_data)

@pytest.mark.parametrize('test_data', tests_strategy_longest)
def test_main_longest(tmpdir, test_data):
    check_main(tmpdir, **test_data)

def test_help():
    try:
        mod.main(['prog', '--help'])
    except SystemExit:
        pass
