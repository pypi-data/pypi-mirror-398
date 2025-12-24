import click
import random
import time
import os
import json

config_file = os.path.join(os.path.expanduser('~'), '.fcbyk', 'pick.json')

default_config = {
    'items': []
}

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
    show_animation_frame(random.randint(3, 20), 0.7)     # 慢速阶段
    
    click.echo("\nPick finished!")

@click.command(name='pick', help='Randomly pick one item from the list')
@click.option('--config', '-c', is_flag=True, expose_value=False, callback=show_config, help='Show configuration')
@click.option('--add', '-a', multiple=True, help='Add item to list (can be used multiple times)')
@click.option('--remove', '-r', multiple=True, help='Remove item from list (can be used multiple times)')
@click.option('--clear', is_flag=True, help='Clear the list')
@click.option('--list', '-l', 'show_list', is_flag=True, help='Show current list')
@click.argument('items', nargs=-1)
@click.pass_context
def pick(ctx, add, remove, clear, show_list, items):
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

