# Feel free to override this.
ifndef PYTHONUSERBASE
  PYTHONUSERBASE:=LOCAL
  PATH:=${PYTHONUSERBASE}/bin:${PATH}
  export PYTHONUSERBASE
  export PATH
endif

WHEELHOUSE?="/mnt/software/p/python/wheelhouse/develop/"

MY_TEST_FLAGS?=-v -s --durations=0

DOCTEST_MODULES= falcon_kit/functional.py falcon_kit/mains/consensus_task.py falcon_kit/mains/fasta_filter.py falcon_kit/mains/fasta_subsample.py falcon_kit/FastaReader.py

install-edit:
	pip3 install --user  --find-links=${WHEELHOUSE} --edit .
install: wheel
	pip3 install --user --use-wheel --find-links=dist/ .
pylint:
	pylint --extension-pkg-whitelist=edlib --errors-only falcon_kit/
test:
	python3 -c 'import falcon_kit; print(falcon_kit.falcon)'
	which py.test || pip3 install --user pytest pytest-mock
	py.test ${MY_TEST_FLAGS} -W 'error' --junit-xml=test.xml --doctest-modules ${DOCTEST_MODULES} test/
autopep8:
	autopep8 --max-line-length=120 -ir -j0 falcon_kit/ examples/ test/ setup.py

old-wheel:
	pip3 install --upgrade --user pip
	python3 setup.py bdist_wheel
	# Look for dist/*.whl

wheel:
	which pip3
	pip3 wheel -v --wheel-dir=./wheelhouse --no-deps .
	ls -larth ${WHEELHOUSE}

tar:
	rm -f FALCON.tar.gz
	tar cvzf FALCON.tar.gz -C ${PYTHONUSERBASE} .
# Much smaller than the wheel, and includes all necessary dependencies,
# but also includes anything already in the user-site.

clean:
	\rm -f *.xml


.PHONY: install test install-no-edit wheel tar clean
