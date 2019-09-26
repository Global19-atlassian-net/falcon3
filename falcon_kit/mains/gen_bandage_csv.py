import argparse
import os
import sys

from falcon_kit.fc_asm_graph import AsmGraph
from falcon_kit.FastaReader import FastaReader
from falcon_kit.gfa_graph import *

def run(fp_out, fp_in, collected_gfa):
    gfa_graph = deserialize_gfa(fp_in)
    gfa_graph.write_bandage_csv(fp_out)

class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def parse_args(argv):
    parser = argparse.ArgumentParser(description="Generates the Bandage CSV file with node colors, from FALCON's assembly.",
                                     formatter_class=HelpF)
    parser.add_argument('collected_gfa', type=str, default='asm.gfa.json',
                        help='Path to the file with collected and formatted data for generating the GFA')
    args = parser.parse_args(argv[1:])
    return args

def main(argv=sys.argv):
    args = parse_args(argv)

    with open(args.collected_gfa, 'r') as fp_in:
        run(sys.stdout, fp_in, **vars(args))

if __name__ == '__main__':  # pragma: no cover
    main()
