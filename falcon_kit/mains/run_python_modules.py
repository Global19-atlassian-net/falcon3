import argparse
import logging
import importlib
import os
import sys
from . import (
        collect_pread_gfa, collect_contig_gfa,
        gen_gfa_v1,
        gen_gfa_v2,
        gen_bandage_csv,
)
LOG = logging.getLogger()

"""
    # Collect all info needed to format the GFA-1 and GFA-2 representations of
    # the assembly graphs.
    time python3 -m falcon_kit.mains.collect_pread_gfa >| asm.gfa.json
    time python3 -m falcon_kit.mains.collect_pread_gfa --add-string-graph >| sg.gfa.json
    time python3 -m falcon_kit.mains.collect_contig_gfa >| contig.gfa.json

    # Output the assembly pread graph.
    time python3 -m falcon_kit.mains.gen_gfa_v1 asm.gfa.json >| asm.gfa
    time python3 -m falcon_kit.mains.gen_gfa_v2 asm.gfa.json >| asm.gfa2
    time python3 -m falcon_kit.mains.gen_bandage_csv asm.gfa.json >| asm.csv

    # Output the string graph.
    time python3 -m falcon_kit.mains.gen_gfa_v1 sg.gfa.json >| sg.gfa
    time python3 -m falcon_kit.mains.gen_gfa_v2 sg.gfa.json >| sg.gfa2
    time python3 -m falcon_kit.mains.gen_bandage_csv sg.gfa.json >| sg.csv

    # Output the contig graph with associate contigs attached to each primary contig.
    time python3 -m falcon_kit.mains.gen_gfa_v2 contig.gfa.json >| contig.gfa2
"""

def run_line(line):
    parts = line.split()
    while parts:
        top = parts.pop(0)
        # if top == "time": We could time it here! TODO, maybe.
        if not top.startswith('python'):
            LOG.info("Skipping '{}' in '{}'".format(top, line))
        else:
            break
    else:
        raise Exception("No 'python' executable name found.")
    if not parts or not parts[0] == "-m":
        raise Exception("Expected line of form '... python3 -m ...'")
    parts.pop(0)
    if not parts or 'falcon_kit.mains.' not in parts[0]:
        raise Exception("Expected line of form '... python3 -m falcon_kit.mains.(foo) ...'")
    module = parts.pop(0)
    mod = importlib.import_module(module)

    LOG.info("module={}".format(module))
    LOG.debug("dir(module)={}".format(dir(mod)))

    stdout = None

    if len(parts) >= 2 and parts[-2].startswith('>'):
        redirector = parts[-2]
        out_fn = parts[-1]
        parts = parts[:-2]
        if redirector == ">>":
            LOG.info(" Appending ({}) to '{}'".format(redirector, out_fn))
            stdout = open(out_fn, 'a')
        else:
            LOG.info(" Writing ({}) to '{}'".format(redirector, out_fn))
            stdout = open(out_fn, 'w')
        sys.stdout = stdout

    #argv = [sys.executable] + parts
    argv = ['python3'] + parts
    LOG.info(" For '{}', ARGV={!r}".format(module, argv))

    mod.main(argv)

    if stdout:
        stdout.close() # in case we need to flush

def run(script_fn):
    with open(script_fn) as ifs:
        for line in ifs:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            argv = sys.argv
            stdin = sys.stdin
            stdout = sys.stdout
            try:
                run_line(line)
            except Exception:
                msg = "Line was:\n'{}'".format(line)
                LOG.fatal(msg)
                #LOG.exception(msg)
                #msg = "Running next lines anway ..."
                #LOG.warning(msg)
                raise # We could continue, but we will quit for simplicity.
            finally:
                sys.argv = argv
                sys.stdin = stdin
                sys.stdout = stdout

class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass

def parse_args(argv):
    epilog = """Example input:
python3 -m falcon_kit.mains.foo > stdout.txt
python3 -m falcon_kit.mains.bar --option arg1 arg2
...

Note: We are not trying to handle every possible use-case. This is meant to save start-up time.
"""
    parser = argparse.ArgumentParser(description="Run several python programs, without re-invoking python.",
                                     epilog=epilog,
                                     formatter_class=HelpF)
    parser.add_argument('script_fn', #type=str,
                        help='File containing lines of python module executions.')
    args = parser.parse_args(argv[1:])
    return args

def main(argv=sys.argv):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    run(**vars(args))

if __name__ == '__main__':  # pragma: no cover
    main()
