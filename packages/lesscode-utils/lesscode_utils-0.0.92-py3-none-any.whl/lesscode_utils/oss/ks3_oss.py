import importlib
import math
import os


class Ks3Oss:
    def __init__(self, **kwargs):
        """
        :param kwargs:{
                        "access_key_id":"",
                        "access_key_secret":"",
                        "host":"",
                        "is_secure":None,
                        "bucket_name":None
                    }
        """
        bucket_name = kwargs.pop("bucket_name", None)
        try:
            ks3_connection = importlib.import_module("ks3.connection")
        except ImportError:
            raise Exception(f"ks3sdk is not exist,run:pip install ks3sdk==1.5.0")
        self.client = ks3_connection.Connection(**kwargs)
        if bucket_name is not None:
            self.instance = self.client.get_bucket(bucket_name)
        else:
            self.instance = None

    def create_bucket(self, bucket_name, **kwargs):
        bucket = self.client.create_bucket(bucket_name=bucket_name, **kwargs)
        return bucket

    def list_buckets(self, **kwargs):
        buckets = self.client.get_all_buckets(**kwargs)
        return [b.name for b in buckets]

    def delete_bucket(self, bucket_name, **kwargs):
        return self.client.delete_bucket(bucket_name, **kwargs)

    def save(self, key, bucket_name="", content_type="string", protocol="https", domain="ksyun.com",
             region="ks3-cn-beijing", **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        k = self.instance.new_key(key)
        ret = None
        if content_type == "string":
            ret = k.set_contents_from_string(**kwargs)
        elif content_type == "file":
            ret = k.set_contents_from_file(**kwargs)
        elif content_type == "filename":
            ret = k.set_contents_from_filename(**kwargs)
        elif content_type == "network":
            ret = k.fetch_object(**kwargs)
        if ret:
            if ret.status == 200:
                return f'{protocol}://{self.instance.name}.{region}.{domain}/{key}'
            else:
                return False
        else:
            return False

    def get_url(self, key, bucket_name="", region="ks3-cn-beijing", domain="ksyun.com", protocol="https", **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        if self.instance.get_key(key, **kwargs):
            return f'{protocol}://{self.instance.name}.{region}.{domain}/{key}'
        else:
            return None

    def get_file(self, key, bucket_name="", file_path=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        k = self.instance.get_key(key)
        if file_path:
            k.get_contents_to_filename(file_path, **kwargs)
            return True
        else:
            contents = k.get_contents_as_string(**kwargs)
            return contents

    def get_key(self, key, bucket_name="", **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name, **kwargs)
        k = self.instance.get_key(key)
        return k

    def delete_file(self, key, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name, **kwargs)
        res = self.instance.delete_key(key)
        return res

    def list_file(self, bucket_name, delimiter="/", **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        keys = self.instance.list(delimiter=delimiter, **kwargs)
        files = list()
        dirs = list()
        try:
            ks3_key = importlib.import_module("ks3.key")
            ks3_prefix = importlib.import_module("ks3.prefix")
        except ImportError:
            raise Exception(f"ks3sdk is not exist,run:pip install ks3sdk==1.5.0")
        for k in keys:
            if isinstance(k, ks3_key.Key):
                files.append(k.name)
            elif isinstance(k, ks3_prefix.Prefix):
                dirs.append(k.name)

        for p in dirs:
            keys = self.instance.list(prefix=p, delimiter=delimiter, **kwargs)
            for k in keys:
                if isinstance(k, ks3_key.Key):
                    files.append(k.name)
                elif isinstance(k, ks3_prefix.Prefix):
                    dirs.append(k.name)
        return dirs, files

    def get_bucket_acl(self, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        acl = self.instance.get_acl(**kwargs)
        return acl

    def set_bucket_acl(self, bucket_name=None, *args, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        return self.instance.set_acl(*args, **kwargs)

    def get_bucket_policy(self, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        policy = self.instance.get_bucket_policy(**kwargs)
        return policy

    def set_bucket_policy(self, policy, bucket_name=None, headers=None):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        return self.instance.set_bucket_policy(policy, headers)

    def delete_bucket_policy(self, bucket_name=None, headers=None):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        return self.instance.delete_bucket_policy(headers)

    def multipart_upload(self, file_path, chunk_size, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        file_size = os.stat(file_path).st_size
        mp = self.instance.initiate_multipart_upload(os.path.basename(file_path), **kwargs)
        chunk_count = int(math.ceil(file_size * 1.0 / chunk_size * 1.0))
        for i in range(chunk_count):
            offset = chunk_size * i
            chunk_bytes = min(chunk_size, file_size - offset)
            try:
                filechunkio = importlib.import_module("filechunkio")
            except ImportError:
                raise Exception(f"filechunkio is not exist,run:pip install filechunkio==1.8")
            with filechunkio.FileChunkIO(file_size, 'r', offset=offset, bytes=chunk_bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)
        ret = mp.complete_upload()
        return ret

    def list_multipart_upload_parts(self, key, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        mp = self.instance.initiate_multipart_upload(key, **kwargs)
        return mp.get_all_parts()

    def list_multipart_uploads(self, key, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        return self.instance.list_multipart_uploads(key, **kwargs)

    def generate_url(self, key, bucket_name=None, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        key_kwargs = kwargs.get("key_kwargs", {})
        url_kwargs = kwargs.get("url_kwargs", {})
        k = self.instance.get_key(key, **key_kwargs)
        if k:
            url = k.generate_url(**url_kwargs)
            return url
        else:
            return None

    def get_presigned_url(self, key, second, bucket_name=None, expires_in_absolute=False, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        k = self.instance.new_key(key)
        if k:
            url = k.get_presigned_url(second=second, expires_in_absolute=expires_in_absolute, **kwargs)
            return url
        else:
            return None

    def modify_object(self, bucket_name=None, *args, **kwargs):
        if bucket_name:
            self.instance = self.client.get_bucket(bucket_name)
        return self.instance.copy_key(*args, **kwargs)
