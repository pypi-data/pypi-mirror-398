#coding=utf-8
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography import x509
from cryptography.x509.oid import NameOID
import datetime
from buildz import xf
from buildz import fz
from getpass import getpass
def sign(private_key, bs):
    return private_key.sign(bs, padding.PKCS1v15(), hashes.SHA256())
def verify(public_key, bs, sig):
    public_key.verify(sig,bs, padding.PKCS1v15(), hashes.SHA256())

pass
def encrypt(public_key, bs):
    encrypted = public_key.encrypt(
        bs,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted

pass
def decrypt(private_key, bs):
    decrypted = private_key.decrypt(
        bs,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted

pass
# 生成RSA私钥
def gen_prv(filepath, pwd = None):
    """
        生成pem格式私钥, 存放到filepath文件上
    """
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    # 将私钥序列化为PEM格式
    if pwd is None:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
    else:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(pwd)
        )
    # 将私钥保存在磁盘上
    with open(filepath, "wb") as f:
        f.write(pem)

pass

def gen_pub(filepath, fp_prv, pwd = None):
    """
        从私钥文件fp_prv生成pem格式公钥, 保存到filepath文件上
    """
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    # 从磁盘上读取私钥
    with open(fp_prv, "rb") as f:
        pem_data = f.read()
    # 将PEM格式的私钥反序列化为私钥对象
    private_key = serialization.load_pem_private_key(pem_data, password=pwd, backend=default_backend())
    # 生成RSA公钥
    public_key = private_key.public_key()
    # 将RSA公钥序列化为PEM格式
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    # 将RSA公钥保存在磁盘上
    with open(filepath, "wb") as f:
        f.write(pem)

pass

def load_prv(fp_prv, pwd = None):
    # 从磁盘上读取私钥
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    pem_data = fz.read(fp_prv, 'rb')
    # 将PEM格式的私钥反序列化为私钥对象
    private_key = serialization.load_pem_private_key(pem_data, password=pwd, backend=default_backend())
    return private_key

pass
def load_pub(fp_pub):
    # 从磁盘上读取公钥
    pem_data = fz.read(fp_pub, 'rb')
    # 将PEM格式的公钥反序列化为公钥对象
    public_key = serialization.load_pem_public_key(pem_data, backend=default_backend())
    return public_key

pass
def get(map, key, default = None):
    if key not in map:
        return default
    return map[key]

pass
def gen_subject(conf = {}):
    # 生成证书的主体名称
    names = [
        # 国家
        x509.NameAttribute(NameOID.COUNTRY_NAME, get(conf, "contry", "CN")),
        # 省份
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,  get(conf, "provice", "CN")),
        # 城市
        x509.NameAttribute(NameOID.LOCALITY_NAME, get(conf, 'local', 'cityz')),
        # 组织
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, get(conf, 'org', 'orgz')),
        # 这里其实应该是域名/ip
        x509.NameAttribute(NameOID.COMMON_NAME, get(conf, 'comman', 'commanz')),
        # email
        x509.NameAttribute(NameOID.EMAIL_ADDRESS, get(conf, 'email', 'emailz'))
    ]
    subject = x509.Name(names)
    return subject

pass

def add_extensions(builder, conf = {}):
    dns = xf.g(conf, dns = [])
    if len(dns)>0:
        #print("dns:", dns)
        dns_arr = [x509.DNSName(k) for k in dns]
        dns_arr = x509.SubjectAlternativeName(dns_arr)
        builder = builder.add_extension(dns_arr, critical=False)
    ca = xf.g(conf, ca = False)
    if ca:
        builder = builder.add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True
        )
    # DNS
    # builder = builder.add_extension(
    #     x509.SubjectAlternativeName([
    #         x509.DNSName(get(conf, 'dns1', 'localhost')),
    #         x509.DNSName(get(conf, 'dns2', 'localhost'))
    #     ]),
    #     critical=False
    # )
    # builder = builder.add_extension(
    #     x509.BasicConstraints(ca=True, path_length=None),
    #     critical=True
    # )
    return builder

