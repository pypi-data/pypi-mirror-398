import click
import random
import string
import time
import os
import json
import webbrowser
import socket
import uuid
from typing import Optional, Iterable, Dict, Set
from flask import Flask, jsonify, render_template, request, send_file, url_for
from datetime import datetime
import threading, asyncio

config_file = os.path.join(os.path.expanduser('~'), '.fcbyk', 'pick.json')
SERVER_SESSION_ID = str(uuid.uuid4())
ADMIN_PASSWORD = None

default_config = {
    'items': []
}

# Flask 应用（模板目录复用 web 目录）
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'web'))

# Web 模式状态
current_template = 'pick/index.html'
files_mode_root = None  # 指定目录或单文件路径

# 抽奖限制模式：
# - 旧逻辑：按 IP 限制（ip_draw_records）
# - 新逻辑：按兑换码限制（redeem_codes），当 redeem_codes 不为空时优先生效
# 另外增加 ip_file_history：记录每个 IP 已经抽中过哪些文件，避免同一 IP 重复抽到同一个文件
ip_draw_records = {}                         # {ip: filename}
redeem_codes: Dict[str, bool] = {}           # {code: used_flag}
ip_file_history: Dict[str, Set[str]] = {}    # {ip: {filename, ...}}
code_results: Dict[str, Dict] = {}           # {code: {file: {...}, download_url: str, timestamp: str}} 保存兑换码的抽奖结果


@app.route('/')
def pick_index():
    """抽奖网页入口"""
    return render_template(current_template)


@app.route('/style.css')
@app.route('/pick/style.css')
def style_css():
    """提供公共样式文件"""
    css_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'pick', 'style.css')
    return send_file(css_path, mimetype='text/css')


@app.route('/api/items')
def api_items():
    """返回当前配置中的抽奖项"""
    config = load_config()
    return jsonify({'items': config.get('items', [])})


def _get_client_ip():
    """获取客户端 IP，优先 X-Forwarded-For"""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _list_files():
    """列出文件模式下可供抽取的文件"""
    if not files_mode_root:
        return []
    root = files_mode_root
    if os.path.isfile(root):
        return [{
            'name': os.path.basename(root),
            'path': root,
            'size': os.path.getsize(root) if os.path.exists(root) else 0
        }]
    files = []
    try:
        for name in sorted(os.listdir(root)):
            full = os.path.join(root, name)
            if os.path.isfile(full):
                files.append({
                    'name': name,
                    'path': full,
                    'size': os.path.getsize(full)
                })
    except FileNotFoundError:
        return []
    return files


