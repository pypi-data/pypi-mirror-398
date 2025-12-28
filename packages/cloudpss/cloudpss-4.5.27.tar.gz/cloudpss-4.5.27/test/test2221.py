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
# model = cloudpss.Model.fetch('model/C_yanjiongcheng/Qingdong-DC-simple')  # 注意最后那个#号不要加，写完项目名称即可。
mode =cloudpss.Model.load("D:\history\model_admin_S-H-dcac.cmdl",'ubjson')

print('model的rid为', mode.rid)

