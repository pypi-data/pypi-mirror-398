#!/usr/bin/env python3
"""
用户认证模块
============

提供基于 MySQL 的用户登录认证功能。
"""

from .database import DatabaseManager, get_db_manager
from .auth_manager import AuthManager, get_auth_manager

__all__ = [
    "DatabaseManager",
    "get_db_manager",
    "AuthManager",
    "get_auth_manager",
]
