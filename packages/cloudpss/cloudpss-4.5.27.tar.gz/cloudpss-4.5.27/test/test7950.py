import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time
if __name__ == '__main__':
    print('start')
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6W10sInR5cGUiOiJhcHBseSIsImV4cCI6MTcyNjkwMjA0MCwiaWF0IjoxNjk1Nzk4MDQwfQ.qktX85dOW21jJb-sunrXZjiYSAj94ZRfh6XPE_pnMGsBMXffRc5zp40sDuJ4jVSlI2ak6ybAsm9vbY0cPWpiBg'
    )

    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.119/'
    ts1 = time.time()
    ### 获取指定 rid 的项目
    model = cloudpss.Model.fetch('model/admin/core_test')

    job=model.jobs[2]
    job['args']['n_cpu']='8'
    job['args']['@debug']='min_cpu=0'
    
    ts2 = time.time()
    print('time 1:', ts2 - ts1, flush=True)
    runner = model.run()
    while not runner.status():
        time.sleep(1)

    logs = runner.result.getLogs()
    for log in logs:
        if log['type'] == 'log':
            if log['data']['content'].find('thread 0 total time')>0:
                print(log['data']['content'])
                break
    print('end')
