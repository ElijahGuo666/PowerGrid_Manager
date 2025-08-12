from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import base64

# RSA公钥字符串（PEM格式），用于加密ID
# 这个公钥用于对人员/组织ID等敏感信息进行加密，供后续接口调用
enckey = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCNfcV+KcSNFZDJat4c1IHkDZNmqJ9F9SVTq30S4X3RAiZgLLeULHvEo12zEZGUqN/7pt55E3jVipTS76V8VNKJUj7phakUH/WErJjfdKaU4jD/Vkkx+anwCG14+jDRashs4E91CG0M+Bmq0KZeqfi086dlr8C53ONBVQDV/PQuRwIDAQAB"
# enckey = base64.b64decode(enckey)
# # print(enckey)

# 导入公钥对象，用于RSA加密
pubKey = RSA.import_key('-----BEGIN PUBLIC KEY-----\n' + enckey + '\n-----END PUBLIC KEY-----')

# print(pubKey)

# 使用公钥加密ID，返回base64编码的密文
def encrypt_id(msg):
    """
    使用RSA公钥加密ID字符串
    Args:
        msg: 需要加密的ID字符串
    Returns:
        str: base64编码的加密结果
    """
    encryptor = PKCS1_v1_5.new(pubKey)
    encrypted = encryptor.encrypt(msg.encode())
    return base64.b64encode(encrypted).decode()

if __name__ == "__main__":
    # 测试加密函数
    msg = "62DFDA59020A454A827087848C892BA5"
    print(encrypt_id(msg))