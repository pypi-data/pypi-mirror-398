# -*- coding: utf-8 -*-
"""
Created on 2024/8/17

@author: Lucy
"""
# # 振荡源定位之模态功率结合比幅寻优

import sys,os

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import numpy as np
import matplotlib.pyplot as plt
import cloudpss
import time

if __name__ == '__main__': 
    #根据提供的SDK获取FuncStudio当前函数的任务信息
    job = cloudpss.currentJob() 

    # # 利用提供的args函数按照键名获取函数的参数(算例RID及用户输入的振荡频率)
    # modelid = job.args.rid
    # f_harm = job.args.f_harm
    # time_start = job.args.time_start
    # time_end = job.args.time_end

    modelid = 'model/lsm_thu/OsciModel1_testSDK'
    f_harm =65.5
    time_start = 6
    time_end = 15

    # modelid = 'model/lsm_thu/zztprob_into_IEEE_9_SDK'
    # f_harm = 78.5
    # modelid = 'model/lsm_thu/zztprob_testSDK'
    
    job.log(modelid,key='log-1')
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NjMzLCJ1c2VybmFtZSI6ImxzbV90aHUiLCJzY29wZXMiOlsibW9kZWw6OTgzNjciLCJmdW5jdGlvbjo5ODM2NyIsImFwcGxpY2F0aW9uOjMyODMxIl0sInJvbGVzIjpbImxzbV90aHUiXSwidHlwZSI6ImFwcGx5IiwiZXhwIjoxNzUxMTgwMDE2LCJub3RlIjoidG9rZW4xIiwiaWF0IjoxNzIwMDc2MDE2fQ.LDcGNTxHMqzbSpUIhpKQDW1Z63FgGHBMQDjHIho5uWRcxgC17fiXHA8t44xWLrdqJQR08zU57E-shManF91acQ')
    os.environ['CLOUDPSS_API_URL'] = 'http://cloudpss-calculate.local.ddns.cloudpss.net/'
    # 获取指定rid的项目
    model = cloudpss.Model.fetch(modelid)
    #启动计算任务
    config = model.configs[0]  #参数方案
    job_cal = model.jobs[2]       #计算方案(电磁暂态仿真方案1)

    # 获取可能是振荡源的模块
    model_PMSG = model.getComponentsByRid('model/lsm_thu/PMSG_model')  # PMSG网侧变流器模型获取
    model_DFIG = model.getComponentsByRid('model/CloudPSS/DFIG_WindFarm_Equivalent_Model')  # 双馈风机风场等值模型获取
    model_PVStation = model.getComponentsByRid('model/CloudPSS/PVStation')  # 光伏电站模型获取
    model_SVG = model.getComponentsByRid('model/lsm_thu/SVG_VV_avg_zzt')    # SVG模块获取
    # model_SVG1 = model.getComponentsByRid('model/lsm_thu/SVG_VV_avg_zzt') or {}   # SVG模块获取
    # model_SVG2 = model.getComponentsByRid('model/lsm_thu/SVG_VQ_avg_comp_temp') or {} 
    # model_SVG1.update(model_SVG2)
    # model_SVG = model_SVG1


    keys_PMSG = list(model_PMSG.keys())
    labels_PMSG = [model_PMSG[key].label for key in keys_PMSG]
    ids_PMSG = [model_PMSG[key].id for key in keys_PMSG]
    keys_DFIG = list(model_DFIG.keys())
    labels_DFIG = [model_DFIG[key].label for key in keys_DFIG]
    ids_DFIG = [model_DFIG[key].id for key in keys_DFIG]
    keys_PVStation = list(model_PVStation.keys())
    labels_PVStation = [model_PVStation[key].label for key in keys_PVStation]
    ids_PVStation = [model_PVStation[key].id for key in keys_PVStation]
    keys_SVG = list(model_SVG.keys())
    labels_SVG = [model_SVG[key].label for key in keys_SVG]
    ids_SVG = [model_SVG[key].id for key in keys_SVG]
   
    # 振荡源模块列表(拼成一个列表)
    oscillation_sources = ids_PMSG + ids_DFIG + ids_PVStation + ids_SVG
    sources_labels = labels_PMSG + labels_DFIG +labels_PVStation + labels_SVG

    # 初始化计数器
    counter = 1
    connect_points = []

    # 对每一个可能的振荡源模块均须添加电压表、电流表、模态功率结合比幅寻优模块和输出通道
    for source in oscillation_sources:
        # 获取当前振荡源模块
        comp_sel = model.getComponentByKey(source)
        canvas_name = comp_sel.canvas

        # 添加电压表
        voltmeter_label = f'新增电压表{counter}'
        voltmeter_name = f'#V_newmodule{counter}'
        new_voltmeter = model.addComponent(
            definition='model/CloudPSS/_NewVoltageMeter',
            label=voltmeter_label,
            args={'Dim': '3', 'V': voltmeter_name},
            pins={'0': ''},
            canvas=canvas_name
        )

        # 添加电流表
        currmeter_label = f'新增电流表{counter}'
        currmeter_name = f'#I_newmodule{counter}'
        new_currmeter = model.addComponent(
            definition='model/CloudPSS/_NewCurrentMeter',
            label=currmeter_label,
            args={'Dim': '3', 'I': currmeter_name},
            pins={'0': '', '1': ''},
            canvas=canvas_name
        )

        # 将电压表和电流表接到所测位置
        if comp_sel.pins['0']:  # 该引脚非空
            connect_point = comp_sel.pins['0']

            connect_points.append(connect_point)
            # new_voltmeter.pins['0'] = connect_point
            new_currmeter.pins['1'] = connect_point
            comp_sel.pins['0'] = f'sel_newpin{counter}'
            new_currmeter.pins['0'] = comp_sel.pins['0']
            new_voltmeter.pins['0'] = comp_sel.pins['0']
            # print(f"电压量测点为：{new_voltmeter.pins['0']}.")
            # print(f"电流表的两个引脚分别为:{new_currmeter.pins['0']},{new_currmeter.pins['1']}")
            # print(f"该模块所接引脚为：{comp_sel.pins['0']}")

        else:  # 该引脚为空
            print(f'选取的模块{source}引脚为空，error!')

        # 添加模态功率结合比幅寻优模块
        module1_label = f'新增模态功率结合比幅寻优模块{counter}'
        module1_name = f'#module{counter}'
        ratioV_name = f'#ratioV{counter}'
        ratioI_name = f'#ratioI{counter}'
        new_module1 = model.addComponent(
            definition='model/lsm_thu/modepower_ampratio',
            label=module1_label,
            args={'f_h':f_harm},
            pins={'V':voltmeter_name,'I':currmeter_name,'ratio_V':ratioV_name,'ratio_I':ratioI_name},
            canvas=canvas_name
        )

        # 新增一个ratio_I输出通道
        channel_ampratio_label = f'新增输出通道0_{counter}'
        channel_ampratio = model.addComponent(
            definition='model/CloudPSS/_newChannel',
            label=channel_ampratio_label,
            args={'Name': ratioI_name, 'Dim': '1'},
            pins={'0': ratioI_name},
            canvas=canvas_name
        )
       
        # 在仿真方案的输出通道中添加上去
        if counter == 1:
            job_cal['args']['output_channels'].append({'0': '', '1': '5000', '2': 'compressed', '3': 0, '4': [channel_ampratio.id], 'ɵid':''})
            A = job_cal['args']['output_channels']
        else:
            job_cal['args']['output_channels'][len(job_cal['args']['output_channels'])-1]['4'].append(channel_ampratio.id) 
            A = job_cal['args']['output_channels']
        # 更新计数器
        counter += 1

    ## 电磁暂态仿真，获取仿真结果
    endtime = job_cal['args']['end_time']
    begintime = job_cal['args']['begin_time']
    runner = model.run(job_cal,config)
    while not runner.status():
        logs = runner.result.getLogs()
        # if(runner.result.getPlotChannelNames(0)!=None):
        #     ckeytemp = runner.result.getPlotChannelNames(0)
        #     stime = runner.result.getPlotChannelData(0,ckeytemp[0])['x'][-1]
        #     progress = stime/(endtime-begintime)
        #     job.progress(progress, '测试进度消息', 'progress-1')
        time.sleep(1)
        for log in logs:
            print(log)
    print('end')

    result = runner.result
    plots = result.getPlots()     #获取全部输出通道
    nChannel = len(plots)

    legend = runner.result.getPlotChannelNames(nChannel-1)
    plots = []  # 初始化一个列表来存储所有曲线的数据
    ampratio = []
    mean_ampratios = []
    finalsources = []

    for i in range(len(legend)):
        data = runner.result.getPlotChannelData(nChannel-1, legend[i])
        t = data['x']
        ampratio1 = data['y']
        ampratio.append(ampratio1) 

        # 获取6-20s的数据索引
        indices = [index for index, time in enumerate(t) if time_start <= time <= time_end]

        # 判断这些数据是否都大于0
        if all(ampratio1[index] > 0 for index in indices):
            # 创建曲线数据，并添加到plots列表
            curve = {
                "name": sources_labels[i],  # 曲线名称可以根据需要进行格式化
                "type": "scatter",
                 "x": t,
                 "y": ampratio1  # 使用标幺化后的数据
                     }
            plots.append(curve) 
            # 计算indices中数据的平均值
            mean_value = sum(ampratio1[index] for index in indices) / len(indices)
            mean_ampratios.append(mean_value)  # 将平均值添加到列表中
            finalsources.append(sources_labels[i])
            
    # 使用 zip 将两个列表配对，然后进行排序
    sorted_pairs = sorted(zip(mean_ampratios, finalsources), key=lambda pair: pair[0], reverse=True)

    # 解压排序后的对
    mean_ampratios_sorted, finalsources_sorted = zip(*sorted_pairs)

    # 转换为列表（如果需要的话）
    mean_ampratios_sorted = list(mean_ampratios_sorted)
    finalsources_sorted = list(finalsources_sorted)
    # 设置散点图的坐标轴样式
    layout = {
        'xaxis':{
        'title':'时间t/s', 
        'type':'linear', 
        'range':'auto' 
        },
        'yaxis':{
        'title':'振荡电流分量比值',
        'type':'linear', # 线性坐标
        'range':'auto' # 显示范围自适应
        }        
    }
    # 绘制所有曲线
    job.plot(plots,layout=layout,title ='振荡电流分量比值',key='plot-1')

    c1 = {
        'name':'<b>可能的振荡源</b>',  # 给<b></b>之间的文字字体加粗
        'type':'text', # 支持在`data`里面添加`html`标签
        'data': finalsources_sorted
    }
    c2 = {
        'name': "<b>振荡分量比值</b>",
        'type': 'number',
        'data': mean_ampratios_sorted
    }

    job.table([c1,c2],title = '系统中可能的振荡源及其振荡贡献量排序结果',key = 'table-1')
    # job.log(sorted_labels_list,key='sources')


