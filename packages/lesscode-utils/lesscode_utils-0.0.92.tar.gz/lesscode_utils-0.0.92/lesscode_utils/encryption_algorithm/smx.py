import importlib


class SMX:
    @staticmethod
    def generate_sm2_key():
        try:
            smx_sm2 = importlib.import_module("pysmx.SM2")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        pk, sk = smx_sm2.generate_keypair()
        return {"pk": pk, "sk": sk}

    @staticmethod
    def generate_sm2_sign(string: str, sk, k, len_para, is_hex=0, encoding="utf-8"):
        """
        :param string: 签名字符串
        :param sk: 私钥
        :param k: 随机数, 16进制字符串
        :param len_para: 目前固定为64
        :param is_hex:M是否是hex字符串
        :param encoding: 若M不是16进制字符串
        :return:
        """
        try:
            smx_sm2 = importlib.import_module("pysmx.SM2")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        return smx_sm2.Sign(E=string, DA=sk, K=k, len_para=len_para, Hexstr=is_hex, encoding=encoding)

    @staticmethod
    def verify_sm2_sign(sign, string: str, pk, len_para=64, is_hex=0, encoding="utf-8"):
        """
        :param sign: 签名 r||s
        :param string: E消息hash
        :param pk: PA公钥
        :param len_para: 目前固定为64
        :param is_hex: M是否是hex字符串
        :param encoding: 若M不是16进制字符串
        :return:
        """
        try:
            smx_sm2 = importlib.import_module("pysmx.SM2")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        return smx_sm2.Verify(Sign=sign, E=string, PA=pk, len_para=len_para, Hexstr=is_hex, encoding=encoding)

    @staticmethod
    def sm2_encrypt(string: str, pk, len_para=64, is_hex=False, encoding='utf-8', hash_algorithm='sm3'):
        """
        :param string: 加密信息
        :param pk: 公钥
        :param len_para: 目前固定为64
        :param is_hex: M是否是hex字符串
        :param encoding: 若M不是16进制字符串
        :param hash_algorithm: hash算法
        :return:
        """
        try:
            smx_sm2 = importlib.import_module("pysmx.SM2")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        encrypt_string = smx_sm2.Encrypt(M=string, PA=pk, len_para=len_para, Hexstr=is_hex, encoding=encoding,
                                         hash_algorithm=hash_algorithm)
        return encrypt_string

    @staticmethod
    def sm3_encrypt(string: str):
        """
        :param string: 加密字符串
        :return:
        """
        try:
            smx_sm3 = importlib.import_module("pysmx.SM3")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        sm3 = smx_sm3.SM3()
        sm3.update(string)
        encrypt_string = sm3.hexdigest()
        return encrypt_string

    @staticmethod
    def sm2_decrypt(string: str, sk: str, len_para=64, is_hex=False, encoding='utf-8', hash_algorithm='sm3'):
        """
        :param string: 密文
        :param sk: 私钥
        :param len_para: 目前固定为64
        :param is_hex: M是否是hex字符串
        :param encoding: 若M不是16进制字符串
        :param hash_algorithm: hash算法
        :return:
        """
        try:
            smx_sm2 = importlib.import_module("pysmx.SM2")
        except ImportError as e:
            raise Exception(f"snowland-smx is not exist,run:pip install snowland-smx==0.3.1")
        decrypt_string = smx_sm2.Decrypt(C=string, DA=sk, len_para=len_para,
                                         Hexstr=is_hex,
                                         encoding=encoding, hash_algorithm=hash_algorithm)
        return decrypt_string
