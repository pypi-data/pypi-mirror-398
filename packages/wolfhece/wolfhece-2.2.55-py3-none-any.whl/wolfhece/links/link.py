import os
import sys
import traceback
from pathlib import Path

def create_link(directory, link_path):
    """ Create a link to the directory from link_path """
    if os.path.exists(link_path):
        os.remove(link_path)

    if sys.platform == "win32":
        import _winapi
        _winapi.CreateJunction(str(directory), str(link_path))
    else:
        os.symlink(str(directory), str(link_path), target_is_directory=True)
