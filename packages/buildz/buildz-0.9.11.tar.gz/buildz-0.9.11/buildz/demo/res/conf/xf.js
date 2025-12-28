{
    datas: [
        {
            id: help.xf
            type: object
            source: buildz.demo.xf.help.Help
            construct: {
                args: [
                    [ref, help.dir]
                    [val, xf.js]
                ]
            }
        }
        {
            id: deal.xf
            type: object
            source: buildz.demo.xf.deal.Deal
            construct: {}
        }
    ]
}