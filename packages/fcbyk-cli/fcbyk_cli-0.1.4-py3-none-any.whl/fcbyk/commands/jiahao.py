import click
import random
import time
import sys
import os
import shutil
from threading import Thread, Event

try:
    import colorama
except ImportError:
    colorama = None

class FullscreenHacker:
    def __init__(self, duration=10, speed=0.05, mode='binary', density=0.7):
        """
        全屏黑客终端模拟器
        
        Args:
            duration: 运行时间（秒）
            speed: 字符刷新速度（秒）
            mode: 显示模式 ('binary', 'code', 'matrix', 'glitch')
            density: 字符密度 0.1-1.0
        """
        self.duration = duration
        self.speed = speed
        self.mode = mode
        self.density = density
        self.running = False
        self.start_time = None
        self.stop_event = Event()
        
        # 获取终端尺寸
        self.terminal_size = self.get_terminal_size()
        
        # 黑客代码片段
        self.hacker_sentences = [
            "INITIALIZING CYBER ATTACK PROTOCOL...",
            "BYPASSING FIREWALL...",
            "ACCESSING MAINFRAME...",
            "DECRYPTING SECURITY LAYERS...",
            "ESTABLISHING BACKDOOR...",
            "EXFILTRATING DATA...",
            "COVERING TRACES...",
            "ROOT ACCESS GRANTED...",
            "DATABASE PENETRATION SUCCESSFUL...",
            "NEURAL NETWORK INFILTRATED...",
            "QUANTUM ENCRYPTION BREACHED...",
            "AI SECURITY OVERRIDDEN...",
            "SATELLITE LINK ESTABLISHED...",
            "DEEP WEB ACCESS OBTAINED...",
            "BLOCKCHAIN INTEGRITY COMPROMISED...",
        ]
        
        # 系统名称
        self.systems = [
            "GOV-SECURE-NET", "PENTAGON-ALPHA", "CIA-CLOUD-7", 
            "NSA-QUANTUM", "MILITARY-GRID", "SWIFT-CORE",
            "NASA-JPL-MAIN", "TESLA-AI-CENTRAL", "SPACEX-COMM",
            "GOOGLE-DEEP-MIND", "FACEBOOK-META-VR", "APPLE-SECURE",
            "AMAZON-AWS-CONTROL", "MICROSOFT-AZURE-CORE",
            "TOR-HIDDEN-SERVICE", "DARKNET-EXCHANGE"
        ]
        
        # 更多字符集
        self.binary_chars = "01"
        self.hex_chars = "0123456789ABCDEF"
        self.matrix_chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
        self.code_chars = "{}[]()<>;:=+-*/&|!~#@%$_"
        self.glitch_chars = "░▒▓█▀▄▌▐■□▲►▼◄◆◇○●◎☆★☯☮☣☢☠♛♕♔♚"
        self.alphanum_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        # Windows 下尝试启用 ANSI 支持
        self.enable_windows_ansi()
        self.ansi_enabled = self.detect_ansi_support()

    def detect_ansi_support(self):
        """检测终端是否支持 ANSI / VT 控制"""
        if not sys.stdout.isatty():
            return False
        if os.name != 'nt':
            return True
        if os.environ.get("WT_SESSION") or os.environ.get("TERM"):
            return True
        if colorama:
            return True
        return False

    def enable_windows_ansi(self):
        """在 Windows cmd/powershell 下启用 ANSI 支持"""
        if os.name == 'nt' and colorama:
            try:
                colorama.just_fix_windows_console()
            except Exception:
                # 失败时忽略，继续用退化的效果
                pass
        
    def get_terminal_size(self):
        """获取终端尺寸"""
        try:
            size = shutil.get_terminal_size()
            return (size.columns, size.lines)
        except:
            return (80, 24)  # 默认值
    
    def clear_screen(self):
        """清屏并重置光标"""
        if not self.ansi_enabled:
            return
        sys.stdout.write('\033[2J\033[H')
        sys.stdout.flush()
    
    def hide_cursor(self):
        """隐藏光标"""
        if not self.ansi_enabled:
            return
        sys.stdout.write('\033[?25l')
        sys.stdout.flush()
    
    def show_cursor(self):
        """显示光标"""
        if not self.ansi_enabled:
            return
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
    
    def move_cursor(self, x, y):
        """移动光标到指定位置"""
        if not self.ansi_enabled:
            return
        sys.stdout.write(f'\033[{y};{x}H')
        sys.stdout.flush()
    
    def generate_binary_screen(self):
        """生成全屏二进制"""
        cols, rows = self.terminal_size
        screen = []
        
        for row in range(rows - 2):  # 留出底部空间
            line = []
            for col in range(cols):
                if random.random() < self.density:
                    char = random.choice(self.binary_chars)
                    # 随机高亮
                    if random.random() < 0.1:
                        char = f"\033[1;32m{char}\033[0m"  # 亮绿色
                    elif random.random() < 0.3:
                        char = f"\033[0;32m{char}\033[0m"  # 绿色
                    else:
                        char = f"\033[0;90m{char}\033[0m"  # 暗灰色
                else:
                    char = " "
                line.append(char)
            
            # 偶尔插入十六进制块
            if random.random() < 0.05:
                pos = random.randint(0, cols - 9)
                hex_block = "".join(random.choice(self.hex_chars) for _ in range(8))
                line[pos:pos+8] = [f"\033[1;33m{c}\033[0m" for c in hex_block]
            
            screen.append("".join(line))
        
        return screen
    
    def generate_matrix_screen(self):
        """生成矩阵风格屏幕"""
        cols, rows = self.terminal_size
        screen = []
        
        for row in range(rows - 2):
            line = []
            for col in range(cols):
                if random.random() < self.density:
                    char = random.choice(self.matrix_chars + self.alphanum_chars)
                    # 创建瀑布流效果
                    brightness = int((row / rows) * 10) + random.randint(0, 5)
                    if brightness > 8:
                        char = f"\033[1;32m{char}\033[0m"  # 亮绿
                    elif brightness > 4:
                        char = f"\033[0;32m{char}\033[0m"  # 绿
                    else:
                        char = f"\033[0;90m{char}\033[0m"  # 暗绿
                else:
                    char = " "
                line.append(char)
            
            screen.append("".join(line))
        
        return screen
    
    def generate_code_screen(self):
        """生成代码风格屏幕"""
        cols, rows = self.terminal_size
        screen = []
        
        # 先填充随机字符
        for row in range(rows - 2):
            line = []
            for col in range(cols):
                if random.random() < self.density * 0.8:
                    char = random.choice(self.code_chars + self.alphanum_chars)
                    line.append(f"\033[0;36m{char}\033[0m")
                else:
                    line.append(" ")
            screen.append("".join(line))
        
        # 添加一些代码行
        code_lines = [
            f"root@{random.choice(self.systems)}:~# {random.choice(['sudo', 'python3', 'nmap', 'hydra', 'metasploit', 'sqlmap'])}",
            f"ACCESS: {random.choice(['GRANTED', 'DENIED', 'PENDING'])} | LEVEL: {random.choice(['ROOT', 'ADMIN', 'USER'])}",
            f"ENCRYPTION: {random.choice(['AES-256', 'RSA-4096', 'ECC-521'])} | STATUS: {random.choice(['CRACKED', 'PENDING', 'FAILED'])}",
            f"IP: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}: {random.randint(1,65535)}",
            f"TRANSFER: {random.randint(1,999)}.{random.randint(0,99)} GB | SPEED: {random.randint(10,999)} MB/s",
            f"PROXY: TOR_NODE_{random.randint(1,9999)} | ANONYMITY: {random.randint(70,100)}%",
        ]
        
        # 在随机位置插入代码行
        for _ in range(random.randint(2, 5)):
            if len(screen) > 5:
                row = random.randint(0, len(screen) - 3)
                col = random.randint(0, max(0, cols - 50))
                line = screen[row]
                code = random.choice(code_lines)
                if col + len(code) < cols:
                    screen[row] = line[:col] + f"\033[1;33m{code}\033[0m" + line[col + len(code):]
        
        return screen
    
    def generate_glitch_screen(self):
        """生成故障效果屏幕"""
        cols, rows = self.terminal_size
        screen = []
        
        for row in range(rows - 2):
            line = []
            for col in range(cols):
                if random.random() < self.density * 0.6:
                    chars = self.glitch_chars + self.binary_chars + self.code_chars
                    char = random.choice(chars)
                    # 随机颜色
                    colors = [
                        '\033[0;31m',  # 红
                        '\033[0;32m',  # 绿
                        '\033[0;33m',  # 黄
                        '\033[0;34m',  # 蓝
                        '\033[0;35m',  # 紫
                        '\033[0;36m',  # 青
                        '\033[1;37m',  # 白
                    ]
                    color = random.choice(colors)
                    line.append(f"{color}{char}\033[0m")
                else:
                    line.append(" ")
            
            # 随机加入故障效果
            if random.random() < 0.1:
                pos = random.randint(0, cols - 5)
                glitch = "".join(random.choice(self.glitch_chars) for _ in range(4))
                line[pos:pos+4] = [f"\033[1;37m{c}\033[0m" for c in glitch]
            
            screen.append("".join(line))
        
        return screen
    
    
    def display_progress(self, elapsed, rows):
        """在底部显示进度条"""
        progress = min(elapsed / self.duration, 1.0)
        bar_width = max(20, self.terminal_size[0] - 20)
        
        # 进度条
        filled = int(bar_width * progress)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # 状态信息
        speed = f"{1/self.speed:.1f}FPS" if self.speed > 0 else "MAX"
        status = random.choice(["ACTIVE", "RUNNING", "SCANNING", "DECRYPTING", "INJECTING"])
        
        if not self.ansi_enabled:
            # 简单单行进度，避免定位指令
            sys.stdout.write(f"\r[{bar}] {progress*100:5.1f}% | {elapsed:5.1f}s/{self.duration}s | {status:<10} | {speed}")
            sys.stdout.flush()
            return

        # 移动到倒数第二行
        self.move_cursor(1, rows - 1)
        
        progress_line = f"\033[1;37m[{bar}] {progress*100:5.1f}% | {elapsed:5.1f}s/{self.duration}s | {status:<12} | {speed}\033[0m"
        sys.stdout.write(progress_line)
        sys.stdout.flush()
        
        # 移动到倒数第三行显示系统信息
        self.move_cursor(1, rows - 2)
        system_info = f"\033[0;36mTARGET: {random.choice(self.systems):<20} | BREACH: {progress*100:5.1f}% | THREAT: {random.randint(1,100):>3}%\033[0m"
        sys.stdout.write(system_info)
        sys.stdout.flush()
    
    def countdown_timer(self, rows, cols):
        """在右上角显示倒计时"""
        if not self.ansi_enabled:
            return
        while not self.stop_event.is_set():
            if self.start_time:
                elapsed = time.time() - self.start_time
                remaining = max(0, self.duration - elapsed)
                
                # 移动到右上角
                self.move_cursor(cols - 20, 1)
                
                # 闪烁效果
                if remaining < 5:
                    color = "\033[1;31m"  # 红色闪烁
                elif remaining < 10:
                    color = "\033[1;33m"  # 黄色
                else:
                    color = "\033[1;32m"  # 绿色
                
                timer_text = f"{color}[ {remaining:05.1f}s ]\033[0m"
                sys.stdout.write(timer_text)
                sys.stdout.flush()
            
            time.sleep(0.1)
    
    def run(self):
        """运行全屏黑客终端"""
        try:
            self.running = True
            self.start_time = time.time()
            
            # 设置终端
            self.clear_screen()
            self.hide_cursor()
                        
            # 启动倒计时线程
            timer_thread = Thread(target=self.countdown_timer, args=(self.terminal_size[1], self.terminal_size[0]))
            timer_thread.start()
            
            # 主循环
            while self.running:
                elapsed = time.time() - self.start_time
                
                if elapsed >= self.duration:
                    break
                
                # 生成并显示全屏内容
                if self.mode == 'binary':
                    screen = self.generate_binary_screen()
                elif self.mode == 'matrix':
                    screen = self.generate_matrix_screen()
                elif self.mode == 'code':
                    screen = self.generate_code_screen()
                elif self.mode == 'glitch':
                    screen = self.generate_glitch_screen()
                else:
                    screen = self.generate_binary_screen()
                
                # 移动到内容区域开始位置（顶部），避免留出大段空行
                self.move_cursor(1, 2)
                
                # 输出屏幕内容
                for line in screen:
                    sys.stdout.write(line + '\n')
                
                # 显示进度
                self.display_progress(elapsed, self.terminal_size[1])
                
                sys.stdout.flush()
                time.sleep(self.speed)
                
        except KeyboardInterrupt:
            self.running = False
            self.stop_event.set()
            
        finally:
            self.running = False
            self.stop_event.set()
            time.sleep(0.1)  # 让线程结束
            
            # 恢复终端
            self.show_cursor()
            self.display_completion()
    
    def display_completion(self):
        """显示完成信息"""
        self.clear_screen()
        cols, rows = self.terminal_size
        
        if not self.ansi_enabled:
            print("\nOPERATION COMPLETED SUCCESSFULLY")
            print(f"Duration: {self.duration}s")
            print(f"Data exfiltrated: {random.randint(100, 999)}.{random.randint(0,99)} GB")
            print(f"Targets: {random.randint(5, 20)}")
            input("\nPress Enter to exit...")
            return
        
        # 居中显示完成信息
        message = f"""
\033[1;32m{'█' * cols}\033[0m

{' ' * ((cols - 50) // 2)}\033[1;36m╔══════════════════════════════════════════════╗\033[0m
{' ' * ((cols - 50) // 2)}\033[1;36m║       OPERATION COMPLETED SUCCESSFULLY       ║\033[0m
{' ' * ((cols - 50) // 2)}\033[1;36m╚══════════════════════════════════════════════╝\033[0m

{' ' * ((cols - 60) // 2)}\033[1;33m[✓] All systems penetrated: {random.randint(5, 20)} targets
{' ' * ((cols - 60) // 2)}\033[1;33m[✓] Data exfiltrated: {random.randint(100, 999)}.{random.randint(0,99)} GB
{' ' * ((cols - 60) // 2)}\033[1;33m[✓] Zero-day exploits used: {random.randint(1, 5)}
{' ' * ((cols - 60) // 2)}\033[1;33m[✓] Anonymity maintained: {random.randint(95, 100)}%
{' ' * ((cols - 60) // 2)}\033[1;33m[✓] Forensic evidence: 0 bytes

{' ' * ((cols - 70) // 2)}\033[1;35m"THE ONLY IMPOSSIBLE HACK IS THE ONE YOU NEVER ATTEMPT."
{' ' * ((cols - 70) // 2)}\033[1;35m                                   - Jiahao 2077

\033[1;31m{'█' * cols}\033[0m
"""
        print(message)
        
        # 等待按键退出
        input(f"\n{' ' * ((cols - 30) // 2)}\033[1;37mPress Enter to return to reality...\033[0m")

