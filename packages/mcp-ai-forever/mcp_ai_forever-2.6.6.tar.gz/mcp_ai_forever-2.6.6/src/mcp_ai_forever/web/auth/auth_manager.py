#!/usr/bin/env python3
"""
认证管理模块
============

提供 Session 管理和认证中间件功能。
"""

import hashlib
import os
import time
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from ...debug import web_debug_log as debug_log


class AuthManager:
    """认证管理器"""

    def __init__(self, session_timeout: int = 86400):
        """
        初始化认证管理器

        Args:
            session_timeout: Session 超时时间（秒），默认 24 小时
        """
        self.session_timeout = session_timeout
        self._sessions: dict[str, dict] = {}
        self._enabled = True  # 是否启用认证

    @property
    def enabled(self) -> bool:
        """是否启用认证"""
        # 可通过环境变量禁用认证
        env_value = os.getenv("MCP_AUTH_ENABLED", "true").lower()
        return self._enabled and env_value != "false"

    @enabled.setter
    def enabled(self, value: bool):
        """设置是否启用认证"""
        self._enabled = value

    def generate_session_id(self) -> str:
        """生成新的 Session ID"""
        random_bytes = os.urandom(32)
        timestamp = str(time.time()).encode()
        return hashlib.sha256(random_bytes + timestamp).hexdigest()

    def create_session(self, username: str, vip_expire_at: Optional[str] = None) -> str:
        """
        创建新的登录会话

        Args:
            username: 用户名
            vip_expire_at: VIP 过期时间（ISO 格式字符串）

        Returns:
            str: Session ID
        """
        session_id = self.generate_session_id()
        self._sessions[session_id] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "vip_expire_at": vip_expire_at,
        }
        debug_log(f"创建新会话: {username}, VIP过期: {vip_expire_at}")
        return session_id

    def validate_session(self, session_id: Optional[str]) -> Optional[str]:
        """
        验证会话是否有效

        Args:
            session_id: Session ID

        Returns:
            Optional[str]: 如果有效返回用户名，否则返回 None
        """
        if not session_id or session_id not in self._sessions:
            return None

        session = self._sessions[session_id]
        now = datetime.now()

        # 检查会话是否超时
        if (now - session["last_activity"]).total_seconds() > self.session_timeout:
            del self._sessions[session_id]
            debug_log(f"会话已超时: {session['username']}")
            return None

        # 更新最后活动时间
        session["last_activity"] = now
        return session["username"]

    def destroy_session(self, session_id: str):
        """
        销毁会话

        Args:
            session_id: Session ID
        """
        if session_id in self._sessions:
            username = self._sessions[session_id]["username"]
            del self._sessions[session_id]
            debug_log(f"会话已销毁: {username}")

    def get_session_from_request(self, request: Request) -> Optional[str]:
        """
        从请求中获取 Session ID

        Args:
            request: FastAPI 请求对象

        Returns:
            Optional[str]: Session ID
        """
        return request.cookies.get("mcp_session_id")

    def cleanup_expired_sessions(self):
        """清理过期的会话"""
        now = datetime.now()
        expired = [
            sid
            for sid, session in self._sessions.items()
            if (now - session["last_activity"]).total_seconds() > self.session_timeout
        ]
        for sid in expired:
            del self._sessions[sid]
        if expired:
            debug_log(f"清理了 {len(expired)} 个过期会话")


# 全局认证管理器实例
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """获取全局认证管理器实例"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager
