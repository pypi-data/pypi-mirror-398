from lesscode_utils.oss.aliyun_oss import AliYunOss
from lesscode_utils.oss.ks3_oss import Ks3Oss


class CommonOss:
    def __init__(self, storage_type, **kwargs):
        """
        初始化OSS
        Args:
            storage_type (str): 存储类型，目前支持ks3和aliyun
        """
        self.storage_type = storage_type
        self.storage_config = kwargs.get("storage_config", {})
        if self.storage_type == "ks3":
            self.storage_instance = Ks3Oss(**self.storage_config)
        elif self.storage_type == "aliyun":
            self.storage_instance = AliYunOss(**self.storage_config)
        else:
            raise Exception("storage_type is not support")

    def __getattr__(self, item):
        return getattr(self.storage_instance, item)

    def upload(self, data_type: str, key: str, **kwargs):
        if self.storage_type == "ks3":
            if data_type == "string":
                data = {
                    "key": key,
                    "string_data": kwargs.pop("string_data"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            elif data_type == "file":
                data = {
                    "key": key,
                    "fp": kwargs.pop("data"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            elif data_type == "filename":
                data = {
                    "key": key,
                    "filename": kwargs.pop("filename"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            elif data_type == "network":
                data = {
                    "key": key,
                    "object_key_name": kwargs.pop("object_key_name"),
                    "source_url": kwargs.pop("source_url"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            else:
                raise Exception("data_type is not support")
        elif self.storage_type == "aliyun":
            if data_type == "string":
                data = {
                    "key": key,
                    "data": kwargs.pop("string_data"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            elif data_type == "file":
                data = {
                    "key": key,
                    "data": kwargs.pop("data"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            elif data_type == "filename":
                data = {
                    "key": key,
                    "filename": kwargs.pop("filename"),
                    "content_type": data_type
                }
                return self.storage_instance.save(**data, **kwargs)
            else:
                raise Exception("data_type is not support")
        else:
            raise Exception("storage_type is not support")

    def download(self, key):
        if self.storage_type == "ks3":
            return self.storage_instance.get_file(key)
        elif self.storage_type == "aliyun":
            return self.storage_instance.get_file(key)
        else:
            raise Exception("storage_type is not support")
