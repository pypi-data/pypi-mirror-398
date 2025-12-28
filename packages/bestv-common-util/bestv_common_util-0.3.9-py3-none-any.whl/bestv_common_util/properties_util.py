#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
脚本名称：properties_handler.py
脚本功能：解析.properties配置文件
编写人：  pangtaishi
编写日期：2021-02-28
'''

import os
import sys
import logging


def __get_dict(str_name, dict_name, value):
    if str_name.find('.') > 0:
        k = str_name.split('.')[0]
        dict_name.setdefault(k, {})
        return __get_dict(str_name[len(k) + 1:], dict_name[k], value)
    else:
        dict_name[str_name] = value
        return


def load_dict(filename):
    props_file = open(filename, 'Ur')
    props = parse_properties(props_file.readlines())
    props_file.close()
    return props


def parse_dict(lines):
    props = {}
    for line in lines:
        line = line.strip().replace('\n', '')
        if line.find("#") != -1:
            line = line[0:line.find('#')]
        if line.find('=') > 0:
            strs = line.split('=')
            strs[1] = line[len(strs[0]) + 1:]
            __get_dict(strs[0].strip().strip("'").strip(), props, strs[1].strip().strip("'").strip())
    return props


def load_properties(filename):
    props_file = open(filename, 'Ur')
    props = parse_properties(props_file.readlines())
    props_file.close()
    return props


def parse_properties(lines):
    props = {}
    for line in lines:
        line = line.strip().replace('\n', '')
        if line.find("#") != -1:
            line = line[0:line.find('#')]
        if line.find('=') > 0:
            strs = line.split('=')
            strs[1] = line[len(strs[0]) + 1:]
            props[strs[0].strip().strip("'").strip()] = strs[1].strip().strip("'").strip()
    return props


def properties_to_dict(props):
    dict = {}
    if props and props.items():
        for key, value in props.items():
            __get_dict(key.strip().strip("'").strip(), dict, value.strip().strip("'").strip())
    return dict


def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def yaml_to_properties(yaml_str):
    import yaml
    data = yaml.safe_load(yaml_str)
    flat_data = flatten_dict(data)
    properties = "\n".join([f"{k}={v}" for k, v in flat_data.items()])
    return properties


def get_properties_by_prefix(props: dict, prefix: str):
    if props and prefix:
        prefix_len = len(prefix)
        dict = {}
        if props and props.items():
            for key, value in props.items():
                if key.startswith(prefix):
                    dict[key[prefix_len:]] = value
        return dict
    return props