def select_mode_interactively(current):
    """使用上下键选择模式并按回车确认"""
    modes = ['binary', 'code', 'matrix', 'glitch']
    descriptions = {
        'binary': 'Matrix-style binary rain',
        'code': 'Random code blocks and snippets',
        'matrix': 'Green cascade characters',
        'glitch': 'Glitch symbols and blocks'
    }
    index = modes.index(current) if current in modes else 0
    lines_to_render = len(modes) + 3  # 标题 + 模式行 + 空行

    def render():
        click.echo("\nUse ↑/↓ to choose display mode, Enter to confirm:")
        for i, m in enumerate(modes):
            selected = i == index
            pointer = "\033[1;32m> \033[0m" if selected else "  "
            color = "\033[1;37m" if selected else "\033[0;37m"
            click.echo(f"{pointer}{color}{m:<7}\033[0m - {descriptions[m]}")
        click.echo("")  # 保持一个空行

    render()
    while True:
        ch = click.getchar()

        # 兼容多种箭头键序列：
        # - *nix / Windows Terminal: "\x1b[A" / "\x1b[B"
        # - Windows 控制台 getch: 前缀 "\xe0" + "H"/"P"
        # - 部分场景返回完整序列一次性 "\x1b[A"
        seq = ch
        if ch in ('\x1b', '\xe0', '\x00'):
            second = click.getchar()
            third = click.getchar() if second in ('[', 'O') else ''
            seq = ch + second + third

        if seq in ('\x1b[A', '\xe0H'):
            index = (index - 1) % len(modes)
        elif seq in ('\x1b[B', '\xe0P'):
            index = (index + 1) % len(modes)
        elif seq.startswith('\x1b[A'):  # 兼容一次性返回的序列
            index = (index - 1) % len(modes)
        elif seq.startswith('\x1b[B'):
            index = (index + 1) % len(modes)
        elif ch in ('w', 'W'):
            index = (index - 1) % len(modes)
        elif ch in ('s', 'S'):
            index = (index + 1) % len(modes)
        elif ch in ('\r', '\n'):
            break
        else:
            continue

        # 如果终端支持 ANSI，移动光标回到菜单顶部重绘
        if sys.stdout.isatty():
            sys.stdout.write('\033[F' * lines_to_render)
            sys.stdout.write('\033[J')
            sys.stdout.flush()
        render()

    return modes[index]