pass
def gen_csr(filepath, fp_prv, conf = {}, pwd = None):
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    private_key = load_prv(fp_prv, pwd)
    subject = gen_subject(conf)
    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(subject)
    builder = add_extensions(builder, conf)
    # 将证书签名
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )
    pem = certificate.public_bytes(serialization.Encoding.PEM)
    fz.write(pem, filepath, 'wb')

pass

def load_csr(filepath):
    pem = fz.read(filepath, 'rb')
    csr = x509.load_pem_x509_csr(pem)
    return csr

pass
#要生成证书链，是从网站证书开始写入，往上写到根证书
"""
chains.cert文件结构:
网站证书
中间节点证书
...
根证书
"""
def sign_csr(filepath, fp_csr, fp_cert, fp_prv, conf = {}, pwd = None, add_chains = True):
    # 将PEM格式的私钥反序列化为私钥对象
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    private_key = load_prv(fp_prv, pwd)
    cert = load_cert(fp_cert)
    csr = load_csr(fp_csr)
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(csr.subject)
    builder = builder.issuer_name(cert.subject)
    builder = builder.public_key(csr.public_key())
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=xf.g(conf, valid_before=1)))
    builder = builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=xf.g(conf, valid=365)))
    for extension in csr.extensions:
        #print(f"csr excention: {extension}")
        builder = builder.add_extension(extension.value, extension.critical)
    # 将证书签名
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )
    pem = certificate.public_bytes(serialization.Encoding.PEM)
    if add_chains:
        pem += fz.read(fp_cert, 'rb')
    # 将证书保存在磁盘上
    fz.write(pem, filepath, 'wb')

pass


def gen_cert(filepath, fp_prv, conf={}, pwd = None):
    """
    用私钥fp_prv签名公钥fp_pub和配置conf, 生成证书到filepath
    """
    # 将PEM格式的私钥反序列化为私钥对象
    if pwd == True:
        pwd = getpass("input private_key password:").encode()
    if type(pwd)==str:
        pwd = pwd.encode()
    private_key = load_prv(fp_prv, pwd)
    public_key = private_key.public_key()
    # 将PEM格式的公钥反序列化为公钥对象
    #public_key = load_pub(fp_pub)
    # 生成证书的主体名称
    subject = gen_subject(conf)
    # 生成SSL证书
    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    issuer = subject
    builder = builder.issuer_name(subject)
    builder = builder.public_key(public_key)
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=xf.g(conf, valid_before=1)))
    builder = builder.not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=xf.g(conf, valid=365)))
    builder = add_extensions(builder, conf)
    # 将证书签名
    certificate = builder.sign(
        private_key=private_key,
        algorithm=hashes.SHA256(),
        backend=default_backend()
    )
    pem = certificate.public_bytes(serialization.Encoding.PEM)
    # 将证书保存在磁盘上
    fz.write(pem, filepath, 'wb')

pass
class CertVerifyException(Exception):
    pass

pass
def loadf_certs(fp):
    bs = fz.read(fp,'rb')
    return load_certs(bs)
def load_certs(bs):
    spt = b"-----END CERTIFICATE-----"
    pems = bs.split(spt)
    pems = [k+spt for k in pems if k.strip()!=b""]
    certs = [x509.load_pem_x509_certificate(pem) for pem in pems]
    return certs
def verify_certs_fp(fp, cas = None, verify_time=True):
    certs = loadf_certs(fp)
    if len(certs)==0:
        raise CertVerifyException(f"not any cert info in {fp}")
    if cas is None:
        cas = []
    if type(cas)!=list:
        cas = [cas]
    cas = [load_cert(ca) for ca in cas]
    return verify_certs(certs, cas, verify_time)

