"""This was copied from falcon_unzip, but we
needed to modify the TASK SCRIPT to use our copy of
generic_gather.py (not used now).
"""


import logging
import os
from pypeflow.simple_pwatcher_bridge import (PypeTask, Dist)
from pypeflow.tasks import gen_task as pype_gen_task
from pypeflow.do_task import wait_for
from . import io

LOG = logging.getLogger(__name__)

TASK_GENERIC_RUN_UNITS_SCRIPT = """\
python3 -m falcon_kit.mains.generic_run_units_of_work --nproc={params.pypeflow_nproc} --units-of-work-fn={input.units_of_work} --bash-template-fn={input.bash_template} --results-fn={output.results}
"""
TASK_GENERIC_SCATTER_ONE_UOW_SCRIPT = """\
python3 -m falcon_kit.mains.generic_scatter_one_uow --all-uow-list-fn={input.all} --one-uow-list-fn={output.one} --split-idx={params.split_idx}
"""
TASK_GENERIC_UNSPLIT_SCRIPT = """
python3 -m falcon_kit.mains.generic_unsplit --result-fn-list-fn={output.result_fn_list} --gathered-fn={output.gathered}
"""
#TASK_GENERIC_CHUNKING_SCRIPT = """\
# This is done via pbtag now, I think.
#python3 -m falcon_kit.mains.generic_chunking split-fn={input.split} --bash-template-temp-fn={input.bash_template_temp} --units-of-work-fn={output.units_of_work} --uow-template-fn={output.uow_template} --split-idx={params.split_idx}
#"""


def wrap_gen_task(script, inputs, outputs, rule_writer=None, parameters=None, dist=None):
    if parameters is None:
        parameters = dict()
    if dist is None:
        dist = Dist()
    rel_inputs = dict()
    rel_outputs = dict()
    # Make relative to CWD. (But better if caller does this.)
    def get_rel(maybe_abs):
        rel = dict()
        for (k, v) in maybe_abs.items():
            try:
                if os.path.isabs(v):
                    v = os.path.relpath(v)
                rel[k] = v
            except Exception:
                LOG.exception('Error for {!r}->{!r}'.format(k, v))
                raise
        return rel
    inputs = get_rel(inputs)
    outputs = get_rel(outputs)

    first_output_dir = os.path.normpath(os.path.dirname(list(outputs.values())[0]))
    rel_topdir = os.path.relpath('.', first_output_dir) # redundant for rel-inputs, but fine
    params = dict(parameters)
    params['topdir'] = rel_topdir

    pt = pype_gen_task(script, inputs, outputs, params, dist)

    # Run pype_gen_task first because it can valid some stuff.
    if rule_writer:
        rule_writer(inputs, outputs, params, script)
    return pt


