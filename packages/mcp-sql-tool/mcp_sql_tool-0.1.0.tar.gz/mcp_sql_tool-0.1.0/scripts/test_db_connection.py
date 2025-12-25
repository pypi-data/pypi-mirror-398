#!/usr/bin/env python3
"""测试数据库连接脚本"""

import sys
import os

# 添加项目根目录到 Python 路径（用于开发模式）
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

try:
    from mcp_sql_tool.utils.config_loader import ConfigLoader
    from mcp_sql_tool.database import ConnectionManager
except ImportError:
    # 开发模式回退
    from utils.config_loader import ConfigLoader
    from database import ConnectionManager


def test_connection(config_path: str = "config/config.yaml"):
    """测试数据库连接"""
    print("=" * 60)
    print("数据库连接测试")
    print("=" * 60)
    
    # 加载配置
    config_loader = ConfigLoader(config_path)
    config = config_loader.load()
    database_configs = config_loader.get_database_configs()
    
    if not database_configs:
        print("❌ 错误：未找到数据库配置")
        return False
    
    connection_manager = ConnectionManager()
    
    all_success = True
    
    for db_config in database_configs:
        db_name = db_config.get("name", "unknown")
        db_type = db_config.get("type", "unknown")
        db_host = db_config.get("host", "localhost")
        db_port = db_config.get("port", "")
        database = db_config.get("database", "")
        
        print(f"\n测试数据库: {db_name}")
        print(f"  类型: {db_type}")
        print(f"  主机: {db_host}")
        if db_port:
            print(f"  端口: {db_port}")
        print(f"  数据库: {database}")
        
        try:
            # 注册数据库
            connection_manager.register_database(db_name, db_config)
            
            # 测试连接
            if connection_manager.test_connection(db_name):
                print(f"✅ 连接成功！")
                
                # 尝试列出表
                try:
                    adapter = connection_manager.get_adapter(db_name)
                    adapter.connect()
                    tables = adapter.list_tables()
                    adapter.disconnect()
                    
                    if tables:
                        print(f"  找到 {len(tables)} 个表:")
                        for table in tables[:10]:  # 只显示前10个
                            print(f"    - {table}")
                        if len(tables) > 10:
                            print(f"    ... 还有 {len(tables) - 10} 个表")
                    else:
                        print("  数据库中没有表")
                except Exception as e:
                    print(f"  ⚠️  无法列出表: {e}")
            else:
                print(f"❌ 连接失败！")
                all_success = False
                
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            all_success = False
    
    print("\n" + "=" * 60)
    if all_success:
        print("✅ 所有数据库连接测试通过！")
    else:
        print("❌ 部分数据库连接失败，请检查配置")
    print("=" * 60)
    
    return all_success


if __name__ == "__main__":
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config/config.yaml"
    success = test_connection(config_path)
    sys.exit(0 if success else 1)

