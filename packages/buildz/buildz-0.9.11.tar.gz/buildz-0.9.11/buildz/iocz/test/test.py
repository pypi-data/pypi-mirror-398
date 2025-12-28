#

from buildz import iocz,xf, pyz, Base
profiles = xf.loads(r"""
xxx.test_var=profile_var_test
""")
wraps = iocz.build_wraps()
ns = wraps().wrap
@ns.obj(id='test_wrap')
@ns.obj.args("ref,xxx.test_var")
class Test(Base):
    def str(self):
        return f'Test(<{id(self)}>|id={self.id})'
    def init(self, id=0):
        super().init()
        self.id = id
    def call(self, val=None):
        if val is None:
            val = self
        print("Test.show:", val)
        return self

pass
ns.load_profiles(profiles)
#ns.obj.args("env,PATH")(Test)
#ns.obj(id='test')(Test)
var = 'test_var'
confs1 = r'''
ns: xxx
envs: {
    a=0
    b=1
}
confs: [
    [(val,test_var), conf_var_test]
]
confs.ns: [
    [[obj, test1], <buildz>.iocz.test.test.Test, null,{id=[cvar, <buildz>.iocz.test.test.var]}]
    {
        id=test
        type=obj
        source=<buildz>.iocz.test.test.Test
        single=1
        args=[
            #[ref, test1]
            #[env, PATH]
            [method, call,test_wrap]
        ]
        call: [method, call]
    }
    [[call,test_call], test, (0)]
]
'''.replace("<buildz>", "buildz")
def get_env_sys(self, id, sid=None):
    sysdt = os.getenv(id)
    return sysdt
def test():
    mg = iocz.build()
    wraps.bind(mg)
    print(mg)
    #unit = mg.add_conf(confs)
    unit = mg.add_conf(confs1)
    val,find=unit.get("test_call")
    print(f"test_call: {val,find}")
    exit()
    with mg.push_vars({"test": 123}):
        it, find = unit.get("test")
        print(f"it: {it, id(it)}, find: {find}")
    it, find = unit.get("test")
    print(f"it: {it, id(it)}, find: {find}")
    it, find = mg.get("test", "xxx")
    print(f"it: {it, id(it)}, find: {find}")
    print(f"env: {unit.get_env('b')}")
    print(type(it))
    it = Test(123)
    print(type(it))
    print(it)
    exit()

pyz.lc(locals(), test)