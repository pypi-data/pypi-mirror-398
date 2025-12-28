#
import sys
from buildz.gpuz.test.test_linear_demo import *
def test():
    '''
        占显存用的，直接从test_linear_demo import代码过来完事,调用：
        python -m buildz.gpuz.test.take_gpu_mem
        或
        python -m buildz.gpuz.test.take_gpu_mem num
        num默认12，占用3GB显存
    '''
    nets=10
    dims=2000
    trains = 5
    datas = 60
    batch=30
    lr=0.0001
    win_size=3
    num = 12
    args = sys.argv[1:]
    if len(args)>0:
        num = int(args[0])
    print(f"num: {num}")
    def fc_gen():
        mds = [Model(dims, nets) for i in range(num)]
        mds_sz = [md.size() for md in mds]
        sz, unit = analyze.show_size(sum(mds_sz))
        print(f"Model Size: {sz} {unit}")
        opts =[optim.Adam(md.parameters(), lr=lr) for md in mds]
        gmodel = nn.Sequential(*mds)
        gopt = optim.Adam(gmodel.parameters(), lr=lr)
        return mds, gmodel, opts, gopt
    mds,gmodel,opts,gop=fc_gen()
    ds = TestDataset(datas, dims)
    dl = DataLoader(ds, batch)
    dt = list(dl)[0][0]
    gmodel = gmodel.cuda()
    with torch.no_grad():
        dt=dt.cuda()
        while True:
            out = gmodel(dt)
            print(out.mean())
            time.sleep(1)

pyz.lc(locals(),test)