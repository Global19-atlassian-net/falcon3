from .. import functional as f
from ..util import alarm
import argparse
import os
import sys


def run(genome_size, coverage, capture):
    target = int(genome_size * coverage)
    def yield_capture():
        # This generator ensures that our file is closed at end-of-program.
        if capture != '-':
            with open(capture) as sin:
                yield sin
        else:
            yield sys.stdin
    for sin in yield_capture():
        stats = sin.read()
    try:
        cutoff = f.calc_cutoff(target, stats)
    except Exception as e:
        msg = 'User-provided genome_size: {}\nDesired coverage: {}\n'.format(
            genome_size, coverage)
        raise Exception(msg) from e
    sys.stdout.write(str(cutoff))


def main(argv=sys.argv):
    import argparse

    description = """
Given the result of 'DBstats -u -b1' on stdin,
print the lowest read-length required for sufficient coverage of the genome
(i.e. 'length_cutoff').
"""
    epilog = """
This is useful when length_cutoff is not provided but the genome-size
can be estimated. The purpose is to *reduce* the amount of data seen by
DALIGNER, since otherwise it will miss many alignments when it
encounters resource limits.

Note: If PBFALCON_ERRFILE is defined (and its directory is writable),
we will write errors there in addition to stderr.
"""
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--coverage', type=float, default=20,
                        help='Desired coverage ratio (i.e. over-sampling)')
    parser.add_argument('genome_size', type=int,
                        help='Estimated number of bases in genome. (haploid?)')
    parser.add_argument('capture',  # default='-', # I guess default is not allowed for required args.
                        help='File with captured output of DBstats. (Otherwise, stdin.)')
    args = parser.parse_args(argv[1:])

    try:
        run(**vars(args))
    except Exception as e:
        alarm.alarm(e)
        raise


if __name__ == "__main__":
    main(sys.argv)
