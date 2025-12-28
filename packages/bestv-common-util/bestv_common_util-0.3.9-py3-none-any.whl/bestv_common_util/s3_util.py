# -*- coding: utf-8 -*-

import logging
import os
import boto3
from botocore.exceptions import NoCredentialsError
import itertools
from .str_util import extract_bucket, extract_object_key


class S3Util:
    # ACCESS_KEY_ID = None
    # ACCESS_KEY_SECRET = None
    # REGION = None
    client = None

    def __init__(self, access_key_id, access_key_secret, region, endpoint_url):
        # self.ACCESS_KEY_ID = access_key_id
        # self.ACCESS_KEY_SECRET = access_key_secret
        # self.REGION = REGION
        self.client = boto3.client('s3', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=access_key_secret, endpoint_url=endpoint_url)

    def upload_file(self, local_file, remote_file):
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        try:
            self.client.upload_file(local_file, bucket_name, object_key)
            logging.info("file: %s upload completed!", object_key)
            return True
        except FileNotFoundError:
            logging.error("file: %s local file not found", local_file)
            return False
        except NoCredentialsError:
            logging.error("AWS no Credential")
            return False

    def upload_dir(self, local_dir, remote_dir, excludes=[]):
        bucket_name = extract_bucket(remote_dir)
        object_path = extract_object_key(remote_dir)
        if os.path.isdir(local_dir):
            for root, dir, files in os.walk(local_dir):
                for filename in files:
                    fullpath = os.path.join(root, filename)
                    object_key = object_path + (fullpath[len(local_dir):].replace('\\', '/'))
                    if not any(item and len(item) > 0 and item in fullpath for item in excludes):
                        self.client.upload_file(fullpath, bucket_name, object_key)
                        logging.info("file: %s upload completed!", object_key)
        logging.info("dir: %s upload completed!", local_dir)

    def download_file(self, remote_file, local_file):
        bucket_name = extract_bucket(remote_file)
        object_key = extract_object_key(remote_file)
        try:
            self.client.download_file(bucket_name, object_key, local_file)
            logging.info("%s download completed!", local_file)
            return True
        except FileNotFoundError:
            logging.error("%s S3 object not found", object_key)
            return False
        except NoCredentialsError:
            logging.error("AWS no Credential")
            return False

    def has_object(self, bucket, prefix='', delimiter='/'):
        kwargs = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': delimiter, 'MaxKeys': 2}
        resp = self.client.list_objects_v2(**kwargs)
        return resp.get("KeyCount") > 0

    def get_matching_s3_prefix(self, bucket, prefix='', suffix='', delimiter='/'):
        """
        Generate the prefix in an S3 bucket.

        :param bucket: Name of the S3 bucket.
        :param prefix: Only fetch keys that start with this prefix (optional).
        :param suffix: Only fetch keys that end with this suffix (optional).
        :param delimiter: A delimiter is a character you use to group keys (optional).
        """
        kwargs = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': delimiter, 'MaxKeys': 10000}
        while True:
            resp = self.client.list_objects_v2(**kwargs)
            if resp.get("CommonPrefixes"):
                for dir in resp.get("CommonPrefixes"):
                    key = dir.get("Prefix")
                    if key.endswith(suffix):
                        yield key
            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break

    def scan_deep_s3_prefix(self, bucket, prefix='', layer=1, delimiter='/'):
        """
        Generate the prefix in an S3 bucket.

        :param bucket: Name of the S3 bucket.
        :param prefix: Only fetch keys that start with this prefix (optional).
        :param layer: Directory recursion depth (optional).
        :param delimiter: A delimiter is a character you use to group keys (optional).
        """
        if layer <= 0:
            return
        # 'MaxKeys': 1000
        # 'MaxKeys': 500 * Prefix.count(Delimiter)
        kwargs = {'Bucket': bucket, 'Prefix': prefix, 'Delimiter': delimiter}
        resp = self.client.list_objects_v2(**kwargs)
        # print(resp)
        while True:
            if resp.get("CommonPrefixes"):
                for dir in resp.get("CommonPrefixes"):
                    next_prefix = dir.get("Prefix")
                    if layer > 1:
                        yield from scan_deep_s3_keys(bucket, next_prefix, layer-1, delimiter)
                    else:
                        yield next_prefix
                #     # print(dir.get())
                try:
                    kwargs['ContinuationToken'] = resp['NextContinuationToken']
                except KeyError:
                    break
            else:
                break

    def get_matching_s3_keys(self, bucket, prefix='', suffix=''):
        """
        Generate the keys in an S3 bucket.

        :param bucket: Name of the S3 bucket.
        :param prefix: Only fetch keys that start with this prefix (optional).
        :param suffix: Only fetch keys that end with this suffix (optional).
        """

        # If the prefix is a single string (not a tuple of strings), we can
        # do the filtering directly in the S3 API.
        kwargs = {'Bucket': bucket, 'Prefix': prefix}
        while True:

            # The S3 API response is a large blob of metadata.
            # 'Contents' contains information about the listed objects.
            resp = self.client.list_objects_v2(**kwargs)
            for obj in resp['Contents']:
                key = obj['Key']
                if key.startswith(prefix) and key.endswith(suffix):
                    yield key

            # The S3 API is paginated, returning up to 1000 keys at a time.
            # Pass the continuation token into the next response, until we
            # reach the final page (when this field is missing).
            try:
                kwargs['ContinuationToken'] = resp['NextContinuationToken']
            except KeyError:
                break



# keys = get_matching_s3_keys('ds-prod-rawdata', 'data/', 4)
#
# # paths = list(itertools.chain.from_iterable(keys))
# paths = list(keys)
# # print(sum(1 for _ in keys))
# print(len(paths))
# print(paths)



# paginator = s3.get_paginator("list_objects_v2")
#
# for page in paginator.paginate(Bucket="ds-dev-devops"):
#     print(page["Contents"])