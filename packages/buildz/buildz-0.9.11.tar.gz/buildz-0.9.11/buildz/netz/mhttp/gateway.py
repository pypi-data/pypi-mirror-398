
from . import proxy,mhttp, mhttps
import socket, threading
log = mhttp.log
from buildz import xf
import ssl,re
from os.path import join, isfile
import traceback
from ...iocz.conf import conf as confz
from ... import dz,pyz
class GWDealer(proxy.ProxyDealer):
    conf = confz.Conf()
    conf.ikey(0, 'match', need=1)
    conf.ikey(1, 'replace', need=1)
    conf.ikey(2, 'ssl')
    conf.ikey(3, 'type', 'match_type,http_type'.split(","))
    """
    rules:[
        [match, replace, [opt|ssl], [opt|match_type]]
        {match=match, replace=relace, ssl=false, match_type='GET'}
    ]
    """
    def init(self, skt, rules, verify_context, context, channel_read_size=1024000, record=None):
        self.context = context
        if context is not None:
            skt = context.wrap_socket(skt, server_side=True)
        rules = [self.conf(k)[0] for k in rules]
        self.rules = rules
        self.verify_context = verify_context
        super().init(skt, channel_read_size, record=record, default_deal = self.maps_deal)
    def match(self, line, headers):
        http_type, url, protocol = line
        for item in self.rules:
            pt, rep, mark_ssl, match_type = dz.g(item, match=None, replace=None, ssl=False, type=http_type)
            if match_type != http_type:
                continue
            rst = re.findall(pt, url)
            if len(rst)==0:
                continue
            match = rst[0]
            i = url.find(match)
            pfx, sfx = url[:i], url[i+len(match):]
            rurl = pfx+rep+sfx
            log.debug(f"url match: {rst} for {url}, replace to {rurl} with i={i}")
            return rurl, mark_ssl
        return None, False
    def ssl_connect(self, addr):
        return mhttps.wrap(self.verify_context, mhttp.WSocket.Connect(addr), False)
    def maps_deal(self, skt_cli, line, headers, data_size, skt=None):
        http_type, url, protocol = line
        rel_url, mark_ssl = self.match(line, headers)
        if rel_url is None:
            if data_size>0:
                data = skt_cli.read(data_size)
            if mhttp.check_chunked(headers):
                self.simple_chunked(skt_cli)
            return self.error(skt_cli)
        if mark_ssl:
            prev = "https"
        else:
            prev = "http"
        host = rel_url.split("?")[0].split("/")[0]
        rel_url = prev+"://"+rel_url
        for key in "Host,Origin".split(","):
            if key in headers:
                headers[key] = host
        if 'Referer' in headers:
            ref = headers['Referer']
            prev, src_host, path = mhttp.spt_url(ref)
            ref = mhttp.comb_url(prev, host, path)
            headers["Referer"] = ref
            log.info(f"[REF] host: {host}, ref: {ref}")
        line = http_type, rel_url, protocol
        fc_connect = None
        if mark_ssl:
            fc_connect = self.ssl_connect
        return self.default_deal(skt_cli, line, headers, data_size, skt, fc_connect)


class Gateway(proxy.Proxy):
    '''
        类似nginx的反向代理
    '''
    def init(self, addr, rules, fp_cert=None, fp_prv=None, password = None,listen=5, record=None, cafile=None, capath=None, cadata=None,check_hostname=True):
        super().init(addr, listen, record)
        self.rules = rules
        self.verify_context = mhttps.load_verify_context(cafile, capath, cadata,check_hostname)
        self.context = None if fp_cert is None else mhttps.load_server_context(fp_cert, fp_prv, password)
    def make_dealer(self, skt, addr):
        return GWDealer(skt, self.rules, self.verify_context, self.context, record=self.record.clone())

def test():
    import sys,time
    from buildz import xf
    conf_fp = sys.argv[1]
    conf = xf.loadf(conf_fp)
    addr = tuple(conf['addr'])
    rules = conf['rules']
    px = Gateway(addr, rules)
    th = threading.Thread(target=px,daemon=True)
    th.start()
    print(f"start on {(ip, port)}")
    while px.running:
        time.sleep(1)
pyz.lc(locals(), test)