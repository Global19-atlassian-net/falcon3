from falcon_kit import FastaReader as M
from falcon_kit.io import NativeIO as StringIO
from pypeflow.io import syscall

def test_fasta_empty():
    fasta = ''
    sin = StringIO(fasta)
    result = list(M.yield_fasta_record(sin, None))
    assert not result

FASTA = """\
>foo/bar/0_42 FOO=BAR
ACGT
"""

def test_fasta_simple():
    sin = StringIO(FASTA)
    result = list(M.yield_fasta_record(sin, None))
    assert [rec.sequence for rec in result] == ['ACGT']
    rec = result[0]
    assert rec.metadata == 'FOO=BAR'
    assert rec.id == 'foo/bar/0_42'
    assert rec.name == 'foo/bar/0_42 FOO=BAR'

def test_roundtrip():
    sin = StringIO(FASTA)
    sout = StringIO()
    for record in sin:
        sout.write(record)
    result = sout.getvalue()
    assert result == FASTA

def test_gzip(tmp_path):
    fp = tmp_path / "foo.fasta"
    with fp.open('w') as sout:
        sout.write(FASTA)
    syscall('gzip {}'.format(fp))
    fn_gz = str(fp) + '.gz'
    def noop(*args): pass
    with M.open_fasta_reader(fn_gz, log=noop) as reader:
        for record in reader:
            assert record.sequence == 'ACGT'
