import asyncio


async def module_a():
    print("start module_a")
    await asyncio.sleep(2) # 模拟 module_a 的io操作
    print('end module_a')
    return 'module_a 完成'

async def module_b():
    print("start module_b")
    await asyncio.sleep(1) # 模拟 module_a 的io操作
    print('end module_b')
    return 'module_b 完成'  

task_list = [
    module_a(),
 module_b(), 
]

done,pending = asyncio.run( asyncio.wait(task_list) )
for task in done:
    print(task.result())
print(done)