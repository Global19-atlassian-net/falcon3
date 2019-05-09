from .falcon_kit import *
__version__ = '1.4.2' # should match setup.py

try:
    import sys, pkg_resources
    sys.stderr.write('{}\n'.format(pkg_resources.get_distribution('falcon-kit')))
except Exception:
    pass
