#!/bin/bash -e

type module >& /dev/null || . /mnt/software/Modules/current/init/bash
module purge
module load git
module load gcc
module load ccache
module load python/3.7.3
#module load make

set -vex
git --version
which gcc
which g++
gcc --version
which python

make -C src/test

rm -rf LOCAL
mkdir -p LOCAL
export PYTHONUSERBASE=$(pwd)/LOCAL
export PATH=${PYTHONUSERBASE}/bin:${PATH}
WHEELHOUSE="/mnt/software/p/python/wheelhouse/develop/"

pip3 install --user --no-index --find-links=${WHEELHOUSE} pytest pytest-mock pytest-cov
#pip install --user --no-index --find-links=${WHEELHOUSE} pypeflow
#
## Unfortunately, we need pypeflow for pylint.
#python3 -c 'import pypeflow as p; print p'
#python3 -c 'import pypeflow.sample_tasks as p; print p'

export WHEELHOUSE
make install-edit
# Note: no --edit because we might be building artifacts.
# ... Scratch that. We have trouble getting coverage for
#  source=falcon_kit
# but maybe it will work with a --edit install.

export MY_TEST_FLAGS="-v -s --durations=0 --cov=falcon_kit --cov-report=term-missing --cov-report=xml:coverage.xml --cov-branch"
make test

pip3 install --user --find-links=${WHEELHOUSE} pylint
make pylint

#bash bamboo_wheel.sh ############
