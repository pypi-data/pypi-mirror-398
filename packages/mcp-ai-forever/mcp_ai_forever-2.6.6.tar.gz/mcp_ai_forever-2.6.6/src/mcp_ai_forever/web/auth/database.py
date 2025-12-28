#!/usr/bin/env python3
"""
数据库管理模块
==============

提供 MySQL 数据库连接和用户表管理功能，包括 VIP 会员时间授权。
"""

import asyncio
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import aiomysql

from ...debug import web_debug_log as debug_log


class DatabaseManager:
    """MySQL 数据库管理器"""

    def __init__(
        self,
        host: str = "42.192.110.12",
        port: int = 3306,
        user: str = "user",
        password: str = "pp000000",
        database: str = "user",
    ):
        """
        初始化数据库管理器

        Args:
            host: MySQL 服务器地址
            port: MySQL 服务器端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名称
        """
        # 允许通过环境变量覆盖配置
        self.host = os.getenv("MCP_DB_HOST", host)
        self.port = int(os.getenv("MCP_DB_PORT", str(port)))
        self.user = os.getenv("MCP_DB_USER", user)
        self.password = os.getenv("MCP_DB_PASSWORD", password)
        self.database = os.getenv("MCP_DB_NAME", database)

        self._pool: Optional[aiomysql.Pool] = None
        self._initialized = False

    async def get_pool(self) -> aiomysql.Pool:
        """获取数据库连接池"""
        if self._pool is None or self._pool.closed:
            self._pool = await aiomysql.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                db=self.database,
                charset="utf8mb4",
                autocommit=True,
                minsize=1,
                maxsize=10,
            )
            debug_log(f"数据库连接池已创建: {self.host}:{self.port}/{self.database}")
        return self._pool

    async def close(self):
        """关闭数据库连接池"""
        if self._pool is not None and not self._pool.closed:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            debug_log("数据库连接池已关闭")

    async def init_tables(self):
        """初始化用户表"""
        if self._initialized:
            return

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_vip BOOLEAN DEFAULT FALSE,
            vip_expire_at DATETIME NULL,
            INDEX idx_username (username),
            INDEX idx_vip_expire (vip_expire_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 添加 VIP 字段的升级语句（用于升级现有表，分别处理避免错误）

        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(create_table_sql)
                    debug_log("用户表初始化完成")
                    
                    # 尝试添加 VIP 字段（如果表已存在但没有这些字段）
                    try:
                        await cursor.execute("ALTER TABLE users ADD COLUMN is_vip BOOLEAN DEFAULT FALSE")
                        debug_log("添加 is_vip 字段成功")
                    except Exception:
                        pass  # 字段可能已存在
                    
                    try:
                        await cursor.execute("ALTER TABLE users ADD COLUMN vip_expire_at DATETIME NULL")
                        debug_log("添加 vip_expire_at 字段成功")
                    except Exception:
                        pass  # 字段可能已存在

            # 检查是否需要创建默认管理员账户
            await self._create_default_admin()
            self._initialized = True

        except Exception as e:
            debug_log(f"初始化用户表失败: {e}")
            raise

    async def _create_default_admin(self):
        """创建默认管理员账户和测试用户（如果不存在）"""
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # 检查是否已有用户
                await cursor.execute("SELECT COUNT(*) FROM users")
                result = await cursor.fetchone()
                if result[0] == 0:
                    # 创建默认管理员账户
                    # 默认密码: admin123 (生产环境请立即修改)
                    # 默认设置为永久 VIP
                    # 设置 VIP 过期时间为 100 年后（相当于永久）
                    vip_expire = datetime.now() + timedelta(days=36500)
                    await cursor.execute(
                        "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
                        ("admin", "admin123", True, vip_expire),
                    )
                    debug_log("已创建默认管理员账户 (用户名: admin, 密码: admin123, 永久VIP)")
                    
                    # 创建普通测试用户（非 VIP）
                    await cursor.execute(
                        "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
                        ("user", "user123", False, None),
                    )
                    debug_log("已创建普通用户 (用户名: user, 密码: user123, 非VIP)")
                    
                    # 创建 VIP 测试用户（30 天 VIP）
                    vip_expire_30 = datetime.now() + timedelta(days=30)
                    await cursor.execute(
                        "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
                        ("vip", "vip123", True, vip_expire_30),
                    )
                    debug_log(f"已创建VIP用户 (用户名: vip, 密码: vip123, VIP过期: {vip_expire_30})")

    @staticmethod
    def _hash_password(password: str, salt: str = "") -> str:
        """返回明文密码（已禁用加密）"""
        return password

    async def verify_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        验证用户凭据

        Args:
            username: 用户名
            password: 密码

        Returns:
            Dict: 包含验证结果和用户信息
                - success: 验证是否成功
                - is_vip: 是否是 VIP
                - vip_expired: VIP 是否已过期
                - vip_expire_at: VIP 过期时间
                - message: 错误信息（如有）
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT password, is_active, is_vip, vip_expire_at FROM users WHERE username = %s",
                        (username,),
                    )
                    result = await cursor.fetchone()

                    if not result:
                        debug_log(f"用户不存在: {username}")
                        return {"success": False, "message": "用户名或密码错误"}

                    if not result["is_active"]:
                        debug_log(f"用户已禁用: {username}")
                        return {"success": False, "message": "账户已被禁用"}

                    # 验证密码（明文比较）
                    if password != result["password"]:
                        debug_log(f"密码错误: {username}")
                        return {"success": False, "message": "用户名或密码错误"}

                    # 检查 VIP 状态
                    is_vip = result.get("is_vip", False)
                    vip_expire_at = result.get("vip_expire_at")
                    vip_expired = False
                    
                    if is_vip and vip_expire_at:
                        if datetime.now() > vip_expire_at:
                            vip_expired = True
                            is_vip = False
                            debug_log(f"用户 VIP 已过期: {username}, 过期时间: {vip_expire_at}")

                    # 如果不是 VIP 或 VIP 已过期，拒绝登录
                    if not is_vip:
                        if vip_expired:
                            return {
                                "success": False,
                                "message": f"您的 VIP 会员已于 {vip_expire_at.strftime('%Y-%m-%d %H:%M')} 过期，请续费后再使用",
                                "vip_expired": True,
                                "vip_expire_at": vip_expire_at.isoformat() if vip_expire_at else None,
                            }
                        else:
                            return {
                                "success": False,
                                "message": "您不是 VIP 会员，请开通 VIP 后使用",
                                "is_vip": False,
                            }

                    # 更新最后登录时间
                    await cursor.execute(
                        "UPDATE users SET last_login = %s WHERE username = %s",
                        (datetime.now(), username),
                    )
                    debug_log(f"VIP 用户登录成功: {username}, VIP 过期时间: {vip_expire_at}")
                    
                    return {
                        "success": True,
                        "is_vip": True,
                        "vip_expire_at": vip_expire_at.isoformat() if vip_expire_at else None,
                        "message": "登录成功",
                    }

        except Exception as e:
            debug_log(f"验证用户失败: {e}")
            return {"success": False, "message": f"系统错误: {str(e)}"}

    async def create_user(
        self, username: str, password: str, is_active: bool = True
    ) -> bool:
        """
        创建新用户

        Args:
            username: 用户名
            password: 密码
            is_active: 是否激活

        Returns:
            bool: 创建是否成功
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "INSERT INTO users (username, password, is_active) VALUES (%s, %s, %s)",
                        (username, password, is_active),
                    )
                    debug_log(f"用户创建成功: {username}")
                    return True
        except Exception as e:
            debug_log(f"创建用户失败: {e}")
            return False

    async def change_password(self, username: str, new_password: str) -> bool:
        """
        修改用户密码

        Args:
            username: 用户名
            new_password: 新密码

        Returns:
            bool: 修改是否成功
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute(
                        "UPDATE users SET password = %s WHERE username = %s",
                        (new_password, username),
                    )
                    debug_log(f"密码修改成功: {username}")
                    return True
        except Exception as e:
            debug_log(f"修改密码失败: {e}")
            return False

    async def set_vip(
        self, username: str, days: int = 30, is_vip: bool = True
    ) -> bool:
        """
        设置用户 VIP 状态

        Args:
            username: 用户名
            days: VIP 天数（从当前时间开始计算）
            is_vip: 是否为 VIP

        Returns:
            bool: 设置是否成功
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    if is_vip:
                        vip_expire = datetime.now() + timedelta(days=days)
                        await cursor.execute(
                            "UPDATE users SET is_vip = %s, vip_expire_at = %s WHERE username = %s",
                            (True, vip_expire, username),
                        )
                        debug_log(f"设置 VIP 成功: {username}, 过期时间: {vip_expire}")
                    else:
                        await cursor.execute(
                            "UPDATE users SET is_vip = %s, vip_expire_at = NULL WHERE username = %s",
                            (False, username),
                        )
                        debug_log(f"取消 VIP: {username}")
                    return True
        except Exception as e:
            debug_log(f"设置 VIP 失败: {e}")
            return False

    async def extend_vip(self, username: str, days: int = 30) -> bool:
        """
        延长用户 VIP 时间

        Args:
            username: 用户名
            days: 延长的天数

        Returns:
            bool: 延长是否成功
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    # 获取当前 VIP 过期时间
                    await cursor.execute(
                        "SELECT is_vip, vip_expire_at FROM users WHERE username = %s",
                        (username,),
                    )
                    result = await cursor.fetchone()
                    
                    if not result:
                        debug_log(f"用户不存在: {username}")
                        return False
                    
                    # 计算新的过期时间
                    current_expire = result.get("vip_expire_at")
                    if current_expire and current_expire > datetime.now():
                        # 如果还没过期，从当前过期时间延长
                        new_expire = current_expire + timedelta(days=days)
                    else:
                        # 如果已过期或没有 VIP，从现在开始计算
                        new_expire = datetime.now() + timedelta(days=days)
                    
                    await cursor.execute(
                        "UPDATE users SET is_vip = %s, vip_expire_at = %s WHERE username = %s",
                        (True, new_expire, username),
                    )
                    debug_log(f"延长 VIP 成功: {username}, 新过期时间: {new_expire}")
                    return True
        except Exception as e:
            debug_log(f"延长 VIP 失败: {e}")
            return False

    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            username: 用户名

        Returns:
            Dict: 用户信息，不存在则返回 None
        """
        try:
            pool = await self.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(
                        "SELECT id, username, created_at, last_login, is_active, is_vip, vip_expire_at FROM users WHERE username = %s",
                        (username,),
                    )
                    result = await cursor.fetchone()
                    
                    if result:
                        # 检查 VIP 是否已过期
                        vip_expire_at = result.get("vip_expire_at")
                        is_vip = result.get("is_vip", False)
                        vip_expired = False
                        
                        if is_vip and vip_expire_at:
                            if datetime.now() > vip_expire_at:
                                vip_expired = True
                                is_vip = False
                        
                        return {
                            "id": result["id"],
                            "username": result["username"],
                            "created_at": result["created_at"].isoformat() if result["created_at"] else None,
                            "last_login": result["last_login"].isoformat() if result["last_login"] else None,
                            "is_active": result["is_active"],
                            "is_vip": is_vip,
                            "vip_expired": vip_expired,
                            "vip_expire_at": vip_expire_at.isoformat() if vip_expire_at else None,
                        }
                    return None
        except Exception as e:
            debug_log(f"获取用户信息失败: {e}")
            return None


# 全局数据库管理器实例
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
