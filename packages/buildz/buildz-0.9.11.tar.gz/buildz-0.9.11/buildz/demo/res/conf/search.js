{
    datas: [
        {
            id: help.search
            type: object
            source: buildz.demo.search.help.Help
            construct: {
                args: [
                    [ref, help.dir]
                    [val, search.js]
                ]
            }
        }
        {
            id: deal.search
            type: object
            source: buildz.demo.search.deal.Deal
            construct: {}
        }
    ]
}