pass
def verify_certs(certs, cas = None, verify_time=True):
    if certs is None:
        certs = []
    if type(certs)!=list:
        certs = [certs]
    if len(certs)==0:
        raise CertVerifyException(f"not any cert info in {fp}")
    if cas is None:
        cas = []
    if type(cas)!=list:
        cas = [cas]
    #cas = [load_cert(ca) for ca in cas]
    roots = {ca.subject:[ca.public_key(), ca.signature_hash_algorithm] for ca in cas}
    #print(f"[TESTZ] verify certs: {len(certs)}")
    for i in range(len(certs)-1):
        curr = certs[i]
        up = certs[i+1]
        verify_cert(curr, up.public_key(), verify_time, up.signature_hash_algorithm)
    cert = certs[-1]
    issuer = cert.issuer
    if issuer not in roots:
        raise CertVerifyException(f"not root cert find: {issuer}")
    pk, hash_alg = roots[issuer]
    verify_cert(cert, pk, verify_time, hash_alg)

pass


def verify_cert(cert, public_key=None, verify_time=True, hash_alg = None):
    if type(cert)==str:
        cert = load_cert(cert)
    if public_key is None:
        public_key = cert.public_key()
    if hash_alg is None:
        hash_alg = cert.signature_hash_algorithm
    public_key.verify(cert.signature,cert.tbs_certificate_bytes, padding.PKCS1v15(),hash_alg)
    if not verify_time:
        return
    if cert.not_valid_before_utc<datetime.datetime.now(datetime.timezone.utc)<cert.not_valid_after_utc:
        return
    raise CertVerifyException("date not pass")

pass

def load_cert(fp):
    bs = fz.read(fp, 'rb')
    cert = x509.load_pem_x509_certificate(bs)
    return cert

pass
def load_der(fp):
    bs = fz.read(fp, 'rb')
    cert = x509.load_der_x509_certificate(bs)
    return cert

pass
SOIDS = "COUNTRY_NAME,STATE_OR_PROVINCE_NAME,LOCALITY_NAME,ORGANIZATION_NAME,COMMON_NAME,EMAIL_ADDRESS".split(",")
OIDS = ['BUSINESS_CATEGORY', 'COMMON_NAME', 'COUNTRY_NAME', 'DN_QUALIFIER', 'DOMAIN_COMPONENT', 'EMAIL_ADDRESS', 'GENERATION_QUALIFIER', 'GIVEN_NAME', 'INITIALS', 'INN', 'JURISDICTION_COUNTRY_NAME', 'JURISDICTION_LOCALITY_NAME', 'JURISDICTION_STATE_OR_PROVINCE_NAME', 'LOCALITY_NAME', 'OGRN', 'ORGANIZATIONAL_UNIT_NAME', 'ORGANIZATION_IDENTIFIER', 'ORGANIZATION_NAME', 'POSTAL_ADDRESS', 'POSTAL_CODE', 'PSEUDONYM', 'SERIAL_NUMBER', 'SNILS', 'STATE_OR_PROVINCE_NAME', 'STREET_ADDRESS', 'SURNAME', 'TITLE', 'UNSTRUCTURED_NAME', 'USER_ID', 'X500_UNIQUE_IDENTIFIER']
#oids = [getattr(NameOID, oid) for oid in OIDS if hasattr(NameOID, oid)]

NAMES = ['业务类别', '公共名称', '国家名称', ' DN_限定符', '域_组件', '电子邮件_地址', '代_限定符', '名字', '旅馆', '管辖区_国家名称', '管辖区_地点_名称', '管辖区_州_或_省_名称', '地点_名称', 'OGRN', '组织_单位_名称', '组织_标识符', '组织_名称', '邮政_地址', '邮政_代码', '假名', '序列号', ' SNILS ', '州_或_省_名称', '街道_地址', '姓氏', '头衔', '非结构化名称', '用户_ID ', 'X500']
names = {getattr(NameOID, OID): f"{NAME}({OID.lower()})" for NAME, OID in zip(NAMES, OIDS) if hasattr(NameOID, OID)}
def des_subject(subject):
    arr = subject._attributes
    rst = {}
    for its in arr:
        for it in its:
            oid = it.oid
            val = it.value
            if oid not in names:
                name = oid.dotted_string
            else:
                name = names[oid]
            rst[name]=val
    return rst

pass
def test():
    gen_prv("prv.pem")
    gen_pub("pub.pem", "prv.pem")
    sign("sign.pem", "pub.pem", "prv.pem")

pass

if __name__=="__main__":
    test()

pass