def gen_parallel_tasks(
        wf,
        split_fn,
        gathered_fn,
        run_dict,
        rule_writer=None,
        dist=None,
        run_script=TASK_GENERIC_RUN_UNITS_SCRIPT,
):
    """
    By convention, the first (wildcard) output in run_dict['outputs'] must be the gatherable list,
    in the same format as the gathered_fn to be generated from them.

    For now, we require a single such output, since we do not yet test for wildcards.
    """
    assert 'dist' not in run_dict, 'dist should be a parameter of gen_parallel_tasks(), not of its run_dict'
    if dist is None:
        dist = Dist()
    # run_dict['inputs'] should be patterns to match the inputs in split_fn, by convention.

    #task_parameters = resolved_dict(run_dict.get('parameters', {}))
    task_parameters = run_dict.get('parameters', {})
    assert not task_parameters, 'We do not currently support the "parameters" field of a run_dict. {!r}'.format(task_parameters)

    # Write 3 wildcard rules for snakemake, 2 with dynamic.
    if rule_writer:
        rule_writer.write_dynamic_rules(
            rule_name="foo",
            input_json=split_fn,
            inputs=dict_rel_paths(run_dict['inputs']),
            shell_template=run_dict['script'],
            parameters=task_parameters,
            wildcard_outputs=dict_rel_paths(run_dict['outputs']),
            output_json=gathered_fn,
    )

    #outputs = {k:patt.format(**jobkv) for k,patt in output_patterns}
    #inputs =  {k:patt.format(**jobkv) for k,patt in input_patterns}
    #inputs['SPLIT'] = split_fn # presumably ignored by script; might not be needed at all
    #split_fn = scatter_dict['outputs']['split'] # by convention
    wf.refreshTargets()
    max_jobs = wf.max_jobs

    wait_for(split_fn)
    split = io.deserialize(split_fn)
    bash_template_fn = run_dict['bash_template_fn']

    def find_wildcard_input(inputs):
        for k,v in list(inputs.items()):
            if '{' in v:
                return v
        else:
            raise Exception('No wildcard inputs among {!r}'.format(inputs))

    LOG.debug('PARALLEL OUTPUTS:{}'.format(run_dict['outputs']))
    task_results = dict()
    for split_idx, job in enumerate(split):
        #inputs = job['input']
        #outputs = job['output']
        #params = job['params']
        #wildcards = job['wildcards']
        #params.update({k: v for (k, v) in job['wildcards'].items()}) # include expanded wildcards
        #LOG.warning('OUT:{}'.format(outputs))

        wildcards = job['wildcards']
        def resolved(v):
            return v.format(**wildcards)
        def resolved_dict(d):
            result = dict(d)
            LOG.debug(' wildcards={!r}'.format(wildcards))
            for k,v in list(d.items()):
                LOG.debug('  k={}, v={!r}'.format(k, v))
                result[k] = v.format(**wildcards)
            return result
        #task_inputs = resolved_dict(run_dict['inputs'])
        task_outputs = resolved_dict(run_dict['outputs'])

        wild_input = find_wildcard_input(run_dict['inputs'])
        one_uow_fn = os.path.abspath(wild_input.format(**wildcards))

        wf.addTask(pype_gen_task(
                script=TASK_GENERIC_SCATTER_ONE_UOW_SCRIPT,
                inputs={
                    'all': split_fn,
                },
                outputs={
                    'one': one_uow_fn,
                },
                parameters={
                    'split_idx': split_idx,
                },
                dist=Dist(local=True, use_tmpdir=False),
        ))

        wf.addTask(pype_gen_task(
                script=run_script, # usually TASK_GENERIC_RUN_UNITS_SCRIPT, unless individual load-time is slow
                inputs={
                    'units_of_work': one_uow_fn,
                    'bash_template': bash_template_fn,
                },
                outputs=task_outputs, # TASK_GENERIC_RUN_UNITS_SCRIPT expects only 1, called 'results'
                parameters={}, # some are substituted from 'dist'
                dist=dist,
        ))
        wildcards_str = '_'.join(w for w in job['wildcards'])
        job_name = 'job{}'.format(wildcards_str)
        task_results[job_name] = list(task_outputs.values())[0]

    gather_inputs = dict(task_results)
    ## An implicit "gatherer" simply takes the output filenames and combines their contents.
    gathered_dn = os.path.dirname(gathered_fn)
    result_fn_list_fn = os.path.join(gathered_dn, 'result-fn-list.json')
    # Dump (with rel-paths) into next task-dir before next task starts.
    io.serialize(result_fn_list_fn, [os.path.relpath(v, gathered_dn) for v in list(task_results.values())],
            only_if_needed=True)
    #assert 'result_fn_list' not in gather_inputs
    #gather_inputs['result_fn_list'] = result_fn_list_fn # No! pseudo output, since it must exist in a known directory
    LOG.debug('gather_inputs:{!r}'.format(gather_inputs))
    wf.addTask(pype_gen_task(
        script=TASK_GENERIC_UNSPLIT_SCRIPT,
        inputs=gather_inputs,
        outputs={
            'gathered': gathered_fn,
            'result_fn_list': result_fn_list_fn,
        },
        parameters={},
        dist=Dist(local=True, use_tmpdir=False),
    ))
    wf.max_jobs = dist.job_dict.get('njobs', max_jobs)
    wf.refreshTargets()
    wf.max_jobs = max_jobs


def dict_rel_paths(dict_paths):
    return {k: os.path.relpath(v) for (k, v) in dict_paths.items()}
