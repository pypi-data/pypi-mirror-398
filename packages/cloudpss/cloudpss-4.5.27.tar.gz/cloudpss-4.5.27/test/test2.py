import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time
# import plotly.graph_objects as go   # 使用 plotly 绘制曲线
import numpy as np
# from csv_write_function import csv_write_function


# 仿真设置
# 填写 token，注意不要加大括号{}
# cloudpss.setToken('{token}')
cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NjM4LCJ1c2VybmFtZSI6IkNfeWFuamlvbmdjaGVuZyIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiQ195YW5qaW9uZ2NoZW5nIl0sInR5cGUiOiJhcHBseSIsImV4cCI6MTc3NTMwODY0Miwibm90ZSI6IllKQy10b2tlbiIsImlhdCI6MTc0NDIwNDY0Mn0.H_BdzcOh-MBFMTddb35fNXSe2TAOCgoo2E6RC4mex5k06ouD8GuT0Y60yzCXsR1jsU7YKj6x00KU2OCElg7FQQ')

# 设置访问的地址，即登录后的地址到.net/为止
os.environ['CLOUDPSS_API_URL'] = 'http://cloudpss-nari.ddns.cloudpss.net/'

# 选择算例，获取指定算例 rid 的项目
model = cloudpss.Model.fetch('model/C_yanjiongcheng/Qingdong-DC-simple')  # 注意最后那个#号不要加，写完项目名称即可。


rid=model.rid
configs=model.configs
jobs=model.jobs
print('model的rid为', rid)
print('model的config为', configs)
print('model的jobs为', jobs)

# 选择参数方案，若未设置，则默认用 model 的第一个 config（参数方案）
config = model.configs[0]   # Kes1.1

# 选择计算方案，若未设置，则默认用 model 的第一个 job，此处选择 jobs[0]，为SimStudio中设置的第1个计算方案，即“图A”
job = model.jobs[0]

# 启动计算任务
time1 = time.time()  # 计算当前的秒数
runner = model.runPowerFlow(job, config)  # 运行计算方案

# 监听计算任务实例的运行状态
while not runner.status():
    logs = runner.result.getLogs()  # 获得运行日志
    for log in logs:
        print(log)  # 打印每一条日志
    # 每隔一秒判断一次运行状态
    time.sleep(1)
print('end')  # 运行结束

time2 = time.time()  # 计算当前的秒数
print('潮流计算花费的时间为 %.2f 秒' % (time2 - time1))
print(cloudpss.__version__)

# 获取潮流计算结果
buses = runner.result.getBuses()  # 获取节点电压计算结果
# print(buses)

