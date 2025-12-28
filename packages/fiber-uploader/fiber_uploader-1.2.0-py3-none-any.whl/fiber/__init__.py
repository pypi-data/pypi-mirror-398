__version__ = "1.0.0"

from .core import main, Uploader, AuthManager

def upload(files):
    import sys
    sys.argv = ["fiber"] + files
    main()

