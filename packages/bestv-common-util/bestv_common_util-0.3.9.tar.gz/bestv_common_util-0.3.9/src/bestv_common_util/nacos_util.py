# -*- coding: utf-8 -*-
import logging
import os
import sys


from alibabacloud_mse20190531.client import Client as mse20190531Client
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_mse20190531 import models as mse_20190531_models
from alibabacloud_tea_util import models as util_models
from .kms_util import KMSUtil


class NacosUtil:
    MSE_ENDPOINT = f'mse.cn-shanghai.aliyuncs.com'
    INSTANCE_ID = f'mse_prepaid_public_cn-7pp2io51d09'
    NAMESPACE_ID = None
    mse_client = None
    kms_util: KMSUtil = None

    def __init__(self, **kwargs):
        """
        :param kwargs:
        : server_addresses
        : namespace
        : access_key_id
        : access_key_secret
        : ram_role_name
        : aes_key_arn
        : encryption_context
        : kms_util
        """
        mse_endpoint = kwargs.get('mse_endpoint')
        instance_id = kwargs.get('instance_id')
        namespace_id = kwargs.get('namespace_id')
        access_key_id = kwargs.get('access_key_id')
        access_key_secret = kwargs.get('access_key_secret')
        ram_role_name = kwargs.get('ram_role_name')
        encryption_context = kwargs.get('encryption_context')
        kms_endpoint = kwargs.get('kms_endpoint')

        if not (access_key_id and access_key_secret) and not ram_role_name:
            raise Exception("RamRoleName or AK/SK cannot be null")
        if mse_endpoint and len(mse_endpoint) > 0:
            self.MSE_ENDPOINT = mse_endpoint
        if instance_id and len(instance_id) > 0:
            self.INSTANCE_ID = instance_id
        if namespace_id and len(namespace_id) > 0:
            self.NAMESPACE_ID = namespace_id
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
            credential=credential, endpoint=self.MSE_ENDPOINT
        )
        self.mse_client = mse20190531Client(config)
        self.kms_util = KMSUtil(kms_endpoint, access_key_id, access_key_secret, ram_role_name, encryption_context=encryption_context)

    def get_config(self, data_id=None, group='DEFAULT_GROUP'):
        if data_id and len(data_id) > 0:
            self.data_id = data_id
        if self.data_id and len(self.data_id) > 0:
            get_nacos_config_request = mse_20190531_models.GetNacosConfigRequest(
                instance_id=self.INSTANCE_ID,
                namespace_id=self.NAMESPACE_ID,
                group=group,
                data_id=data_id
            )
            runtime = util_models.RuntimeOptions()
            response = self.mse_client.get_nacos_config_with_options(get_nacos_config_request, runtime)
            context = response.body.configuration.content
            if context:
                return self.kms_util.decrypt_envelope(context, data_id.split(".")[-1])


        #
        #     if self.data_id.endswith('.properties'):
        #         return json.dumps(props_util.properties_to_dict(nacos_props))
        #     return json.dumps(nacos_props)
        # raise Exception("data_id cannot be null without a default value")

#
# nacos_util = NacosUtil(namespace_id="0238e844-3fef-436a-a683-a2eecb888e29",
#                        access_key_id=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_ID'),
#                        access_key_secret=os.environ.get('ALIBABA_CLOUD_ACCESS_KEY_SECRET'),
#                        ram_role_name=os.environ.get('ALIBABA_CLOUD_RAM_ROLE_NAME')
#                                                          )
# print(props_util.flatten_dict(nacos_util.get_config('cipher-ds-dataworks-api-prod.yaml')))
# print(props_util.get_properties_by_prefix(nacos_util.get_config('cipher-kms-aes-256-ds-toolbox.properties'), 'nebula.ds_rec.'))