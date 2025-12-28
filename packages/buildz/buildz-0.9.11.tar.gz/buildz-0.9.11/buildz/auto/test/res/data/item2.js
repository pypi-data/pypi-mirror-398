note: test2
url: "https://$host/"
defs: {
    $host:"#{host}"
}
type: get
headers: {
    User-Agent: "Mozilla/5.0"
}
data: {
}
verify: [
    "status_code, 200"
    "result_headers.Content-Type, 'text/html'"
]
save: {
    test2.headers.content_type: result_headers.Content-Type
}
save.mem: {
    test2.headers.content_type: result_headers.Content-Type
}