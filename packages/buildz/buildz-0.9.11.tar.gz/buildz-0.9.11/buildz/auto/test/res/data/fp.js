configs: config/config.js
datas: [
    //写一个配置
    {
        note: test
        url: test
        type: http.get
        data: {
            url: "#{test.url}"
        }
        save: {
            test.url: data.url
        }
        result: {
            code: 1.99
        }
        verify: [
            "result.code, [>, 1]"
        ]
        save: {
            result.code: result.code
        }
    }
    // 或者配置所在的文件
    item1.js
    item2.js
    {
        type: list
    }
]