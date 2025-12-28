#
import sys
import os
curr_dir = os.path.dirname(__file__)
if len(sys.argv)==1:
    sys.argv.append("build_ext")
    sys.argv.append('--build-lib')
    sys.argv.append(f"{curr_dir}")
if sys.platform =='win32':
    sys.argv.append("--compiler=mingw32")
from buildz.xf.cpp import setup

"""
mingw32 or linux:
python -m buildz.xf.cpp.setup_mingw32
mscrt or linux
python -m buildz.xf.cpp.setup
"""