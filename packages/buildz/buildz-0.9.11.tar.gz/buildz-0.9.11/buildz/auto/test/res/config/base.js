calls: [log, cache, cache.save, dbs, def.deal.type, list, cache.save, dbs.close]
log.shows: [info, warn, debug, error]
//默认格式是 "[{LEVEL}] %Y-%m-%d %H:%M:%S {tag} {msg}\n" (注意LEVEL是大写，有三种：level,Level, LEVEL)
//变量: {level}, {Level}, {LEVEL}, {tag}, {msg}, %Y, %m, %d, %H, %M, %S
log.format: "[{Level}] %Y-%m-%d %H:%M:%S [{tag}] {msg}\n"
def.deal: {
    types: {
        http.get: [defs, request, verify, save]
        get: [defs, request.get, verify, save]
        list: [defs, deal.list]
        test: [defs, save]
    }
}