@app.route('/api/files', methods=['GET'])
def api_files():
    """列出文件列表并返回当前抽奖状态"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400
    files = _list_files()
    resp = {
        'files': [{'name': f['name'], 'size': f['size']} for f in files],
    }

    resp['session_id'] = SERVER_SESSION_ID

    # 如果配置了兑换码，则使用兑换码模式统计
    if redeem_codes:
        total = len(redeem_codes)
        used = sum(1 for v in redeem_codes.values() if v)
        resp.update({
            'mode': 'code',
            'total_codes': total,
            'used_codes': used,
            'draw_count': used,
            'limit_per_code': 1,
        })
    else:
        # 兼容旧逻辑：按 IP 限制
        client_ip = _get_client_ip()
        picked = ip_draw_records.get(client_ip)
        resp.update({
            'mode': 'ip',
            'draw_count': len(ip_draw_records),
            'ip_picked': picked,
            'limit_per_ip': 1,
        })
    return jsonify(resp)


@app.route('/api/files/pick', methods=['POST'])
def api_files_pick():
    """从文件列表随机抽取一个文件

    - 如果配置了兑换码：每个兑换码仅能成功抽取一次
    - 否则回退到旧逻辑：每个 IP 限制一次
    """
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400
    files = _list_files()
    if not files:
        return jsonify({'error': 'no files available'}), 400

    # 获取当前 IP，用于记录该 IP 已抽中过的文件，避免重复
    client_ip = _get_client_ip()

    # 兑换码模式
    if redeem_codes:
        data = request.get_json(silent=True) or {}
        code = str(data.get('code', '')).strip().upper()
        if not code:
            return jsonify({'error': '请输入兑换码'}), 400
        if code not in redeem_codes:
            return jsonify({'error': '兑换码无效'}), 400
        if redeem_codes[code]:
            return jsonify({'error': '兑换码已被使用'}), 429

        # 过滤掉当前 IP 已抽中过的文件
        used_by_ip = ip_file_history.get(client_ip, set())
        candidates = [f for f in files if f['name'] not in used_by_ip]
        if not candidates:
            return jsonify({'error': '本 IP 已无可抽取的文件'}), 400

        selected = random.choice(candidates)
        redeem_codes[code] = True
        # 记录当前 IP 抽中过的文件
        ip_file_history.setdefault(client_ip, set()).add(selected['name'])
        used = sum(1 for v in redeem_codes.values() if v)
        download_url = url_for('download_file', filename=selected['name'], _external=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 保存兑换码的抽奖结果，用于页面刷新后恢复
        code_results[code] = {
            'file': {'name': selected['name'], 'size': selected['size']},
            'download_url': download_url,
            'timestamp': timestamp,
        }
        click.echo(f"[{timestamp}] {client_ip} draw file: {selected['name']} successfully, redeem code: {code} used, remaining redeem codes: {len(redeem_codes)-used}")
        return jsonify({
            'file': {'name': selected['name'], 'size': selected['size']},
            'download_url': download_url,
            'mode': 'code',
            'draw_count': used,
            'total_codes': len(redeem_codes),
            'used_codes': used,
            'code': code,  # 返回兑换码，方便前端保存
        })

    # 兼容旧逻辑：IP 限制
    if client_ip in ip_draw_records:
        return jsonify({'error': 'already picked', 'picked': ip_draw_records[client_ip]}), 429
    # 过滤掉当前 IP 已抽中过的文件
    used_by_ip = ip_file_history.get(client_ip, set())
    candidates = [f for f in files if f['name'] not in used_by_ip]
    if not candidates:
        return jsonify({'error': '本 IP 已无可抽取的文件'}), 400

    selected = random.choice(candidates)
    ip_draw_records[client_ip] = selected['name']
    ip_file_history.setdefault(client_ip, set()).add(selected['name'])
    download_url = url_for('download_file', filename=selected['name'], _external=True)
    return jsonify({
        'file': {'name': selected['name'], 'size': selected['size']},
        'download_url': download_url,
        'mode': 'ip',
        'draw_count': len(ip_draw_records),
        'ip_picked': selected['name']
    })


@app.route('/api/files/result/<code>', methods=['GET'])
def api_files_result(code):
    """查询兑换码的抽奖结果（用于页面刷新后恢复）"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400
    code = str(code).strip().upper()
    if code not in code_results:
        return jsonify({'error': '兑换码未使用或结果不存在'}), 404
    result = code_results[code]
    return jsonify({
        'code': code,
        'file': result['file'],
        'download_url': result['download_url'],
        'timestamp': result['timestamp'],
    })


@app.route('/api/files/download/<path:filename>', methods=['GET'])
def download_file(filename):
    """下载指定文件，受限于文件模式根目录"""
    if not files_mode_root:
        return jsonify({'error': 'files mode not enabled'}), 400

    # 单文件模式：仅允许精确匹配文件名
    if os.path.isfile(files_mode_root):
        if filename != os.path.basename(files_mode_root):
            return jsonify({'error': 'file not found'}), 404
        return send_file(files_mode_root, as_attachment=True, download_name=filename)

    # 目录模式：防止路径穿越
    safe_root = os.path.abspath(files_mode_root)
    target_path = os.path.abspath(os.path.join(safe_root, filename))
    if not target_path.startswith(safe_root + os.sep) and target_path != safe_root:
        return jsonify({'error': 'invalid path'}), 400
    if not os.path.isfile(target_path):
        return jsonify({'error': 'file not found'}), 404
    return send_file(target_path, as_attachment=True, download_name=os.path.basename(target_path))


@app.route('/api/pick', methods=['POST'])
def api_pick_item():
    """从配置列表中随机抽取一项"""
    config = load_config()
    items = config.get('items', [])
    if not items:
        return jsonify({'error': 'no items available'}), 400
    selected = random.choice(items)
    return jsonify({'item': selected, 'items': items})


