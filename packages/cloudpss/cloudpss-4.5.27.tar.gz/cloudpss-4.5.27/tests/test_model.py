import logging
import sys, os
import pytest
from unittest.mock import patch
import json
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..\\"))
import cloudpss
from cloudpss.job.result.EMTResult import EMTResult


""" 运行命令
执行指定文件: pytest -v -s tests/test_model.py
执行制定函数: pytest -v -s tests/test_model.py::test_model_run
执行代码覆盖率测试并生成报告位于htmlcov目录: pytest --cov=cloudpss --cov-report=html
"""


@pytest.fixture(scope="module")
def setup_environment():
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6Nzg2MiwidXNlcm5hbWUiOiJndWFuX2R1bzEyMyIsInNjb3BlcyI6WyJicm93c2VyIl0sInR5cGUiOiJicm93c2VyIiwiZXhwIjoxNzI2OTY5MzMwLCJpYXQiOjE3MjQyOTA5MzB9.CUGPZdNV-Dszx6ePW_9jzqjrEGLpKI-lIGUSKHn71yrnNMuALOVks3SYGZvoOZANuHpqCxywS6N6E4D5YdWNvw'
    )
    os.environ['CLOUDPSS_API_URL'] = 'https://cloudpss.net/'
    model = cloudpss.Model.fetch('model/guan_duo123/demo1')
    return model

def test_model_run(setup_environment):
    model = setup_environment
    config = model.configs[0]  
    job = model.jobs[1]  
    runner = model.run(job, config)
    
    assert runner is not None, "Runner should be created successfully."
    
    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

@pytest.mark.xfail(reason="rid 需要自行修改")
def test_model_create(setup_environment):
    model = setup_environment
    # rid 需要自行修改
    model.rid = 'model/guan_duo123/demo7'
    
    result = cloudpss.Model.create(model)

    assert result is not None
    assert result['data']['createModel']['rid'] == model.rid  

def test_model_update(setup_environment):
    model = setup_environment
    result = cloudpss.Model.update(model)

    assert result is not None

def test_model_dump(setup_environment):
    model = setup_environment
    file_path = 'D:\\files\\demo4.cmdl'
    cloudpss.Model.dump(model, file_path)

    # 验证文件是否已创建
    assert os.path.exists(file_path), "The file was not created."

    # 清理测试环境，删除创建的文件
    # os.remove(file_path)

# @pytest.mark.xfail(reason="rid 需要自行修改")
def test_model_load(setup_environment):
    file_path = 'D:\\files\\demo4.cmdl'
    result = cloudpss.Model.load(file_path)
    print(result)
    # rid 需要自行修改
    # rid = 'newFile'
    # result.save(rid)
    assert result is not None

@pytest.mark.xfail(reason="rid 需要自行修改")
def test_model_save(setup_environment):
    model = setup_environment
    # rid 需要自行修改
    rid = 'newKey'
    r = model.save(rid)

    assert r is not None
    assert rid in r['data']['createModel']['rid']

def test_model_createJob(setup_environment):
    model = setup_environment
    job = model.createJob('emtp', '测试计算方案')
    # print('参数方案', job)

    assert job is not None, "The job should be created successfully."

def test_model_addJob(setup_environment):
    model = setup_environment
    job = model.createJob('emtp', '测试计算方案')
    # # 修改计算方案
    job['args']['end_time'] = '2'
    # 将参数方案加入到项目中
    model.addJob(job)
    filtered_data = [item for item in model.jobs if item["name"] == "测试计算方案"]

    assert len(filtered_data) > 0, "The job should be added successfully."


def test_model_getModelJob(setup_environment):
    model = setup_environment
    job = model.getModelJob('电磁暂态方案 1')
    # print('参数方案', job)

    assert job is not None, "The job should be fetched successfully."

def test_model_createConfig(setup_environment):
    model = setup_environment
    config = model.createConfig('测试参数方案')
    # print('参数方案', config)

    assert  config is not None, "The config should be created successfully."

def test_model_addConfig(setup_environment):
    model = setup_environment
    config = model.createConfig('测试参数方案')
    # # 修改参数方案
    config['args']['T_Tm_change'] = '4'
    # 将参数方案加入到项目中
    model.addConfig(config)

    filtered_data = [item for item in model.configs if item["name"] == "测试参数方案"]
    
    assert len(filtered_data) > 0, "The config should be added successfully."

