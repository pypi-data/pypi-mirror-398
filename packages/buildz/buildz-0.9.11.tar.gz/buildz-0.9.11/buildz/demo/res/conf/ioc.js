{
    datas: [
        {
            id: help.ioc
            type: object
            source: buildz.demo.ioc.help.Help
            construct: {
                maps: {
                    dp: [ref, help.dir]
                    fp: [val, ioc.js]
                }
            }
        }
        {
            id: deal.ioc
            type: object
            source: buildz.demo.ioc.deal.Deal
        }
    ]
}