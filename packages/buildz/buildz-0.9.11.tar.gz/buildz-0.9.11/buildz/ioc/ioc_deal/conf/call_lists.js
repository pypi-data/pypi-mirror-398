// [[id, type, single], source, construct=[args, maps], sets=[]]
[
    {
        nullable: 0,
        out: 1,
        conf: {
            //sort: -1,
            data:[
                {key: type, default: null}
                {key: id, default: null},
            ]
        }
    },
    {
        nullable: 0,
        key: method
    },
    {key: args, default: []},
    {key: maps, default: {}}
]