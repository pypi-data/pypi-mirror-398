{
    datas: [
        {
            id: help.myers
            type: object
            source: buildz.demo.myers.help.Help
            construct: {
                args: [
                    [ref, help.dir]
                    [val, myers.js]
                ]
            }
        }
        {
            id: deal.myers
            type: object
            source: buildz.demo.myers.deal.Deal
            construct: {}
        }
    ]
}