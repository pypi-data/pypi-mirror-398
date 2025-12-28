from buildz import argz,xf,Base,evalz,pathz
'''
python -m buildz.argz.test search /d/rootz
python -m buildz.argz.test_obj search /d/rootz f=asf c=test
'''

def search(dp, filepath = None, content = None):
    print(f"call in search: ({dp}, {filepath}, {content})")
    return f"call in search {dp}"

pass

args = argz.ArrArgs().add(
    argz.RangeListArgs(1)
)
trs = argz.TrsArgs().add(
    argz.ArgItem("filepath", "dict").add("f", "dict").add("fp", "dict").add("filepath", "dict")
).add(
    argz.ArgItem(0, "list",need=True,des="path").add(0, "list")
).add(
    argz.ArgItem("content", "dict").add("c", "dict").add("ct", "dict").add("content", "dict")
)
args.add(trs)
fc = argz.ArgsCall(search, args)
judge = lambda obj:obj[0][0]=='search'
fc = argz.EvalCall(fc, judge)
fcs = argz.Calls([fc])



main_args = argz.ArrArgs().add(argz.RangeListArgs(1))
main = argz.ArgsCall(fcs, main_args)


ins = xf.args(base=0)
args, maps = ins.args, ins.maps
rst = main(args, maps)
print(rst)