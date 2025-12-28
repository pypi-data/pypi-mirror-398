// [[id, type], key]
// [type, key]
{
    sort: 1
    data: [
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
            nullable: 1,
            key: key,
            default: conf
        }
    ]
}