#

import ssl
from . import mhttp

def load_verify_context(cafile=None, capath=None, cadata=None,check_hostname=True):
    if cafile is not None or capath is not None or cadata is not None:
        # 导入根证书，需要单个根证书文件cafile或者根证书文件夹capath或者根证书数据cadata
        # cadata是证书数据，不清楚能不能多个证书字节码拼在一起
        srv_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        srv_context.load_verify_locations(cafile=cafile, capath=capath, cadata=cadata)
        srv_context.check_hostname = check_hostname
    else:
        # 不会校验服务端https证书是否有效，可能有风险？
        srv_context = ssl._create_unverified_context(ssl.PROTOCOL_TLS_CLIENT)
    return srv_context

pass

def load_server_context(fp_cert, fp_prv, pwd=None):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(fp_cert, fp_prv, password=pwd)
    return context

def wrap(context, wrap_cli, server_side, is_wrap = True):
    if is_wrap:
        wrap_cli = wrap_cli.skt
    return mhttp.WSocket.Bind(context.wrap_socket(wrap_cli, server_side=server_side))