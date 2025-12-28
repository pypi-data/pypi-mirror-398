note: test1
url: test
type: http.get
data: {
    url: "#{test.url}"
    val: "#{test.val}"
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