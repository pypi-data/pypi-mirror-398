import os,sys
import time
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss 
import logging

def next(m):
    m.write({'type': 'debug', 'step': '-1'})
def goto(m,step):
    m.write({'type': 'debug', 'step': step})
def pause(m):
    m.write({'type': 'debug', 'step': 10})


def memory(m,path,buffer,offset):
    m.write({'type': 'memory', 'path': path,'value':buffer,'offset':offset})
    

    
if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.45/'
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODMzNSIsImZ1bmN0aW9uOjk4MzM1IiwiYXBwbGljYXRpb246OTgzMzUiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzI2MjA4NjM5LCJub3RlIjoidGVzdDIiLCJpYXQiOjE2OTUxMDQ2Mzl9.ZlFSPCH3u4OSBlDBJWve4GZkWIZAku_DI1j-or-uDtAtyDy-RZecn7RBhymsILNPsmKnwkXcx1UnsjRNiAf5yA')
    # job = cloudpss.Job.fetch()
    
    model = cloudpss.Model.fetch('model/admin/debug')
    
    jobConfig = model.jobs[4]
    jobConfig['args']['stop_on_entry']='1'
    modelJob =model.run(job=jobConfig)
    
    view =modelJob.result
    i=0
    while not view.end:
        i+=1
        print(view.getLogs())
        # print(view.getPlots())
        print('status2',view.end)
        view.next()
        view.control({
            "key":"/component_new_constant_1",
            "value":str(i),
            'uuid': str(uuid.uuid1()),
        })
        time.sleep(0.01)