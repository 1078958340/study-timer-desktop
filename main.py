import time
import csv
from pathlib import Path
from datetime import datetime

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
    正计时模式：按 Enter 开始，学完再按 Enter 结束。
    """
    input("👉 按 Enter 开始计时（正计时）...")
    start = datetime.now()
    print(f"⏱ 开始时间：{start.strftime('%Y-%m-%d %H:%M:%S')}")
    input("学习中……学完后按 Enter 结束计时。")
    end = datetime.now()

    duration = (end - start).total_seconds()
    minutes = format_minutes(duration)
    if minutes:
        print(f"⌛ 本次学习时长：{int(minutes)} 分钟 {int(duration %60)}秒")

    note = input("给这次学习写个备注（例如：高数作业 / 英语单词），直接 Enter 跳过：").strip()
    save_log(start, end, duration, "countup", note)
def start_countdown():
    """
    倒计时模式：输入要学习的分钟数，会倒计时，到点提醒。
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
    start = datetime.now()
    print(f"⏱ 开始 {minutes} 分钟倒计时！")
    for remaining in range(total_seconds, 0, -1):
        if remaining % 60 == 0 or remaining <= 10:
            mins = remaining // 60
            secs = remaining % 60
            print(f"剩余 {mins} 分 {secs} 秒")
        time.sleep(1)
    end = datetime.now()
    duration = (end - start).total_seconds()

    print("⏰ 时间到！辛苦啦～")

    note = input("给这次学习写个备注（例如：专业课复习 / 阅读论文），直接 Enter 跳过：").strip()
    save_log(start, end, duration, "countdown", note)
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
               
def main_menu():
    """
    程序主菜单循环。
    """
    ensure_log_file()

    while True:
        print("============== 学习计时器 v0.1 ==============")
        print("1. 正计时（开始后，学完再按 Enter 结束）")
        print("2. 倒计时（输入要学习的分钟数）")
        print("3. 退出程序")
        print("4. 查看今天总学习时长")

        choice = input("请选择功能（1/2/3/4）：").strip()

        if choice == "1":
            start_countup()
        elif choice == "2":
            start_countdown()
        elif choice == "3":
            print("👋 已退出学习计时器，再见～")
            break
        elif choice=="4":
            today_study_time()
        else:
            print("❌ 无效选项，请输入 1 / 2 / 3。\n")


        

if __name__ == "__main__":
    main_menu()