def load_config():
    """加载配置文件"""
    if not os.path.exists(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        return default_config.copy()
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception:
        config = default_config.copy()
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    updated = False
    for k, v in default_config.items():
        if k not in config:
            config[k] = v
            updated = True
    if updated:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    return config

def save_config(config):
    """保存配置文件"""
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def show_config(ctx, param, value):
    """显示配置信息"""
    if not value:
        return
    config = load_config()
    click.echo(f'Config file: {config_file}')
    click.echo(f'Items list: {config.get("items", [])}')
    ctx.exit()

def pick_item(items):
    """执行抽奖动画"""
    if not items:
        click.echo("Error: No items available. Please use --add to add items first")
        return
    
    click.echo("=== Random Pick ===")
    click.echo("Spinning...")
    
    # 抽奖动画
    max_length = max(len(f"Current pointer: {item}") for item in items) if items else 0

    # 内部函数：显示抽奖动画帧
    def show_animation_frame(iterations: int, delay: float) -> None:
        """显示抽奖动画的一帧
        Args:
            iterations: 动画帧数
            delay: 每帧之间的延迟（秒）
        """
        for _ in range(iterations):
            current = random.choice(items)
            # 使用空格填充确保清除整行
            display_text = f"Current pointer: {current}"
            padding = " " * max(0, max_length - len(display_text))
            click.echo(f"\r{display_text}{padding}", nl=False)
            time.sleep(delay)
    
    # 三个阶段：快速 -> 中速 -> 慢速
    show_animation_frame(random.randint(100, 200), 0.05)  # 快速阶段
    show_animation_frame(random.randint(20, 40), 0.3)    # 中速阶段
    show_animation_frame(random.randint(3, 10), 0.7)     # 慢速阶段
    
    click.echo("\nPick finished!")


def generate_redeem_codes(count: int, length: int = 4) -> Iterable[str]:
    """生成若干个随机兑换码（字母数字混合，大写）"""
    charset = string.ascii_uppercase + string.digits
    codes = set()
    # 简单避免重复
    while len(codes) < count:
        code = ''.join(random.choice(charset) for _ in range(length))
        codes.add(code)
    return sorted(codes)


def start_web_server(
    port: int,
    no_browser: bool,
    template: str = 'pick/index.html',
    files_root: Optional[str] = None,
    codes: Optional[Iterable[str]] = None,
    admin_password: Optional[str] = None,
) -> None:
    """启动抽奖 Web 服务器"""
    global current_template, files_mode_root, ip_draw_records, redeem_codes, ip_file_history, ADMIN_PASSWORD, code_results
    current_template = template
    ADMIN_PASSWORD = admin_password
    files_mode_root = os.path.abspath(files_root) if files_root else None
    ip_draw_records = {}
    redeem_codes = {}
    ip_file_history = {}
    code_results = {}
    if codes:
        # 初始化兑换码使用状态
        redeem_codes = {str(c).strip().upper(): False for c in codes if str(c).strip()}

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    url_local = f"http://127.0.0.1:{port}"
    url_network = f"http://{local_ip}:{port}"
    click.echo()
    click.echo(f" * Local URL: {url_local}")
    click.echo(f" * Network URL: {url_network}")
    click.echo(f" * Admin URL: {url_network}/admin")
    if files_mode_root:
        click.echo(f" * Files root: {files_mode_root}")
    if not no_browser:
        try:
            # 优先使用局域网地址自动打开，方便学生扫码或访问
            webbrowser.open(url_network)
            click.echo(" * Attempted to open picker page in browser (network URL)")
        except Exception:
            click.echo(" * Note: Could not auto-open browser, please visit the URL above")
    # 监听 0.0.0.0 便于局域网访问
    app.run(host='0.0.0.0', port=port)

def delayed_newline_simple():
    """延迟打印空行"""
    time.sleep(2)
    click.echo()


@app.route('/admin')
def admin_page():
    return render_template('pick/admin.html')


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    if not ADMIN_PASSWORD:
        return jsonify({'error': 'admin password not set'}), 500

    data = request.get_json(silent=True) or {}
    password = str(data.get('password', ''))

    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'invalid password'}), 401

    return jsonify({'success': True})


