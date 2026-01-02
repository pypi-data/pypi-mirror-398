"""
NexAgent 数据库模块 - SQLite存储
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from contextlib import contextmanager


class Database:
    """SQLite数据库管理"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.get_conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    user TEXT,
                    extra TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                
                CREATE TABLE IF NOT EXISTS providers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS models (
                    id TEXT PRIMARY KEY,
                    provider_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    thinking_model_id TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (provider_id) REFERENCES providers(id) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user);
                CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider_id);
                
                CREATE TABLE IF NOT EXISTS mcp_servers (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    server_type TEXT DEFAULT 'sse',
                    headers TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                );
            ''')
            # 检查并添加 extra 列（兼容旧数据库）
            try:
                conn.execute('SELECT extra FROM messages LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE messages ADD COLUMN extra TEXT')
            # 检查并添加 mcp_servers 的新列（兼容旧数据库）
            try:
                conn.execute('SELECT server_type FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute("ALTER TABLE mcp_servers ADD COLUMN server_type TEXT DEFAULT 'sse'")
            try:
                conn.execute('SELECT headers FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE mcp_servers ADD COLUMN headers TEXT')
            try:
                conn.execute('SELECT enabled FROM mcp_servers LIMIT 1')
            except sqlite3.OperationalError:
                conn.execute('ALTER TABLE mcp_servers ADD COLUMN enabled INTEGER DEFAULT 1')
    
    # ========== 会话管理 ==========
    def create_session(self, name: str, user: str) -> int:
        """创建新会话"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO sessions (name, user, created_at, updated_at) VALUES (?, ?, ?, ?)',
                (name, user, now, now)
            )
            return cursor.lastrowid
    
    def get_sessions(self, user: str = None, limit: int = None) -> List[Dict]:
        """获取会话列表"""
        with self.get_conn() as conn:
            sql = 'SELECT * FROM sessions WHERE is_active = 1'
            params = []
            if user:
                sql += ' AND user = ?'
                params.append(user)
            sql += ' ORDER BY updated_at DESC'
            if limit:
                sql += ' LIMIT ?'
                params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
    
    def get_session(self, session_id: int) -> Optional[Dict]:
        """获取单个会话"""
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM sessions WHERE id = ? AND is_active = 1', (session_id,)
            ).fetchone()
            return dict(row) if row else None

    def update_session(self, session_id: int, name: str = None) -> bool:
        """更新会话"""
        with self.get_conn() as conn:
            updates = ['updated_at = ?']
            params = [datetime.now().isoformat()]
            if name:
                updates.append('name = ?')
                params.append(name)
            params.append(session_id)
            result = conn.execute(
                f'UPDATE sessions SET {", ".join(updates)} WHERE id = ? AND is_active = 1',
                params
            )
            return result.rowcount > 0
    
    def delete_session(self, session_id: int) -> bool:
        """删除会话（软删除）"""
        with self.get_conn() as conn:
            result = conn.execute(
                'UPDATE sessions SET is_active = 0 WHERE id = ?', (session_id,)
            )
            return result.rowcount > 0
    
    def delete_all_sessions(self, user: str = None) -> int:
        """删除所有会话"""
        with self.get_conn() as conn:
            if user:
                result = conn.execute(
                    'UPDATE sessions SET is_active = 0 WHERE user = ?', (user,)
                )
            else:
                result = conn.execute('UPDATE sessions SET is_active = 0')
            return result.rowcount
    
    # ========== 消息管理 ==========
    def add_message(self, session_id: int, role: str, content: str, user: str = None, extra: dict = None) -> int:
        """添加消息
        
        Args:
            session_id: 会话ID
            role: 角色 (user/assistant/tool)
            content: 消息内容
            user: 用户名（仅user角色）
            extra: 额外数据（如工具调用信息）
        """
        import json
        now = datetime.now().isoformat()
        extra_json = json.dumps(extra, ensure_ascii=False) if extra else None
        with self.get_conn() as conn:
            cursor = conn.execute(
                'INSERT INTO messages (session_id, role, content, user, extra, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (session_id, role, content, user, extra_json, now)
            )
            # 更新会话时间
            conn.execute(
                'UPDATE sessions SET updated_at = ? WHERE id = ?', (now, session_id)
            )
            return cursor.lastrowid
    
    def get_messages(self, session_id: int, limit: int = None) -> List[Dict]:
        """获取会话消息"""
        import json
        with self.get_conn() as conn:
            sql = 'SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC'
            params = [session_id]
            if limit:
                sql = f'SELECT * FROM (SELECT * FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id ASC'
                params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            result = []
            for row in rows:
                msg = dict(row)
                # 解析 extra JSON
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                result.append(msg)
            return result
    
    def delete_message(self, message_id: int) -> bool:
        """删除单条消息"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM messages WHERE id = ?', (message_id,))
            return result.rowcount > 0
    
    def get_message(self, message_id: int) -> Optional[Dict]:
        """获取单条消息"""
        import json
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM messages WHERE id = ?', (message_id,)).fetchone()
            if row:
                msg = dict(row)
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                return msg
            return None
    
    def update_message(self, message_id: int, content: str) -> bool:
        """更新消息内容"""
        with self.get_conn() as conn:
            result = conn.execute(
                'UPDATE messages SET content = ? WHERE id = ?',
                (content, message_id)
            )
            return result.rowcount > 0
    
    def delete_messages_after(self, session_id: int, message_id: int) -> int:
        """删除指定消息之后的所有消息（用于重新生成）"""
        with self.get_conn() as conn:
            result = conn.execute(
                'DELETE FROM messages WHERE session_id = ? AND id > ?',
                (session_id, message_id)
            )
            return result.rowcount
    
    def get_last_user_message(self, session_id: int) -> Optional[Dict]:
        """获取会话中最后一条用户消息"""
        import json
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM messages WHERE session_id = ? AND role = ? ORDER BY id DESC LIMIT 1',
                (session_id, 'user')
            ).fetchone()
            if row:
                msg = dict(row)
                if msg.get('extra'):
                    try:
                        msg['extra'] = json.loads(msg['extra'])
                    except:
                        pass
                return msg
            return None
    
    def delete_session_messages(self, session_id: int) -> int:
        """清空会话消息"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            return result.rowcount
    
    def get_message_count(self, session_id: int) -> int:
        """获取会话消息数量"""
        with self.get_conn() as conn:
            row = conn.execute(
                'SELECT COUNT(*) as count FROM messages WHERE session_id = ?', (session_id,)
            ).fetchone()
            return row['count']
    
    # ========== 设置管理 ==========
    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """获取设置"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT value FROM settings WHERE key = ?', (key,)).fetchone()
            return row['value'] if row else default
    
    def set_setting(self, key: str, value: str) -> None:
        """保存设置"""
        with self.get_conn() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value)
            )
    
    # ========== 兼容旧API ==========
    def get_history(self, limit: int = None) -> List[Dict]:
        """获取历史记录（兼容旧API）"""
        with self.get_conn() as conn:
            sql = '''
                SELECT m.id, m.content as message, m.user, m.created_at as time,
                       (SELECT content FROM messages WHERE session_id = m.session_id AND id = m.id + 1 AND role = 'assistant') as response
                FROM messages m
                WHERE m.role = 'user'
                ORDER BY m.id DESC
            '''
            if limit:
                sql += f' LIMIT {limit}'
            rows = conn.execute(sql).fetchall()
            result = []
            for row in rows:
                if row['response']:
                    result.append({
                        'id': row['id'],
                        'user': row['user'],
                        'message': row['message'],
                        'response': row['response'],
                        'time': row['time']
                    })
            return list(reversed(result))

    # ========== 服务商管理 ==========
    def create_provider(self, provider_id: str, name: str, api_key: str, base_url: str) -> bool:
        """创建服务商"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO providers (id, name, api_key, base_url, created_at) VALUES (?, ?, ?, ?, ?)',
                    (provider_id, name, api_key, base_url, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_providers(self) -> List[Dict]:
        """获取所有服务商"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT * FROM providers ORDER BY created_at DESC').fetchall()
            return [dict(row) for row in rows]
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """获取单个服务商"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM providers WHERE id = ?', (provider_id,)).fetchone()
            return dict(row) if row else None
    
    def update_provider(self, provider_id: str, name: str = None, api_key: str = None, base_url: str = None) -> bool:
        """更新服务商"""
        with self.get_conn() as conn:
            updates = []
            params = []
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if api_key is not None:
                updates.append('api_key = ?')
                params.append(api_key)
            if base_url is not None:
                updates.append('base_url = ?')
                params.append(base_url)
            if not updates:
                return False
            params.append(provider_id)
            result = conn.execute(
                f'UPDATE providers SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_provider(self, provider_id: str) -> bool:
        """删除服务商（同时删除关联的模型）"""
        with self.get_conn() as conn:
            # 先删除关联的模型
            conn.execute('DELETE FROM models WHERE provider_id = ?', (provider_id,))
            result = conn.execute('DELETE FROM providers WHERE id = ?', (provider_id,))
            return result.rowcount > 0
    
    # ========== 模型管理 ==========
    def create_model(self, model_key: str, provider_id: str, model_id: str, display_name: str, thinking_model_id: str = None) -> bool:
        """创建模型"""
        now = datetime.now().isoformat()
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO models (id, provider_id, model_id, display_name, thinking_model_id, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                    (model_key, provider_id, model_id, display_name, thinking_model_id, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_models_list(self) -> List[Dict]:
        """获取所有模型（包含服务商信息）"""
        with self.get_conn() as conn:
            rows = conn.execute('''
                SELECT m.*, p.name as provider_name, p.api_key, p.base_url
                FROM models m
                JOIN providers p ON m.provider_id = p.id
                ORDER BY m.created_at DESC
            ''').fetchall()
            return [dict(row) for row in rows]
    
    def get_model(self, model_key: str) -> Optional[Dict]:
        """获取单个模型（包含服务商信息）"""
        with self.get_conn() as conn:
            row = conn.execute('''
                SELECT m.*, p.name as provider_name, p.api_key, p.base_url
                FROM models m
                JOIN providers p ON m.provider_id = p.id
                WHERE m.id = ?
            ''', (model_key,)).fetchone()
            return dict(row) if row else None
    
    def get_models_by_provider(self, provider_id: str) -> List[Dict]:
        """获取服务商下的所有模型"""
        with self.get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM models WHERE provider_id = ? ORDER BY created_at DESC',
                (provider_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def update_model(self, model_key: str, model_id: str = None, display_name: str = None, thinking_model_id: str = None, clear_thinking: bool = False) -> bool:
        """更新模型"""
        with self.get_conn() as conn:
            updates = []
            params = []
            if model_id is not None:
                updates.append('model_id = ?')
                params.append(model_id)
            if display_name is not None:
                updates.append('display_name = ?')
                params.append(display_name)
            if thinking_model_id is not None:
                updates.append('thinking_model_id = ?')
                params.append(thinking_model_id)
            elif clear_thinking:
                updates.append('thinking_model_id = NULL')
            if not updates:
                return False
            params.append(model_key)
            result = conn.execute(
                f'UPDATE models SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_model(self, model_key: str) -> bool:
        """删除模型"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM models WHERE id = ?', (model_key,))
            return result.rowcount > 0

    # ========== MCP服务器管理 ==========
    def create_mcp_server(self, server_id: str, name: str, url: str, server_type: str = "sse", headers: Dict = None) -> bool:
        """创建MCP服务器"""
        now = datetime.now().isoformat()
        headers_json = json.dumps(headers, ensure_ascii=False) if headers else None
        with self.get_conn() as conn:
            try:
                conn.execute(
                    'INSERT INTO mcp_servers (id, name, url, server_type, headers, enabled, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)',
                    (server_id, name, url, server_type, headers_json, now)
                )
                return True
            except sqlite3.IntegrityError:
                return False
    
    def get_mcp_servers(self) -> List[Dict]:
        """获取所有MCP服务器"""
        with self.get_conn() as conn:
            rows = conn.execute('SELECT * FROM mcp_servers ORDER BY created_at DESC').fetchall()
            result = []
            for row in rows:
                server = dict(row)
                if server.get('headers'):
                    try:
                        server['headers'] = json.loads(server['headers'])
                    except:
                        server['headers'] = {}
                else:
                    server['headers'] = {}
                # 转换 enabled 为布尔值
                server['enabled'] = bool(server.get('enabled', 1))
                result.append(server)
            return result
    
    def get_mcp_server(self, server_id: str) -> Optional[Dict]:
        """获取单个MCP服务器"""
        with self.get_conn() as conn:
            row = conn.execute('SELECT * FROM mcp_servers WHERE id = ?', (server_id,)).fetchone()
            if row:
                server = dict(row)
                if server.get('headers'):
                    try:
                        server['headers'] = json.loads(server['headers'])
                    except:
                        server['headers'] = {}
                else:
                    server['headers'] = {}
                # 转换 enabled 为布尔值
                server['enabled'] = bool(server.get('enabled', 1))
                return server
            return None
    
    def update_mcp_server(self, server_id: str, name: str = None, url: str = None, server_type: str = None, headers: Dict = None, enabled: bool = None) -> bool:
        """更新MCP服务器"""
        with self.get_conn() as conn:
            updates = []
            params = []
            if name is not None:
                updates.append('name = ?')
                params.append(name)
            if url is not None:
                updates.append('url = ?')
                params.append(url)
            if server_type is not None:
                updates.append('server_type = ?')
                params.append(server_type)
            if headers is not None:
                updates.append('headers = ?')
                params.append(json.dumps(headers, ensure_ascii=False) if headers else None)
            if enabled is not None:
                updates.append('enabled = ?')
                params.append(1 if enabled else 0)
            if not updates:
                return False
            params.append(server_id)
            result = conn.execute(
                f'UPDATE mcp_servers SET {", ".join(updates)} WHERE id = ?',
                params
            )
            return result.rowcount > 0
    
    def delete_mcp_server(self, server_id: str) -> bool:
        """删除MCP服务器"""
        with self.get_conn() as conn:
            result = conn.execute('DELETE FROM mcp_servers WHERE id = ?', (server_id,))
            return result.rowcount > 0
