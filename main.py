import time

def main():
    print("学习计时器小程序启动！")
    print("简单测试：记录 3 秒钟……")
    start=time.time()
    time.sleep(3)
    end=time.time()
    print(f"实际经过时间：{end - start:.2f} 秒")

if __name__ == "__main__":
    main()