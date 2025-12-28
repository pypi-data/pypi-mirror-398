#!/usr/bin/env python3
"""
数据库迁移脚本：将密码从加密改为明文存储
===========================================

此脚本会：
1. 备份现有 users 表
2. 删除旧表
3. 创建新的明文密码表结构
4. 创建默认用户

运行方式：python scripts/migrate_password_plaintext.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import aiomysql


async def migrate():
    """执行数据库迁移"""
    
    # 数据库配置（与 database.py 保持一致）
    config = {
        'host': os.getenv("MCP_DB_HOST", "42.192.110.12"),
        'port': int(os.getenv("MCP_DB_PORT", "3306")),
        'user': os.getenv("MCP_DB_USER", "user"),
        'password': os.getenv("MCP_DB_PASSWORD", "pp000000"),
        'db': os.getenv("MCP_DB_NAME", "user"),
        'charset': 'utf8mb4',
    }
    
    print(f"连接数据库: {config['host']}:{config['port']}/{config['db']}")
    
    try:
        conn = await aiomysql.connect(**config)
        cursor = await conn.cursor()
        
        # 1. 检查 users 表是否存在
        await cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = await cursor.fetchone()
        
        if table_exists:
            print("发现现有 users 表")
            
            # 2. 备份现有表
            backup_table = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"备份到: {backup_table}")
            await cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM users")
            
            # 3. 删除旧表
            print("删除旧的 users 表...")
            await cursor.execute("DROP TABLE users")
        
        # 4. 创建新表（明文密码结构）
        print("创建新的 users 表（明文密码）...")
        create_sql = """
        CREATE TABLE users (
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
        await cursor.execute(create_sql)
        
        # 5. 创建默认用户
        print("创建默认用户...")
        
        # admin - 永久 VIP
        vip_expire_forever = datetime.now() + timedelta(days=36500)
        await cursor.execute(
            "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
            ("admin", "admin123", True, vip_expire_forever)
        )
        print("  ✓ admin / admin123 (永久VIP)")
        
        # user - 非 VIP
        await cursor.execute(
            "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
            ("user", "user123", False, None)
        )
        print("  ✓ user / user123 (非VIP)")
        
        # vip - 30天 VIP
        vip_expire_30 = datetime.now() + timedelta(days=30)
        await cursor.execute(
            "INSERT INTO users (username, password, is_vip, vip_expire_at) VALUES (%s, %s, %s, %s)",
            ("vip", "vip123", True, vip_expire_30)
        )
        print(f"  ✓ vip / vip123 (VIP到期: {vip_expire_30.strftime('%Y-%m-%d')})")
        
        await conn.commit()
        print("\n✅ 迁移完成！密码现在以明文方式存储。")
        
        await cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(migrate())
