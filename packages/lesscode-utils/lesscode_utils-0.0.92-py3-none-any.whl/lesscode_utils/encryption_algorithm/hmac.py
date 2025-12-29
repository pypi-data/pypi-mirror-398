import hmac


class HMAC:
    @staticmethod
    def encrypt(string: str, key: str, digest_mod="MD5", encoding='utf-8', flag=True):
        """
        :param string: 待加密的字符串
        :param key: 加密key
        :param digest_mod: 加密算法
        :param encoding: 编码
        :param flag: 16进制开关，默认是16进制
        :return:
        """
        h = hmac.new(key.encode(encoding), string.encode(encoding), digestmod=digest_mod)
        if flag:
            encrypt_string = h.hexdigest()
        else:
            encrypt_string = h.digest()
        return encrypt_string
