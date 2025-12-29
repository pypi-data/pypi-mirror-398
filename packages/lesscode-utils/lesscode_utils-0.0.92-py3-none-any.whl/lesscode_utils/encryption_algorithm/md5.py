class MD5:
    @staticmethod
    def encrypt(string: str):
        """
        :param string: 待加密的字符串
        :return:
        """
        import hashlib
        md5 = hashlib.md5(string.encode('utf-8'))
        encrypt_string = md5.hexdigest()
        return encrypt_string
