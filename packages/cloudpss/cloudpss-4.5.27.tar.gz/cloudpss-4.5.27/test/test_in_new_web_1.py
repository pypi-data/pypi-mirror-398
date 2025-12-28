import StabilityAnalysis as SA
# import ReadSOT as rs

import cloudpss
import os
import time
import json
import re
import numpy as np
import numpy.linalg as LA

# %matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# import plotly.io as pio
# from scipy import interpolate

import pandas as pd

import tkinter
import tkinter.filedialog

import math

# from IPython.display import HTML
from html import unescape

import random
import json
import copy
from cloudpss.model.implements.component import Component
from cloudpss.runner.result import (Result, PowerFlowResult, EMTResult)
from cloudpss.model.revision import ModelRevision
from cloudpss.model.model import Model

# from docx import Document
# from docx.shared import Inches
# from docx.oxml.ns import qn
# from docx.shared import Pt,RGBColor
# from docx.oxml import OxmlElement

# from scipy import optimize
if __name__ == '__main__':
    tk = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NTk4LCJ1c2VybmFtZSI6Imx0aDIwMjEwMTIzNDkiLCJzY29wZXMiOltdLCJ0eXBlIjoiYXBwbHkiLCJleHAiOjE3MjEwNDA3MzYsImlhdCI6MTY4OTkzNjczNn0.kLc6IyB-725vTvj8wWJhWiFAvaDbET5wJUzUOP_SxZTlrBJB19Z-USjKaZW8P8COHqB37mxcMPenXhnhRqU4ZQ'
    apiURL = 'http://10.10.1.33:60002/'
    username = 'lth2021012349'
    projectKey = 'IEEE39_lth'
    cloudpss.setToken(tk)
    os.environ['CLOUDPSS_API_URL'] = apiURL

    # with open('saSource.json', "r", encoding='utf-8') as f:
    #     compLib = json.load(f)  # 添加cloupss平台所有元件库

    sa = SA.StabilityAnalysis()
    sa.setConfig(tk, apiURL, username, projectKey)
    sa.setInitialConditions()  # 初始化，调用cloudpss算例
    # sa.createSACanvas()  # 创造故障图层+暂态监控图层
    N_1LineKey1 = []

    ##  可以设置故障。详见以下函数：
    #     * setGroundFault(self, pinName, fault_start_time, fault_end_time,  fault_type, OtherParas = None) # 接地故障生成,pinName为接地故障引脚位置
    #     * setBreaker_3p(self, busName1, busName2, ctrlSigName = None, OtherParas = None) # busName1和busName2之间插入开关
    #     * setN_1(self, transKey, cut_time, OtherBreakerParas = None) # 设置传输线断路
    #     * setN_1_GroundFault(self, transKey,side, fault_start_time, cut_time, fault_type, OtherFaultParas = None, OtherBreakerParas = None) # N-1断线+接地故障生成
    #     * setN_2_GroundFault(self, transKey1, transKey2, side, fault_start_time, cut_time, fault_type, OtherFaultParas = None, OtherBreakerParas = None) # # N-2断线+接地故障生成

    # N_1LineLabel1 = 'TLine_3p-22'  # 传输线26-29
    # N_1LineKey1 = [j for j in sa.compLabelDict[N_1LineLabel1].keys()][0]
    # LineComp1 = sa.project.getComponentByKey(N_1LineKey1)

    # # 三相断路接地故障生成
    # # fault_type对应平台故障电阻故障类型
    # sa.setGroundFault(LineComp1.pins['0'], 3, 3.1, 7)

    # # 单次N-1断线+接地故障生成
    # sa.setN_1_GroundFault(N_1LineKey1, 0, 4, 4.06, 7)

    # 单次N-2断线+接地故障生成
    # N_2LineLabel1 = ['AC701004','AC701003']
    # for i in N_2LineLabel1:
    #     N_2LineKey1.append([j for j in sa.compLabelDict[i].keys()][0])
    # sa.setN_2_GroundFault(N_2LineKey1[0], N_2LineKey1[1], 0, 4, 4.09, 7)

    # 仿真任务设置
    jobName = 'SA_电磁暂态仿真(旧版本)'
    timeend = 10
    sa.createJob('emtp', name=jobName, args={'begin_time': 0, 'end_time': timeend, 'step_time': 0.00005, \
                                             #    'task_queue': 'taskManager_turbo1','solver_option': 7,'n_cpu': 16})
                                             'task_queue': 'taskManager_turbo1', 'solver_option': 7, 'n_cpu': 4})

    # 设置参数方案，无修改则默认参数方案
    sa.createConfig(name='SA_参数方案')

    # 设置输出
    # sa.addVoltageMeasures('SA_电磁暂态仿真', VMin = 220, freq = 200, PlotName = '220kV以上电压曲线') # 基于电压筛选
    sa.addOutputs('SA_电磁暂态仿真(旧版本)', {'0': 'Gen30,Gen38相对Gen39的功角', '1': 200, '2': 'compressed', '3': 1,
                                '4': ['canvas_11_1085', 'canvas_11_1083']})
    sa.runProject(jobName='SA_电磁暂态仿真(旧版本)', configName='SA_参数方案')

    # 输出通道曲线绘制
    sa.plotResult(sa.runner.result, 0)  # 绘制通道1

    # path = 'results/'+ projectKey
    # folder = os.path.exists(path)
    # if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
    #     os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径

    # Result.dump(sa.runner.result,path+'/SAresult_'+ time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())+'.cjob')
    # SAresult = sa.runner.result

#     sa.displayPFResult()

##  修改cloudpss算例后另存修改后的算例
#     desc = '此为自动暂稳分析程序生成的仿真算例。\n作者：谭镇东；\n日期与时间：'+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+\
#             '\n' + sa.project.description
#     sa.saveProject(projectKey+'Auto_SA',sa.project.name+'_自动暂稳分析',desc = desc + sa.project.description )