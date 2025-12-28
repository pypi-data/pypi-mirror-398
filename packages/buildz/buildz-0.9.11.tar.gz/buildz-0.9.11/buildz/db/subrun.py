
from . import runz

from .sc import ScRunner
def test():
    argv = ScRunner.process_argv()
    fp = runz.FP
    if len(argv)>1:
        fp = argv[1]
    runz.test(fp)