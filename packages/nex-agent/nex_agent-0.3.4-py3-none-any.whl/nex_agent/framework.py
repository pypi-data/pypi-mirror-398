"""
NexAgent 核心模块
"""
from openai import OpenAI
import os
import json
from datetime import datetime
import subprocess
import requests
from typing import Optional, Callable, Generator, Dict, List
from threading import Thread
from .database import Database
from .mcp_client import MCPManager


class NexFramework:
    """AI 对话框架，支持多模型切换、工具调用、流式输出、多会话"""
    
    def __init__(
        self,
        work_dir: str,
        default_model: str = None,
    ):
        """
        初始化 NexFramework
        
        Args:
            work_dir: 工作目录，包含配置文件
            default_model: 默认使用的模型 key
        """
        self.work_dir = os.path.abspath(work_dir)
        
        # 文件路径
        self.prompt_file = os.path.join(self.work_dir, 'prompt_config.txt')
        self.db_file = os.path.join(self.work_dir, 'nex_data.db')
        self.tools_dir = os.path.join(self.work_dir, 'tools')
        
        # 初始化数据库
        self.db = Database(self.db_file)
        
        # 当前会话ID
        self._current_session_id: Optional[int] = None
        
        # 深度思考模式
        self._deep_thinking_enabled: bool = False
        
        # 初始化模型
        self.current_model_key = None
        self._init_model(default_model)
        self._init_tools()
        self._custom_tools: Dict[str, Callable] = {}
        self._load_custom_tools()
        
        # 初始化 MCP 管理器（后台异步，不阻塞启动）
        self.mcp_manager = MCPManager()
        self._init_mcp_servers_async()
    
    def _init_model(self, default_model: str = None):
        """初始化模型配置"""
        # 恢复上次使用的模型
        last_model = self.db.get_setting('last_model')
        models = self.db.get_models_list()
        
        if not models:
            # 没有配置任何模型
            self.current_model_key = None
            self.client = None
            self.model = None
            return
        
        # 确定使用哪个模型
        model_keys = [m['id'] for m in models]
        if default_model and default_model in model_keys:
            self.current_model_key = default_model
        elif last_model and last_model in model_keys:
            self.current_model_key = last_model
        else:
            self.current_model_key = model_keys[0]
        
        self._init_client()
    
    def _init_client(self):
        """初始化模型客户端"""
        if not self.current_model_key:
            self.client = None
            self.model = None
            return
        
        config = self.db.get_model(self.current_model_key)
        if not config:
            self.client = None
            self.model = None
            return
        
        self.client = OpenAI(api_key=config['api_key'], base_url=config['base_url'])
        self.model = config['model_id']
        self._current_model_config = config

    def _init_tools(self):
        """初始化内置工具"""
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "execute_shell",
                    "description": "执行shell命令并返回结果",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string", "description": "要执行的shell命令"}},
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "http_request",
                    "description": "发送HTTP请求获取网页内容或API数据",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "请求的URL"},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                            "headers": {"type": "object", "description": "请求头"},
                            "body": {"type": "string", "description": "请求体"}
                        },
                        "required": ["url"]
                    }
                }
            }
        ]
    
    def _load_custom_tools(self):
        """从 tools/ 目录加载自定义工具
        
        支持两种方式：
        1. JSON + Python: tool.json 定义 + tool.py 执行脚本
        2. 纯 Python: tool.py 中包含 TOOL_DEF 定义和 execute(args) 函数
        """
        if not os.path.exists(self.tools_dir):
            return
        
        loaded_tools = set()
        
        # 方式1: 加载 JSON 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.json'):
                tool_name = filename[:-5]  # 去掉 .json
                json_path = os.path.join(self.tools_dir, filename)
                py_path = os.path.join(self.tools_dir, f"{tool_name}.py")
                
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        tool_def = json.load(f)
                    
                    self.tools.append({"type": "function", "function": tool_def})
                    actual_name = tool_def.get("name", tool_name)
                    
                    # 如果有对应的 .py 文件，加载执行函数
                    if os.path.exists(py_path):
                        handler = self._load_py_handler(py_path, actual_name)
                        if handler:
                            self._custom_tools[actual_name] = handler
                    
                    loaded_tools.add(tool_name)
                except Exception as e:
                    print(f"[警告] 加载工具 {filename} 失败: {e}")
        
        # 方式2: 加载纯 Python 定义的工具
        for filename in os.listdir(self.tools_dir):
            if filename.endswith('.py'):
                tool_name = filename[:-3]
                if tool_name in loaded_tools:
                    continue  # 已经作为 JSON 工具的执行脚本加载过了
                
                py_path = os.path.join(self.tools_dir, filename)
                try:
                    tool_def, handler = self._load_py_tool(py_path)
                    if tool_def and handler:
                        self.tools.append({"type": "function", "function": tool_def})
                        self._custom_tools[tool_def["name"]] = handler
                except Exception as e:
                    print(f"[警告] 加载工具 {filename} 失败: {e}")
    
    def _load_py_handler(self, py_path: str, tool_name: str) -> Optional[Callable]:
        """从 Python 文件加载执行函数"""
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location(tool_name, py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 execute 函数
            if hasattr(module, 'execute'):
                return module.execute
            # 或者查找与工具同名的函数
            if hasattr(module, tool_name):
                return getattr(module, tool_name)
        except Exception as e:
            print(f"[警告] 加载 {py_path} 失败: {e}")
        return None
    
    def _load_py_tool(self, py_path: str) -> tuple:
        """从纯 Python 文件加载工具定义和执行函数"""
        import importlib.util
        tool_name = os.path.basename(py_path)[:-3]
        try:
            spec = importlib.util.spec_from_file_location(tool_name, py_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 需要有 TOOL_DEF 和 execute
            if hasattr(module, 'TOOL_DEF') and hasattr(module, 'execute'):
                return module.TOOL_DEF, module.execute
        except Exception as e:
            print(f"[警告] 加载 {py_path} 失败: {e}")
        return None, None

    # ========== 工具注册 ==========
    def register_tool(self, name: str, description: str, parameters: Dict, handler: Callable) -> None:
        """注册自定义工具"""
        self.tools.append({
            "type": "function",
            "function": {"name": name, "description": description, "parameters": parameters}
        })
        self._custom_tools[name] = handler
    
    # ========== MCP 服务器管理 ==========
    def _init_mcp_servers_async(self):
        """在后台线程中初始化 MCP 服务器连接，不阻塞主线程"""
        def init_servers():
            servers = self.db.get_mcp_servers()
            for server in servers:
                if server.get('enabled'):
                    try:
                        # 使用同步方法，但在后台线程中执行
                        self.mcp_manager.add_server_sync(
                            server['id'], 
                            server['name'], 
                            server['url'],
                            server.get('server_type', 'sse'),
                            server.get('headers')
                        )
                    except Exception as e:
                        print(f"[MCP] 初始化服务器 {server['name']} 失败: {e}")
        
        # 启动后台线程
        thread = Thread(target=init_servers, daemon=True, name="MCP-Init")
        thread.start()
        print("[MCP] 后台初始化 MCP 服务器...")
    
    def get_mcp_servers(self) -> List[Dict]:
        """获取所有 MCP 服务器"""
        servers = self.db.get_mcp_servers()
        status = {s['id']: s for s in self.mcp_manager.get_server_status()}
        for server in servers:
            if server['id'] in status:
                server['connected'] = status[server['id']]['connected']
                server['tool_count'] = status[server['id']]['tool_count']
                server['has_headers'] = status[server['id']].get('has_headers', False)
                server['last_error'] = status[server['id']].get('last_error')
            else:
                server['connected'] = False
                server['tool_count'] = 0
                server['has_headers'] = bool(server.get('headers'))
                server['last_error'] = None
        return servers
    
    def add_mcp_server(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict = None) -> Dict:
        """添加 MCP 服务器（后台连接，快速返回）"""
        if not self.db.create_mcp_server(server_id, name, url, server_type, headers):
            return {"success": False, "error": "服务器ID已存在"}
        
        # 使用异步方式添加，快速返回
        connected = self.mcp_manager.add_server(server_id, name, url, server_type, headers)
        return {"success": True, "connected": connected, "message": "已添加，正在后台连接..." if not connected else None}
    
    def update_mcp_server(self, server_id: str, name: str = None, url: str = None, server_type: str = None, headers: Dict = None, enabled: bool = None) -> bool:
        """更新 MCP 服务器"""
        result = self.db.update_mcp_server(server_id, name, url, server_type, headers, enabled)
        if result:
            server = self.db.get_mcp_server(server_id)
            if server:
                if server['enabled']:
                    # 重新连接（后台异步）
                    self.mcp_manager.remove_server(server_id)
                    self.mcp_manager.add_server(
                        server_id, 
                        server['name'], 
                        server['url'],
                        server.get('server_type', 'sse'),
                        server.get('headers')
                    )
                else:
                    # 断开连接
                    self.mcp_manager.remove_server(server_id)
        return result
    
    def delete_mcp_server(self, server_id: str) -> bool:
        """删除 MCP 服务器"""
        self.mcp_manager.remove_server(server_id)
        return self.db.delete_mcp_server(server_id)
    
    def reconnect_mcp_server(self, server_id: str) -> bool:
        """重新连接 MCP 服务器（同步方式，用于手动重连）"""
        server = self.db.get_mcp_server(server_id)
        if not server or not server['enabled']:
            return False
        self.mcp_manager.remove_server(server_id)
        # 手动重连使用同步方式，让用户能看到结果
        return self.mcp_manager.add_server_sync(
            server_id, 
            server['name'], 
            server['url'],
            server.get('server_type', 'sse'),
            server.get('headers')
        )
    
    def get_mcp_tools(self) -> List[Dict]:
        """获取所有 MCP 工具"""
        return self.mcp_manager.get_all_tools()
    
    def get_all_tools(self) -> List[Dict]:
        """获取所有工具（内置 + 自定义 + MCP）"""
        return self.tools + self.mcp_manager.get_all_tools()
    
    # ========== 模型管理 ==========
    def switch_model(self, model_key: str) -> bool:
        model = self.db.get_model(model_key)
        if model:
            self.current_model_key = model_key
            self._init_client()
            self.db.set_setting('last_model', model_key)
            return True
        return False
    
    def get_models(self) -> List[Dict]:
        models = self.db.get_models_list()
        return [{
            "key": m['id'],
            "name": m['display_name'],
            "model": m['model_id'],
            "provider_id": m['provider_id'],
            "provider_name": m['provider_name'],
            "has_thinking": bool(m.get('thinking_model_id'))
        } for m in models]
    
    def get_current_model(self) -> Optional[Dict]:
        if not self.current_model_key:
            return None
        config = self.db.get_model(self.current_model_key)
        if not config:
            return None
        return {
            "key": self.current_model_key,
            "name": config['display_name'],
            "model": config['model_id'],
            "has_thinking": bool(config.get('thinking_model_id'))
        }
    
    def set_deep_thinking(self, enabled: bool) -> bool:
        """设置深度思考模式"""
        if not self.current_model_key:
            return False
        config = self.db.get_model(self.current_model_key)
        if not config or not config.get('thinking_model_id'):
            return False
        self._deep_thinking_enabled = enabled
        return True
    
    def get_deep_thinking(self) -> bool:
        """获取深度思考模式状态"""
        return self._deep_thinking_enabled
    
    def _get_actual_model(self) -> str:
        """获取实际使用的模型ID（考虑深度思考模式）"""
        if not self.current_model_key:
            return None
        config = getattr(self, '_current_model_config', None)
        if not config:
            config = self.db.get_model(self.current_model_key)
        if not config:
            return None
        if self._deep_thinking_enabled and config.get('thinking_model_id'):
            return config['thinking_model_id']
        return config['model_id']
    
    # ========== 服务商管理 ==========
    def get_providers(self) -> List[Dict]:
        return self.db.get_providers()
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        return self.db.get_provider(provider_id)
    
    def add_provider(self, provider_id: str, name: str, api_key: str, base_url: str) -> bool:
        return self.db.create_provider(provider_id, name, api_key, base_url)
    
    def update_provider(self, provider_id: str, name: str = None, api_key: str = None, base_url: str = None) -> bool:
        result = self.db.update_provider(provider_id, name, api_key, base_url)
        # 如果当前模型使用此服务商，重新初始化客户端
        if result and self.current_model_key:
            config = self.db.get_model(self.current_model_key)
            if config and config['provider_id'] == provider_id:
                self._init_client()
        return result
    
    def delete_provider(self, provider_id: str) -> bool:
        # 检查是否有模型使用此服务商
        models = self.db.get_models_by_provider(provider_id)
        if models:
            # 如果当前模型属于此服务商，需要切换
            if self.current_model_key in [m['id'] for m in models]:
                self.current_model_key = None
                self.client = None
                self.model = None
        return self.db.delete_provider(provider_id)
    
    # ========== 模型配置管理 ==========
    def add_model(self, model_key: str, provider_id: str, model_id: str, display_name: str, thinking_model_id: str = None) -> bool:
        result = self.db.create_model(model_key, provider_id, model_id, display_name, thinking_model_id)
        # 如果是第一个模型，自动设为当前模型
        if result and not self.current_model_key:
            self.current_model_key = model_key
            self._init_client()
        return result
    
    def update_model_config(self, model_key: str, new_key: str = None, model_id: str = None, display_name: str = None, thinking_model_id: str = None, clear_thinking: bool = False) -> str:
        """更新模型配置，返回新的 key（如果有变更）或 None（失败）"""
        result = self.db.update_model(model_key, new_key, model_id, display_name, thinking_model_id, clear_thinking)
        if not result:
            return None
        
        # 确定最终的 key
        final_key = new_key if new_key else model_key
        
        # 如果是当前模型，更新 current_model_key 并重新初始化
        if model_key == self.current_model_key:
            self.current_model_key = final_key
            self._init_client()
        
        return final_key
    
    def delete_model_config(self, model_key: str) -> bool:
        if model_key == self.current_model_key:
            # 切换到其他模型
            models = self.db.get_models_list()
            other_models = [m for m in models if m['id'] != model_key]
            if other_models:
                self.current_model_key = other_models[0]['id']
                self._init_client()
            else:
                self.current_model_key = None
                self.client = None
                self.model = None
        return self.db.delete_model(model_key)
    
    def get_model_detail(self, model_key: str) -> Optional[Dict]:
        return self.db.get_model(model_key)
    
    # ========== 会话管理 ==========
    def create_session(self, name: str, user: str) -> int:
        """创建新会话"""
        session_id = self.db.create_session(name, user)
        self._current_session_id = session_id
        return session_id
    
    def get_sessions(self, user: str = None, limit: int = None) -> List[Dict]:
        """获取会话列表"""
        sessions = self.db.get_sessions(user, limit)
        for s in sessions:
            s['message_count'] = self.db.get_message_count(s['id'])
        return sessions
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """获取单个会话"""
        session = self.db.get_session(session_id)
        if session:
            session['message_count'] = self.db.get_message_count(session_id)
        return session
    
    def switch_session(self, session_id: int) -> bool:
        """切换当前会话"""
        session = self.db.get_session(session_id)
        if session:
            self._current_session_id = session_id
            return True
        return False
    
    def get_current_session(self) -> Optional[Dict]:
        """获取当前会话"""
        if self._current_session_id:
            return self.get_session(self._current_session_id)
        return None
    
    def update_session(self, session_id: int, name: str) -> bool:
        """更新会话名称"""
        return self.db.update_session(session_id, name)
    
    def delete_session(self, session_id: int) -> bool:
        """删除会话"""
        if self._current_session_id == session_id:
            self._current_session_id = None
        return self.db.delete_session(session_id)
    
    def get_session_messages(self, session_id: int, limit: int = None) -> List[Dict]:
        """获取会话消息"""
        return self.db.get_messages(session_id, limit)
    
    # ========== 工具执行 ==========
    def execute_shell(self, command: str) -> str:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30, encoding='utf-8', errors='replace')
            return (result.stdout or result.stderr or "(无输出)")[:2000]
        except subprocess.TimeoutExpired:
            return "命令执行超时(30秒)"
        except Exception as e:
            return f"执行失败: {e}"
    
    def _extract_text_from_html(self, html: str) -> str:
        """从 HTML 中提取正文内容"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # 移除无关标签
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                           'iframe', 'noscript', 'svg', 'form', 'button']):
                tag.decompose()
            
            # 尝试找主要内容区域
            main_content = None
            for selector in ['main', 'article', '[role="main"]', '.content', '.post', '.article', '#content']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # 获取 body 内容
                body = soup.body
                text = body.get_text(separator='\n', strip=True) if body else soup.get_text(separator='\n', strip=True)
            
            # 清理多余空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
        except ImportError:
            # 没有 bs4，用简单正则处理
            import re
            # 移除 script 和 style
            text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', html, flags=re.IGNORECASE)
            text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', text, flags=re.IGNORECASE)
            # 移除所有标签
            text = re.sub(r'<[^>]+>', ' ', text)
            # 清理空白
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            return html
    
    def http_request(self, url: str, method: str = "GET", headers: Dict = None, body: str = None) -> str:
        try:
            if headers is None:
                headers = {}
            # 添加常见请求头避免被拒绝
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            
            resp = requests.request(method.upper(), url, headers=headers, data=body, timeout=15)
            content_type = resp.headers.get('Content-Type', '')
            
            # 处理编码
            # 优先从 Content-Type 获取编码
            encoding = resp.encoding
            if encoding is None or encoding.lower() == 'iso-8859-1':
                # requests 默认用 ISO-8859-1，尝试从内容检测
                if 'charset=' in content_type.lower():
                    import re
                    match = re.search(r'charset=([^\s;]+)', content_type, re.IGNORECASE)
                    if match:
                        encoding = match.group(1)
                else:
                    # 尝试从 HTML meta 标签检测
                    content_start = resp.content[:1024].decode('ascii', errors='ignore').lower()
                    if 'charset=utf-8' in content_start or 'charset="utf-8"' in content_start:
                        encoding = 'utf-8'
                    elif 'charset=gbk' in content_start or 'charset=gb2312' in content_start:
                        encoding = 'gbk'
                    else:
                        # 默认尝试 utf-8
                        encoding = 'utf-8'
            
            # 解码内容
            try:
                text = resp.content.decode(encoding, errors='replace')
            except (LookupError, UnicodeDecodeError):
                text = resp.content.decode('utf-8', errors='replace')
            
            # 如果是 HTML，提取正文
            if 'text/html' in content_type:
                text = self._extract_text_from_html(text)
                return f"状态码: {resp.status_code}\n正文内容:\n{text[:5000]}"
            else:
                return f"状态码: {resp.status_code}\n内容:\n{text[:5000]}"
        except requests.Timeout:
            return "请求超时(15秒)"
        except requests.RequestException as e:
            return f"请求失败: {e}"
    
    def handle_tool_call(self, tool_call) -> str:
        if isinstance(tool_call, dict):
            name, args = tool_call["function"]["name"], json.loads(tool_call["function"]["arguments"])
        else:
            name, args = tool_call.function.name, json.loads(tool_call.function.arguments)
        
        if name == "execute_shell":
            return self.execute_shell(args["command"])
        elif name == "http_request":
            return self.http_request(args["url"], args.get("method", "GET"), args.get("headers"), args.get("body"))
        elif self.mcp_manager.is_mcp_tool(name):
            return self.mcp_manager.call_tool(name, args)
        elif name in self._custom_tools:
            try:
                return str(self._custom_tools[name](args))
            except Exception as e:
                return f"工具执行失败: {e}"
        return "未知工具"

    # ========== 历史管理 ==========
    def get_history(self, limit: int = None) -> List[Dict]:
        """获取历史记录（兼容旧API）"""
        return self.db.get_history(limit)
    
    def delete_history(self, history_id: int = None) -> bool:
        """删除历史记录"""
        if history_id is None:
            # 清空所有会话
            self.db.delete_all_sessions()
            self._current_session_id = None
            return True
        return self.db.delete_message(history_id)
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        return self.db.delete_message(message_id)
    
    def get_message(self, message_id: int) -> Optional[Dict]:
        """获取单条消息"""
        return self.db.get_message(message_id)
    
    def update_message(self, message_id: int, content: str) -> bool:
        """更新消息内容"""
        return self.db.update_message(message_id, content)
    
    def delete_messages_after(self, session_id: int, message_id: int) -> int:
        """删除指定消息之后的所有消息"""
        return self.db.delete_messages_after(session_id, message_id)
    
    def get_last_user_message(self, session_id: int) -> Optional[Dict]:
        """获取会话中最后一条用户消息"""
        return self.db.get_last_user_message(session_id)
    
    def clear_session_messages(self, session_id: int) -> int:
        """清空会话消息"""
        return self.db.delete_session_messages(session_id)
    
    def _read_prompt(self) -> str:
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return "You are a helpful assistant."
    
    def set_prompt(self, prompt: str) -> None:
        self._runtime_prompt = prompt
    
    def _get_prompt(self) -> str:
        return getattr(self, '_runtime_prompt', None) or self._read_prompt()

    # ========== 对话功能 ==========
    def _ensure_session(self, user: str) -> int:
        """确保有当前会话"""
        if not self._current_session_id:
            self._current_session_id = self.create_session("新会话", user)
        return self._current_session_id
    
    def _build_messages(self, session_id: int) -> List[Dict]:
        """构建消息列表"""
        messages = [{"role": "system", "content": self._get_prompt()}]
        history = self.db.get_messages(session_id, limit=None)
        for msg in history:
            if msg['role'] == 'user':
                messages.append({"role": "user", "content": f"[{msg['user']}] {msg['content']}"})
            elif msg['role'] == 'assistant':
                messages.append({"role": "assistant", "content": msg['content']})
        return messages
    
    def chat(self, user: str, message: str, session_id: int = None, save_history: bool = True) -> str:
        if not self.client:
            return "错误：未配置模型，请先添加服务商和模型"
        
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        actual_model = self._get_actual_model()
        
        # 确定会话
        if session_id:
            self._current_session_id = session_id
        sid = self._ensure_session(user)
        
        prompt = f"【系统信息】\n当前时间: {now}\n【以下为输入内容】\n===[{user}] {message}"
        
        messages = self._build_messages(sid)
        messages.append({"role": "user", "content": prompt})
        
        # 保存用户消息
        if save_history:
            self.db.add_message(sid, 'user', message, user)
        
        all_tool_calls = []  # 收集所有工具调用
        
        # 获取所有工具（内置 + 自定义 + MCP）
        all_tools = self.get_all_tools()
        
        response = self.client.chat.completions.create(
            model=actual_model, messages=messages, tools=all_tools, tool_choice="auto", max_tokens=1000, temperature=0.7
        )
        assistant_message = response.choices[0].message
        
        while assistant_message.tool_calls:
            messages.append(assistant_message)
            for tc in assistant_message.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                result = self.handle_tool_call(tc)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
                all_tool_calls.append({"name": name, "args": args, "result": result})
            response = self.client.chat.completions.create(
                model=actual_model, messages=messages, tools=all_tools, tool_choice="auto", max_tokens=1000, temperature=0.7
            )
            assistant_message = response.choices[0].message
        
        reply = assistant_message.content
        if save_history:
            extra = {"tool_calls": all_tool_calls} if all_tool_calls else None
            self.db.add_message(sid, 'assistant', reply, extra=extra)
        return reply

    def chat_stream(self, user: str, message: str, session_id: int = None, on_tool_call: Callable = None, save_history: bool = True, save_user_message: bool = True, on_thinking: Callable = None) -> Generator[str, None, None]:
        if not self.client:
            yield "错误：未配置模型，请先添加服务商和模型"
            return
        
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        actual_model = self._get_actual_model()
        is_thinking_model = self._deep_thinking_enabled and getattr(self, '_current_model_config', {}).get('thinking_model_id')
        
        # 确定会话
        if session_id:
            self._current_session_id = session_id
        sid = self._ensure_session(user)
        
        prompt = f"【系统信息】\n当前时间: {now}\n【以下为输入内容】\n===[{user}] {message}"
        
        messages = self._build_messages(sid)
        messages.append({"role": "user", "content": prompt})
        
        # 保存用户消息（重新生成时不保存，因为用户消息已存在）
        if save_history and save_user_message:
            self.db.add_message(sid, 'user', message, user)
        
        # 使用内容流记录，保存工具调用位置
        content_parts = []  # [{"type": "text", "content": "..."}, {"type": "tool", ...}]
        # Token 统计
        total_tokens = {"prompt": 0, "completion": 0, "total": 0}
        
        # 思考过程
        thinking_content = ""
        
        # 获取所有工具（内置 + 自定义 + MCP）
        all_tools = self.get_all_tools()
        
        while True:
            stream = self.client.chat.completions.create(
                model=actual_model, messages=messages, tools=all_tools, tool_choice="auto",
                max_tokens=4000 if is_thinking_model else 1000, temperature=0.7, stream=True,
                stream_options={"include_usage": True}
            )
            
            content_buffer = ""
            tool_calls_buffer = {}
            thinking_started = False
            
            for chunk in stream:
                # 收集 token 使用量（在最后一个 chunk 中）
                if hasattr(chunk, 'usage') and chunk.usage:
                    total_tokens["prompt"] += chunk.usage.prompt_tokens or 0
                    total_tokens["completion"] += chunk.usage.completion_tokens or 0
                    total_tokens["total"] += chunk.usage.total_tokens or 0
                
                if not chunk.choices:
                    continue
                
                delta = chunk.choices[0].delta
                
                # 检查是否有 reasoning_content（思考过程）- 适用于 DeepSeek 等模型
                if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                    if not thinking_started:
                        if on_thinking:
                            on_thinking("thinking_start", {})
                        thinking_started = True
                        yield ""  # yield 空字符串让事件有机会被处理
                    thinking_content += delta.reasoning_content
                    if on_thinking:
                        on_thinking("thinking", delta.reasoning_content)
                    yield ""  # yield 空字符串让事件有机会被处理
                    continue
                
                # 如果之前在思考，现在开始输出内容，标记思考结束
                if thinking_started and delta.content:
                    if on_thinking:
                        on_thinking("thinking_end", {})
                    thinking_started = False
                    yield ""  # yield 空字符串让事件有机会被处理
                
                if delta.content:
                    content_buffer += delta.content
                    yield delta.content
                    
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                        if tc.id:
                            tool_calls_buffer[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_buffer[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_buffer[idx]["arguments"] += tc.function.arguments
            
            # 如果思考还没结束，在这里结束
            if thinking_started and on_thinking:
                on_thinking("thinking_end", {})
                yield ""  # yield 空字符串让事件有机会被处理
            
            if tool_calls_buffer:
                # 保存思考过程
                if thinking_content:
                    content_parts.append({"type": "thinking", "content": thinking_content})
                
                # 保存工具调用前的文本
                if content_buffer:
                    content_parts.append({"type": "text", "content": content_buffer})
                
                tool_calls_list = [{"id": tc["id"], "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                                   for tc in [tool_calls_buffer[i] for i in sorted(tool_calls_buffer.keys())]]
                
                # 构建 assistant 消息，包含 reasoning_content（DeepSeek 思考模式工具调用需要）
                assistant_msg = {"role": "assistant", "content": content_buffer or None, "tool_calls": tool_calls_list}
                if thinking_content:
                    assistant_msg["reasoning_content"] = thinking_content
                messages.append(assistant_msg)
                
                for tc in tool_calls_list:
                    name, args = tc["function"]["name"], json.loads(tc["function"]["arguments"])
                    if on_tool_call:
                        on_tool_call("tool_start", {"name": name, "args": args})
                    yield ""  # yield 空字符串让 tool_start 事件有机会被处理
                    result = self.handle_tool_call(tc)
                    if on_tool_call:
                        on_tool_call("tool_end", {"name": name, "result": result})
                    yield ""  # yield 空字符串让 tool_end 事件有机会被处理
                    messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
                    # 记录工具调用到内容流
                    content_parts.append({
                        "type": "tool",
                        "name": name,
                        "args": args,
                        "result": result
                    })
                continue
            else:
                # 保存思考过程
                if thinking_content:
                    content_parts.append({"type": "thinking", "content": thinking_content})
                # 保存最终文本
                if content_buffer:
                    content_parts.append({"type": "text", "content": content_buffer})
                break
        
        # 返回 tokens 信息
        self._last_tokens = total_tokens
        
        if save_history:
            # 构建完整内容和 extra
            full_content = ""
            for part in content_parts:
                if part["type"] == "text":
                    full_content += part["content"]
            
            extra = {"content_parts": content_parts}
            if total_tokens["total"] > 0:
                extra["tokens"] = total_tokens
            self.db.add_message(sid, 'assistant', full_content, extra=extra)
