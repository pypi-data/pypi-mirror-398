# encoding: utf-8
import pytz
import time
import datetime
import pandas as pd
import requests
import json
import re
import logging


if __name__ == '__main__':
    ram_role_name = 'ecs-opg211-prod-ds-rec'
    url = 'http://100.100.100.200/latest/meta-data/ram/security-credentials/%s'
    logging.info(url)
    headers = {
        "Content-Type": "application/json; charset=UTF-8"
    }

    res = requests.get(url % ram_role_name, headers=headers)
    if res.ok:
        result_json = json.dumps(res.text)
        print(result_json['AccessKeyId'], result_json['AccessKeySecret'])




