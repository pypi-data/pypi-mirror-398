import importlib
import os
from typing import List


class AliYunOss:
    def __init__(self, **kwargs):

        """

        :param kwargs: {
                        "access_key_id":"",
                        "access_key_secret":"",
                        "endpoint":"",
                        "session":None,
                        "connect_timeout":None,
                        "app_name":None,
                        "proxies":None,
                        "region":"",
                        "cloudbox_id":"",
                        "is_path_style":"",
                        "bucket_name":""

                    }
        """

        try:
            oss2 = importlib.import_module("oss2")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        bucket_name = kwargs.pop("bucket_name", "")
        auth_config = {
            "access_key_id": kwargs.pop("access_key_id", ""),
            "access_key_secret": kwargs.pop("access_key_secret", "")
        }
        self.auth = oss2.Auth(**auth_config)
        self.endpoint = kwargs.pop("endpoint", "")
        config = {
            "auth": self.auth,
            "endpoint": self.endpoint,
            "session": kwargs.pop("session", None),
            "connect_timeout": kwargs.pop("connect_timeout", None),
            "app_name": kwargs.pop("app_name", ''),
            "proxies": kwargs.pop("proxies", None),
            "region": kwargs.pop("region", None),
            "cloudbox_id": kwargs.pop("cloudbox_id", None),
            "is_path_style": kwargs.pop("is_path_style", False)
        }
        self.client = oss2.Service(**config)
        if bucket_name is not None:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        else:
            self.instance = None

    def get_bucket_instance(self, bucket_name=None):
        try:
            oss2 = importlib.import_module("oss2")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        return self.instance

    def create_bucket(self, bucket_name, **kwargs):
        if not self.instance:
            self.instance = self.get_bucket_instance(bucket_name)
        bucket = self.instance.create_bucket(**kwargs)
        return bucket

    def list_buckets(self, **kwargs):
        try:
            oss2 = importlib.import_module("oss2")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        return [b.name for b in oss2.BucketIterator(self.client, **kwargs)]

    def delete_bucket(self, bucket_name):
        if not self.instance:
            self.instance = self.get_bucket_instance(bucket_name)
        return self.instance.delete_bucket()

    def save(self, key, content_type, data, bucket_name="", **kwargs):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        if content_type == "filename":
            self.instance.put_object_from_file(key=key, filename=data, **kwargs)
        elif content_type == "network":
            self.instance.put_object(key=key, data=data, **kwargs)
        else:
            self.instance.put_object(key=key, data=data, **kwargs)

    def get_url(self, key, bucket_name="", region="oss-cn-hangzhou", domain="aliyuncs.com", protocol="https"):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        return f'{protocol}://{self.instance.name}.{region}.{domain}/{key}'

    def get_file(self, key, bucket_name="", file_path=None, **kwargs):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        if file_path:
            self.instance.get_object_to_file(key=key, filename=file_path, **kwargs)
        else:
            return self.instance.get_object(key=key, **kwargs)

    def get_key(self, key, bucket_name="", **kwargs):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        k = self.instance.head_object(key, **kwargs)
        return k

    def delete_file(self, key, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        res = self.instance.delete_object(key, **kwargs)
        return res

    def list_file(self, bucket_name, **kwargs):
        try:
            oss2 = importlib.import_module("oss2")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        files = [k.key for k in oss2.ObjectIterator(self.instance, **kwargs)]
        return files

    def get_bucket_referer(self, bucket_name=None):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        acl = self.instance.get_bucket_referer()
        return acl

    def set_bucket_referer(self, bucket_name=None, **kwargs):
        try:
            oss2 = importlib.import_module("oss2")
            models = importlib.import_module("oss2.models")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        return self.instance.put_bucket_referer(models.BucketReferer(**kwargs))

    def get_bucket_cors(self, bucket_name=None):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        cors = self.instance.get_bucket_cors()
        return cors

    def set_bucket_cors(self, cors: List[dict], bucket_name=None):
        try:
            oss2 = importlib.import_module("oss2")
            models = importlib.import_module("oss2.models")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        rules = [models.CorsRule(**_) for _ in cors]
        return self.instance.put_bucket_cors(rules)

    def delete_bucket_cors(self, bucket_name=None):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        return self.instance.delete_bucket_cors()

    def multipart_upload(self, key, file_path, preferred_size, bucket_name=None, **kwargs):
        try:
            oss2 = importlib.import_module("oss2")
            models = importlib.import_module("oss2.models")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        total_size = os.path.getsize(file_path)
        part_size = oss2.determine_part_size(total_size, preferred_size=preferred_size)
        upload_id = self.instance.init_multipart_upload(key).upload_id
        parts = []
        with open(file_path, 'rb') as f:
            part_number = 1
            offset = 0
            while offset < total_size:
                num_to_upload = min(part_size, total_size - offset)
                result = self.instance.upload_part(key, upload_id, part_number,
                                                   oss2.SizedFileAdapter(f, num_to_upload))
                parts.append(models.PartInfo(part_number, result.etag))

                offset += num_to_upload
                part_number += 1
        ret = self.instance.complete_multipart_upload(key, upload_id, parts, **kwargs)
        return {"result": ret, "upload_id": upload_id}

    def list_multipart_uploads(self, key, upload_id, bucket_name=None, **kwargs):
        try:
            oss2 = importlib.import_module("oss2")
        except ImportError:
            raise Exception(f"oss2 is not exist,run:pip install oss2")
        if bucket_name:
            self.instance = oss2.Bucket(auth=self.auth, endpoint=self.endpoint, bucket_name=bucket_name)
        return oss2.PartIterator(self.instance, key, upload_id, **kwargs)

    def get_sign_url(self, key, expires, bucket_name=None, headers=None, params=None, slash_safe=False):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        url = self.instance.sign_url('GET', key, expires, slash_safe=slash_safe, headers=headers, params=params)
        return url

    def modify_object(self, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.get_bucket_instance(bucket_name)
        source_bucket_name = bucket_name if bucket_name else self.instance.name
        return self.instance.copy_object(source_bucket_name=source_bucket_name, **kwargs)

    def get_regions(self, regions):
        return self.client.describe_regions(regions=regions)
