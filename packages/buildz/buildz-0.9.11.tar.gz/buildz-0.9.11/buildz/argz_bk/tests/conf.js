{
    id: main
    type: calls
    range: 1
    calls: [
        search
    ]
}
{
    id: search
    type: call
    src: search
    judge: ['=', args[0], search]
    args: [1, [[0,()], [1, ()], {}]]
    args: {
        range: 1
        keep: 1
        list: {
            0: {
                des: path
                need: 1
                src: 0
            }
        }
        dict: {
            filepath: {
                srcs: [f, fp, filepath]
            }
            content: {
                srcs: [c, ct, content]
            }
        }
    }
}
