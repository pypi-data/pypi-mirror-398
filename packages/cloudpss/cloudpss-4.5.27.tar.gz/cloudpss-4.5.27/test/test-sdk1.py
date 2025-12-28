import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time
if __name__ == '__main__':
    print('start')
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.45/'
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODMzNSIsImZ1bmN0aW9uOjk4MzM1IiwiYXBwbGljYXRpb246OTgzMzUiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzI2MjA4NjM5LCJub3RlIjoidGVzdDIiLCJpYXQiOjE2OTUxMDQ2Mzl9.ZlFSPCH3u4OSBlDBJWve4GZkWIZAku_DI1j-or-uDtAtyDy-RZecn7RBhymsILNPsmKnwkXcx1UnsjRNiAf5yA')
    ts1 = time.time()
    ### 获取指定 rid 的项目
    project = cloudpss.Model.fetch('model/CloudPSS/IEEE3')

    ts2 = time.time()
    print('time 1:', ts2 - ts1, flush=True)
    runner = project.run()
    while not runner.status():
        # print('running', flush=True)
        logs = runner.result.getLogs()
        if (len(logs) > 1):
            print(logs)
            t = time.time()
            print('s time 2:', t - ts1, t - ts2, flush=True)
        # for log in logs:
        #     print(log)
        time.sleep(0.1)

    # 打印 0 号分组数据
    # print(runner.result.getPlot(0))
    # filePath = 'D:\\data\\result\\test.cjob'
    # cloudpss.Result.dump(runner.result, filePath)
    print('end')
