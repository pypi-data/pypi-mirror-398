
import time
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss
import time
import json

if __name__ == '__main__':
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.45/'
    print('CLOUDPSS connected')
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzk3NjgwMjIyLCJub3RlIjoieCIsImlhdCI6MTc2NjU3NjIyMn0.-9ysSYICRRdujF3i6-5LWyMphllw_0S8GHc3pxlnczJcRpOqMpmhDUSInBDRpiMgi4YhPc5NkkRCqePbOrFhkg')
    print('Token done')
    project = cloudpss.Model.fetch('model/admin/asdf1')
    # topology = cloudpss.ModelTopology.fetch("-xrS3SewFhpVYKBtIXLk-XDLCQRQnUmlIbXS3s4sdPUkPKeAMhXHjRgZD1JPjPfQ","emtp",{'args':{}})
    topology= project.fetchTopology(implementType='emtp',config={'args':{}},maximumDepth=50)
    print(topology.components)
    
    
    topology.dump(topology,'testTopology11.json',indent=2)
    
    
    # topology2 = cloudpss.ModelTopology.fetch('', 'emtp', {'args': {}}, maximumDepth=5, topology=topology)
    
    
    # print(topology2.components)
    # topology2.dump(topology2,'testTopology2.json',indent=2)
    
    
    # topology3= project.fetchTopology(config={'args':{}},maximumDepth=5)
    # print(topology3.components)
    
    
    # topology3.dump(topology3,'testTopology3.json',indent=2)