# -*- coding: utf-8 -*-

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def init_database():
    """
    读取并执行SQL初始化脚本
    """
    # 加载环境变量
    load_dotenv()
    
    # 数据库连接参数
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'langchain_user',
        'password': 'langchain_password',
        'database': 'langchain_chat',
    }
    
    # 连接数据库
    print(f"正在连接到数据库 {db_params['host']}:{db_params['port']}...")
    try:
        conn = psycopg2.connect(
            host=db_params['host'],
            port=db_params['port'],
            user=db_params['user'],
            password=db_params['password'],
            database=db_params['database']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # 读取SQL文件
        sql_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', '01-init.sql')
        print(f"正在读取SQL文件: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 执行SQL脚本
        print("正在执行SQL脚本...")
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
        
        print("SQL脚本执行成功")
        conn.close()
        return True
    
    except Exception as e:
        print(f"数据库初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始初始化数据库...")
    success = init_database()
    if success:
        print("数据库初始化完成")
    else:
        print("数据库初始化失败")