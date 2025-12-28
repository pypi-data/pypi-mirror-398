// [[id, type, single], source, construct=[args, maps], sets=[]]
[
    {
        nullable: 0,
        out: 1,
        conf: [
            {key: type, default: null},
            {key: id, default: null},
            {key: single, default: 1}
        ]
    },
    {
        nullable: 0,
        key: source
    },
    {key: args, default: []},
    {key: maps, default: {}},
    // {
    //     key: construct,
    //     default: {args: [], maps: {}},
    //     conf: [
    //         {key: args, default: []},
    //         {key: maps, default: {}}
    //     ]
    // },
    {
        key: sets,
        default: []
    },
    {
        key: call,
        default: null
    }
]