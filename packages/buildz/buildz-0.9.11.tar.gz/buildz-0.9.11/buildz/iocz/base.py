from ..base import Base, fcBase
from .. import pathz
path = pathz.Path()
path.set('local', path.dir(__file__))
path.set('conf', path.local('conf'), curr=0)

