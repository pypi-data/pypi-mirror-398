# coding=UTF-8

import json
import requests
import os
from collections import OrderedDict
from ..version import __version__
import logging
from cloudpss.utils.IO import IO

def request(method, uri, baseUrl=None, params={}, token=None, **kwargs):
    if baseUrl == None:
        baseUrl = os.environ.get('CLOUDPSS_API_URL', 'https://cloudpss.net/')
    url = requests.compat.urljoin(baseUrl,uri)
    if token is None:
        token = os.environ.get('CLOUDPSS_TOKEN', None)
    if token:
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json+gzip; charset=utf-8',
            "User-Agent": "cloudpss-sdk-python/" + __version__
        }
    else:
        raise Exception('token undefined')

    xToken =kwargs.get('xToken',None)
    if xToken:
        headers['x-Authorization'] = 'Bearer ' +xToken
        del kwargs['xToken']
        
    data = kwargs.get('data',None)
    if data:
        # headers['Content-Length'] = str(len(data))
        ## 判断 data 是否使用zip 压缩
        if data[0:2] != b'\x1f\x8b':
            headers = {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
                "User-Agent": "cloudpss-sdk-python/" + __version__
            }
        kwargs['data'] = data
    
    r = requests.request(method, url, params=params, headers=headers, **kwargs)
    
    if (uri.startswith('graphql')):
        if 'X-Cloudpss-Version' not in r.headers:
            raise Exception(
                '当前SDK版本（ver '+__version__ +'）与服务器版本（3.0.0 以下）不兼容，请更换服务器地址或更换SDK版本。')
        os.environ['X_CLOUDPSS_VERSION'] = r.headers['X-Cloudpss-Version']
        if float(r.headers['X-Cloudpss-Version']) >= 5:
            raise Exception('当前SDK版本（ver '+__version__ +'）与服务器版本（ver ' +
                            r.headers['X-Cloudpss-Version'] +
                            '.X.X）不兼容，请更换服务器地址或更换SDK版本(pip 使用 pip install -U cloudpss 命令更新, conda 使用 conda update cloudpss 命令更新)。')

    if r.ok:
        return r
    # logging.debug(r.text)
    # if r.text =="":
    print(r.status_code,r.text,kwargs)
    r.raise_for_status()
    if "statusCode" in r.text:
        t = json.loads(r.text)
        raise  Exception(t.get('errors',r.text))
    return r
    
