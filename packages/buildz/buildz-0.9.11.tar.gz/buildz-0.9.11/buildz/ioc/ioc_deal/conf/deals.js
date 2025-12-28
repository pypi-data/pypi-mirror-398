{
    deals: [
        {
            type: val,
            note: 数据, //note是注释，非必须
            build: buildz.ioc.ioc_deal.val.ValDeal,
            aliases: ['default']
        },
        {
            type: object,
            note: 对象,
            build: buildz.ioc.ioc_deal.obj.ObjectDeal,
            aliases: [obj]
        },
        {
            type: env,
            note: 环境变量,
            build: buildz.ioc.ioc_deal.env.EnvDeal
        },
        {
            type: ref,
            note: 引用,
            build: buildz.ioc.ioc_deal.ref.RefDeal
        },
        {
            type: refs,
            note: 正则匹配查引用列表,
            build: buildz.ioc.ioc_deal.refs.RefsDeal
        },
        {
            type: mcall,
            note: 对象方法调用,
            build: buildz.ioc.ioc_deal.mcall.MethodCallDeal
        },
        {
            type: ovar,
            note: 对象变量,
            build: buildz.ioc.ioc_deal.ovar.ObjectVarDeal
        },
        {
            type: call,
            note: 函数调用,
            build: buildz.ioc.ioc_deal.call.CallDeal
        },
        {
            type: var,
            note: 代码变量,
            build: buildz.ioc.ioc_deal.var.VarDeal
        },
        {
            type: calls,
            note: 调用序列,
            build: buildz.ioc.ioc_deal.calls.CallsDeal
        },
        {
            type: ioc,
            note: 控制反转内部数据,
            build: buildz.ioc.ioc_deal.ioc.IOCObjectDeal
        },
        {
            type: list,
            note: 列表,
            build: buildz.ioc.ioc_deal.list.ListDeal
        },
        {
            type: map,
            note: 字典,
            build: buildz.ioc.ioc_deal.map.MapDeal
        },
        {
            type: join,
            note: 文件路径拼接,
            build: buildz.ioc.ioc_deal.join.JoinDeal
        },
        {
            type: xfile,
            note: xf配置文件读取,
            build: buildz.ioc.ioc_deal.xfile.XfileDeal,
            aliases: [xf]
        },
        {
            type: deal,
            note: 扩展的自定义deal方法,
            build: buildz.ioc.ioc_deal.deal.DealDeal
        },
        {
            type: iocf,
            note: 加配置文件,
            build: buildz.ioc.ioc_deal.iocf.IOCFObjectDeal
        },
        {
            type: branch,
            note: 条件配置,
            build: buildz.ioc.ioc_deal.branch.BranchDeal
        }
    ]
}