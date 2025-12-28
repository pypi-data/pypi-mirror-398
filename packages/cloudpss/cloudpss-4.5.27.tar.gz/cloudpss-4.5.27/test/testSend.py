import os,sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..\\'))
import cloudpss 
import logging


    
if __name__ == '__main__':
    # logging.basicConfig(level=logging.DEBUG)
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.45/'
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODMzNSIsImZ1bmN0aW9uOjk4MzM1IiwiYXBwbGljYXRpb246OTgzMzUiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzI2MjA4NjM5LCJub3RlIjoidGVzdDIiLCJpYXQiOjE2OTUxMDQ2Mzl9.ZlFSPCH3u4OSBlDBJWve4GZkWIZAku_DI1j-or-uDtAtyDy-RZecn7RBhymsILNPsmKnwkXcx1UnsjRNiAf5yA')
    # job = cloudpss.Job.fetch()
    
    model = cloudpss.Model.fetch('model/admin/shm_test_2')
    
    jobConfig = model.jobs[0]
    jobConfig['args']['stop_on_entry']='1'
    runner =model.run(job=jobConfig)
    
  
    ## 程序启动时将在第一个时步暂停，以下代码实现每隔 5s 算例往前运行 0.5s
    step=1
    i=1
    t=0
    while not runner.status():
        time.sleep(0.1)
        runner.result.goto(t)
        i+=1
        runner.result.writeShm('flag2',float(i),0)
        # d =runner.result.getPlotChannelData(1,'a:0')
        # runner.result.writeShm('flag2',float(i),0)
        # i+=1
        # if t ==0:
        #     t+=step
            
        #     runner.result.goto(t)
        # if d is not None:
        #     ## 最后一个时间点为小于停止时间点的前一个时步，所以需要计算每个时步差（当前算例为等步长计算），由于输出的时间点为浮点数，因此需要考虑精度问题，这里使用了最后三个时步的差值来判断是否到达停止时间点
        #     if d['x'][-1]+(d['x'][-1]-d['x'][-3]) >=t:
        #         t+=step
        #         runner.result.goto(t)
        #         # runner.result.writeShm('flag2',float(t),0)
                
        #         time.sleep(5)
        #     print(d['x'][-1],d['x'][-3])
    print("end")