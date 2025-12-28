#!/usr/bin/env python3
"""
认证路由模块
============

提供登录、登出等认证相关的路由处理。
"""

from typing import TYPE_CHECKING

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from ... import __version__
from ...debug import web_debug_log as debug_log
from ..auth import get_auth_manager, get_db_manager


if TYPE_CHECKING:
    from ..main import WebUIManager


class LoginRequest(BaseModel):
    """登录请求模型"""

    username: str
    password: str
    remember_me: bool = False


def setup_auth_routes(manager: "WebUIManager"):
    """设置认证相关路由"""

    auth_manager = get_auth_manager()
    db_manager = get_db_manager()

    @manager.app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        """登录页面"""
        # 如果已经登录，重定向到首页
        session_id = auth_manager.get_session_from_request(request)
        if auth_manager.validate_session(session_id):
            return RedirectResponse(url="/", status_code=302)

        return manager.templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "version": __version__,
            },
        )

    @manager.app.post("/api/login")
    async def api_login(login_data: LoginRequest):
        """处理登录请求"""
        try:
            # 确保数据库表已初始化
            await db_manager.init_tables()

            # 验证用户凭据（现在返回详细信息）
            result = await db_manager.verify_user(login_data.username, login_data.password)
            
            if result.get("success"):
                # 创建会话
                session_id = auth_manager.create_session(
                    login_data.username,
                    vip_expire_at=result.get("vip_expire_at"),
                )

                # 设置会话超时时间
                max_age = 86400 * 30 if login_data.remember_me else 86400  # 30天或1天

                response = JSONResponse(
                    content={
                        "success": True,
                        "message": "登录成功",
                        "redirect": "/",
                        "is_vip": result.get("is_vip", False),
                        "vip_expire_at": result.get("vip_expire_at"),
                    }
                )
                response.set_cookie(
                    key="mcp_session_id",
                    value=session_id,
                    max_age=max_age,
                    httponly=True,
                    samesite="lax",
                )
                return response
            else:
                # 返回详细的错误信息
                return JSONResponse(
                    content={
                        "success": False,
                        "message": result.get("message", "登录失败"),
                        "vip_expired": result.get("vip_expired", False),
                        "is_vip": result.get("is_vip", False),
                        "vip_expire_at": result.get("vip_expire_at"),
                    },
                    status_code=401,
                )
        except Exception as e:
            debug_log(f"登录失败: {e}")
            return JSONResponse(
                content={
                    "success": False,
                    "message": f"登录失败: {str(e)}",
                },
                status_code=500,
            )

    @manager.app.post("/api/logout")
    async def api_logout(request: Request):
        """处理登出请求"""
        session_id = auth_manager.get_session_from_request(request)
        if session_id:
            auth_manager.destroy_session(session_id)

        response = JSONResponse(
            content={
                "success": True,
                "message": "已登出",
                "redirect": "/login",
            }
        )
        response.delete_cookie(key="mcp_session_id")
        return response

    @manager.app.get("/api/auth/status")
    async def auth_status(request: Request):
        """检查认证状态"""
        session_id = auth_manager.get_session_from_request(request)
        username = auth_manager.validate_session(session_id)
        
        # 获取会话中的 VIP 信息
        vip_expire_at = None
        if session_id and session_id in auth_manager._sessions:
            vip_expire_at = auth_manager._sessions[session_id].get("vip_expire_at")

        return JSONResponse(
            content={
                "authenticated": username is not None,
                "username": username,
                "auth_enabled": auth_manager.enabled,
                "is_vip": vip_expire_at is not None,
                "vip_expire_at": vip_expire_at,
            }
        )

    @manager.app.get("/api/user/info")
    async def user_info(request: Request):
        """获取当前用户信息"""
        session_id = auth_manager.get_session_from_request(request)
        username = auth_manager.validate_session(session_id)
        
        if not username:
            return JSONResponse(
                content={"success": False, "message": "未登录"},
                status_code=401,
            )
        
        try:
            # 从数据库获取最新的用户信息
            user_info = await db_manager.get_user_info(username)
            if user_info:
                return JSONResponse(content={"success": True, "user": user_info})
            else:
                return JSONResponse(
                    content={"success": False, "message": "用户不存在"},
                    status_code=404,
                )
        except Exception as e:
            debug_log(f"获取用户信息失败: {e}")
            return JSONResponse(
                content={"success": False, "message": str(e)},
                status_code=500,
            )
