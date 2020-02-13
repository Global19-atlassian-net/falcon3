"""
Takes a CSV file with a list of ZMWs with their corresponding lengths.
The script outputs a JSON file with a whitelist of ZMWs selected by a given
strategy (random, longest, etc.) and desired coverage of a genome.
Author: Ivan Sovic
"""
import falcon_kit.util.system as system

import falcon_kit.io as io

import os
import sys
import argparse
import logging
import contextlib
import itertools
import random
import json

LOG = logging.getLogger()

STRATEGY_RANDOM = 'random'
STRATEGY_LONGEST = 'longest'

def strategy_func_random(zmws):
    """
    >>> random.seed(12345); strategy_func_random([])
    []
    >>> random.seed(12345); strategy_func_random([('synthetic/1', 9)])
    [('synthetic/1', 9)]
    >>> random.seed(12345); strategy_func_random([('synthetic/1', 9), ('synthetic/2', 21), ('synthetic/3', 9), ('synthetic/4', 15), ('synthetic/5', 20)])
    [('synthetic/5', 20), ('synthetic/3', 9), ('synthetic/2', 21), ('synthetic/1', 9), ('synthetic/4', 15)]
    """
    ret = list(zmws)
    random.shuffle(ret)
    return ret

def strategy_func_longest(zmws):
    """
    >>> strategy_func_longest([])
    []
    >>> strategy_func_longest([('synthetic/1', 9)])
    [('synthetic/1', 9)]
    >>> strategy_func_longest([('synthetic/1', 9), ('synthetic/2', 21), ('synthetic/3', 9), ('synthetic/4', 15), ('synthetic/5', 20)])
    [('synthetic/2', 21), ('synthetic/5', 20), ('synthetic/4', 15), ('synthetic/1', 9), ('synthetic/3', 9)]
    """
    return sorted(zmws, key = lambda x: x[1], reverse = True)

STRATEGY_TYPE_TO_FUNC = {   STRATEGY_RANDOM: strategy_func_random,
                            STRATEGY_LONGEST: strategy_func_longest,
                        }

def select_zmws(zmws, min_requested_bases):
    """
    >>> select_zmws([], 0)
    ([], 0)
    >>> select_zmws([], 10)
    ([], 0)
    >>> select_zmws([('zmw/1', 1), ('zmw/2', 2), ('zmw/3', 5), ('zmw/4', 7), ('zmw/5', 10), ('zmw/6', 15)], 10)
    (['zmw/1', 'zmw/2', 'zmw/3', 'zmw/4'], 15)
    >>> select_zmws([('zmw/1', 1), ('zmw/2', 2), ('zmw/3', 5), ('zmw/4', 7), ('zmw/5', 10), ('zmw/6', 15)], 20)
    (['zmw/1', 'zmw/2', 'zmw/3', 'zmw/4', 'zmw/5'], 25)
    >>> select_zmws([('zmw/1', 1), ('zmw/1', 2), ('zmw/1', 5), ('zmw/1', 7), ('zmw/1', 10), ('zmw/1', 15)], 20)
    (['zmw/1', 'zmw/1', 'zmw/1', 'zmw/1', 'zmw/1'], 25)
    """
    # Select the first N ZMWs which sum up to the desired coverage.
    num_bases = 0
    subsampled_zmws = []
    for zmw_name, seq_len in zmws:
        num_bases += seq_len
        subsampled_zmws.append(zmw_name)
        if num_bases >= min_requested_bases:
            break
    return subsampled_zmws, num_bases

def calc_stats(total_unique_molecular_bases, total_bases, output_bases, genome_size, coverage):
    """
    >>> calc_stats(0, 0, 0, 0, 0) == \
    {'genome_size': 0, 'coverage': 0, 'total_bases': 0, 'total_unique_molecular_bases': 0, \
    'output_bases': 0, 'unique_molecular_avg_cov': 0.0, 'output_avg_cov': 0.0, 'total_avg_cov': 0.0}
    True
    >>> calc_stats(10000, 100000, 2000, 1000, 2) == \
    {'genome_size': 1000, 'coverage': 2, 'total_bases': 100000, 'total_unique_molecular_bases': 10000, \
    'output_bases': 2000, 'unique_molecular_avg_cov': 10.0, 'output_avg_cov': 2.0, 'total_avg_cov': 100.0}
    True
    """
    unique_molecular_avg_cov = 0.0 if genome_size == 0 else float(total_unique_molecular_bases) / float(genome_size)
    total_avg_cov = 0.0 if genome_size == 0 else float(total_bases) / float(genome_size)
    output_avg_cov = 0.0 if genome_size == 0 else float(output_bases) / float(genome_size)

    ret = {
        'genome_size': genome_size,
        'coverage': coverage,
        'total_bases': total_bases,
        'total_unique_molecular_bases': total_unique_molecular_bases,
        'output_bases': output_bases,
        'total_avg_cov': total_avg_cov,
        'unique_molecular_avg_cov': unique_molecular_avg_cov,
        'output_avg_cov': output_avg_cov,
    }

    return ret

def collect_zmws(fp_in):
    zmws = []
    seen_zmws = set()
    unique_molecular_size = 0
    total_size = 0
    for line in fp_in:
        sl = line.strip().split()
        movie_zmw, zmw_median_len, zmw_total_len, zmw_num_passes = sl[0], int(sl[1]), int(sl[2]), int(sl[3])
        assert movie_zmw not in seen_zmws, 'Duplicate ZMWs detected in the input. Offender: "{}".'.format(movie_zmw)
        unique_molecular_size += zmw_median_len
        total_size += zmw_total_len
        zmws.append((movie_zmw, zmw_median_len))
        seen_zmws.add(movie_zmw)
    return zmws, unique_molecular_size, total_size

def run(fp_in, coverage, genome_size, strategy_func):
    zmws, total_unique_molecular_bases, total_bases = collect_zmws(fp_in)
    zmws = strategy_func(zmws)
    subsampled_zmws, output_bases = select_zmws(zmws, coverage * genome_size)
    stats_dict = calc_stats(total_unique_molecular_bases, total_bases, output_bases, genome_size, coverage)
    return subsampled_zmws, zmws, stats_dict

class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Produces a list of ZMW where the median unique molecular "\
                                        "coverage sums up to the desired coverage of the given genome size, "\
                                        "given a specified subsampling strategy. Input is a TSV passed via stdin. "\
                                        "Output is to stdout.",
                                        formatter_class=HelpF)
    parser.add_argument('--strategy', type=str, default='random',
                        help='Subsampling strategy: random, longest')
    parser.add_argument('--coverage', type=float, default=60,
                        help='Desired coverage for subsampling.')
    parser.add_argument('--genome-size', type=float, default=0,
                        help='Genome size estimate of the input dataset.', required=True)
    parser.add_argument('--random-seed', type=int, default=12345,
                        help='Seed value used for the random generator.', required=False)
    parser.add_argument('out_fn', type=str, default='zmw.whitelist.json',
                        help='Output JSON file with subsampled ZMWs.')
    args = parser.parse_args(argv[1:])
    return args

def main(argv=sys.argv):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    strategy_func = STRATEGY_TYPE_TO_FUNC[args.strategy]
    LOG.info('Using subsampling strategy: "{}"'.format(args.strategy))

    system.set_random_seed(args.random_seed)

    zmws_whitelist, zmws_all, stats_dict = run(
            sys.stdin, args.coverage, args.genome_size, strategy_func)

    io.serialize(args.out_fn, zmws_whitelist)

if __name__ == "__main__":  # pragma: no cover
    main(sys.argv)          # pragma: no cover
