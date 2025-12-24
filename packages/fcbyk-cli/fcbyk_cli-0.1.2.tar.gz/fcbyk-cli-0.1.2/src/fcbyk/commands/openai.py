import click
import os
import json
import requests
import colorama

config_file = os.path.join(os.path.expanduser('~'), '.fcbyk', 'openai.json')

default_config = {
    'model': 'deepseek-chat',
    'base_url': 'https://api.deepseek.com',
    'api_key': None,
    'stream': False,
}

def load_config():
    if not os.path.exists(config_file):
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config.copy()
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception:
        config = default_config.copy()
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    updated = False
    for k, v in default_config.items():
        if k not in config:
            config[k] = v
            updated = True
    if updated:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    return config

def show_config(ctx, param, value):
    if not value:
        return
    config = load_config()
    click.echo(f'config file: {config_file}')
    click.echo(f'model: {config.get("model")}')
    click.echo(f'api_key: {config.get("api_key")}')
    click.echo(f'base_url: {config.get("base_url")}')
    click.echo(f'stream: {config.get("stream")}')
    ctx.exit()

def chat_api(messages, model, api_key, base_url, stream=False, timeout=30):
    url = base_url.rstrip('/') + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, stream=stream, timeout=timeout)
        if not stream:
            try:
                resp.raise_for_status()
                data = resp.json()
                if 'error' in data:
                    print(f"[API错误] {data['error'].get('message', str(data['error']))}")
                    return None
                return data
            except requests.HTTPError as e:
                try:
                    err = resp.json()
                    print(f"[HTTP错误] {err.get('error', {}).get('message', str(err))}")
                except Exception:
                    print(f"[HTTP错误] {e}")
                return None
            except Exception as e:
                print(f"[响应解析错误] {e}")
                return None
        else:
            # 流式返回，逐行yield内容
            for line in resp.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if 'error' in chunk:
                                print(f"[API错误] {chunk['error'].get('message', str(chunk['error']))}")
                                return
                            yield chunk
                        except Exception as e:
                            print(f"[流式解析错误] {e}")
                            continue
    except requests.Timeout:
        print('[请求超时] 请检查网络或稍后重试。')
        return None
    except requests.ConnectionError:
        print('[网络错误] 无法连接到API服务器。')
        return None
    except Exception as e:
        print(f'[请求异常] {e}')
        return None

def get_reply_from_response(response, stream=False):
    if not stream:
        try:
            return response['choices'][0]['message']['content']
        except Exception as e:
            if isinstance(response, dict) and 'error' in response:
                print(f"[API错误] {response['error'].get('message', str(response['error']))}")
            else:
                print(f'[响应内容异常] {e}')
            return ''
    else:
        reply = ''
        try:
            print('\033[94mAI：\033[0m', end='', flush=True)
            for chunk in response:
                delta = chunk['choices'][0]['delta'].get('content', '')
                print(delta, end='', flush=True)
                reply += delta
            print()
        except Exception as e:
            print(f'[流式响应异常] {e}')
        return reply

@click.command(name='openai', help='use openai api to chat in terminal')
@click.option('--config', '-c', is_flag=True, expose_value=False, callback=show_config, help='show config')
@click.option('--model', '-m', help='set model')
@click.option('--api-key', '-k', help='set api key')
@click.option('--base-url', '-u', help='set base url')
@click.option('--stream', '-s', help='set stream, 0 for false, 1 for true')
@click.pass_context
def openai_chat(ctx, model, api_key, base_url, stream):
    colorama.init()
    if not model and not api_key and not base_url and not stream:
        config = load_config()
        model = config['model']
        api_key = config['api_key']
        base_url = config['base_url']
        stream_flag = config['stream']
        if not api_key or api_key in [None, '', 'none']:
            click.echo('未配置 api_key，请先通过 --api-key 或配置文件设置。')
            return
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant. Respond in plain text suitable for a console environment. Avoid using Markdown, code blocks, or any rich formatting. Use simple line breaks and spaces for alignment."
            }
        ]
        while True:
            try:
                user_input = input('You: ')
                if user_input.strip().lower() == 'exit':
                    break
                if user_input.strip() == '':
                    continue
                messages.append({"role": "user", "content": user_input})
                response = chat_api(messages, model, api_key, base_url, stream_flag)
                if response is None:
                    print('请求失败，请检查网络或API Key配置。')
                    continue
                reply = get_reply_from_response(response, stream_flag)
                messages.append({"role": "assistant", "content": reply})
            except KeyboardInterrupt:
                print('\n已退出对话。')
                break
            except Exception as e:
                print(f'[主循环异常] {e}')
                continue
        return
    else:
        config = load_config()
        if model:
            config['model'] = model
        if api_key:
            config['api_key'] = api_key
        if base_url:
            config['base_url'] = base_url
        if stream:
            config['stream'] = True if stream == '1' else False
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        click.echo('config saved')
        ctx.exit()

if __name__ == '__main__':
    colorama.init()