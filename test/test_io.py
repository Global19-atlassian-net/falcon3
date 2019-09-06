import pytest, os
import falcon_kit.io as M

def test_serialize(tmp_path):
    fnp = tmp_path / 'foo.json'
    fn = str(fnp)

    v = {'a': 2}
    M.serialize(fn, v)
    nv = M.deserialize(fn)
    assert nv == v

    os.chmod(fn, 0o444)
    M.serialize(fn, v, only_if_needed=True)
    nv = M.deserialize(fn)
    assert nv == v
    # That is only testing that nothing raises.

    os.chmod(fn, 0o666)
    v1 = {'b': 4}
    M.serialize(fn, v1, only_if_needed=True)
    nv = M.deserialize(fn)
    assert nv == v1
    assert v != v1
