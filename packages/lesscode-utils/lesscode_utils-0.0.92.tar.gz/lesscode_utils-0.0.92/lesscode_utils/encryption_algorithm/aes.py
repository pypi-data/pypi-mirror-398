# -*- coding: utf-8 -*-
import base64
import binascii
import importlib


class AES:
    @staticmethod
    def encrypt(text="", key="haohaoxuexi"):
        """
        :param key: 密钥
        :param text: 需要被加密的数据
        """
        try:
            _AES = importlib.import_module("Cryptodome.Cipher.AES")
        except ImportError as e:
            raise Exception(f"pycryptodomex is not exist,run:pip install pycryptodomex==3.17")
        text = str(text)
        aes = _AES.new(AES.add_to_16(key), _AES.MODE_ECB)
        encrypt_aes = aes.encrypt(AES.add_to_16(text))
        encrypted_text = str(base64.encodebytes(encrypt_aes), encoding='utf-8')
        return bytes.decode(binascii.b2a_hex(bytes(encrypted_text, encoding="utf8")))

    @staticmethod
    def decrypt(text="", key="haohaoxuexi"):
        """
        :param key: 密钥
        :param text: 需要被加密的数据
        """
        try:
            _AES = importlib.import_module("Cryptodome.Cipher.AES")
        except ImportError as e:
            raise Exception(f"pycryptodomex is not exist,run:pip install pycryptodomex==3.17")
        text = bytes.decode(binascii.a2b_hex(bytes(text, encoding="utf8")))
        # 密文
        # 初始化加密器
        aes = _AES.new(AES.add_to_16(key), _AES.MODE_ECB)
        # 优先逆向解密base64成bytes
        base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
        # 执行解密密并转码返回str
        decrypted_text = str(aes.decrypt(base64_decrypted), encoding='utf-8').replace('\0', '')
        return decrypted_text

    @staticmethod
    def add_to_16(value):
        """
        :param value: 待处理的数据
        """
        while len(value) % 16 != 0:
            value += '\0'
        return str.encode(value)  # 返回bytes
