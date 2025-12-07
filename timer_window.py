import tkinter as tk
from tkinter import messagebox, simpledialog
import csv
from pathlib import Path
from datetime import datetime, timedelta

# 尝试导入 matplotlib（用于画图），如果没有也能正常跑，只是不能画图
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

# 日志文件
LOG_FILE = Path("study_log.csv")


# ================== CSV 工具函数 ==================

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


def summarize_today() -> str:
    """
    返回“今日学习总时长”的文本描述。
    """
    ensure_log_file()
    if not LOG_FILE.exists():
        return "目前还没有任何学习记录。"

    today_str = datetime.now().strftime("%Y-%m-%d")
    total_minutes = 0.0
    record_count = 0

    with LOG_FILE.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            date_str = row[0][:10]
            if date_str == today_str:
                try:
                    m = float(row[2])
                except ValueError:
                    continue
                total_minutes += m
                record_count += 1

    return f"今日记录次数：{record_count}\n今日学习总时长：{round(total_minutes, 2)} 分钟"


def summarize_recent(days: int = 7, do_plot: bool = False) -> str:
    """
    统计最近 days 天的每日学习总时长，并可选择画图。
    返回文本描述。
    """
    ensure_log_file()
    if not LOG_FILE.exists():
        return "目前还没有任何学习记录。"

    daily_minutes = {}
    with LOG_FILE.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) < 3:
                continue
            date_str = row[0][:10]
            try:
                m = float(row[2])
            except ValueError:
                continue
            daily_minutes[date_str] = daily_minutes.get(date_str, 0.0) + m

    today = datetime.now().date()
    dates = []
    values = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.strftime("%Y-%m-%d")
        dates.append(d_str)
        values.append(round(daily_minutes.get(d_str, 0.0), 2))

    lines = [f"最近 {days} 天每日学习时长："]
    for d_str, v in zip(dates, values):
        lines.append(f"{d_str}：{v} 分钟")
    text = "\n".join(lines)

    if do_plot:
        if plt is None:
            text += "\n\n（未安装 matplotlib，无法画图）"
        else:
            plt.figure()
            plt.plot(dates, values, marker="o")
            plt.title(f"最近 {days} 天每日学习时长")
            plt.xlabel("日期")
            plt.ylabel("学习时长（分钟）")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

    return text


# ================== 悬浮 GUI 计时器 ==================

