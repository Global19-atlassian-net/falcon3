"""
Performs a single pass over an input FASTA (file or streamed), and collects
all ZMWs. For each ZMW it calculates the expected molecular size by picking
the internal median subread length.
The script writes one line per ZMW indicating:
movie_zmw median_insert_length total_insert_sum num_passes
Author: Ivan Sovic
"""
from falcon_kit.mains.fasta_filter import ZMWTuple

import falcon_kit.FastaReader as FastaReader
import falcon_kit.mains.fasta_filter as fasta_filter
import falcon_kit.io as io

import os
import sys
import argparse
import logging
import contextlib
import itertools

LOG = logging.getLogger()

def yield_record(fp_in):
    fasta_records = FastaReader.yield_fasta_record(fp_in, log=LOG.info)
    for record in fasta_records:
        yield record

def run(fp_out, yield_zmw_tuple_func):
    for zmw_id, zmw_subreads in itertools.groupby(yield_zmw_tuple_func, lambda x: x.zmw_id):
        zmw_subreads_list = list(zmw_subreads)
        zrec = fasta_filter.internal_median_zmw_subread(zmw_subreads_list)
        movie_zmw = zrec.movie_name + '/' + zrec.zmw_id
        zmw_unique_molecular_size = zrec.seq_len
        zmw_total_size = sum([zmw.seq_len for zmw in zmw_subreads_list])
        zmw_num_passes = len(zmw_subreads_list)
        fp_out.write('{}\t{}\t{}\t{}\n'.format(movie_zmw, zmw_unique_molecular_size, zmw_total_size, zmw_num_passes))

class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def parse_args(argv):
    parser = argparse.ArgumentParser(description="For a given streamed FASTA file, it collects all subreads per ZMW, "\
                                        "calculates the median insert size, and writes out a TSV file with base counts.",
                                        formatter_class=HelpF)
    args = parser.parse_args(argv[1:])
    return args

def main(argv=sys.argv):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)

    run(sys.stdout, fasta_filter.yield_zmwtuple(yield_record(sys.stdin), whitelist_set=None, store_record=False))

if __name__ == "__main__":  # pragma: no cover
    main(sys.argv)          # pragma: no cover