def test_model_getModelConfig(setup_environment):
    model = setup_environment
    config = model.getModelConfig('测试参数方案')

    assert config is not None, "The config should be fetched successfully."

def test_model_addComponent(setup_environment):
    model = setup_environment

    dic = dict()
    dic = {'args': {'Cs': 0.05, 'I': '', 'Itotal': '', 'Name': '', 'Roff': 1000000, 'Ron': 0.01, 'Rs': 5000, 'Snubber': '0', 'Tme': 0, 'V': '', 'Vfb': 100000, 'Vfd': 0, 'Vrw': 100000}, 'canvas': 'canvas_0', 'context': {}, 'definition': 'model/CloudPSS/_newDiode', 'flip': False, 'id': 'component_new_diode_2', 'label': '自定义二极管2', 'pins': {'0': '', '1': ''}, 'position': {'x': 375, 'y': 530}, 'props': {'enabled': True, 'outlineLevel': 0}, 'shape': 'diagram-component', 'size': {'height': 50, 'width': 40}, 'style': {}, 'zIndex': 1}

    component = model.addComponent(dic["definition"], dic["label"], dic["args"], dic["pins"], dic["canvas"], dic["position"], dic["size"])

    model.save()



    assert component is not None, "The component should be created successfully."


@pytest.mark.xfail(reason="id需要根据实际情况修改")
def test_model_removeComponent(setup_environment):
    model = setup_environment
    # id需要根据实际情况修改
    id = 'comp_61921e2a-7e24-46bc-a777-96cf5c751f32'
    flag = model.removeComponent(id)

    model.save()

    assert flag, "The component should be removed successfully."

def test_model_updateComponent(setup_environment):
    model = setup_environment
    component = model.addComponent(definition='model/CloudPSS/newResistorRouter',
    label='电阻1',
    args={
        'Name': '电阻1',
        'Dim': '0',
        'R': '1'
    },
    pins={
        '0': '',
        '1': ''
    })
    # model.save()
    print(component)
    r = model.updateComponent(component.id, {"label":'电阻2'})

    model.save()

    assert r, "The component should be updated successfully."

def test_model_getAllComponents(setup_environment):
    model = setup_environment
    comps = model.getAllComponents()
    print("元件列表", type(comps), comps['canvas_0_10'].__dict__)

    assert len(comps) > 0, "The component list should not be empty."

def test_model_getComponentByKey(setup_environment):
    model = setup_environment
    comps = model.getComponentByKey('canvas_0_111')
    print(comps.__dict__)
    assert comps is not None, "The component should be fetched successfully."

def test_model_getComponentsByRid(setup_environment):
    model = setup_environment
    comps = model.getComponentsByRid('model/guan_duo123/demo1')
    print(comps)
    assert comps is not None, "The component should be fetched successfully."

def test_model_fetchTopology(setup_environment):
    model = setup_environment
    topology = model.fetchTopology()
    print(topology.__dict__)

    assert topology is not None, "The topology should be fetched successfully."

def test_model_runEMT(setup_environment):
    model = setup_environment
    runner = model.runEMT()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

def test_model_runSFEMT(setup_environment):
    model = setup_environment
    runner = model.runSFEMT()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

def test_model_runPowerFlow(setup_environment):
    model = setup_environment
    runner = model.runPowerFlow()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

@pytest.mark.xfail(reason="不是三相不平衡潮流内核运行生成算法的计算方案")
def test_model_runThreePhasePowerFlow(setup_environment):
    model = setup_environment
    runner = model.runThreePhasePowerFlow()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

@pytest.mark.xfail(reason="不是负荷预测方案内核运行生成算法的计算方案")
def test_model_runIESLoadPrediction(setup_environment):
    model = setup_environment
    runner = model.runIESLoadPrediction()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

@pytest.mark.xfail(reason=" 不是时序潮流方案内核运行生成算法的计算方案")
def test_model_runIESPowerFlow(setup_environment):
    model = setup_environment
    runner = model.runIESPowerFlow()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

@pytest.mark.xfail(reason=" 不是储能规划方案内核运行生成算法的计算方案")
def test_model_runIESEnergyStoragePlan(setup_environment):
    model = setup_environment
    runner = model.runIESEnergyStoragePlan()

    assert runner is not None, "Runner should be created successfully."

    while not runner.status():
        logs = runner.result.getLogs()
        for log in logs:
            print(log)
        time.sleep(1)
    
    assert runner.status(), "Runner should finish successfully."

