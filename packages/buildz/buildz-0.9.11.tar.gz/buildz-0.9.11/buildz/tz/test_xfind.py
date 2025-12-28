#

from buildz.tz import xfind as sh
from buildz import xf
s = r"""
name=zero
age=12000
datas = [
    {
        name=notebook
        price=6500
        power=200w
        contains=[buildz,pyz]
    }
    {
        name=buildz
        function='easy coding'
        contains = [
            {
                name=xf
                function = 'json-like easier format'
            }
            {
                name=ioc
                function = 'factory build items by profile or wrap'
            }
            {
                name=auto
                function = 'easy to make auto functions'
            }
        ]
    }
    {
        name=pyz
        function = 'tools'
        contains = [
            {
                name=nxf
                function = 'safely transfer data by devices'
            }
            {
                name=netx
                function = 'both side RPC support'
            }
            {
                name=logz
                function = 'log recoding'
            }
        ]
    }
]
"""
"""

python test_xfind.py

"""
data = xf.loads(s)
print(xf.dumps(data, format=1))
node = sh.Node.parse(data)
arr = sh.SearchArray.single(node)
pts = r"""
[
    [
        or, 
        (mkv, name, nxf)
        (mkv, name, xf)
    ]
    [re, key, "[f].*"]
]
"""
arr = arr.searchs_dfc(pts)
print("Rst:", arr.datas())
print("Vals:", arr.vals())
