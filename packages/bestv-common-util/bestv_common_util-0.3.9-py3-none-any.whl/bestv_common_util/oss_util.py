import logging
import os
import oss2

from .str_util import extract_bucket, extract_object_key


# def extract_path(filepath):
#     """
#     D:/mnt/data/private/model/20230607 => /mnt/data/private/model/20230607
#     oss://opg211-dev-ds-export/private/model/20230607 => /mnt/data/private/model/20230607
#     :param filepath:
#     :return:
#     """


class OSSUtil:
    ACCESS_KEY_ID = None
    ACCESS_KEY_SECRET = None
    ENDPOINT = None

    def __init__(self, access_key_id, access_key_secret, endpoint):
        self.ACCESS_KEY_ID = access_key_id
        self.ACCESS_KEY_SECRET = access_key_secret
        self.ENDPOINT = endpoint

    def get_object(self, remote_file):
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        try:
            if bucket_name:
                bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
                return str(bucket.get_object(object_key).read(), encoding='utf-8')
            else:
                logging.error("file: %s, format error, must be complete!", object_key)
        except Exception as e:
            logging.error(e)

    def put_object(self, object, remote_file):
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        if bucket_name:
            bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
            bucket.put_object(object_key, object)
            logging.info("file: %s upload completed!", object_key)
            return True
        else:
            logging.error("file: %s, format error, must be complete!", object_key)

    def upload_file(self, local_file, remote_file):
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        if bucket_name:
            bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
            with open(local_file, "rb") as f:
                bucket.put_object(object_key, f)
                logging.info("file: %s upload completed!", object_key)
                return True
        else:
            logging.error("file: %s, format error, must be complete!", object_key)

    def upload_dir(self, local_dir, remote_dir, excludes=[]):
        bucket_name = extract_bucket(remote_dir)
        object_path = extract_object_key(remote_dir)
        bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
        upload_files_num = 0
        if os.path.isdir(local_dir):
            for root, dir, files in os.walk(local_dir):
                for filename in files:
                    fullpath = os.path.join(root, filename)
                    object_key = object_path + (fullpath[len(local_dir):].replace('\\', '/'))
                    if not any(item and len(item) > 0 and item in fullpath for item in excludes):
                        with open(fullpath, "rb") as f:
                            bucket.put_object(object_key, f)
                            upload_files_num += 1
                            logging.info("file: %s upload completed!", object_key)
        logging.info("dir: %s upload completed! upload files num: %s", local_dir, upload_files_num)

    def download_file(self, remote_file, local_file, force=False):
        if not force and os.path.exists(local_file):
            logging.info("file: %s local already exists", local_file)
            return True
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
        object_stream = bucket.get_object(object_key)
        local_dir = os.path.dirname(local_file)
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        with open(local_file, "wb") as f:
            f.write(object_stream.read())
            logging.info("file: %s download completed!", local_file)
            return True

    def download_dir(self, remote_dir, local_dir, ext='', excludes=[]):
        """
        :param remote_dir:
        :param local_dir:
        :param ext:
        :param excludes:
        :return:
        """
        bucket_name = extract_bucket(remote_dir)
        prefix = extract_object_key(remote_dir)
        bucket = oss2.Bucket(oss2.Auth(self.ACCESS_KEY_ID, self.ACCESS_KEY_SECRET), self.ENDPOINT, bucket_name)
        for obj in oss2.ObjectIterator(bucket, prefix=prefix):
            if not obj.key.endswith("/") and obj.key.endswith(ext):
                if not any(item and len(item) > 0 and item in obj.key for item in excludes):
                    local_file = os.path.join(local_dir, obj.key[len(prefix):]).replace('\\', '/')
                    local_path = os.path.dirname(local_file)
                    if not os.path.exists(local_path):
                        os.makedirs(local_path)
                    object_stream = bucket.get_object(obj.key)
                    with open(local_file, "wb") as f:
                        f.write(object_stream.read())
                        logging.info("file: %s download completed!", obj.key)
        logging.info("dir: %s download completed!", remote_dir)

# 调用示例
# uploaded = upload_file('D:/mnt/2023-05-06-epg.csv', 'temp/remote_file.csv')
# downloaded = download_file('temp/remote_file.csv', 'D:/mnt/local_file_001.csv')
# upload_dir('D:/mnt/data/private/temp', 'temp/test_dir', [''])
# print(os.path.dirname('D:/mnt/data/private/test/remote_file.csv'))
# print(extract_dir("oss://opg211-dev-ds-export/private/model/20230607"))
# print(extract_dir("s3://opg211-dev-ds-export/private/model/20230607"))
