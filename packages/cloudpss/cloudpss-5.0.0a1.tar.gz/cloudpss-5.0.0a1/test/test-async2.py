import asyncio


async def consumer(n, q):
    print('consumer {}: starting'.format(n))
    while True:
        print('consumer {}: waiting for item'.format(n))
        item = await q.get()
        print('consumer {}: has item {}'.format(n, item))
        if item is None:
            # None 是一个停止信号。
            q.task_done()
            break
        else:
            await asyncio.sleep(n)
            q.task_done()
    print('consumer {}: ending'.format(n))


async def producer(q, num_workers):
    print('producer: starting')
    # 向队列中添加一些数字来模拟作业
    for i in range(num_workers * 30):
        await q.put(i)
        await asyncio.sleep(0.1)
        print('生产者: 添加任务 {} 到队列'.format(i))
        # 添加 None 到队列
    # 发出消费者退出的信号
    print('生产者: 向队列添加停止信号')
    for i in range(num_workers):
        await q.put(None)
    print('producer: waiting for queue to empty')
    await q.join()
    print('producer: ending')


async def main(loop, num_consumers):
    # 创建具有固定大小的队列，用于生产者
    # 将阻塞，直到消费者取出一些item。
    q = asyncio.Queue(maxsize=num_consumers)

    # 消费者任务调度
    consumers = [
        loop.create_task(consumer(i, q))
        for i in range(num_consumers)
    ]

    # 生产者任务调度
    prod = loop.create_task(producer(q, num_consumers))

    # 等待所有协程完成。
    await asyncio.wait(consumers + [prod])


event_loop = asyncio.get_event_loop()
try:
    event_loop.run_until_complete(main(event_loop, 2))
finally:
    event_loop.close()
