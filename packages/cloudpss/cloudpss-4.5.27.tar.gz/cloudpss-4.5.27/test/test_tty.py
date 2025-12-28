import threading
import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def log_worker():
    """后台日志输出线程"""
    count = 0
    while True:
        logging.info(f"后台日志输出 - 计数: {count}")
        count += 1
        time.sleep(2)  # 每2秒输出一次日志

# 启动后台日志线程
log_thread = threading.Thread(target=log_worker, daemon=True)
log_thread.start()

# 主线程处理用户输入
try:
    while True:
        user_input = input("请输入内容 (输入 'quit' 退出): ")
        if user_input.lower() == 'quit':
            break
        print(f"你输入了: {user_input}")
except KeyboardInterrupt:
    print("\n程序被用户中断")