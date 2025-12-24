import click
import os
import webbrowser
import pyperclip
import socket
from flask import Flask, send_from_directory, abort, render_template, request, jsonify
import re

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'web'))
shared_directory = None
display_name = "共享文件夹"  # 默认显示名称
upload_password = None  # 上传密码

def init_app(directory=None, name=None, password=None):
    global shared_directory, display_name, upload_password
    shared_directory = directory
    if name:
        display_name = name
    if password:
        upload_password = password

def safe_filename(filename):
    return re.sub(r'[^\w\s\u4e00-\u9fff\-\.]', '', filename)

def get_path_parts(current_path):
    parts = []
    if current_path:
        path_parts = current_path.split('/')
        current = ''
        for part in path_parts:
            if part:  # 跳过空的部分
                current = os.path.join(current, part)
                parts.append({
                    'name': part,
                    'path': current
                })
    return parts

@app.route('/')
def index():
    if not shared_directory:
        return "未指定共享目录，请使用 -d 参数指定目录"
    return serve_directory('')

@app.route('/<path:filename>')
def serve_file(filename):
    if not shared_directory:
        abort(404, description="未指定共享目录")
    
    file_path = os.path.join(shared_directory, filename)
    if not os.path.exists(file_path):
        abort(404, description="文件不存在")
    
    if os.path.isdir(file_path):
        return serve_directory(filename)
    
    return send_from_directory(shared_directory, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not shared_directory:
        return jsonify({'error': '未指定共享目录'}), 400
    
    if upload_password:
        if 'password' not in request.form:
            return jsonify({'error': '需要上传密码'}), 401
        if request.form['password'] != upload_password:
            return jsonify({'error': '密码错误'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file:
        filename = safe_filename(file.filename)
        if not filename:
            filename = '未命名文件'
        
        # 检查文件是否已存在
        target_path = os.path.join(shared_directory, filename)
        if os.path.exists(target_path):
            # 生成新文件名
            name, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(target_path):
                new_filename = "{}_{}{}".format(name, counter, ext)
                target_path = os.path.join(shared_directory, new_filename)
                counter += 1
            filename = new_filename
        
        file.save(os.path.join(shared_directory, filename))
        return jsonify({
            'message': '文件上传成功',
            'filename': filename,
            'renamed': counter > 1 if 'counter' in locals() else False
        })
    
    return jsonify({'error': '上传失败'}), 500

def serve_directory(relative_path):
    current_path = os.path.join(shared_directory, relative_path)
    items = []
    
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        item_path = os.path.join(relative_path, name)
        items.append({
            'name': name,
            'path': item_path,
            'is_dir': os.path.isdir(full_path)
        })
    
    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    share_name = os.path.basename(shared_directory)  # 使用实际的文件夹名称作为路径显示
    
    return render_template('lansend.html',
                         current_path=relative_path or '根目录',
                         path_parts=get_path_parts(relative_path),
                         items=items,
                         share_name=share_name,
                         display_name=display_name,
                         require_password=bool(upload_password))  # 传递显示名称到模板

def _lansend_impl(port, directory, name, password, no_browser):
    """lansend 命令的实际实现"""
    global shared_directory, display_name, upload_password
    
    if not os.path.exists(directory):
        click.echo("Error: Directory {} does not exist".format(directory))
        return
    
    if not os.path.isdir(directory):
        click.echo("Error: {} is not a directory".format(directory))
        return
    
    shared_directory = os.path.abspath(directory)
    if name:
        display_name = name
    if password:
        upload_password = password
    
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    click.echo(f"\n * File Sharing Server")
    click.echo(f" * Directory: {shared_directory}")
    click.echo(f" * Display Name: {display_name}")
    if upload_password:
        click.echo(f" * Upload Password: Enabled")
    click.echo(f" * Local URL: http://localhost:{port}")
    click.echo(f" * Local URL: http://127.0.0.1:{port}")
    click.echo(f" * Network URL: http://{local_ip}:{port}")
    
    try:
        pyperclip.copy("http://{}:{}".format(local_ip, port))
        click.echo(" * URL has been copied to clipboard")
    except:
        click.echo(" * Warning: Could not copy URL to clipboard")
    
    if not no_browser:
        webbrowser.open("http://{}:{}".format(local_ip, port))
    
    app.run(host='0.0.0.0', port=port)

@click.command(help='Start a local web server for sharing files over LAN')
@click.option(
    "-p", "--port",
    default=80,
    help="Web server port (default: 80)"
)
@click.option(
    "-d", "--directory",
    default='.',
    help="Directory to share (default: current directory)"
)
@click.option(
    "-n", "--name",
    help="Display name for the page title (default: '共享文件夹')"
)
@click.option(
    "-pw","--password",
    help="Password for file upload (optional)"
)
@click.option(
    "-nb","--no-browser",
    is_flag=True,
    help="Disable automatic browser opening"
)
def lansend(port, directory, name, password, no_browser):
    _lansend_impl(port, directory, name, password, no_browser)

@click.command(name='ls', help='alias for lansend')
@click.option(
    "-p", "--port",
    default=80,
    help="Web server port (default: 80)"
)
@click.option(
    "-d", "--directory",
    default='.',
    help="Directory to share (default: current directory)"
)
@click.option(
    "-n", "--name",
    help="Display name for the page title (default: '共享文件夹')"
)
@click.option(
    "-pw","--password",
    help="Password for file upload (optional)"
)
@click.option(
    "-nb","--no-browser",
    is_flag=True,
    help="Disable automatic browser opening"
)
def ls(port, directory, name, password, no_browser):
    """ls 是 lansend 的别名"""
    _lansend_impl(port, directory, name, password, no_browser) 