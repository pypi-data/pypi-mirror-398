"""
NexAgent MCP 客户端 - 支持 SSE 和 Streamable HTTP 格式的 MCP 服务器
"""
import json
import requests
from typing import Dict, List, Optional, Any
from threading import Lock, Thread
import time
import traceback
from ._version import __version__


class MCPClient:
    """MCP 客户端，连接远程 MCP 服务器"""
    
    # 服务器类型
    TYPE_SSE = "sse"
    TYPE_STREAMABLE_HTTP = "streamable_http"
    
    def __init__(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict[str, str] = None):
        self.server_id = server_id
        self.name = name
        self.url = url.rstrip('/')
        self.server_type = server_type
        self.custom_headers = headers or {}
        self.tools: List[Dict] = []
        self.connected = False
        self._lock = Lock()
        self._message_endpoint = None
        self._last_error = None
        self._session_id = None
    
    def _get_headers(self, accept: str = "application/json") -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "Accept": accept
        }
        headers.update(self.custom_headers)
        return headers
    
    def connect(self) -> bool:
        """连接到 MCP 服务器并获取工具列表"""
        self._last_error = None
        try:
            if self.server_type == self.TYPE_STREAMABLE_HTTP:
                return self._connect_streamable_http()
            else:
                return self._connect_sse()
        except requests.exceptions.Timeout:
            self._last_error = "连接超时"
            print(f"[MCP] 连接 {self.name} 超时")
            self.connected = False
            return False
        except requests.exceptions.ConnectionError as e:
            self._last_error = f"无法连接到服务器: {e}"
            print(f"[MCP] 无法连接 {self.name}: {e}")
            self.connected = False
            return False
        except Exception as e:
            self._last_error = str(e)
            print(f"[MCP] 连接 {self.name} 失败: {e}")
            traceback.print_exc()
            self.connected = False
            return False
    
    def _connect_streamable_http(self) -> bool:
        """Streamable HTTP 方式连接 (Home Assistant MCP 使用此协议)"""
        try:
            # 初始化请求
            print(f"[MCP] 正在连接 {self.name} ({self.url})...")
            
            init_resp = requests.post(
                self.url,
                headers=self._get_headers(),
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "clientInfo": {
                            "name": "NexAgent",
                            "version": __version__
                        }
                    },
                    "id": 1
                },
                timeout=15
            )
            
            print(f"[MCP] 初始化响应: {init_resp.status_code}")
            
            if init_resp.status_code == 401:
                self._last_error = "认证失败，请检查 Authorization 请求头"
                print(f"[MCP] {self._last_error}")
                self.connected = False
                return False
            
            if init_resp.status_code == 404:
                self._last_error = "MCP 端点不存在，请检查 URL"
                print(f"[MCP] {self._last_error}")
                self.connected = False
                return False
            
            if init_resp.status_code not in [200, 202]:
                self._last_error = f"初始化失败: HTTP {init_resp.status_code}"
                try:
                    error_data = init_resp.json()
                    self._last_error += f" - {error_data}"
                except:
                    self._last_error += f" - {init_resp.text[:200]}"
                print(f"[MCP] {self._last_error}")
                self.connected = False
                return False
            
            # 解析初始化响应
            try:
                init_data = init_resp.json()
                print(f"[MCP] 初始化数据: {json.dumps(init_data, ensure_ascii=False)[:500]}")
                
                # 检查是否有 session ID (某些实现需要)
                if "result" in init_data and "sessionId" in init_data.get("result", {}):
                    self._session_id = init_data["result"]["sessionId"]
            except:
                pass
            
            # 发送 initialized 通知
            try:
                notify_headers = self._get_headers()
                requests.post(
                    self.url,
                    headers=notify_headers,
                    json={"jsonrpc": "2.0", "method": "notifications/initialized"},
                    timeout=5
                )
            except Exception as e:
                print(f"[MCP] 发送 initialized 通知失败 (可忽略): {e}")
            
            # 获取工具列表
            print(f"[MCP] 正在获取工具列表...")
            tools_resp = requests.post(
                self.url,
                headers=self._get_headers(),
                json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                timeout=15
            )
            
            print(f"[MCP] 工具列表响应: {tools_resp.status_code}")
            
            if tools_resp.status_code == 200:
                data = tools_resp.json()
                print(f"[MCP] 工具数据: {json.dumps(data, ensure_ascii=False)[:500]}")
                
                if "result" in data:
                    self.tools = data["result"].get("tools", [])
                elif "tools" in data:
                    self.tools = data.get("tools", [])
                else:
                    self.tools = []
                
                self.connected = True
                self._message_endpoint = self.url
                print(f"[MCP] 连接成功! 获取到 {len(self.tools)} 个工具")
                return True
            else:
                self._last_error = f"获取工具失败: HTTP {tools_resp.status_code}"
                print(f"[MCP] {self._last_error}")
                
        except Exception as e:
            self._last_error = str(e)
            print(f"[MCP] Streamable HTTP 连接失败: {e}")
            traceback.print_exc()
        
        self.connected = False
        return False
    
    def _connect_sse(self) -> bool:
        """SSE 方式连接"""
        # 尝试多种方式
        
        # 方式1: 尝试简单 HTTP API
        try:
            resp = requests.post(
                f"{self.url}/tools/list",
                headers=self._get_headers(),
                json={},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self.tools = data.get("tools", [])
                self.connected = True
                self._message_endpoint = self.url
                print(f"[MCP] SSE 简单 API 连接成功! 获取到 {len(self.tools)} 个工具")
                return True
        except Exception as e:
            print(f"[MCP] SSE 简单 API 失败: {e}")
        
        # 方式2: 尝试 JSON-RPC
        try:
            init_resp = requests.post(
                self.url,
                headers=self._get_headers(),
                json={
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "NexAgent", "version": __version__}
                    },
                    "id": 1
                },
                timeout=10
            )
            
            if init_resp.status_code in [200, 202]:
                # 获取工具列表
                tools_resp = requests.post(
                    self.url,
                    headers=self._get_headers(),
                    json={"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 2},
                    timeout=10
                )
                if tools_resp.status_code == 200:
                    data = tools_resp.json()
                    if "result" in data:
                        self.tools = data["result"].get("tools", [])
                    else:
                        self.tools = data.get("tools", [])
                    self.connected = True
                    self._message_endpoint = self.url
                    print(f"[MCP] SSE JSON-RPC 连接成功! 获取到 {len(self.tools)} 个工具")
                    return True
        except Exception as e:
            print(f"[MCP] SSE JSON-RPC 失败: {e}")
        
        self._last_error = "无法连接到 MCP 服务器"
        self.connected = False
        return False
    
    def get_tools_for_openai(self) -> List[Dict]:
        """获取 OpenAI 格式的工具定义"""
        result = []
        for tool in self.tools:
            result.append({
                "type": "function",
                "function": {
                    "name": f"mcp_{self.server_id}_{tool['name']}",
                    "description": f"[MCP:{self.name}] {tool.get('description', '')}",
                    "parameters": tool.get("inputSchema", {"type": "object", "properties": {}})
                }
            })
        return result
    
    def call_tool(self, tool_name: str, arguments: Dict) -> str:
        """调用 MCP 工具"""
        try:
            endpoint = self._message_endpoint or self.url
            
            resp = requests.post(
                endpoint,
                headers=self._get_headers(),
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": arguments},
                    "id": int(time.time() * 1000)
                },
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    return self._parse_tool_response(data["result"])
                elif "error" in data:
                    return f"MCP错误: {data['error'].get('message', '未知错误')}"
                return self._parse_tool_response(data)
            
            return f"MCP调用失败: HTTP {resp.status_code}"
            
        except Exception as e:
            return f"MCP调用失败: {e}"
    
    def _parse_tool_response(self, data: Dict) -> str:
        """解析工具返回内容"""
        content = data.get("content", [])
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        texts.append(item.get("text", ""))
                    else:
                        texts.append(json.dumps(item, ensure_ascii=False))
                else:
                    texts.append(str(item))
            return "\n".join(texts) if texts else "(无返回内容)"
        return str(content)


class MCPManager:
    """MCP 服务器管理器"""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self._lock = Lock()
    
    def add_server(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict[str, str] = None) -> bool:
        """添加并连接 MCP 服务器（异步，不阻塞）"""
        client = MCPClient(server_id, name, url, server_type, headers)
        with self._lock:
            self.clients[server_id] = client
        
        # 在后台线程中连接，完全不阻塞
        def connect_async():
            try:
                client.connect()
            except Exception as e:
                print(f"[MCP] 后台连接失败: {e}")
        
        thread = Thread(target=connect_async, daemon=True, name=f"MCP-Connect-{server_id}")
        thread.start()
        
        # 不等待，立即返回
        return False  # 返回 False 表示还在连接中
    
    def add_server_sync(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict[str, str] = None) -> bool:
        """添加并连接 MCP 服务器（同步）"""
        client = MCPClient(server_id, name, url, server_type, headers)
        with self._lock:
            self.clients[server_id] = client
        
        try:
            return client.connect()
        except Exception as e:
            print(f"[MCP] 连接失败: {e}")
            return False
    
    def remove_server(self, server_id: str) -> bool:
        """移除 MCP 服务器"""
        with self._lock:
            if server_id in self.clients:
                del self.clients[server_id]
                return True
            return False
    
    def reconnect_server(self, server_id: str) -> bool:
        """重新连接 MCP 服务器"""
        with self._lock:
            if server_id not in self.clients:
                return False
            client = self.clients[server_id]
        
        try:
            return client.connect()
        except Exception as e:
            print(f"[MCP] 重连失败: {e}")
            return False
    
    def update_server(self, server_id: str, name: str = None, url: str = None, server_type: str = None, headers: Dict[str, str] = None) -> bool:
        """更新服务器配置"""
        with self._lock:
            if server_id not in self.clients:
                return False
            client = self.clients[server_id]
            if name:
                client.name = name
            if url:
                client.url = url.rstrip('/')
            if server_type:
                client.server_type = server_type
            if headers is not None:
                client.custom_headers = headers
            return True
    
    def get_all_tools(self) -> List[Dict]:
        """获取所有已连接服务器的工具（OpenAI 格式）"""
        tools = []
        with self._lock:
            for client in self.clients.values():
                if client.connected:
                    tools.extend(client.get_tools_for_openai())
        return tools
    
    def call_tool(self, full_tool_name: str, arguments: Dict) -> str:
        """调用 MCP 工具"""
        if not full_tool_name.startswith("mcp_"):
            return f"无效的MCP工具名: {full_tool_name}"
        
        parts = full_tool_name[4:].split("_", 1)
        if len(parts) != 2:
            return f"无效的MCP工具名格式: {full_tool_name}"
        
        server_id, tool_name = parts
        
        with self._lock:
            if server_id not in self.clients:
                return f"MCP服务器未连接: {server_id}"
            client = self.clients[server_id]
        
        return client.call_tool(tool_name, arguments)
    
    def get_server_status(self) -> List[Dict]:
        """获取所有服务器状态"""
        result = []
        with self._lock:
            for server_id, client in self.clients.items():
                result.append({
                    "id": server_id,
                    "name": client.name,
                    "url": client.url,
                    "server_type": client.server_type,
                    "connected": client.connected,
                    "tool_count": len(client.tools),
                    "has_headers": bool(client.custom_headers),
                    "last_error": client._last_error
                })
        return result
    
    def is_mcp_tool(self, tool_name: str) -> bool:
        """判断是否是 MCP 工具"""
        return tool_name.startswith("mcp_")
