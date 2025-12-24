from os import name
import string
import click
import tkinter as tk
import random
import threading
import time

def show_warm_tip(title,tips):
    # 创建窗口
    window = tk.Tk()

    # 获取屏幕宽高
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # 随机窗口位置(确保窗口完全显示在屏幕内)
    window_width = 250
    window_height = 60
    x = random.randrange(0, screen_width - window_width)
    y = random.randrange(0, screen_height - window_height)

    # 设置窗口标题和大小位置
    window.title(title)
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")

    tip = random.choice(tips)

    # 多样的背景颜色
    bg_colors = [
        'lightpink', 'skyblue', 'lightgreen', 'lavender',
        'lightyellow', 'plum', 'coral', 'bisque', 'aquamarine',
        'mistyrose', 'honeydew', 'lavenderblush', 'oldlace'
    ]
    bg = random.choice(bg_colors)

    # 创建标签并显示文字
    tk.Label(
        window,
        text=tip,
        bg=bg,
        font=('微软雅黑', 16),
        width=30,
        height=3
    ).pack()

    # 窗口置顶显示
    window.attributes('-topmost', True)

    window.mainloop()

@click.command(name='popup', help='Display multiple popup windows with random tips at random screen positions')
@click.option('--title', '-t', default='温馨提示', help='Title text for the popup windows')
@click.option('--numbers', '-n', default=20, type=int, help='Number of popup windows to display (default: 20, max recommended: 50)')
@click.argument('tips', nargs=-1)
def popup(title,numbers,tips):
    # 创建线程列表
    threads = []

    if not tips:
        tips = ['多喝水哦~', '保持微笑呀', '每天都要元气满满',
        '记得吃水果', '保持好心情', '好好爱自己', '我想你了',
        '梦想成真', '期待下一次见面', '金榜题名',
        '顺顺利利', '早点休息', '愿所有烦恼都消失',
        '别熬夜', '今天过得开心嘛', '天冷了，多穿衣服']

    # 验证参数
    if numbers < 1:
        click.echo("Number of popups must be greater than 0")
        return
        
    if numbers > 50:
        click.echo(f"Warning: Will create {numbers} windows, this may affect performance!")
        if not click.confirm('Do you want to continue?'):
            return

    # 窗口数量(根据屏幕大小可调整)
    for i in range(numbers):
        t = threading.Thread(target=show_warm_tip, args=(title,tips))
        threads.append(t)
        time.sleep(0.005)  # 快速弹出窗口
        threads[i].start()







