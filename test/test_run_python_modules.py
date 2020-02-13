import pytest
from falcon_kit.mains import run_python_modules as MOD
from falcon_kit.io import cd

OUT_FN = "stdout.txt"

script = """
# a comment
python3 -m falcon_kit.mains.noop >| stdout.txt
python3 -m falcon_kit.mains.noop arg1 arg2 >> stdout.txt
"""

expected = """\
python3 on ()
python3 on ('arg1', 'arg2')
"""

def test_mod(tmp_path):
    with cd(tmp_path):
        script_fn = "script.sh"

        with open(script_fn, 'w') as ofs:
            ofs.write(script)

        MOD.run(script_fn)

        with open(OUT_FN) as ifs:
            result = ifs.read()
            assert result == expected
