#coding=utf-8
# 生成RSA私钥
def gen_prv(filepath, pwd = None):
    """
        生成pem格式私钥, 存放到filepath文件上
    """
def gen_pub(filepath, fp_prv, pwd = None):
    """
        从私钥文件fp_prv生成pem格式公钥, 保存到filepath文件上
    """
def load_prv(fp_prv, pwd = None):
    # 从磁盘上读取私钥
def load_pub(fp_pub):
    # 从磁盘上读取公钥
def gen_csr(filepath, fp_prv, conf = {}, pwd = None):
    '''
        生成csr文件，由fp_prv签名
    '''
def load_csr(filepath):
    # 读取csr
#要生成证书链，是从网站证书开始写入，往上写到根证书
"""
chains.cert文件结构:
网站证书
中间节点证书
...
根证书
"""
def sign_csr(filepath, fp_csr, fp_cert, fp_prv, conf = {}, pwd = None, add_chains = True):
    '''
        用cert证书签名csr，生成新的证书，add_chains如果为真，生成证书链
        证书链结构:
            网站证书
            中间节点证书
            ...
            根证书
    '''
def gen_cert(filepath, fp_prv, conf={}, pwd = None):
    """
    用私钥fp_prv签名公钥fp_pub和配置conf, 生成证书到filepath
    """
def loadf_certs(fp):
    # 从文件读取证书链
def load_certs(bs):
    # 读取证书链
def verify_certs_fp(fp, cas = None, verify_time=True):
    # 证书链校验，fp是需要校验的证书链文件，cas是根证书文件数组
def verify_certs(certs, cas = None, verify_time=True):
    # 证书链校验，certs是需要校验的证书链，cas是根证书数组

def verify_cert(cert, public_key=None, verify_time=True, hash_alg = None):
    # 证书校验
def load_cert(fp):
    # 读取证书