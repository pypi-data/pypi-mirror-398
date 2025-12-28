{
    datas: [
        {
            id: help.dir
            type: join
            data: [
                [var, buildz.demo.test.dp]
                res/help
            ]
        }
        {
            id: help.default, type: object, source: buildz.demo.test.Help
            construct: {
                args: [(ref, help.dir), default.js]
            }
        }
        {
            id: demo, type: object, source: buildz.demo.test.Deal
            construct: {
                //args: []
                maps: {
                    conf: {
                        type: ioc
                        key: conf
                    }
                    deals: {
                        type: val
                        // 这里让test.Deal自己查id对应的object，也可以写成在配置里直接映射好，但写起来比较麻烦
                        data: {
                            ioc: {
                                deal: deal.ioc
                                help: help.ioc
                            },
                            xf: {
                                deal: deal.xf
                                help: help.xf
                            },
                            search: {
                                deal: deal.search
                                help: help.search
                            },
                            myers: {
                                deal: deal.myers
                                help: help.myers
                            }
                        }
                    }
                    default: {
                        type: ref
                        key: help.default
                    }
                }
            }
        }
        {
            id: run
            type: mcall
            source: demo
            method: run
        }
    ]
}