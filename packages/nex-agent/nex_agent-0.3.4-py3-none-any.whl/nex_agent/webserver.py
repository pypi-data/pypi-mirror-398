"""
NexAgent WebServer - 集成 API 和前端的 Web 服务器
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import json
import os
from .framework import NexFramework
from ._version import __version__

app = FastAPI(title="NexAgent WebServer", version=__version__)

# 使用当前工作目录
nex = NexFramework(os.getcwd())

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


class ChatRequest(BaseModel):
    user: str = "guest"
    message: str
    session_id: Optional[int] = None
    stream: bool = False
    save_user_message: bool = True  # 重新生成时设为False


class DeleteRequest(BaseModel):
    id: Optional[int] = None


class SwitchModelRequest(BaseModel):
    model_key: str


class CreateSessionRequest(BaseModel):
    name: str = "新会话"
    user: str = "guest"


class UpdateSessionRequest(BaseModel):
    name: str


class DeleteMessageRequest(BaseModel):
    message_id: int


class EditMessageRequest(BaseModel):
    content: str
    regenerate: bool = False


class RegenerateRequest(BaseModel):
    session_id: int


# 服务商相关请求模型
class AddProviderRequest(BaseModel):
    id: str
    name: str
    api_key: str
    base_url: str


class UpdateProviderRequest(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


# 模型相关请求模型
class AddModelRequest(BaseModel):
    provider_id: str
    model_id: str
    display_name: str
    thinking_model_id: Optional[str] = None


class UpdateModelRequest(BaseModel):
    model_id: Optional[str] = None
    display_name: Optional[str] = None
    thinking_model_id: Optional[str] = None
    clear_thinking: bool = False


class DeepThinkingRequest(BaseModel):
    enabled: bool


# MCP 服务器相关请求模型
class AddMCPServerRequest(BaseModel):
    id: str
    name: str
    url: str
    server_type: str = "sse"  # "sse" 或 "streamable_http"
    headers: Optional[dict] = None


class UpdateMCPServerRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    server_type: Optional[str] = None
    headers: Optional[dict] = None
    enabled: Optional[bool] = None


# ========== API 接口 ==========
@app.post("/nex/chat")
async def chat(req: ChatRequest):
    """对话接口"""
    try:
        if req.stream:
            def generate():
                tool_events = []
                thinking_events = []
                def collect_tool(event, data):
                    tool_events.append((event, data))
                def collect_thinking(event, data):
                    thinking_events.append((event, data))
                for chunk in nex.chat_stream(req.user, req.message, session_id=req.session_id, on_tool_call=collect_tool, save_user_message=req.save_user_message, on_thinking=collect_thinking):
                    # 先处理思考事件（实时输出）
                    while thinking_events:
                        e, d = thinking_events.pop(0)
                        if e == 'thinking_start':
                            yield f"data: {json.dumps({'type': 'thinking_start'}, ensure_ascii=False)}\n\n"
                        elif e == 'thinking':
                            yield f"data: {json.dumps({'type': 'thinking', 'data': d}, ensure_ascii=False)}\n\n"
                        elif e == 'thinking_end':
                            yield f"data: {json.dumps({'type': 'thinking_end'}, ensure_ascii=False)}\n\n"
                    # 处理工具事件
                    while tool_events:
                        e, d = tool_events.pop(0)
                        yield f"data: {json.dumps({'type': e, 'data': d}, ensure_ascii=False)}\n\n"
                    # 输出内容（只有非空时才输出）
                    if chunk:
                        yield f"data: {json.dumps({'type': 'content', 'data': chunk}, ensure_ascii=False)}\n\n"
                # 返回当前会话ID和tokens
                tokens = getattr(nex, '_last_tokens', None)
                yield f"data: {json.dumps({'type': 'done', 'session_id': nex._current_session_id, 'tokens': tokens}, ensure_ascii=False)}\n\n"
            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            reply = nex.chat(req.user, req.message, session_id=req.session_id)
            return {"code": 0, "data": {"reply": reply, "session_id": nex._current_session_id}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nex/history")
async def get_history(limit: Optional[int] = None):
    return {"code": 0, "data": nex.get_history(limit)}


@app.delete("/nex/history")
async def delete_history(req: DeleteRequest = None):
    if nex.delete_history(req.id if req else None):
        return {"code": 0, "message": "删除成功"}
    raise HTTPException(status_code=404, detail="记录不存在")


@app.get("/nex/models")
async def get_models():
    current = nex.get_current_model()
    return {
        "code": 0, 
        "data": {
            "models": nex.get_models(), 
            "current": current,
            "deep_thinking": nex.get_deep_thinking()
        }
    }


@app.post("/nex/models/switch")
async def switch_model(req: SwitchModelRequest):
    if nex.switch_model(req.model_key):
        return {"code": 0, "data": nex.get_current_model(), "message": "切换成功"}
    raise HTTPException(status_code=404, detail="模型不存在")


@app.post("/nex/models/deep-thinking")
async def set_deep_thinking(req: DeepThinkingRequest):
    """设置深度思考模式"""
    if nex.set_deep_thinking(req.enabled):
        return {"code": 0, "data": {"enabled": req.enabled}, "message": "设置成功"}
    raise HTTPException(status_code=400, detail="当前模型不支持深度思考")


@app.get("/nex/models/deep-thinking")
async def get_deep_thinking():
    """获取深度思考模式状态"""
    return {"code": 0, "data": {"enabled": nex.get_deep_thinking()}}


@app.post("/nex/models")
async def add_model(req: AddModelRequest):
    """添加新模型"""
    # 检查服务商是否存在
    provider = nex.get_provider(req.provider_id)
    if not provider:
        raise HTTPException(status_code=400, detail="服务商不存在")
    
    # 自动生成模型key: provider_id + model_id (去除特殊字符)
    import re
    model_key = f"{req.provider_id}_{re.sub(r'[^a-zA-Z0-9_-]', '_', req.model_id)}"
    
    if not nex.add_model(model_key, req.provider_id, req.model_id, req.display_name, req.thinking_model_id):
        raise HTTPException(status_code=400, detail="该模型已存在")
    return {"code": 0, "message": "添加成功"}


@app.put("/nex/models/{model_key}")
async def update_model(model_key: str, req: UpdateModelRequest):
    """更新模型配置"""
    import re
    
    # 如果模型ID变更，需要生成新的 key
    new_key = None
    if req.model_id:
        # 获取当前模型的 provider_id
        model_detail = nex.get_model_detail(model_key)
        if not model_detail:
            raise HTTPException(status_code=404, detail="模型不存在")
        new_key = f"{model_detail['provider_id']}_{re.sub(r'[^a-zA-Z0-9_-]', '_', req.model_id)}"
        if new_key == model_key:
            new_key = None  # key 没变化
    
    result = nex.update_model_config(model_key, new_key, req.model_id, req.display_name, req.thinking_model_id, req.clear_thinking)
    if not result:
        raise HTTPException(status_code=400, detail="更新失败，可能模型ID已被使用")
    return {"code": 0, "message": "更新成功", "data": {"new_key": result}}


@app.delete("/nex/models/{model_key}")
async def delete_model(model_key: str):
    """删除模型"""
    models = nex.get_models()
    if len(models) <= 1:
        raise HTTPException(status_code=400, detail="至少保留一个模型")
    current = nex.get_current_model()
    if current and model_key == current['key']:
        raise HTTPException(status_code=400, detail="不能删除当前使用的模型")
    if not nex.delete_model_config(model_key):
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"code": 0, "message": "删除成功"}


@app.get("/nex/models/{model_key}")
async def get_model_detail(model_key: str):
    """获取模型详情"""
    config = nex.get_model_detail(model_key)
    if not config:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"code": 0, "data": {
        "key": model_key,
        "display_name": config.get("display_name", model_key),
        "model_id": config.get("model_id", ""),
        "provider_id": config.get("provider_id", ""),
        "provider_name": config.get("provider_name", ""),
        "thinking_model_id": config.get("thinking_model_id", "")
    }}


# ========== 服务商管理 API ==========
@app.get("/nex/providers")
async def get_providers():
    """获取所有服务商"""
    providers = nex.get_providers()
    # 隐藏部分 API key
    for p in providers:
        if p.get('api_key'):
            p['api_key'] = p['api_key'][:8] + '***' if len(p['api_key']) > 8 else '***'
    return {"code": 0, "data": providers}


@app.post("/nex/providers")
async def add_provider(req: AddProviderRequest):
    """添加服务商"""
    if not nex.add_provider(req.id, req.name, req.api_key, req.base_url):
        raise HTTPException(status_code=400, detail="服务商ID已存在")
    return {"code": 0, "message": "添加成功"}


@app.get("/nex/providers/{provider_id}")
async def get_provider(provider_id: str):
    """获取服务商详情"""
    provider = nex.get_provider(provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="服务商不存在")
    # 隐藏部分 API key
    if provider.get('api_key'):
        provider['api_key_masked'] = provider['api_key'][:8] + '***' if len(provider['api_key']) > 8 else '***'
    return {"code": 0, "data": provider}


@app.put("/nex/providers/{provider_id}")
async def update_provider(provider_id: str, req: UpdateProviderRequest):
    """更新服务商"""
    if not nex.update_provider(provider_id, req.name, req.api_key, req.base_url):
        raise HTTPException(status_code=404, detail="服务商不存在或更新失败")
    return {"code": 0, "message": "更新成功"}


@app.delete("/nex/providers/{provider_id}")
async def delete_provider(provider_id: str):
    """删除服务商"""
    # 检查是否有模型使用此服务商
    models = nex.get_models()
    using_models = [m for m in models if m.get('provider_id') == provider_id]
    if using_models:
        raise HTTPException(status_code=400, detail=f"有 {len(using_models)} 个模型使用此服务商，请先删除这些模型")
    if not nex.delete_provider(provider_id):
        raise HTTPException(status_code=404, detail="服务商不存在")
    return {"code": 0, "message": "删除成功"}


@app.get("/nex/tools")
async def get_tools():
    """获取所有可用工具列表"""
    tools_list = []
    # 内置和自定义工具
    for tool in nex.tools:
        func = tool.get("function", {})
        tools_list.append({
            "name": func.get("name"),
            "description": func.get("description"),
            "parameters": func.get("parameters"),
            "type": "builtin" if func.get("name") in ["execute_shell", "http_request"] else "custom",
            "has_handler": func.get("name") in nex._custom_tools or func.get("name") in ["execute_shell", "http_request"]
        })
    # MCP 工具
    for tool in nex.get_mcp_tools():
        func = tool.get("function", {})
        tools_list.append({
            "name": func.get("name"),
            "description": func.get("description"),
            "parameters": func.get("parameters"),
            "type": "mcp",
            "has_handler": True
        })
    return {"code": 0, "data": tools_list}


# ========== MCP 服务器管理 API ==========
@app.get("/nex/mcp/servers")
async def get_mcp_servers():
    """获取所有 MCP 服务器"""
    servers = nex.get_mcp_servers()
    return {"code": 0, "data": servers}


@app.post("/nex/mcp/servers")
async def add_mcp_server(req: AddMCPServerRequest):
    """添加 MCP 服务器"""
    result = nex.add_mcp_server(req.id, req.name, req.url, req.server_type, req.headers)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "添加失败"))
    return {"code": 0, "data": result, "message": "添加成功"}


@app.put("/nex/mcp/servers/{server_id}")
async def update_mcp_server(server_id: str, req: UpdateMCPServerRequest):
    """更新 MCP 服务器"""
    if not nex.update_mcp_server(server_id, req.name, req.url, req.server_type, req.headers, req.enabled):
        raise HTTPException(status_code=404, detail="服务器不存在或更新失败")
    return {"code": 0, "message": "更新成功"}


@app.delete("/nex/mcp/servers/{server_id}")
async def delete_mcp_server(server_id: str):
    """删除 MCP 服务器"""
    if not nex.delete_mcp_server(server_id):
        raise HTTPException(status_code=404, detail="服务器不存在")
    return {"code": 0, "message": "删除成功"}


@app.post("/nex/mcp/servers/{server_id}/reconnect")
async def reconnect_mcp_server(server_id: str):
    """重新连接 MCP 服务器"""
    if nex.reconnect_mcp_server(server_id):
        return {"code": 0, "message": "重新连接成功"}
    raise HTTPException(status_code=400, detail="重新连接失败")


# ========== 会话管理 API ==========
@app.get("/nex/sessions")
async def get_sessions(user: Optional[str] = None, limit: Optional[int] = None):
    """获取会话列表"""
    sessions = nex.get_sessions(user, limit)
    current = nex.get_current_session()
    return {"code": 0, "data": {"sessions": sessions, "current_id": current['id'] if current else None}}


@app.post("/nex/sessions")
async def create_session(req: CreateSessionRequest):
    """创建新会话"""
    session_id = nex.create_session(req.name, req.user)
    return {"code": 0, "data": {"session_id": session_id}, "message": "创建成功"}


@app.get("/nex/sessions/{session_id}")
async def get_session(session_id: int):
    """获取单个会话详情"""
    session = nex.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"code": 0, "data": session}


@app.put("/nex/sessions/{session_id}")
async def update_session(session_id: int, req: UpdateSessionRequest):
    """更新会话名称"""
    if nex.update_session(session_id, req.name):
        return {"code": 0, "message": "更新成功"}
    raise HTTPException(status_code=404, detail="会话不存在")


@app.delete("/nex/sessions/{session_id}")
async def delete_session(session_id: int):
    """删除会话"""
    if nex.delete_session(session_id):
        return {"code": 0, "message": "删除成功"}
    raise HTTPException(status_code=404, detail="会话不存在")


@app.get("/nex/sessions/{session_id}/messages")
async def get_session_messages(session_id: int, limit: Optional[int] = None):
    """获取会话消息"""
    messages = nex.get_session_messages(session_id, limit)
    return {"code": 0, "data": messages}


@app.delete("/nex/sessions/{session_id}/messages")
async def clear_session_messages(session_id: int):
    """清空会话消息"""
    count = nex.clear_session_messages(session_id)
    return {"code": 0, "message": f"已删除 {count} 条消息"}


@app.delete("/nex/messages/{message_id}")
async def delete_message(message_id: int):
    """删除单条消息"""
    if nex.delete_message(message_id):
        return {"code": 0, "message": "删除成功"}
    raise HTTPException(status_code=404, detail="消息不存在")


@app.get("/nex/messages/{message_id}")
async def get_message(message_id: int):
    """获取单条消息"""
    msg = nex.get_message(message_id)
    if msg:
        return {"code": 0, "data": msg}
    raise HTTPException(status_code=404, detail="消息不存在")


@app.put("/nex/messages/{message_id}")
async def update_message(message_id: int, req: EditMessageRequest):
    """编辑消息内容"""
    msg = nex.get_message(message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")
    
    # 更新消息内容
    if not nex.update_message(message_id, req.content):
        raise HTTPException(status_code=500, detail="更新失败")
    
    # 如果需要重新生成，删除该消息之后的所有消息
    if req.regenerate and msg['role'] == 'user':
        nex.delete_messages_after(msg['session_id'], message_id)
    
    return {"code": 0, "message": "更新成功", "data": {"regenerate": req.regenerate, "session_id": msg['session_id']}}


@app.post("/nex/sessions/{session_id}/regenerate")
async def regenerate_response(session_id: int):
    """重新生成最后一条回复（流式）"""
    # 获取最后一条用户消息
    last_user_msg = nex.get_last_user_message(session_id)
    if not last_user_msg:
        raise HTTPException(status_code=400, detail="没有可重新生成的消息")
    
    # 删除该用户消息之后的所有消息（即AI回复）
    nex.delete_messages_after(session_id, last_user_msg['id'])
    
    # 返回需要重新发送的消息信息
    return {
        "code": 0, 
        "data": {
            "message": last_user_msg['content'],
            "user": last_user_msg['user'] or "guest",
            "message_id": last_user_msg['id']
        }
    }


# ========== 系统信息 API ==========
@app.get("/nex/version")
async def get_version():
    """获取版本号"""
    return {"code": 0, "data": {"version": __version__}}


# ========== 前端页面 ==========
@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(STATIC_DIR, 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()
