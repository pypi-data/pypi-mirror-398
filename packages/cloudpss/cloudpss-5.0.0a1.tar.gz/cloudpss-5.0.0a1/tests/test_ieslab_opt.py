import logging
import sys, os
import pytest
from unittest.mock import patch
import json
import time

sys.path.append(os.path.join(os.path.dirname(__file__), "..\\"))
import cloudpss
from cloudpss.job.result.EMTResult import EMTResult

@pytest.fixture(scope="module")
def setup_environment():
    cloudpss.setToken(
        'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MSwidXNlcm5hbWUiOiJhZG1pbiIsInNjb3BlcyI6WyJicm93c2VyIl0sInR5cGUiOiJicm93c2VyIiwiZXhwIjoxNzI3NTA1ODEyLCJpYXQiOjE3MjQ4Mjc0MTJ9.ee67ik8h6cmFM2oP-5nZwonigbe-EMAt_ceVORszVBQp8gmb_HOXNaidUFzE40htykQF60QKOqQlMZGk9u_zTA'
    )
    os.environ['CLOUDPSS_API_URL'] = 'http://10.101.10.34'
    project = cloudpss.IESLabOpt.fetch('375')
    return project

def test_ieslabOPT_createProjectGroup(setup_environment):
    rid = cloudpss.IESLabOpt.createProjectGroup('test_group2', 'test_group2')
    print(rid)
    assert rid > 0

def test_ieslabOPT_createProject(setup_environment):
    rid= cloudpss.IESLabOpt.createProject('test_project', 73, 2020, 2025, 5)
    assert rid > 0

def test_ieslabOPT_iesLabPlanRun(setup_environment):
    project = setup_environment 
    # 启动计算
    runner = project.iesLabOptRun()
    last_plan_num = 0
    while not runner.status():
        print('running', flush=True)
        time.sleep(1)
        plan_result = runner.result
        plan_num = plan_result.GetPlanNum()
        if plan_num > last_plan_num:
            for plan_id in range(last_plan_num, plan_num):
                print("新生成的方案: ", plan_id + 1)
                
                # # 获取每个优化方案的基础信息和配置信息
                # print("优化方案", plan_id + 1)
                # plan_info = plan_result.GetPlanInfo(plan_id)
                # print("基础信息:", plan_info)
                # plan_config = plan_result.GetPlanConfiguration(plan_id)
                # print("配置信息:", plan_config)
                # plan_config = plan_result.GetComponentResult(plan_id, "/component_absorption_chiller_1", "1月典型日1")
                # print("运行信息:", plan_config)
                print("=" * 30)
            last_plan_num = plan_num
    print('计算完成')


def test_ieslabOPT_iesLabEvaluationRun(setup_environment):
    project = setup_environment
    evaluationRunner = project.iesLabEvaluationRun(1, '环保评价')
    while not evaluationRunner.status():
        print('running', flush=True)
        time.sleep(1)
    print('评估完成')