@click.command(name='jiahao', help='Jiahao Hacker Terminal Simulator')
@click.option('--duration', '-d', default=30, type=int, 
              help='Run duration in seconds', show_default=True)
@click.option('--speed', '-s', default=0.05, type=float,
              help='Refresh interval in seconds (smaller is faster)', show_default=True)
@click.option('--density', default=0.7, type=float,
              help='Character density 0.1-1.0', show_default=True)
def jiahao(duration, speed, density):
    click.clear()
    
    # 警告信息
    click.echo("\n" + "="*80)
    click.echo("\033[1;31m[!] WARNING: Entering full-screen hacker mode\033[0m")
    click.echo("\033[1;33m[!] Press Ctrl+C to exit at any time\033[0m")
    click.echo("\033[1;32m[!] This is a visual simulation only; no real network activity will occur\033[0m")
    click.echo("="*80)
    
    # 模式选择（上下键选择，回车确认）
    mode = select_mode_interactively('binary')
    
    # 按回车进入
    input("\033[1;35m[+] Press Enter to enter hacker mode...\033[0m")
    click.echo("\r\033[1;32m[+] Entering the Matrix...                          \033[0m")
    time.sleep(1)
    
    # 启动黑客终端
    hacker = FullscreenHacker(
        duration=duration, 
        speed=speed, 
        mode=mode,
        density=min(max(density, 0.1), 1.0)  # 限制在0.1-1.0之间
    )
    
    try:
        hacker.run()
    except Exception as e:
        click.echo(f"\n\033[1;31m[!] 错误: {e}\033[0m")
    finally:
        # 确保光标恢复
        sys.stdout.write('\033[?25h')
        sys.stdout.flush()
