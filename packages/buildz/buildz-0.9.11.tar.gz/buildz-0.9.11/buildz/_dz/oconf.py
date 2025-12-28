class ObjConf:
    def __str__(self):
        return str(self._maps)
    def __repr__(self):
        return self.__str__()
    def __init__(self):
        self._maps = {}
    def __getitem__(self, key):
        return self._maps[key]
    def __getattr__(self, key):
        if key in self._maps:
            return self._maps[key][0]
        return self.__getattribute__(key)
    def __setattr__(self, key, val):
        if key != '_maps':
            self(key, val)
        else:
            object.__setattr__(self,key,val)
    def __call__(self, *args, **maps):
        '''
            call(key,val)
            or
            call(key0=val0, key1=val1)
        '''
        if len(args)==2:
            key,val = args
            self._maps[key] = val
        else:
            for key,val in maps.items():
                self._maps[key] = val
    def __delattr__(self, key):
        if key in self._maps:
            del self._maps[key]
        return super().__delattr__(key)
    def __contains__(self, key):
        return self._maps.__contains__(key)

pass

class ObjTypeConf(ObjConf):
    def __init__(self, vtype=0):
        super().__init__()
        self._vtypes = {}
        self._vtype = vtype
    def __getitem__(self, vtype=None):
        if vtype is None:
            return self._maps
        maps = {}
        for key in self._maps:
            _vtype = self._vtypes[key]
            if _vtype==vtype:
                maps[key]=self._maps[key]
        return maps
    def __setattr__(self, key, val):
        if key not in {'_maps','_vtype','_vtypes'}:
            self(key, val)
        else:
            object.__setattr__(self,key,val)
    def __call__(self, *args, **maps):
        '''
            call(key,val)
            call(key,val,vtype)
            or
            call(key0=val0, key1=val1)
        '''
        if len(maps)==0:
            if len(args)<=1:
                return self.__getitem__(*args)
        if len(args) in {2,3}:
            key = args[0]
            val = args[1]
            vtype = None
            if len(args)==3:
                vtype = args[2]
            vtype = vtype or self._vtype
            self._maps[key] = val
            self._vtypes[key] = vtype
        else:
            for key,val in maps.items():
                self._maps[key] = val
                self._vtypes[key] = self._vtype
    def __delattr__(self, key):
        if key in self._maps:
            del self._maps[key]
            del self._vtypes[key]
            return
        return super().__delattr__(key)

pass