@app.route('/api/admin/codes', methods=['GET'])
def admin_codes():
    if not ADMIN_PASSWORD:
        return jsonify({'error': 'admin password not set'}), 500

    password = request.headers.get('X-Admin-Password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'unauthorized'}), 401

    codes_list = [{'code': code, 'used': used} for code, used in redeem_codes.items()]
    total = len(codes_list)
    used = sum(1 for c in codes_list if c['used'])
    left = total - used

    return jsonify({
        'codes': codes_list,
        'total_codes': total,   # 总数
        'used_codes': used,     # 已用
        'left_codes': left      # 剩余
    })


@app.route('/api/admin/codes/add', methods=['POST'])
def admin_codes_add():
    """新增兑换码"""
    if not ADMIN_PASSWORD:
        return jsonify({'error': 'admin password not set'}), 500

    password = request.headers.get('X-Admin-Password', '')
    if password != ADMIN_PASSWORD:
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    code = str(data.get('code', '')).strip().upper()

    if not code:
        return jsonify({'error': '兑换码不能为空'}), 400

    # 验证格式：只允许字母和数字
    if not all(c.isalnum() for c in code):
        return jsonify({'error': '兑换码只能包含字母和数字'}), 400

    # 检查是否已存在
    if code in redeem_codes:
        return jsonify({'error': '兑换码已存在'}), 400

    # 添加新兑换码
    redeem_codes[code] = False
    click.echo(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Admin added new redeem code: {code}")
    
    return jsonify({
        'success': True,
        'code': code,
        'message': f'成功新增兑换码: {code}'
    })


@click.command(name='pick', help='Randomly pick one item from the list')
@click.option('--config', '-c', is_flag=True, expose_value=False, callback=show_config, help='Show configuration')
@click.option('--add', '-a', multiple=True, help='Add item to list (can be used multiple times)')
@click.option('--remove', '-r', multiple=True, help='Remove item from list (can be used multiple times)')
@click.option('--clear', is_flag=True, help='Clear the list')
@click.option('--list', '-l', 'show_list', is_flag=True, help='Show current list')
@click.option('--web', '-w', is_flag=True, help='Start web picker server')
@click.option('--port', '-p', default=80, show_default=True, type=int, help='Port for web mode')
@click.option('--no-browser', is_flag=True, help='Do not auto-open browser in web mode')
@click.option('--files','-f', type=click.Path(exists=True, dir_okay=True, file_okay=True, readable=True, resolve_path=True), help='Start web file picker with given file')
@click.option('--gen-codes','-gc', type=int, default=5, show_default=True, help='Generate redeem codes for web file picker (only with --files)')
@click.option('--show-codes','-sc', is_flag=True, help='Show the redeem codes in console (only with --files)')
@click.option('--password', '-pw', is_flag=True, default=False, help='Prompt to set admin password (default: 123456 if not set)')
@click.argument('items', nargs=-1)
@click.pass_context
def pick(ctx, add, remove, clear, show_list, web, port, no_browser, files, gen_codes, show_codes, password, items):
    config = load_config()
    
    # 显示配置
    if show_list:
        items_list = config.get('items', [])
        if items_list:
            click.echo("Current items list:")
            for i, item in enumerate(items_list, 1):
                click.echo(f"  {i}. {item}")
        else:
            click.echo("List is empty. Please use --add to add items")
        return
    
    # 清空列表
    if clear:
        config['items'] = []
        save_config(config)
        click.echo("List cleared")
        return
    
    # 添加元素
    if add:
        items_list = config.get('items', [])
        for item in add:
            if item not in items_list:
                items_list.append(item)
                click.echo(f"Added: {item}")
            else:
                click.echo(f"Item already exists: {item}")
        config['items'] = items_list
        save_config(config)
        return
    
    # 移除元素
    if remove:
        items_list = config.get('items', [])
        for item in remove:
            if item in items_list:
                items_list.remove(item)
                click.echo(f"Removed: {item}")
            else:
                click.echo(f"Item does not exist: {item}")
        config['items'] = items_list
        save_config(config)
        return
    
    # 文件抽奖模式（优先）
    if files:
        codes = None
        if gen_codes and gen_codes > 0:
            codes = list(generate_redeem_codes(gen_codes))
            if show_codes:
                click.echo()
                click.echo("Generated redeem codes (each can be used once):")
                for c in codes:
                    click.echo(f"  {c}")


        if password:
            admin_password = click.prompt('Admin password (press Enter to use default: 123456)', hide_input=True, default='123456', show_default=False)
            admin_password = admin_password if admin_password else '123456'
        else:
            admin_password = '123456'

        # 在启动Web服务器前，先启动延迟任务线程
        delay_thread = threading.Thread(target=delayed_newline_simple, daemon=True)
        delay_thread.start()

        start_web_server(port, no_browser, template='pick/pick_files.html', files_root=files, codes=codes, admin_password=admin_password)
        return

    # Web 抽奖模式
    if web:
        start_web_server(port, no_browser, template='pick/index.html')
        return
    
    # 执行抽奖
    # 如果命令行提供了参数，使用命令行参数；否则使用配置文件中的列表
    if items:
        pick_item(list(items))
    else:
        items_list = config.get('items', [])
        if not items_list:
            click.echo("Error: No items available")
            click.echo("Usage:")
            click.echo("  1. Use --add to add items: fcbyk pick --add item1 --add item2")
            click.echo("  2. Or provide items directly: fcbyk pick item1 item2 item3")
            return
        pick_item(items_list)

