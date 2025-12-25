import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import time
tk = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTAyNiwidXNlcm5hbWUiOiJncmV5ZCIsInNjb3BlcyI6W10sInR5cGUiOiJhcHBseSIsImV4cCI6MTcxNDI2ODg5MSwiaWF0IjoxNjgzMTY0ODkxfQ.PdMMmsX1etXdPyS6ktZB3LvgRvqh6FL5jrJj2dfNhQyMKktWrKo64JLegWqsqnEJG-zwyTRS5vVsg-6eiVinXQ'
apiURL = 'https://cloudpss.net/';
username = 'greyd'
projectKey = '3m9btest'
cloudpss.setToken(tk)
os.environ['CLOUDPSS_API_URL'] = apiURL
project = cloudpss.Model.fetch('model/'+username+'/'+projectKey)
job = project.getModelJob("潮流计算方案 1")[0]
config = project.getModelConfig("参数方案 1")[0]
runner=project.run(job=job,config=config)
while runner.status()<1:
    for log in runner.result.getLogs():
        print(log)
        if('data' in log.keys() and 'content' in log['data'].keys()):
            print(log['data']['content'])
    print(runner.status())
    if runner.status()==-1:
        break
    time.sleep(2)
try:
    print(runner.result.getBuses())
except:
    print('nothing')

