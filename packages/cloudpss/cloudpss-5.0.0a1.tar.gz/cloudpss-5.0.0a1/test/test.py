
import time
import sys
import os

import redis

sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss
import time
import numpy as np
import pandas as pd
import json

if __name__ == '__main__':
    
    client = redis.Redis(host='10.101.10.46',port=6379)
    client.publish('read','1')
    ps = client.pubsub()
    # os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.45/'
    # print('CLOUDPSS connected')
    # cloudpss.setToken(
    #     'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODMzNSIsImZ1bmN0aW9uOjk4MzM1IiwiYXBwbGljYXRpb246OTgzMzUiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzI0NTU3MDIzLCJub3RlIjoiYSIsImlhdCI6MTY5MzQ1MzAyM30._Xuyo62ESKLcIAFeNdnfBM44yPiiXli9OPKvXDzL2rPV4J1_qsGZP--bsS1tXAVy-x8ooUIIAAG1yhwmZuk7-Q')
    # print('Token done')
    # # project = cloudpss.Model.fetch('model/admin/7744b02b-0636-5a39-8c16-eca939259ee1')
    # topology = cloudpss.ModelTopology.fetch("-xrS3SewFhpVYKBtIXLk-XDLCQRQnUmlIbXS3s4sdPUkPKeAMhXHjRgZD1JPjPfQ","emtp",{'args':{}})
    
    
    
    # # topology= project.fetchTopology(config={'args':{}})

    # topology.dump(topology,'test.json')
    
    
    
