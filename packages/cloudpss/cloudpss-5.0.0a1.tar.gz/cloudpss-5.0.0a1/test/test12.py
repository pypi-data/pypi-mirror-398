import time

def sleep_microseconds(microseconds):
    start_time = time.perf_counter()
    end_time = start_time + microseconds / 1_000_000  # 将微秒转换为秒
    while time.perf_counter() < end_time:
        pass

# 睡眠500微秒（0.5毫秒）
print("Sleeping for 500 microseconds")
sleep_microseconds(500)
print("Awake!")

# 测量实际睡眠时间
start_time = time.perf_counter()
# sleep_microseconds(10)
time.sleep(0.05)
end_time = time.perf_counter()

elapsed_time = (end_time - start_time) * 1_000_000  # 将秒转换为微秒
print(f"实际睡眠时间: {elapsed_time:.2f} 微秒")