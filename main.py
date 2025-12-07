from pathlib import Path
import time
import csv
import matplotlib.pyplot as plt
from datetime import datetime, timedelta   # 记得把 timedelta 也导入


LOG_FILE = Path("study_log.csv")

def ensure_log_file():
    """
    如果日志文件不存在，就创建并写入表头。
    """
    if not LOG_FILE.exists():
        with LOG_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["start_time", "end_time", "duration_minutes", "mode", "note"])
            
def format_minutes(seconds: float) -> float:
    """
    把秒换算成分钟，保留两位小数。
    """
    return round(seconds / 60, 2)

def save_log(start: datetime, end: datetime, duration_seconds: float, mode: str, note: str):
    """
    把一条学习记录追加写入 CSV 文件。
    """
    ensure_log_file()
    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            start.strftime("%Y-%m-%d %H:%M:%S"),
            end.strftime("%Y-%m-%d %H:%M:%S"),
            format_minutes(duration_seconds),
            mode,
            note
        ])
    print("✅ 本次学习记录已保存到 study_log.csv\n")

def start_countup():
    """
    正计时模式：按 Enter 开始，学习过程中实时显示，按 Ctrl+C 结束。
    """
    input("👉 按 Enter 开始计时（正计时），学习过程中按 Ctrl+C 结束...\n")
    start_dt = datetime.now()
    start_ts = time.time()
    print(f"⏱ 开始时间：{start_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        while True:
            elapsed = int(time.time() - start_ts)  # 已经过的秒数
            mins, secs = divmod(elapsed, 60)
            hours, mins = divmod(mins, 60)
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            print(f"\r⏳ 已学习时间：{time_str}", end="", flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        # 捕获 Ctrl+C 结束计时
        end_dt = datetime.now()
        print()  # 换行
        duration = (end_dt - start_dt).total_seconds()
        minutes = format_minutes(duration)
        print(f"\n⌛ 本次学习时长：{minutes} 分钟")

        note = input("给这次学习写个备注（例如：高数作业 / 英语单词），直接 Enter 跳过：").strip()
        save_log(start_dt, end_dt, duration, "countup", note)
def start_countdown():
    """
    倒计时模式：输入要学习的分钟数，会实时显示剩余时间。
    """
    minutes_str = input("请输入要学习的分钟数（例如 25）：").strip()
    try:
        minutes = float(minutes_str)
        if minutes <= 0:
            print("❌ 分钟数必须大于 0。\n")
            return
    except ValueError:
        print("❌ 输入不是有效的数字，请重试。\n")
        return

    total_seconds = int(minutes * 60)
    start_dt = datetime.now()
    print(f"⏱ 开始 {minutes} 分钟倒计时！学习过程中按 Ctrl+C 可提前结束。\n")

    remaining = total_seconds
    try:
        while remaining > 0:
            hours, rem = divmod(remaining, 3600)
            mins, secs = divmod(rem, 60)
            time_str = f"{hours:02d}:{mins:02d}:{secs:02d}"
            print(f"\r⏳ 剩余时间：{time_str}", end="", flush=True)
            time.sleep(1)
            remaining -= 1
    except KeyboardInterrupt:
        # 提前终止倒计时
        end_dt = datetime.now()
        print("\n⏹ 已手动终止倒计时。")
        duration = (end_dt - start_dt).total_seconds()
        minutes_used = format_minutes(duration)
        print(f"本次实际学习时长：{minutes_used} 分钟")

        note = input("给这次学习写个备注（例如：专业课复习 / 阅读论文），直接 Enter 跳过：").strip()
        save_log(start_dt, end_dt, duration, "countdown", note)
        return

    # 正常倒计时结束
    end_dt = datetime.now()
    duration = (end_dt - start_dt).total_seconds()
    print("\n⏰ 时间到！辛苦啦～")
    minutes_used = format_minutes(duration)
    print(f"本次实际学习时长：{minutes_used} 分钟")

    note = input("给这次学习写个备注（例如：专业课复习 / 阅读论文），直接 Enter 跳过：").strip()
    save_log(start_dt, end_dt, duration, "countdown", note)

def today_study_time():
    ensure_log_file()
    
    today_str= datetime.now().strftime("%Y-%m-%d")
    total_minutes=0.0
    record_count=0
    
    if not LOG_FILE.exists():
        print("目前还没有任何学习记录！")
        return
    
    with LOG_FILE.open("r",encoding="utf-8") as f:
        reader=csv.reader(f)
        next(reader,None)    
        for row in reader:
            if len(row)<3:
                continue
                
            row_date=row[0][:10].strip()
            if row_date==today_str:
                duration= float(row[2]) 
                total_minutes+=duration
                record_count+=1
    print("============== 今日学习汇总 ==============")
    print(f"今日记录次数：{record_count}")
    print(f"今日学习总时长：{int(total_minutes)} 分钟 {int(total_minutes*60)%60}秒\n")               
def show_recent_curve(days: int = 7):
    """
    统计最近 days 天的每日学习总时长，并画出折线图。
    """
    ensure_log_file()

    if not LOG_FILE.exists():
        print("目前还没有任何学习记录！")
        return

    # 1. 先把 CSV 里所有记录读出来，按日期累加分钟数
    daily_minutes = {}  # key: 'YYYY-MM-DD', value: 总分钟数(float)

    with LOG_FILE.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # 跳过表头

        for row in reader:
            if len(row) < 3:
                continue
            date_str = row[0][:10]  # 'YYYY-MM-DD'
            try:
                minutes = float(row[2])
            except ValueError:
                continue

            daily_minutes[date_str] = daily_minutes.get(date_str, 0.0) + minutes

    # 2. 构造最近 days 天的日期列表（从旧到新）
    today = datetime.now().date()
    dates = []
    values = []

    for i in range(days - 1, -1, -1):  # 例如 days=7 → 6,5,4,3,2,1,0
        day = today - timedelta(days=i)
        d_str = day.strftime("%Y-%m-%d")
        dates.append(d_str)
        values.append(round(daily_minutes.get(d_str, 0.0), 2))

    # 3. 打印简单文本汇总
    print(f"============== 最近 {days} 天学习情况 ==============")
    for d, v in zip(dates, values):
        print(f"{d}：{v} 分钟")
    print("（同时会弹出一张折线图窗口）\n")

    # 4. 画折线图
    plt.figure()
    plt.plot(dates, values, marker="o")
    plt.title(f"最近 {days} 天每日学习时长")
    plt.xlabel("日期")
    plt.ylabel("学习时长（分钟）")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
              
def main_menu():
    """
    程序主菜单循环。
    """
    ensure_log_file()

    while True:
        print("============== 学习计时器 v0.2 ==============")
        print("1. 正计时（实时显示，Ctrl+C 结束）")
        print("2. 倒计时（实时显示，Ctrl+C 可提前结束）")
        print("3. 退出程序")
        print("4. 查看今天总学习时长")
        print("5. 查看最近 7 天学习曲线图")

        choice = input("请选择功能（1/2/3/4/5）：").strip()

        if choice == "1":
            start_countup()
        elif choice == "2":
            start_countdown()
        elif choice == "3":
            print("👋 已退出学习计时器，再见～")
            break
        elif choice == "4":
            show_today_summary()
        elif choice == "5":
            show_recent_curve(days=7)
        else:
            print("❌ 无效选项，请重新选择。\n")



        

if __name__ == "__main__":
    main_menu()