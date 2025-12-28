from ast import mod
import sys,os

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss # 引入 cloudpss 依赖
import json
import time


if __name__ == '__main__':
    
    # 申请 token 
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzk0MzE5MDUwLCJub3RlIjoidGVzdC1ydCIsImlhdCI6MTc2MzIxNTA1MH0.BgWaHXf1Zoy6THILV44RYY21xKjhFh-O5MyYSK6nOpqvEVRus8kpfL4sow26yrM4UAAe-boZ_J7zOqiygYYxqg')

    # 设置目标 API 地址（可选，默认地址为 https://cloudpss.net/ ）
    os.environ['CLOUDPSS_API_URL'] = 'http://10.109.10.31/'
    
    
    
    model = cloudpss.Model.fetch('model/admin/YuE_MMC_RTDS_Model_Main_CM') # 获取指定 rid 的算例项目
    
    
    virtual_input_cell = model.getComponentsByRid('model/CloudPSS/_VirtualInput')  # 获取虚拟输入单元组件
    inputs ={}
    for key,cell in virtual_input_cell.items():
        inputs[cell.args['portName']] = cell.args['initial_value']
    print('初始虚拟输入数据:',inputs) # 输出初始虚拟输入数据,可以打印出来查看哪些输入参数可以设置
    runner = model.run() # 启动计算任务
    runner.result.virtualInput.update(**inputs) # 设置虚拟输入数据
    xx =[1,2,3,4,5,6,7,8,9,10]
    tt=1
    while not runner.status(): 
        mLen = runner.result.getMessageLength()
        if mLen > 0:
            for _ in range(mLen):
                log = runner.result.pop() # 实时的日志两比较大，需要将日志及时从缓存中弹出，否则会占用大量内存
                if log.get('key','')=='table-1':
                    print(log) #输出日志
        
        if tt%500==0:
            mag = xx[(tt//500)%10]
            print(f'更新虚拟输入数据 Mag={mag}')
            runner.result.virtualInput.update(Mag=mag) # 每隔一段时间更新虚拟输入数据，参数根据实际需要设置，可以设置多个update(Mag=mag,xx=yy,zz=zz)
            runner.result.send(runner.result.virtualInput) # 发送更新后的虚拟输入数据到计算任务中
        time.sleep(0.01) # 本测试例为快速循环等待，实际应用中可根据需要调整等待时间
        tt+=1
        
    print('计算任务完成，获取所有消息数据')
    print('end',runner.status()) # 运行结束
    