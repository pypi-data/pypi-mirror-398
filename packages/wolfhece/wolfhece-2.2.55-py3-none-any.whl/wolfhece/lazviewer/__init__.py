import logging
# Check __onWindows__ variable from wolfhece/__init__.py
from ..os_check import isWindows

if not isWindows():
    # If not on Windows, raise an exception
    logging.info('Not on Windows, ignoring the lazviewer package')

else:
    from . import _add_path
    from .viewer.viewer import *
    from .points.points import *
    from .points.expr import *
    from scipy.spatial import kdtree

    try:
        from .processing.estimate_normals.estimate_normals import estimate_normals
    except Exception as e:
        print(e)
        print('Could not import estimate_normals')
        print('Please installed the VC++ redistributable from https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads')

