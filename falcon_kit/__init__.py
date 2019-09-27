try:
    from .falcon_kit import *
except ModuleNotFoundError as exc:
    import warnings
    warnings.warn(exc)
__version__ = '1.7.0'

try:
    import sys, pkg_resources
    sys.stderr.write('falcon-kit {} (pip thinks "{}")\n'.format(__version__, pkg_resources.get_distribution('falcon-kit')))
except Exception:
    pass
