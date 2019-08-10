from .falcon_kit import *
__version__ = '1.5.0'

try:
    import sys, pkg_resources
    sys.stderr.write('falcon-kit {} (pip thinks "{}")\n'.format(__version__, pkg_resources.get_distribution('falcon-kit')))
except Exception:
    pass
