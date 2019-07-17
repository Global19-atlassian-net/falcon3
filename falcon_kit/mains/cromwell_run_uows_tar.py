from multiprocessing import cpu_count
import argparse
import collections
import glob
import logging
import os
import sys
import pypeflow.do_task
from .. import io
from ..multiproc import Pool
from ..util.io import run_func

LOG = logging.getLogger()

def run_uow(uow):
    with io.cd(uow):
        cmd = 'bash -vex uow.sh'
        io.syscall(cmd)

def dir_from_tar(tar_fn):
    # standard convention for tar-files
    return os.path.splitext(os.path.basename(tar_fn))[0]

def run(tool, uows_tar_fn, nproc, nproc_per_uow):
    if nproc_per_uow < 1:
        LOG.error('nproc_per_uow == {} < 1; using 1 instead'.format(nproc_per_uow))
        nproc_per_uow = 1

    njobs = (nproc // nproc_per_uow) if (nproc > 0) else 0
    LOG.info('For multiprocessing, parallel njobs={} (cpu_count={}, nproc={}, nproc_per_uow={})'.format(
        njobs, cpu_count(), nproc, nproc_per_uow))

    cmd = 'tar --strip-components=1 -xvf {}'.format(uows_tar_fn)
    io.syscall(cmd)
    #uows_dn = dir_from_tar(uows_tar_fn)
    uows_dn = '.'
    uows = list(sorted(glob.glob('{}/uow-*'.format(uows_dn))))
    print(uows)

    inputs = [(run_uow, uow) for uow in uows]
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

    #las_fns.extend(sorted(glob.glob('{}/*.las'.format(uow))))
    #cmd = 'LAmerge {} {}'.format(
    #    result_fn, ' '.join(las_fns))
    #io.syscall(cmd)
    #io.rm(*las_fns)

    # Nah. Cromwell simply globs the .las files.


class HelpF(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


def parse_args(argv):
    description = 'Run a bash script once for each unit-of-work, in its own sub-dir. Handle results case-by-case, according to "tool".'
    epilog = '''Some UOWs can be run in parallel, if nproc_per_uow < nproc.
'''
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
        '--uows-tar-fn',
        help='Input. Tarfile of directories of unit-of-work.')
    parser.add_argument(
        '--tool', default='daligner', choices=['daligner', 'datander'],
        help='The tool for each unit of work. (Currently ignored. We could merge .las files.)')

    args = parser.parse_args(argv[1:])
    return args


def main(argv=sys.argv):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO)
    run(**vars(args))


if __name__ == '__main__':  # pragma: no cover
    main()
