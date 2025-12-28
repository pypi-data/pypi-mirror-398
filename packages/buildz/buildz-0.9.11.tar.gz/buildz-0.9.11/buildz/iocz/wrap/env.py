#

from .base import *
class EnvWrap(WrapBase):
    def call(self, maps, flush=False, tag=None):
        self.unit.update_env(maps, tag=tag, flush=flush)