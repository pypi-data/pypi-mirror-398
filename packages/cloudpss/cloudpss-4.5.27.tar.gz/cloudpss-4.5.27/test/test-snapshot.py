import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time
import matplotlib.pyplot as plt
if __name__ == '__main__':
    #cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTEzLCJ1c2VybmFtZSI6ImRwc2hzdyIsInNjb3BlcyI6W10sInR5cGUiOiJhcHBseSIsImV4cCI6MTY4ODUyMzQ4NSwiaWF0IjoxNjgwNzQ3NDg1fQ.1c_ZhFDsx-Agn9cxr781UVr5OtB7LaJX96_I4zG0NvbJeuxyGtDPAe4RReWbbzpAZOzqMtCUCUuzl5YrOA5Daw')


    ### 获取指定 rid 的项目
    os.environ['CLOUDPSS_API_URL'] = 'http://166.111.60.76:50001/'
    cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6NjExLCJ1c2VybmFtZSI6ImRwc2hzdyIsInNjb3BlcyI6W10sInR5cGUiOiJhcHBseSIsImV4cCI6MTY4OTU1NzgxNCwiaWF0IjoxNjgxNzgxODE0fQ.4zYPiEDRK9nm8zRlCUiquPjp0RvP910Hxg8OO7ahFZIcre-lW_4eo-vYjVRZ40EiIo8VxH9lR9TEo-ZZ4Fck4g')
    model = cloudpss.Model.fetch('model/dpshsw/IEEE39')

    try:
        job = model.jobs[1]
        job['args']['end_time'] = 0.06
        runner = model.run(config={
            "args": {
                "save_snapshot_new": "1",  ## 是否保存快照，1 保存，0 不保存
                "save_snapshot_time_new": "0.05",  ## 保存快照的时间  单位：秒
                "snapshot_number_new": "12312",  ## 快照编号，用于区分不同的快照
            }
        })
        while  not runner.status() :
            print('running',flush=True)
            #print(runner.result.getPlots(0))
            time.sleep(1)

        print('end')

    except Exception as e:
        print('error',e)

    print(runner.result.getPlotChannelData(0, "#KL4:0"))

    #comp = model.getComponentByKey('/component_new_breaker_3_p_98:0')
    comp = model.getComponentByKey("component_new_constant_118")
    comp.args["Value"] = "0"


    print('restart from snapshot')

    job = model.jobs[1]
    job['args']['begin_time'] = 0.05
    job['args']['end_time'] = 0.10
    runner = model.run(config={
        "args": {"load_snapshot_new": "1",  ## 是否加载快照，1 加载，0 不加载
                 "load_snapshot_time_new": "0.05",  # 加载快照的时间  单位：秒
                 "load_snapshot_number_new": "12312"  # 快照编号，用于区分不同的快照
                 }
    })
    plotMap = {}
    fig, ax = plt.subplots()
    while not runner.status():
        time.sleep(1)
        print('running', flush=True)
        print(runner.result.getLogs())
        plotKeys = runner.result.getPlotChannelNames(1)
        if plotKeys is not None:
            for val in plotKeys:
                line = plotMap.get(val, None)

                # 获取曲线数据
                channel = runner.result.getPlotChannelData(1, val)
                if line is None:

                    line, = ax.plot(channel['x'], channel['y'], label=val)
                    plotMap[val] = line
                else:
                    line.set_data(channel['x'], channel['y'])

        plt.pause(0.1)
    plt.show()
    print(runner.result.getPlotChannelData(0, "#KL4:0"))