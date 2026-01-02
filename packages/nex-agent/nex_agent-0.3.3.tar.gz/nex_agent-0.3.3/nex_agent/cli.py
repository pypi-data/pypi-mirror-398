"""
NexAgent CLI - 命令行工具
"""
import click
import os
import json
from ._version import __version__


@click.group()
@click.version_option(version=__version__, prog_name="nex")
def cli():
    """NexAgent 命令行工具"""
    pass


@cli.command()
@click.option('--port', '-p', default=8000, help='服务端口')
@click.option('--host', '-h', default='0.0.0.0', help='监听地址')
@click.option('--dir', '-d', default='.', help='工作目录')
def serve(port, host, dir):
    """启动 WebServer (API + 前端)"""
    os.chdir(os.path.abspath(dir))
    import uvicorn
    from .webserver import app
    click.echo(f"🚀 启动 NexAgent WebServer")
    click.echo(f"🌐 访问地址: http://{host}:{port}")
    click.echo(f"📁 工作目录: {os.getcwd()}")
    uvicorn.run(app, host=host, port=port)


@cli.command()
@click.option('--dir', '-d', default='.', help='项目目录')
def init(dir):
    """初始化工作目录"""
    dir = os.path.abspath(dir)
    os.makedirs(dir, exist_ok=True)
    tools_dir = os.path.join(dir, 'tools')
    os.makedirs(tools_dir, exist_ok=True)
    
    # 创建提示词
    prompt_file = os.path.join(dir, 'prompt_config.txt')
    if not os.path.exists(prompt_file):
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write("You are a helpful assistant.")
        click.echo(f"✅ 创建 prompt_config.txt")
    else:
        click.echo(f"⏭️  跳过 prompt_config.txt (已存在)")
    
    # 创建示例工具 - JSON + Python 方式
    example_json = os.path.join(tools_dir, 'get_time.json')
    example_py = os.path.join(tools_dir, 'get_time.py')
    if not os.path.exists(example_json):
        with open(example_json, 'w', encoding='utf-8') as f:
            json.dump({
                "name": "get_time",
                "description": "获取当前时间，可指定时区",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "时区，如 Asia/Shanghai, UTC 等，默认本地时间"
                        }
                    },
                    "required": []
                }
            }, f, ensure_ascii=False, indent=2)
        click.echo(f"✅ 创建 tools/get_time.json")
    
    if not os.path.exists(example_py):
        with open(example_py, 'w', encoding='utf-8') as f:
            f.write('''"""
示例工具：获取当前时间
JSON + Python 方式：get_time.json 定义工具，get_time.py 实现执行逻辑
"""
from datetime import datetime

def execute(args):
    """执行函数，接收参数字典，返回字符串结果"""
    tz = args.get("timezone")
    now = datetime.now()
    if tz:
        try:
            from zoneinfo import ZoneInfo
            now = datetime.now(ZoneInfo(tz))
        except:
            return f"时区 {tz} 无效，当前本地时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    return now.strftime('%Y-%m-%d %H:%M:%S')
''')
        click.echo(f"✅ 创建 tools/get_time.py")
    
    # 创建纯 Python 方式的示例工具
    calc_py = os.path.join(tools_dir, 'calculator.py')
    if not os.path.exists(calc_py):
        with open(calc_py, 'w', encoding='utf-8') as f:
            f.write('''"""
示例工具：简单计算器
纯 Python 方式：在一个文件中定义 TOOL_DEF 和 execute 函数
"""

# 工具定义
TOOL_DEF = {
    "name": "calculator",
    "description": "执行简单的数学计算",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，如 2+3*4"
            }
        },
        "required": ["expression"]
    }
}

def execute(args):
    """执行函数"""
    expr = args.get("expression", "")
    try:
        # 安全计算：只允许数字和基本运算符
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expr):
            return "表达式包含非法字符"
        result = eval(expr)
        return f"{expr} = {result}"
    except Exception as e:
        return f"计算错误: {e}"
''')
        click.echo(f"✅ 创建 tools/calculator.py")
    
    click.echo(f"\n🎉 初始化完成！目录: {dir}")
    click.echo("\n📝 配置说明:")
    click.echo("   模型配置已改为通过 Web 界面管理，存储在 nex_data.db 中")
    click.echo("   启动后请在设置中添加服务商和模型")
    click.echo("\n📦 自定义工具说明:")
    click.echo("   方式1: JSON + Python (如 get_time.json + get_time.py)")
    click.echo("   方式2: 纯 Python (如 calculator.py，包含 TOOL_DEF 和 execute)")
    click.echo("\n🚀 运行 nex serve 启动服务")


@cli.command()
@click.option('--dir', '-d', default='.', help='工作目录')
def tools(dir):
    """列出所有可用工具"""
    dir = os.path.abspath(dir)
    tools_dir = os.path.join(dir, 'tools')
    
    click.echo("📦 内置工具:")
    click.echo("   • execute_shell - 执行shell命令")
    click.echo("   • http_request - 发送HTTP请求")
    
    if not os.path.exists(tools_dir):
        click.echo("\n⚠️  tools/ 目录不存在，运行 nex init 创建")
        return
    
    click.echo("\n🔧 自定义工具:")
    
    loaded = set()
    # JSON 定义的工具
    for f in os.listdir(tools_dir):
        if f.endswith('.json'):
            name = f[:-5]
            json_path = os.path.join(tools_dir, f)
            py_path = os.path.join(tools_dir, f"{name}.py")
            try:
                with open(json_path, 'r', encoding='utf-8') as file:
                    tool_def = json.load(file)
                tool_name = tool_def.get("name", name)
                desc = tool_def.get("description", "无描述")
                has_py = "✓" if os.path.exists(py_path) else "✗"
                click.echo(f"   • {tool_name} [{has_py}] - {desc}")
                loaded.add(name)
            except Exception as e:
                click.echo(f"   • {name} [错误] - {e}")
    
    # 纯 Python 工具
    for f in os.listdir(tools_dir):
        if f.endswith('.py') and f[:-3] not in loaded:
            py_path = os.path.join(tools_dir, f)
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(f[:-3], py_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'TOOL_DEF') and hasattr(module, 'execute'):
                    tool_def = module.TOOL_DEF
                    click.echo(f"   • {tool_def['name']} [✓] - {tool_def.get('description', '无描述')}")
                else:
                    click.echo(f"   • {f[:-3]} [?] - 缺少 TOOL_DEF 或 execute")
            except Exception as e:
                click.echo(f"   • {f[:-3]} [错误] - {e}")
    
    click.echo("\n[✓]=有执行脚本  [✗]=仅定义无执行  [?]=格式不完整")


def main():
    cli()


if __name__ == '__main__':
    main()
