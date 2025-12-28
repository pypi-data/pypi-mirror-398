#

from . import obj
from . import env
def build(wraps):
    wraps.set_fc("obj", obj.ObjectWrap())
    fc = env.EnvWrap()
    wraps.set_fc("env", fc)
    wraps.set_fc("load_envs", fc)
    wraps.set_fc("profile", fc)
    wraps.set_fc("load_profiles", fc)
    return wraps

pass