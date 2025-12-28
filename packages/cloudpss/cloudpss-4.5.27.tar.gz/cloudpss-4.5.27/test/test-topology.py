import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss
import time
import numpy as np
import json

if __name__ == '__main__':
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.233/'
    print('CLOUDPSS connected')
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzY1NTI4NTc3LCJub3RlIjoieHgiLCJpYXQiOjE3NjUyNjkzNzd9.zsnfm8P08gwcW8mKKwq7qvJtbTz5lLyVFLe14SGe8JynNb6Ag-ghG3Pq-NRUrcQM2mOD46f8N__hJtfAnLrzLg')
    print('Token done')
    project = cloudpss.Model.fetch('model/admin/test2')
    
    topology = project.fetchTopology(config={'args':{}},maximumDepth=10)




    topology.dump(topology,'test.json')
    
    
    