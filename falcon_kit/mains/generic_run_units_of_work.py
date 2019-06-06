from multiprocessing import cpu_count
import argparse
import collections
import glob
import logging
import os
import sys
import pypeflow.do_task

from ..multiproc import Pool
from .. import io
from ..util.io import run_func

LOG = logging.getLogger()


# Here is some stuff basically copied from pypeflow.sample_tasks.py.
def validate(bash_template, inputs, outputs, parameterss):
    LOG.info('bash_script_from_template({}\n\tinputs={!r},\n\toutputs={!r})'.format(
        bash_template, inputs, outputs))
    def validate_dict(mydict):
        "Python identifiers are illegal as keys."
        try:
            collections.namedtuple('validate', list(mydict.keys()))
        except ValueError as exc:
            LOG.exception('Bad key name in task definition dict {!r}'.format(mydict))
            raise
    validate_dict(inputs)
    validate_dict(outputs)
    validate_dict(parameterss)

def update_values_rel_to(things, dn):
    for key, val in list(things.items()):
        try:
            if not os.path.isabs(val):
                things[key] = os.path.normpath(os.path.join(dn, val))
        except Exception:
            # Probably just not a string. But could be str, unicode, ...
            pass

def run_uow(uow_dir, script, inputs, outputs, params):
        io.rmdir(uow_dir)
        io.mkdirs(uow_dir)
        with io.cd(uow_dir):
            pypeflow.do_task.run_bash(script, inputs, outputs, params)
            resolved_outputs = {k: os.path.abspath(v) for k,v in list(outputs.items())}
        return {k: os.path.join('.', os.path.relpath(v)) for k,v in list(resolved_outputs.items())}
        # Must be relative to this dir.
        # (We assume outputs are under the current directory.)
        # The reason for the './' prefix? So we can substitute in CWD later,
        # in case we ran in /tmp. This also helps the pbsmrtpipe "gatherer".

        #wildcards_str = '_'.join(w for w in itervalues(job['wildcards']))
        #job_name = 'job{}'.format(wildcards_str)
        #for (output_name, output_fn) in viewitems(outputs):
        #    giname = '{}_{}'.format(job_name, output_name)
        #    gather_inputs[giname] = output_fn

def yield_uows(units_of_work_fn, bash_template_fn, nproc):
    units_of_work_fn = os.path.realpath(units_of_work_fn)
    script = open(bash_template_fn).read()
    uows = io.deserialize(units_of_work_fn)

    for i, uow in enumerate(uows):
        uow_dir = 'uow-{:02d}'.format(i)
        rel_units_of_work_dn = os.path.normpath(os.path.relpath(os.path.dirname(units_of_work_fn), uow_dir))
        job = uow
        inputs = job['input']
        update_values_rel_to(inputs, rel_units_of_work_dn)
        outputs = job['output'] # assumed to be relative to run-dir
        params = dict(job['params'])
        params['pypeflow_nproc'] = nproc
        # We could also verify that any nproc from a splitter (which was a hint for splitting)
        # matches pypeflow_nproc.

        #params.update({k: v for (k, v) in viewitems(job['wildcards'])}) # include expanded wildcards
        LOG.debug('----')
        LOG.debug('INPUT:{}'.format(inputs))
        LOG.debug('OUTPUT:{}'.format(outputs))
        LOG.debug('PARAMS:{}'.format(params))
        #uow_dirs.append(uow_dir)
        yield (run_uow, uow_dir, script, inputs, outputs, params)

def run(bash_template_fn, units_of_work_fn, nproc, nproc_per_uow,
        results_fn):
    if nproc_per_uow < 1:
        LOG.error('nproc_per_uow == {} < 1; using 1 instead'.format(nproc_per_uow))
        nproc_per_uow = 1
    inputs = list(yield_uows(units_of_work_fn, bash_template_fn, nproc=nproc_per_uow))

    njobs = (nproc // nproc_per_uow) if (nproc > 0) else 0
    LOG.info('For multiprocessing, parallel njobs={} (cpu_count={}, nproc={}, nproc_per_uow={})'.format(
        njobs, cpu_count(), nproc, nproc_per_uow))

    results = list()

    def Start():
        LOG.info('Started a worker in {} from parent {}'.format(
            os.getpid(), os.getppid()))
    exe_pool = Pool(njobs, initializer=Start)
    try:
        LOG.info('running {} units-of-work, {} at a time...'.format(len(inputs), njobs))
        for res in exe_pool.imap(run_func, inputs):
            results.append(res)
        LOG.info('finished {} units-of-work'.format(len(inputs)))
    except:
        LOG.exception('failed multiprocessing')
        exe_pool.terminate()
        raise

    io.serialize(results_fn, results)


class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


def parse_args(argv):
    description = 'Run a bash script once for each unit-of-work, in its own sub-dir.'
    epilog = 'For now, runs will be in series, since we do not know how many processors we can use.'
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=HelpF,
    )
    parser.add_argument(
        '--nproc', type=int, default=0,
        help='Number of processors allowed to be used (0 => avoid multiprocessing module)')
    parser.add_argument(
        '--nproc-per-uow', type=int, default=1,
        help='Number of processors expected to be used by each units-of-work (num parallel procs will be nproc/nproc-per-uow)')
    parser.add_argument(
        '--bash-template-fn',
        help='Input. Template of bash script to run on each unit-of-work, with snakemake-style substitutions.')
    parser.add_argument(
        '--units-of-work-fn',
        help='Input. JSON list of records of unit-of-work. Each record is a dict of input, output, and params (snakemake-style).')
    parser.add_argument(
        '--results-fn',
        help='Output. JSON list of result records.')
    args = parser.parse_args(argv[1:])
    return args


def main(argv=sys.argv):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    run(**vars(args))


if __name__ == '__main__':  # pragma: no cover
    main()
