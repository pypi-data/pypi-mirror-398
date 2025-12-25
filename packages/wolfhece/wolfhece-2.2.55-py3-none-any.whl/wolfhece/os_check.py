import os

# Check if we are on Windows
if os.name == 'nt':
    __onWindows__ = True
else:
    __onWindows__ = False

def isWindows():
    """
    Check if the current operating system is Windows.

    Returns:
        bool: True if the OS is Windows, False otherwise.
    """
    return __onWindows__