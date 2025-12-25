# coding=UTF-8
import json
from cloudpss.utils import request
from cloudpss.utils.IO import IO


def graphql_request(query, variables=None, baseUrl=None,token=None,**kwargs):
    payload = {'query': query, 'variables': variables}
    
    
    r = request('POST', 'graphql', data=IO.serialize(payload,'json'),baseUrl=baseUrl,token=token, **kwargs)

    return json.loads(r.text)
