import sys,os
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
import cloudpss
import json
import time

if __name__ == '__main__':
    
      cloudpss.setToken('eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTE1NTcsInVzZXJuYW1lIjoiYmFuZ2ppbGVnYW9sZWdhbyIsInNjb3BlcyI6WyJtb2RlbDo5ODM2NyIsImZ1bmN0aW9uOjk4MzY3IiwiYXBwbGljYXRpb246MzI4MzEiXSwicm9sZXMiOlsiYmFuZ2ppbGVnYW9sZWdhbyJdLCJ0eXBlIjoiYXBwbHkiLCJleHAiOjE3OTExODg2OTEsIm5vdGUiOiIxMjMiLCJpYXQiOjE3NjAwODQ2OTF9.RoHSICdh_6ygNuXde166K5rDujPReskYdgCcJTfTrdsXlQ4x6hleVCRedpvYbDzZZYwrwZ8XG5FT8ops3BLICg')

      os.environ['CLOUDPSS_API_URL'] = 'https://cloudpss.net/'
      
      # 获取指定 rid 的项目
      model = cloudpss.Model.fetch('model/songyankan/3_Gen_9_Bus')

      # 修改 Gen2 发电机有功功率
      comp = model.getComponentByKey('canvas_0_757')
      print(comp.args)
      comp.args['pf_P'] = '180'
      
      # 启动计算任务
      config = model.configs[0]  # 若未设置，则默认用model的第一个config（参数方案）
      job = model.jobs[0]  # 若未设置，则默认用model的第一个job（计算方案）
      runner = model.run(job,config)
      while not runner.status():
         logs = runner.result.getLogs()
         for log in logs:
               print(log)
         time.sleep(1)
      print('end')
      
      # 打印结果
      print(runner.result.getBranches())
      print(runner.result.getBuses())