class FloatingPomodoroTimer:
    def __init__(self):
        ensure_log_file()

        # ---- 粉色系配色 ----
        self.bg_color = "#2b182b"          # 深一点的紫粉
        self.card_color = "#3b203b"
        self.primary_color = "#ff79c6"     # 粉
        self.text_color = "#ffeefc"
        self.accent_color = "#ffb3d9"      # 浅粉

        # ---- 窗口设置 ----
        self.root = tk.Tk()
        self.root.overrideredirect(True)       # 去掉系统标题栏
        self.root.attributes("-topmost", True) # 总在最前
        self.root.configure(bg=self.bg_color)
        self.root.attributes("-alpha", 0.92)   # 默认有一点透明

        # 先暂时设置个大小，后面再挪到右上角
        width, height = 380, 270
        self.root.geometry(f"{width}x{height}+0+0")
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        # 距离右边和顶部稍微留一点边距
        x = screen_w - width - 20
        y = 20
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # 拖动用到的变量
        self._drag_start_x = 0
        self._drag_start_y = 0

        # ---- 状态变量 ----
        self.mode = "countup"          # "countup" 或 "countdown"
        self.running = False
        self.start_time = None
        self.elapsed = timedelta(0)
        self.countdown_total_seconds = 0

        # =====  自定义“标题栏”区域  =====
        title_bar = tk.Frame(self.root, bg=self.card_color)
        title_bar.pack(fill="x")

        self.title_label = tk.Label(
            title_bar,
            text="  粉色番茄学习钟",
            bg=self.card_color,
            fg=self.primary_color,
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side="left", padx=(5, 0))

        close_label = tk.Label(
            title_bar,
            text="×",
            bg=self.card_color,
            fg=self.text_color,
            font=("Segoe UI", 10, "bold")
        )
        close_label.pack(side="right", padx=5)

        # 标题栏支持拖动
        for widget in (title_bar, self.title_label):
            widget.bind("<Button-1>", self.start_move)
            widget.bind("<B1-Motion>", self.on_move)

        close_label.bind("<Button-1>", lambda e: self.root.destroy())

        # ===== 主内容区域 =====
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill="both", expand=True, padx=8, pady=5)

        # 时间显示
        self.time_label = tk.Label(
            main_frame,
            text="00:00:00",
            font=("Consolas", 32, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.time_label.pack(pady=(5, 0))

        # 模式提示
        self.mode_label = tk.Label(
            main_frame,
            text="模式：正计时",
            font=("Segoe UI", 9),
            bg=self.bg_color,
            fg=self.accent_color
        )
        self.mode_label.pack(pady=(0, 5))

                # 按钮区域
        btn_frame = tk.Frame(main_frame, bg=self.bg_color)
        btn_frame.pack(pady=3)

        # 开始 / 暂停 / 继续
        self.start_btn = tk.Button(
            btn_frame,
            text="开始",
            font=("Segoe UI", 9, "bold"),
            width=6,
            command=self.toggle,
            bg=self.primary_color,
            fg="#ffffff",
            activebackground="#ff92d2",
            activeforeground="#ffffff",
            bd=0,
            relief="flat"
        )
        self.start_btn.grid(row=0, column=0, padx=3)

        # ✅ 新增：自定义倒计时按钮
        self.custom_btn = tk.Button(
            btn_frame,
            text="自定义",
            font=("Segoe UI", 8),
            width=6,
            command=self.start_custom_countdown,
            bg="#4b2b4b",
            fg=self.text_color,
            activebackground="#5c3560",
            activeforeground=self.text_color,
            bd=0,
            relief="flat"
        )
        self.custom_btn.grid(row=0, column=1, padx=3)

        # 结束并保存
        self.finish_btn = tk.Button(
            btn_frame,
            text="结束并存",
            font=("Segoe UI", 8),
            width=7,
            command=self.finish_and_save,
            bg="#4b2b4b",
            fg=self.text_color,
            activebackground="#5c3560",
            activeforeground=self.text_color,
            bd=0,
            relief="flat"
        )
        self.finish_btn.grid(row=0, column=2, padx=3)

        # 番茄钟 25分钟
        self.pomodoro_btn = tk.Button(
            btn_frame,
            text="🍅25分钟",
            font=("Segoe UI", 8, "bold"),
            width=8,
            command=self.start_pomodoro,
            bg="#ffb3d9",
            fg="#5a0033",
            activebackground="#ffc6e3",
            activeforeground="#5a0033",
            bd=0,
            relief="flat"
        )
        self.pomodoro_btn.grid(row=0, column=3, padx=3)


        # 统计按钮
        stat_frame = tk.Frame(main_frame, bg=self.bg_color)
        stat_frame.pack(pady=(5, 0))

        self.today_btn = tk.Button(
            stat_frame,
            text="今日",
            font=("Segoe UI", 8),
            width=5,
            command=self.show_today_stat,
            bg="#4b2b4b",
            fg=self.text_color,
            activebackground="#5c3560",
            activeforeground=self.text_color,
            bd=0,
            relief="flat"
        )
        self.today_btn.grid(row=0, column=0, padx=2)

        self.recent_btn = tk.Button(
            stat_frame,
            text="N天",
            font=("Segoe UI", 8),
            width=5,
            command=self.show_recent_stat,
            bg="#4b2b4b",
            fg=self.text_color,
            activebackground="#5c3560",
            activeforeground=self.text_color,
            bd=0,
            relief="flat"
        )
        self.recent_btn.grid(row=0, column=1, padx=2)

        # 透明度调节（小号版）
        alpha_frame = tk.Frame(main_frame, bg=self.bg_color)
        alpha_frame.pack(pady=(3, 0))

        alpha_label = tk.Label(
            alpha_frame,
            text="透明",
            font=("Segoe UI", 8),
            bg=self.bg_color,
            fg=self.accent_color
        )
        alpha_label.pack(side="left", padx=(2, 2))

        self.alpha_scale = tk.Scale(
            alpha_frame,
            from_=50,
            to=100,
            orient="horizontal",
            showvalue=True,
            length=90,
            command=self.on_alpha_change,
            bg=self.bg_color,
            fg=self.text_color,
            troughcolor="#5c3560",
            highlightthickness=0,
            bd=0,
        )
        self.alpha_scale.set(92)
        self.alpha_scale.pack(side="left")

        # 启动刷新
        self.update_time()
        self.root.mainloop()

    # ---------- 窗口拖动 ----------
    def start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def on_move(self, event):
        x = event.x_root - self._drag_start_x
        y = event.y_root - self._drag_start_y
        self.root.geometry(f"+{x}+{y}")

    # ---------- 透明度 ----------
    def on_alpha_change(self, value):
        try:
            alpha = float(value) / 100.0
        except ValueError:
            return
        alpha = max(0.3, min(1.0, alpha))
        self.root.attributes("-alpha", alpha)

    # ---------- 番茄钟一键 25 分钟 ----------
        # ---------- 番茄钟一键 25 分钟 ----------
    def start_pomodoro(self):
        if self.running:
            messagebox.showinfo("提示", "请先结束或暂停当前计时，再开启番茄钟。")
            return

        self.mode = "countdown"
        self.countdown_total_seconds = 25 * 60
        self.elapsed = timedelta(0)

        self.mode_label.config(text="模式：番茄钟 25 分钟")
        self.update_time_label_for_countdown()

        # 保持静止，等待用户点“开始”
        self.running = False
        self.start_btn.config(text="开始", bg=self.primary_color, activebackground="#ff92d2")

        # 可选提示
        # messagebox.showinfo("提示", "番茄钟已设置为 25 分钟，点击“开始”按键启动。")

    def start_custom_countdown(self):
        if self.running:
            messagebox.showinfo("提示", "请先结束或暂停当前计时，再开启新的倒计时。")
            return

        minutes = simpledialog.askfloat("自定义倒计时", "请输入倒计时的分钟数：", minvalue=0.1)
        if minutes is None:
            return  # 用户取消
        if minutes <= 0:
            messagebox.showinfo("提示", "倒计时时间必须大于 0 分钟。")
            return

        # 只做“模式设置”和“显示”，不自动开始
        self.mode = "countdown"
        self.countdown_total_seconds = int(minutes * 60)
        self.elapsed = timedelta(0)

        self.mode_label.config(text=f"模式：倒计时 {minutes:.1f} 分钟")
        self.update_time_label_for_countdown()

        # 确保当前是“未启动状态”
        self.running = False
        self.start_btn.config(text="开始", bg=self.primary_color, activebackground="#ff92d2")

        # 可选：给个提示
        # messagebox.showinfo("提示", "倒计时已设置，点击“开始”按键启动。")



    # ---------- 开始 / 暂停 / 继续 ----------
    def toggle(self):
        if not self.running:
            # 开始或继续
            self.start_time = datetime.now() - self.elapsed
            self.running = True
            self.start_btn.config(text="暂停", bg="#ff92d2", activebackground="#ffb3e1")
        else:
            # 暂停
            self.elapsed = datetime.now() - self.start_time
            self.running = False
            self.start_btn.config(text="继续", bg=self.primary_color, activebackground="#ff92d2")

    # ---------- 结束本次学习并保存 ----------
    def finish_and_save(self):
        if self.running:
            self.elapsed = datetime.now() - self.start_time
            self.running = False

        self.start_btn.config(text="开始", bg=self.primary_color, activebackground="#ff92d2")

        if self.elapsed.total_seconds() <= 0:
            messagebox.showinfo("提示", "当前没有正在进行或已暂停的学习记录。")
            return

        end_dt = datetime.now()
        start_dt = end_dt - self.elapsed
        duration_seconds = self.elapsed.total_seconds()

        note = simpledialog.askstring("备注", "给本次学习写个备注（可空）：")
        if note is None:
            note = ""

        save_log(start_dt, end_dt, duration_seconds, self.mode, note)
        messagebox.showinfo("保存成功", "本次学习记录已保存到 study_log.csv")

        # 重置
        self.elapsed = timedelta(0)
        self.time_label.config(text="00:00:00")
        self.mode = "countup"
        self.mode_label.config(text="模式：正计时")

    # ---------- 每 100ms 更新时间 ----------
    def update_time(self):
        if self.running:
            now = datetime.now()
            self.elapsed = now - self.start_time
            if self.mode == "countup":
                self.update_time_label_for_countup()
            else:
                self.update_time_label_for_countdown(auto_stop=True)
        self.root.after(100, self.update_time)

    def update_time_label_for_countup(self):
        seconds = int(self.elapsed.total_seconds())
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

    def update_time_label_for_countdown(self, auto_stop=False):
        elapsed_sec = int(self.elapsed.total_seconds())
        remaining = self.countdown_total_seconds - elapsed_sec
        if remaining < 0:
            remaining = 0

        h, rem = divmod(remaining, 3600)
        m, s = divmod(rem, 60)
        self.time_label.config(text=f"{h:02d}:{m:02d}:{s:02d}")

        if auto_stop and remaining <= 0 and self.running:
            # 倒计时结束
            self.running = False
            self.start_btn.config(text="开始", bg=self.primary_color, activebackground="#ff92d2")
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(seconds=self.countdown_total_seconds)
            duration_seconds = self.countdown_total_seconds

            note = simpledialog.askstring("倒计时结束", "时间到！给本次学习写个备注（可空）：")
            if note is None:
                note = ""
            save_log(start_dt, end_dt, duration_seconds, "countdown", note)
            messagebox.showinfo("提示", "倒计时已结束，本次学习记录已保存到 study_log.csv")

            self.elapsed = timedelta(0)
            self.mode = "countup"
            self.mode_label.config(text="模式：正计时")

    # ---------- 今日 & 最近统计 ----------
    def show_today_stat(self):
        text = summarize_today()
        messagebox.showinfo("今日学习统计", text)

    def show_recent_stat(self):
        days = simpledialog.askinteger("最近 N 天", "请输入要查看的天数（例如 7）：", minvalue=1, maxvalue=365)
        if days is None:
            return
        want_plot = messagebox.askyesno("画图？", "是否画出最近天数的学习折线图？（需要安装 matplotlib）")
        text = summarize_recent(days=days, do_plot=want_plot)
        messagebox.showinfo("最近学习统计", text)


if __name__ == "__main__":
    FloatingPomodoroTimer()
