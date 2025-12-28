# -*- coding: utf-8 -*-
import os
import sys
import logging
import re
import base64

from alibabacloud_kms20160120.client import Client as Kms20160120Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.client import Config as CredentialConfig
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_kms20160120 import models as kms_20160120_models
from alibabacloud_tea_util import models as util_models


class KMSUtil:
    ENCRYPTED_PROPERTY_PREFIX = "{cipher}"
    ENCRYPTED_PATTERN = "^(\\((?P<context>.*)\\)|\\[(?P<options>.*)]){0,2}(?P<cipher>.*)$"
    UTF_8 = "utf-8"
    ENDPOINT = 'kms.cn-shanghai.aliyuncs.com'
    ENCRYPTION_CONTEXT = {"ValidKey": "@@JL*%$DF@VS"}
    kms_client = None

    def __init__(self, endpoint=None, access_key_id=None, access_key_secret=None, ram_role_name=None, encryption_context=None):
        if not (access_key_id and access_key_secret) and not ram_role_name:
            raise Exception("RamRoleName or AK/SK cannot be null")
        if endpoint and len(endpoint) > 0:
            self.ENDPOINT = endpoint
        if encryption_context and len(encryption_context) > 0:
            self.ENCRYPTION_CONTEXT = encryption_context
        if ram_role_name and len(ram_role_name) > 0:
            credential = CredentialClient(CredentialConfig(
                type='ecs_ram_role',
                role_name=ram_role_name
            ))
        else:
            credential = CredentialClient(CredentialConfig(
                type='access_key',
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
            ))
        config = open_api_models.Config(
            credential=credential, endpoint=self.ENDPOINT
        )
        self.kms_client = Kms20160120Client(config)

    @staticmethod
    def parse_encrypted_token(cipher_text: str):
        temp = cipher_text.strip()
        if len(temp) > 0:
            if temp.startswith(KMSUtil.ENCRYPTED_PROPERTY_PREFIX):
                temp = temp[len(KMSUtil.ENCRYPTED_PROPERTY_PREFIX):]
            match_group = re.search(KMSUtil.ENCRYPTED_PATTERN, temp).groupdict()
            return KMSUtil.parse_encryption_context(match_group.get("context")), match_group.get("cipher")

    @staticmethod
    def parse_encryption_context(context: str):
        temp = context.strip()
        if temp and len(temp) > 0:
            dict = {}
            for pair in temp.split(","):
                kv = pair.split("=")
                if len(kv) > 1:
                    dict[kv[0]] = str(base64.b64decode(kv[1]), KMSUtil.UTF_8)
            return dict


    def encrypt(self, key_id, plain_text):
        encrypt_request = kms_20160120_models.EncryptRequest(
            key_id=key_id,
            plaintext=base64.b64encode(plain_text.encode('utf-8')).decode('utf-8'),
            encryption_context=self.ENCRYPTION_CONTEXT,
        )
        runtime = util_models.RuntimeOptions()
        response = self.kms_client.encrypt_with_options(encrypt_request, runtime)
        return response.body.ciphertext_blob


    def decrypt(self, cipher_text):
        decrypt_request = kms_20160120_models.DecryptRequest(
            encryption_context=self.ENCRYPTION_CONTEXT,
            ciphertext_blob=cipher_text
        )
        runtime = util_models.RuntimeOptions()
        response = self.kms_client.decrypt_with_options(decrypt_request, runtime)
        return base64.b64decode(response.body.plaintext).decode('utf-8')


    def decrypt_envelope(self, context: str, context_type: str):
        if context:
            if "properties" == context_type.lower().strip():
                from .properties_util import parse_properties
                cipher_props = parse_properties(context.split("\n"))
                plain_props = {}
                if cipher_props:
                    for key, value in cipher_props.items():
                        if str(value).startswith(self.ENCRYPTED_PROPERTY_PREFIX):
                            plain_props[key] = self.decrypt(str(value)[str(value).rfind(')') + 1:])
                        else:
                            plain_props[key] = value
                return plain_props
            elif "yaml" == context_type.lower().strip():
                import yaml
                cipher_yaml = yaml.load(context, Loader=yaml.FullLoader)
                KMSUtil.decrypt_dict(cipher_yaml, self.decrypt)
                return cipher_yaml

    @staticmethod
    def decrypt_dict(data, _func):
        if data and isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    KMSUtil.decrypt_dict(value, _func)
                elif isinstance(value, str) and str(value).startswith(KMSUtil.ENCRYPTED_PROPERTY_PREFIX):
                    context, cipher = KMSUtil.parse_encrypted_token(value)
                    data[key] = _func(cipher)
                else:
                    data[key] = value

#
# kms_util = KMSUtil(access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
#                    access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
#                    ram_role_name=os.environ.get('ALIBABA_CLOUD_RAM_ROLE_NAME'))
# print(kms_util.encrypt("9900c848-5626-4f64-9eb3-ec91493852d3", "nebula"))