import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time
if __name__ == '__main__':
    print('start')
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiYWRtaW4iXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzk1MjQ0MTY5LCJub3RlIjoidCIsImlhdCI6MTc2NDE0MDE2OX0.v7PRdYzgP9ok_TeEwLzQKobNJpDT66Nbj8aFmexb-JNo21q5gwrtTiukBtnmSa-FX42ZeSZPjPBbYBemLNlmfg'
    )
    os.environ["CLOUDPSS_API_URL"] = "https://dev.local.ddns.cloudpss.net/" 
    model =cloudpss.Model.fetch("model/admin/test12")  
    
    
    runner= model.run()
    result=runner.result
    status=0
    while not runner.status():  ## 等待计算完成
        
        mLen = runner.result.getMessageLength()
        if mLen > 0:
            log =None
            for _ in range(mLen):
                m = runner.result.pop()  # 长时间运行的日志两比较大，需要将日志及时从缓存中弹出，否则会占用大量内存
                if m.get('type','plot')=='plot':
                    log = m
            print(log)  # 只打印一段时间内的最后一条日志，避免日志过多影响观察
        
        status = 1 if status == 0 else 0
        
        controlList=[{
            "key": "/component_new_constant_1",  # 需要控制的元件key
            "value": str(status),  # 修改constant元件的constant值
            "message": {"log": f"测试实时控制修改constant值为{status}"}, # 自定义控制日志
        }]   # 需要控制的元件列表
        result.control(controlList)  
        
        time.sleep(1)
        
        