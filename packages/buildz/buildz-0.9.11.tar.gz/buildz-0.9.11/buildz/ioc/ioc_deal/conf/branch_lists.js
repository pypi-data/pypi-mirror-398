// [[id, type], key]
[
    {
        nullable: 0,
        out: 1,
        conf: {
            //sort:-1,
            data:[
                {key: type, default: null }
                {key: id, default: null},
            ]
        }
    },
    {
        nullable: 0,
        key: judge
    },
    {
        nullable: 0,
        key: vals
    },
    {
        nullable: 1,
        key: default
    }
]