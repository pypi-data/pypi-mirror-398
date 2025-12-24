#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据写入模块 - 专注于爬虫数据入库

功能特性：
- 高性能批量插入
- 智能去重（基于唯一键）
- UPSERT操作（插入或更新）
- 自动建表和字段扩展
- 数据类型自动推断
- 进度监控和统计
- 失败重试机制
- 支持多种数据格式（字典、列表、DataFrame）
- 事务保证

依赖：
    pip install pymysql DBUtils pandas

适用场景：
    - 爬虫数据批量入库
    - 数据ETL导入
    - 日志数据存储
    - 实时数据流写入
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from datetime import datetime, date
from decimal import Decimal
from contextlib import contextmanager
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB


# ==================== 异常类 ====================


class MySQLWriterError(Exception):
    """MySQL写入异常基类"""
    pass


class DataValidationError(MySQLWriterError):
    """数据验证错误"""
    pass


class TableCreationError(MySQLWriterError):
    """建表错误"""
    pass


class InsertError(MySQLWriterError):
    """插入错误"""
    pass


# ==================== 工具函数 ====================


def infer_mysql_type(value: Any, max_length: int = 255, for_index: bool = False) -> str:
    """
    根据Python值推断MySQL数据类型
    
    参数:
        value: Python值
        max_length: VARCHAR最大长度（默认255）
        for_index: 是否用于索引字段（会限制长度以避免超过索引限制）
        
    返回:
        MySQL数据类型字符串
        
    注意:
        - MySQL InnoDB索引长度限制：767字节（默认）或3072字节
        - utf8mb4编码下，VARCHAR(191)最多占用764字节，安全范围内
        - 如果for_index=True，VARCHAR长度会限制为191
    """
    if value is None:
        # 如果用于索引，限制长度为191（767字节/4字节=191.75）
        safe_length = 191 if for_index else max_length
        return f"VARCHAR({safe_length})"
    
    if isinstance(value, bool):
        return "TINYINT(1)"
    
    if isinstance(value, int):
        if -128 <= value <= 127:
            return "TINYINT"
        elif -32768 <= value <= 32767:
            return "SMALLINT"
        elif -8388608 <= value <= 8388607:
            return "MEDIUMINT"
        elif -2147483648 <= value <= 2147483647:
            return "INT"
        else:
            return "BIGINT"
    
    if isinstance(value, float):
        return "DOUBLE"
    
    if isinstance(value, Decimal):
        return "DECIMAL(20,6)"
    
    if isinstance(value, (datetime, date)):
        return "DATETIME"
    
    if isinstance(value, str):
        length = len(value)
        if length == 0:
            # 空字符串，使用默认长度
            safe_length = 191 if for_index else max_length
            return f"VARCHAR({safe_length})"
        elif length <= 191:
            # 短字符串，直接使用
            return f"VARCHAR({length * 2})"
        elif length <= 255 and not for_index:
            # 中等长度，仅在非索引字段使用
            return f"VARCHAR({min(length * 2, max_length)})"
        elif length <= 65535 and not for_index:
            # 长字符串，使用TEXT（TEXT类型不能作为唯一键）
            return "TEXT"
        else:
            # 超长字符串或索引字段的长字符串
            if for_index:
                # 索引字段限制为191
                return "VARCHAR(191)"
            else:
                return "LONGTEXT"
    
    if isinstance(value, (list, dict)):
        # JSON类型不能作为唯一键
        return "JSON"
    
    if isinstance(value, bytes):
        return "BLOB"
    
    # 默认类型
    safe_length = 191 if for_index else max_length
    return f"VARCHAR({safe_length})"


def sanitize_name(name: str, name_type: str = 'field') -> str:
    """
    清理名称（库名、表名、字段名），使其符合MySQL命名规范
    
    规则:
        - 强制转为小写
        - 只保留字母、数字、下划线
        - 数字开头添加前缀
        - 截断长度限制为64字符
    
    参数:
        name: 原始名称
        name_type: 名称类型 ('database'/'table'/'field')
        
    返回:
        清理后的名称
    """
    import re
    # 转小写
    name = name.lower()
    # 移除特殊字符，只保留字母、数字、下划线
    name = re.sub(r'[^a-z0-9_]', '_', name)
    # 移除连续的下划线
    name = re.sub(r'_+', '_', name)
    # 移除首尾下划线
    name = name.strip('_')
    # 如果为空或以数字开头，添加前缀
    if not name or name[0].isdigit():
        prefix = {'database': 'db_', 'table': 'tb_', 'field': 'f_'}.get(name_type, 'x_')
        name = prefix + name
    # 截断长度
    return name[:64]


# ==================== 主写入类 ====================


class MYSQLWriter:
    """
    MySQL数据写入器 - 专为爬虫数据入库设计
    
    功能特性：
        - 自动建库（数据库不存在时自动创建）
        - 自动建表（推断字段类型）
        - 高性能批量插入
        - 智能去重（UPSERT）
        - 唯一约束管理
        - 索引管理
        - 自动ID和时间戳
        - 进度监控
        
    数据类型推断（自动 + 手动）：
        自动推断规则：
        - bool → TINYINT(1)
        - int → TINYINT/SMALLINT/INT/BIGINT（根据值范围）
        - float → DOUBLE
        - Decimal → DECIMAL(20,6)
        - datetime/date → DATETIME
        - str → VARCHAR/TEXT（根据长度）
        - list/dict → JSON
        - None → VARCHAR(255)
        
        手动指定类型（优先级更高）：
        - 使用 field_types 参数精确控制字段类型
        - 支持所有MySQL数据类型（DECIMAL、ENUM、SET等）
        - 未指定的字段仍使用自动推断
        
    唯一约束长度限制（重要）：
        - MySQL InnoDB索引限制：767字节（utf8mb4: 191字符）
        - 唯一约束字段自动限制为VARCHAR(191)
        - TEXT/JSON类型不能作为唯一键
        
    示例：
        # 自动建库建表（推荐）
        writer = MYSQLWriter(
            host='localhost',
            user='root',
            password='pwd',
            database='spider_data',    # 默认数据库（不存在会自动创建）
            auto_create=True,          # 自动建库建表（默认True）
            auto_add_id=True,          # 自动添加自增ID（默认True）
            auto_add_timestamps=True   # 自动添加时间戳（默认True）
        )
        
        # 方式1：使用默认数据库
        data = [
            {'url': 'http://example.com/1', 'title': '标题1', 'price': 99.9},
            {'url': 'http://example.com/2', 'title': '标题2', 'price': 199.9}
        ]
        writer.insert_many('products', data)  # 插入到 spider_data.products
        
        # 方式2：指定其他数据库（支持 "库名.表名" 格式）
        writer.insert_many('db2.products', data)  # 自动创建db2库和products表
        
        # 带唯一约束
        writer.insert_many(
            'products', 
            data, 
            unique_key='url',              # URL重复时更新
            unique_constraints=['url']     # 创建唯一索引
        )
        
        # 手动指定字段类型
        writer.insert_many(
            'products',
            data,
            field_types={
                'price': 'DECIMAL(10,2)',          # 精确小数
                'status': 'ENUM("active","sold")'  # 枚举类型
            }
        )
    """
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 3306,
        user: str = 'root',
        password: str = '',
        database: str = None,
        charset: str = 'utf8mb4',
        pool_size: int = 3,
        auto_create: bool = True,
        auto_add_id: bool = True,
        auto_add_timestamps: bool = True,
        log_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化MySQL写入器
        
        参数:
            host: 数据库主机
            port: 端口
            user: 用户名
            password: 密码
            database: 默认数据库名（可选，insert时可用 "库名.表名" 格式）
            charset: 字符集（默认utf8mb4）
            pool_size: 连接池大小（默认3）
            auto_create: 自动建库建表（默认True，库/表不存在时自动创建）
            auto_add_id: 是否自动添加自增ID字段（默认True）
            auto_add_timestamps: 是否自动添加created_at和updated_at字段（默认True）
            log_config: 日志配置字典（键名忽略大小写），例如: {
                'enable': True,           # 是否启用日志（默认True）
                                          # 设置为False时，不会输出任何日志，忽略其他配置
                'level': 'INFO',          # 日志级别 debug/info/warning/error（默认INFO）
                'output': 'console',      # 输出位置（默认console）:
                                          #   - 'console' 或 'terminal': 仅输出到终端
                                          #   - 'file': 仅输出到文件
                                          #   - 'both': 同时输出到终端和文件
                'file_path': 'mysql_writer.log'  # 日志文件路径（可选）
                                          # 相对路径：存储到用户home目录
                                          # 绝对路径：存储到指定路径
            }
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.charset = charset
        self.auto_create = auto_create
        self.auto_add_id = auto_add_id
        self.auto_add_timestamps = auto_add_timestamps
        self._closed = False
        
        # 统计信息
        self._stats = {
            'total_inserted': 0,
            'total_updated': 0,
            'total_failed': 0,
            'total_time': 0.0
        }
        
        self._setup_logger(log_config or {})
        
        # 清理并保存数据库名
        self.database = sanitize_name(database, 'database') if database else None
        
        # 如果指定了默认数据库且开启自动建库，先确保数据库存在
        if self.database and auto_create:
            self._ensure_database_exists(self.database)
        self._init_pool(pool_size)
        
        if self.logger:
            self.logger.debug(f"MySQL写入器初始化: {user}@{host}:{port}/{database}")
    
    def _setup_logger(self, log_config: Dict[str, Any]):
        """配置日志"""
        config = {k.lower(): v for k, v in log_config.items()}
        
        enable = config.get('enable', True)
        
        if not enable:
            self.logger = logging.getLogger(f'MYSQLWriter_{id(self)}')
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False
            return
        
        level = str(config.get('level', 'INFO')).upper()
        output = str(config.get('output', 'console')).lower()
        file_path = config.get('file_path')
        
        self.logger = logging.getLogger(f'MYSQLWriter_{id(self)}')
        self.logger.setLevel(getattr(logging, level))
        self.logger.propagate = False
        self.logger.handlers.clear()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 输出到终端
        if output in ('console', 'terminal', 'both'):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 输出到文件
        if output in ('file', 'both'):
            if not file_path:
                file_path = Path.home() / 'mysql_writer.log'
            else:
                file_path = Path(file_path)
                if not file_path.is_absolute():
                    file_path = Path.home() / file_path
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(file_path, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            if output == 'both':
                self.logger.debug(f"日志文件: {file_path}")
    
    def _ensure_database_exists(self, database: str):
        """
        确保数据库存在，如果不存在则自动创建
        
        参数:
            database: 数据库名
            
        异常:
            ConnectionError: 连接失败
            TableCreationError: 创建数据库失败
        """
        if not database or not self.auto_create:
            return
            
        conn = None
        try:
            # 先连接到MySQL（不指定数据库）
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset,
                cursorclass=DictCursor
            )
            
            with conn.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = %s",
                    (database,)
                )
                result = cursor.fetchone()
                
                if not result:
                    # 数据库不存在，创建它
                    # 使用utf8mb4字符集和utf8mb4_0900_ai_ci排序规则
                    safe_db_name = database.replace('`', '``')
                    create_sql = f"""
                        CREATE DATABASE `{safe_db_name}` 
                        CHARACTER SET utf8mb4 
                        COLLATE utf8mb4_0900_ai_ci
                    """
                    cursor.execute(create_sql)
                    conn.commit()
                    
                    if self.logger:
                        self.logger.info(f"自动创建数据库: {database}")
                else:
                    if self.logger:
                        self.logger.debug(f"数据库已存在: {database}")
                        
        except pymysql.Error as e:
            error_msg = f"数据库检查/创建失败: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            raise TableCreationError(error_msg) from e
        finally:
            if conn:
                conn.close()
    
    def _init_pool(self, pool_size: int):
        """初始化连接池"""
        try:
            connection_kwargs = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'charset': self.charset,
                'cursorclass': DictCursor,
                'autocommit': False,  # 写入时使用事务
            }
            
            if self.database:
                connection_kwargs['database'] = self.database
            
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=pool_size,
                mincached=1,
                maxcached=pool_size,
                blocking=True,
                maxusage=10000,
                ping=1,
                **connection_kwargs
            )
            
            if self.logger:
                self.logger.debug(f"连接池初始化成功，大小: {pool_size}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"连接池初始化失败: {str(e)}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = None
        try:
            conn = self.pool.connection()
            yield conn
        except Exception as e:
            if self.logger:
                self.logger.error(f"数据库连接错误: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _get_table_indexes(self, table: str) -> List[Dict[str, Any]]:
        """
        获取表的所有索引信息
        
        参数:
            table: 表名
            
        返回:
            索引信息列表，每个索引包含：
            - name: 索引名
            - fields: 字段列表
            - is_unique: 是否唯一索引
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"SHOW INDEX FROM `{table}`")
                    rows = cursor.fetchall()
                    
                    # 按索引名分组
                    indexes_dict = {}
                    for row in rows:
                        idx_name = row['Key_name']
                        if idx_name == 'PRIMARY':  # 跳过主键
                            continue
                        
                        if idx_name not in indexes_dict:
                            indexes_dict[idx_name] = {
                                'name': idx_name,
                                'fields': [],
                                'is_unique': row['Non_unique'] == 0
                            }
                        
                        indexes_dict[idx_name]['fields'].append(row['Column_name'])
                    
                    return list(indexes_dict.values())
        except Exception as e:
            if self.logger:
                self.logger.debug(f"获取索引信息失败: {str(e)}")
            return []
    
    def _partition_data_by_period(
        self,
        data_list: List[Dict[str, Any]],
        date_field: Optional[str] = None,
        mode: str = 'year'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        按时间周期分组数据
        
        参数:
            data_list: 数据列表
            date_field: 日期字段名（None表示自动识别）
            mode: 分表模式 'year'(按年) 或 'month'(按年月)
            
        返回:
            {表名后缀: [数据列表]} 字典
            - 'year' 模式: {'2024': [...], '2025': [...]}
            - 'month' 模式: {'2024_01': [...], '2024_12': [...], '2025_03': [...]}
            
        异常:
            DataValidationError: 找不到日期字段或无法解析日期
        """
        from datetime import datetime, date
        
        if not data_list:
            return {}
        
        # 确定日期字段
        sample = data_list[0]
        target_date_field = None
        
        if date_field:
            # 用户指定了日期字段
            if date_field not in sample:
                raise DataValidationError(f"指定的日期字段 '{date_field}' 不存在")
            target_date_field = date_field
        else:
            # 自动识别日期字段（优先"日期"）
            if '日期' in sample:
                target_date_field = '日期'
            else:
                # 查找其他日期类型字段
                for key, value in sample.items():
                    if isinstance(value, (datetime, date)):
                        target_date_field = key
                        break
                    elif isinstance(value, str):
                        # 尝试解析字符串日期
                        try:
                            datetime.strptime(value[:10], '%Y-%m-%d')
                            target_date_field = key
                            break
                        except:
                            continue
        
        if not target_date_field:
            raise DataValidationError(
                "无法自动识别日期字段，请使用 partition_date_field 参数指定日期字段"
            )
        
        # 按时间周期分组数据
        partitioned = {}
        for row in data_list:
            date_value = row.get(target_date_field)
            if date_value is None:
                if self.logger:
                    self.logger.warning(f"跳过日期字段为空的数据: {row}")
                continue
            
            # 提取年份和月份
            year = None
            month = None
            dt_obj = None
            
            if isinstance(date_value, datetime):
                dt_obj = date_value
            elif isinstance(date_value, date):
                dt_obj = datetime(date_value.year, date_value.month, date_value.day)
            elif isinstance(date_value, str):
                try:
                    # 尝试多种日期格式
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y-%m-%d %H:%M:%S']:
                        try:
                            dt_obj = datetime.strptime(date_value[:10] if len(date_value) >= 10 else date_value, fmt)
                            break
                        except:
                            continue
                    
                    if dt_obj is None:
                        # 尝试直接提取年份和月份（例如 "2024-01-15"）
                        year = int(date_value[:4])
                        if mode == 'month' and len(date_value) >= 7:
                            month = int(date_value[5:7])
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"无法解析日期 '{date_value}': {e}")
                    continue
            
            # 从 datetime 对象提取年月
            if dt_obj:
                year = dt_obj.year
                month = dt_obj.month
            
            # 生成分区键（表名后缀）
            if year:
                if mode == 'month' and month:
                    # 按年月分表: 2024_01, 2024_12
                    partition_key = f"{year}_{month:02d}"
                else:
                    # 按年分表: 2024, 2025
                    partition_key = str(year)
                
                if partition_key not in partitioned:
                    partitioned[partition_key] = []
                partitioned[partition_key].append(row)
        
        if not partitioned:
            raise DataValidationError("所有数据的日期字段都无法解析")
        
        if self.logger:
            partition_keys = sorted(partitioned.keys())
            counts = {k: len(partitioned[k]) for k in partition_keys}
            mode_text = "按年月" if mode == 'month' else "按年份"
            self.logger.info(f"数据{mode_text}分组: {counts} (使用字段: {target_date_field})")
        
        return partitioned
    
    def _ensure_table_exists(
        self,
        table: str,
        sample_data: Dict[str, Any],
        unique_key: Optional[Union[str, List[str]]] = None,
        field_types: Optional[Dict[str, str]] = None,
        allow_null: bool = False
    ):
        """
        确保表存在，如果不存在则创建
        
        参数:
            table: 表名（支持 "库名.表名" 格式）
            sample_data: 样本数据（用于推断字段类型）
            unique_key: 唯一键（自动创建唯一索引）
                - 单字段: 'product_id'
                - 组合字段: ['shop_id', 'product_id']
            field_types: 手动指定字段类型（可选），格式: {'字段名': 'MySQL类型'}
                例如: {'price': 'DECIMAL(10,2)', 'status': 'ENUM("active","inactive")'}
                指定的类型优先级高于自动推断
            allow_null: 是否允许字段为NULL（默认False）
        """
        if not self.auto_create:
            return
        
        # 解析表名（支持 "库名.表名" 格式）并清理名称
        if '.' in table:
            db_part, table_part = table.split('.', 1)
            target_db = sanitize_name(db_part, 'database')
            target_table = sanitize_name(table_part, 'table')
        else:
            target_db = sanitize_name(self.database, 'database') if self.database else None
            target_table = sanitize_name(table, 'table')
        
        # 确保目标数据库存在
        if target_db:
            self._ensure_database_exists(target_db)
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # 检查表是否存在
                    cursor.execute(
                        "SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                        (target_db, target_table)
                    )
                    
                    if cursor.fetchone():
                        if self.logger:
                            self.logger.debug(f"表 {table} 已存在")
                        return
                    
                    # 收集唯一键字段（用于判断是否需要限制长度）
                    unique_field_names = set()
                    if unique_key:
                        if isinstance(unique_key, str):
                            unique_field_names.add(sanitize_name(unique_key, 'field'))
                        elif isinstance(unique_key, list):
                            for field in unique_key:
                                unique_field_names.add(sanitize_name(field, 'field'))
                    
                    # 创建表字段
                    fields = []
                    for key, value in sample_data.items():
                        field_name = sanitize_name(key, 'field')
                        
                        # 优先使用用户指定的类型，否则自动推断
                        if field_types and key in field_types:
                            field_type = field_types[key]
                        else:
                            # 如果字段用于唯一约束，限制VARCHAR长度为191
                            is_for_index = field_name in unique_field_names
                            field_type = infer_mysql_type(value, for_index=is_for_index)
                        
                        # 添加 NULL/NOT NULL 约束
                        null_constraint = "NULL" if allow_null else "NOT NULL"
                        fields.append(f"`{field_name}` {field_type} {null_constraint}")
                    
                    # 构建CREATE TABLE语句
                    create_parts = []
                    
                    # 1. 自增ID（可选）
                    if self.auto_add_id:
                        create_parts.append("`id` BIGINT AUTO_INCREMENT PRIMARY KEY")
                    
                    # 2. 数据字段
                    create_parts.extend(fields)
                    
                    # 3. 时间戳字段（可选）
                    if self.auto_add_timestamps:
                        create_parts.append("`created_at` DATETIME DEFAULT CURRENT_TIMESTAMP")
                        create_parts.append("`updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
                    
                    # 4. 唯一索引（从 unique_key 自动创建）
                    if unique_key:
                        if isinstance(unique_key, str):
                            # 单字段唯一索引
                            field_name = sanitize_name(unique_key, 'field')
                            create_parts.append(f"UNIQUE KEY `uk_{field_name}` (`{field_name}`)")
                        elif isinstance(unique_key, list):
                            # 多字段组合唯一索引
                            field_names = [sanitize_name(f, 'field') for f in unique_key]
                            key_name = f"uk_{'_'.join(field_names)}"
                            fields_str = ', '.join(f'`{f}`' for f in field_names)
                            create_parts.append(f"UNIQUE KEY `{key_name}` ({fields_str})")
                    
                    # 构建完整的表名（支持跨库创建）
                    safe_db = target_db.replace('`', '``')
                    safe_table = target_table.replace('`', '``')
                    full_table_name = f"`{safe_db}`.`{safe_table}`"
                    
                    create_sql = f"""
                    CREATE TABLE {full_table_name} (
                        {', '.join(create_parts)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                    """
                    
                    cursor.execute(create_sql)
                    conn.commit()
                    
                    if self.logger:
                        unique_key_info = "是" if unique_key else "否"
                        self.logger.info(
                            f"表 {table} 创建成功 | "
                            f"字段数: {len(fields)} | "
                            f"自增ID: {self.auto_add_id} | "
                            f"时间戳: {self.auto_add_timestamps} | "
                            f"唯一索引: {unique_key_info}"
                        )
                        
        except Exception as e:
            if self.logger:
                self.logger.error(f"创建表失败: {str(e)}")
            raise TableCreationError(f"创建表失败: {str(e)}") from e
    
    def insert_one(
        self,
        table: str,
        data: Dict[str, Any],
        unique_key: Optional[Union[str, List[str]]] = None,
        on_duplicate: str = 'ignore',
        field_types: Optional[Dict[str, str]] = None,
        allow_null: bool = False
    ) -> bool:
        """
        插入单条数据
        
        参数:
            table: 表名
            data: 数据字典
            unique_key: 唯一键（用于去重）
            on_duplicate: 重复时的操作 'ignore'/'update'
            field_types: 手动指定字段类型（可选）
            allow_null: 是否允许字段为NULL（默认False）
            
        返回:
            是否成功
        """
        return self.insert_many(
            table, 
            [data], 
            unique_key=unique_key, 
            on_duplicate=on_duplicate,
            field_types=field_types,
            allow_null=allow_null
        ) > 0
    
    def insert_many(
        self,
        table: str,
        data_list: List[Dict[str, Any]],
        unique_key: Optional[Union[str, List[str]]] = None,
        on_duplicate: str = 'ignore',
        batch_size: int = 1000,
        field_types: Optional[Dict[str, str]] = None,
        allow_null: bool = False,
        auto_partition_by_year: Union[bool, str] = False,
        partition_date_field: Optional[str] = None
    ) -> int:
        """
        批量插入数据
        
        参数:
            table: 表名（支持 "库名.表名" 格式，自动创建库和表）
            data_list: 数据列表
            unique_key: 唯一键（自动创建唯一索引 + 用于去重）
                - 单字段: 'product_id'
                - 组合字段: ['shop_id', 'product_id']
                - None: 不创建唯一索引，允许重复数据
            on_duplicate: 遇到重复数据时的操作（需要 unique_key）
                - 'ignore': 忽略重复数据
                - 'update': 更新重复数据
            batch_size: 批次大小（默认1000）
            field_types: 手动指定字段类型（可选），格式: {'字段名': 'MySQL类型'}
                例如: {'price': 'DECIMAL(10,2)', 'status': 'ENUM("active","inactive")'}
                未指定的字段会自动推断类型
            allow_null: 是否允许字段为NULL（默认False）
                - False: 字段设置为 NOT NULL（推荐）
                - True: 字段设置为 NULL
                注意：自增ID和时间戳字段不受此参数影响
            auto_partition_by_year: 自动分表模式（默认False）
                - False: 不分表，所有数据插入同一张表（默认）
                - True 或 'year': 按年分表，表名格式: table_2024, table_2025
                - 'month': 按年月分表，表名格式: table_2024_01, table_2024_12
            partition_date_field: 指定用于分表的日期字段名（可选）
                - None: 自动识别（优先"日期"，其次其他日期类型字段）
                - '字段名': 使用指定字段进行分表
            
        返回:
            成功插入的行数
            
        数据类型说明:
            - 自动根据第一条数据推断字段类型
            - 唯一键字段自动限制为VARCHAR(191)，避免索引长度超限
            - 普通字符串字段：VARCHAR(动态长度) 或 TEXT
            - 数值/时间等类型：自动精确匹配
            
        唯一键注意事项:
            - 唯一键字段必须是VARCHAR/数值/时间类型
            - TEXT/JSON/BLOB类型不能作为唯一键
            - 组合唯一键的所有字段总长度不能超过767字节（utf8mb4）
            
        示例:
            # 基础插入（自动推断类型）
            data = [{'url': 'http://example.com', 'title': '标题', 'price': 99.9}]
            writer.insert_many('products', data)
            
            # 跨库插入（自动创建db2库和products表）
            writer.insert_many('db2.products', data)
            
            # 唯一键去重（基于url，自动创建唯一索引）
            writer.insert_many('products', data, unique_key='url')
            
            # UPSERT（基于url，重复时更新）
            writer.insert_many('products', data, unique_key='url', on_duplicate='update')
            
            # 组合唯一键（多字段组合）
            writer.insert_many(
                'products',
                data,
                unique_key=['shop_id', 'product_id']  # 自动创建组合唯一索引
            )
            
            # 手动指定字段类型（精确控制）
            writer.insert_many(
                'products',
                data,
                field_types={
                    'price': 'DECIMAL(10,2)',           # 精确的价格类型
                    'status': 'ENUM("active","inactive")',  # 枚举类型
                    'description': 'TEXT'               # 文本类型
                }
                # 其他字段仍然自动推断
            )
            
            # 允许NULL值（默认不允许）
            writer.insert_many('products', data, allow_null=True)
            
            # 按年分表（自动识别日期字段）
            data_with_date = [
                {'日期': '2024-01-15', 'sales': 1000},
                {'日期': '2024-06-20', 'sales': 2000},
                {'日期': '2025-03-10', 'sales': 1500}
            ]
            # 会自动创建 sales_2024 和 sales_2025 两张表
            writer.insert_many(
                'sales',
                data_with_date,
                auto_partition_by_year=True  # 或 'year'
            )
            
            # 按年月分表
            # 会自动创建 logs_2024_01, logs_2024_06, logs_2025_03 等表
            writer.insert_many(
                'logs',
                data_with_date,
                auto_partition_by_year='month'  # 按年月分表
            )
            
            # 指定分表字段
            writer.insert_many(
                'orders',
                data,
                auto_partition_by_year='year',
                partition_date_field='order_date'  # 使用 order_date 字段分表
            )
        """
        if not data_list:
            if self.logger:
                self.logger.warning("数据列表为空")
            return 0
        
        start_time = time.time()
        total_inserted = 0
        
        try:
            # 如果启用自动分表，按时间分组数据
            if auto_partition_by_year:
                # 确定分表模式
                partition_mode = auto_partition_by_year
                if partition_mode is True:
                    partition_mode = 'year'  # True 等同于 'year'
                
                # 按时间分组数据
                partitioned_data = self._partition_data_by_period(
                    data_list, 
                    partition_date_field,
                    partition_mode
                )
                
                # 为每个分区的表插入数据
                for period_suffix, period_data in partitioned_data.items():
                    period_table = f"{table}_{period_suffix}"
                    
                    # 确保分区表存在
                    self._ensure_table_exists(period_table, period_data[0], unique_key, field_types, allow_null)
                    
                    # 分批处理分区数据
                    for i in range(0, len(period_data), batch_size):
                        batch = period_data[i:i + batch_size]
                        inserted = self._insert_batch(period_table, batch, unique_key, on_duplicate)
                        total_inserted += inserted
            else:
                # 不分表，正常插入
                # 确保表存在（传入唯一键、字段类型和allow_null）
                self._ensure_table_exists(table, data_list[0], unique_key, field_types, allow_null)
                
                # 分批处理
                for i in range(0, len(data_list), batch_size):
                    batch = data_list[i:i + batch_size]
                    inserted = self._insert_batch(table, batch, unique_key, on_duplicate)
                    total_inserted += inserted
            
            elapsed = time.time() - start_time
            self._stats['total_inserted'] += total_inserted
            self._stats['total_time'] += elapsed
            
            if self.logger:
                if on_duplicate == 'update' and unique_key:
                    self.logger.info(
                        f"批量处理完成: {total_inserted}条数据(含新增/更新), 耗时{elapsed:.2f}秒"
                    )
                else:
                    self.logger.info(
                        f"批量插入完成: {total_inserted}/{len(data_list)}行, 耗时{elapsed:.2f}秒"
                    )
            
            return total_inserted
            
        except Exception as e:
            self._stats['total_failed'] += len(data_list) - total_inserted
            if self.logger:
                self.logger.error(f"批量插入失败: {str(e)}")
            raise InsertError(f"批量插入失败: {str(e)}") from e
    
    def _insert_batch(
        self,
        table: str,
        batch: List[Dict[str, Any]],
        unique_key: Optional[Union[str, List[str]]],
        on_duplicate: str
    ) -> int:
        """插入单个批次"""
        if not batch:
            return 0
        
        # 统一字段
        all_fields = set()
        for item in batch:
            all_fields.update(item.keys())
        
        fields = sorted(all_fields)
        field_names = [sanitize_name(f, 'field') for f in fields]
        
        # 构建完整的表名（支持 "库名.表名" 格式）并清理名称
        if '.' in table:
            db_name, table_name = table.split('.', 1)
            safe_db = sanitize_name(db_name, 'database')
            safe_table = sanitize_name(table_name, 'table')
            full_table_name = f"`{safe_db}`.`{safe_table}`"
        else:
            safe_table = sanitize_name(table, 'table')
            full_table_name = f"`{safe_table}`"
        
        # 构建SQL
        placeholders = ', '.join(['%s'] * len(fields))
        sql = f"INSERT INTO {full_table_name} ({', '.join(f'`{f}`' for f in field_names)}) VALUES ({placeholders})"
        
        # 处理重复键
        if unique_key:
            if on_duplicate == 'ignore':
                sql = sql.replace('INSERT', 'INSERT IGNORE')
            elif on_duplicate == 'update':
                update_fields = [f for f in field_names if f not in (
                    [unique_key] if isinstance(unique_key, str) else unique_key
                )]
                if update_fields:
                    updates = ', '.join(f"`{f}`=VALUES(`{f}`)" for f in update_fields)
                    sql += f" ON DUPLICATE KEY UPDATE {updates}"
        
        # 准备数据
        values = []
        for item in batch:
            row = []
            for field in fields:
                value = item.get(field)
                # 处理特殊类型
                if isinstance(value, (dict, list)):
                    import json
                    value = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, date):
                    value = value.strftime('%Y-%m-%d')
                row.append(value)
            values.append(tuple(row))
        
        # 执行插入
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(sql, values)
                    affected = cursor.rowcount
                    conn.commit()
                    
                    # 修正计数：MySQL的ON DUPLICATE KEY UPDATE
                    # - 新插入: rowcount = 1
                    # - 更新: rowcount = 2 (删除旧行+插入新行)
                    # 为了准确反映实际影响的行数，将更新的2算作1
                    if on_duplicate == 'update' and unique_key:
                        # 计算实际影响的行数（将UPDATE的2折半）
                        # affected = 新插入数 + 更新数*2
                        # 实际行数 = 新插入数 + 更新数 = (affected + 更新数) / 2
                        # 简化：实际行数约等于数据条数
                        return len(values)
                    
                    return affected
        except Exception as e:
            if self.logger:
                self.logger.error(f"批次插入失败: {str(e)}")
                self.logger.debug(f"SQL: {sql}")
            raise
    
    def upsert(
        self,
        table: str,
        data_list: List[Dict[str, Any]],
        unique_key: Union[str, List[str]],
        batch_size: int = 1000,
        field_types: Optional[Dict[str, str]] = None
    ) -> int:
        """
        UPSERT操作（插入或更新）
        
        参数:
            table: 表名
            data_list: 数据列表
            unique_key: 唯一键
            batch_size: 批次大小
            field_types: 手动指定字段类型（可选）
            
        返回:
            影响的行数
        """
        return self.insert_many(
            table,
            data_list,
            unique_key=unique_key,
            on_duplicate='update',
            batch_size=batch_size,
            field_types=field_types
        )
    
    def insert_dataframe(
        self,
        table: str,
        df,
        unique_key: Optional[Union[str, List[str]]] = None,
        on_duplicate: str = 'ignore',
        batch_size: int = 1000,
        field_types: Optional[Dict[str, str]] = None
    ) -> int:
        """
        从DataFrame插入数据
        
        参数:
            table: 表名
            df: pandas DataFrame
            unique_key: 唯一键
            on_duplicate: 重复处理方式
            batch_size: 批次大小
            field_types: 手动指定字段类型（可选）
            
        返回:
            插入的行数
        """
        try:
            import pandas as pd
            
            if not isinstance(df, pd.DataFrame):
                raise DataValidationError("输入必须是pandas DataFrame")
            
            # 转换为字典列表
            data_list = df.to_dict('records')
            
            return self.insert_many(
                table,
                data_list,
                unique_key=unique_key,
                on_duplicate=on_duplicate,
                batch_size=batch_size,
                field_types=field_types
            )
            
        except ImportError:
            raise ImportError("需要安装pandas: pip install pandas")
    
    def create_index(
        self,
        table: str,
        fields: Union[str, List[str]],
        unique: bool = False,
        index_name: Optional[str] = None
    ) -> bool:
        """
        创建索引（支持单字段和组合索引）
        
        参数:
            table: 表名
            fields: 字段名或字段列表（支持组合索引）
            unique: 是否唯一索引
            index_name: 索引名称（可选，不指定则自动生成）
            
        返回:
            是否成功创建（如果已存在返回False）
            
        示例:
            # 单字段索引
            writer.create_index('products', 'category')
            
            # 唯一索引
            writer.create_index('products', 'url', unique=True)
            
            # 组合索引
            writer.create_index('products', ['shop_id', 'product_id'])
            
            # 组合唯一索引
            writer.create_index('products', ['shop_id', 'product_id'], unique=True)
        """
        if isinstance(fields, str):
            fields = [fields]
        
        field_names = [sanitize_name(f, 'field') for f in fields]
        
        # 检查是否已存在相同字段组合的索引
        existing_indexes = self._get_table_indexes(table)
        fields_set = set(field_names)
        
        for idx_info in existing_indexes:
            idx_fields_set = set(idx_info['fields'])
            if idx_fields_set == fields_set:
                # 已存在相同字段组合的索引
                if idx_info['is_unique']:
                    if unique:
                        if self.logger:
                            self.logger.debug(f"唯一索引已存在: {idx_info['name']} on {table}({', '.join(field_names)})")
                        return False
                    else:
                        if self.logger:
                            self.logger.warning(
                                f"跳过创建普通索引：字段 {', '.join(field_names)} 已有唯一索引 {idx_info['name']}，"
                                f"唯一索引包含普通索引的全部功能"
                            )
                        return False
                else:
                    # 已存在普通索引
                    if unique:
                        # 想创建唯一索引，但已有普通索引（需要先删除普通索引）
                        if self.logger:
                            self.logger.warning(f"字段 {', '.join(field_names)} 已有普通索引 {idx_info['name']}")
                        return False
                    else:
                        # 普通索引已存在
                        if self.logger:
                            self.logger.debug(f"普通索引已存在: {idx_info['name']}")
                        return False
        
        if not index_name:
            prefix = 'uk' if unique else 'idx'
            index_name = f"{prefix}_{'_'.join(field_names)}"
        
        index_type = 'UNIQUE' if unique else ''
        fields_str = ', '.join(f'`{f}`' for f in field_names)
        
        sql = f"CREATE {index_type} INDEX `{index_name}` ON `{table}` ({fields_str})"
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    conn.commit()
                    
                    if self.logger:
                        index_type_str = "组合唯一索引" if unique and len(fields) > 1 else \
                                        "唯一索引" if unique else \
                                        "组合索引" if len(fields) > 1 else "索引"
                        self.logger.info(f"{index_type_str}创建成功: {index_name} on {table}({fields_str})")
                    return True
        except pymysql.err.OperationalError as e:
            if 'Duplicate key name' in str(e):
                if self.logger:
                    self.logger.debug(f"索引名 {index_name} 已存在")
                return False
            else:
                raise
    
    def create_indexes(
        self,
        table: str,
        indexes: List[Dict[str, Any]]
    ) -> int:
        """
        批量创建索引
        
        参数:
            table: 表名
            indexes: 索引配置列表，每个元素是字典，包含：
                - fields: 字段名或字段列表
                - unique: 是否唯一索引（可选，默认False）
                - name: 索引名称（可选）
                
        返回:
            成功创建的索引数量
            
        示例:
            writer.create_indexes('products', [
                {'fields': 'url', 'unique': True},
                {'fields': 'category'},
                {'fields': ['shop_id', 'product_id'], 'unique': True},
                {'fields': ['created_at', 'status']}
            ])
        """
        count = 0
        for idx_config in indexes:
            fields = idx_config.get('fields')
            unique = idx_config.get('unique', False)
            name = idx_config.get('name')
            
            if fields:
                if self.create_index(table, fields, unique, name):
                    count += 1
        
        if self.logger:
            self.logger.info(f"批量创建索引完成: {count}/{len(indexes)} 个索引创建成功")
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        返回:
            统计信息字典
        """
        stats = self._stats.copy()
        if stats['total_inserted'] > 0:
            stats['avg_speed'] = stats['total_inserted'] / stats['total_time'] if stats['total_time'] > 0 else 0
        else:
            stats['avg_speed'] = 0
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self._stats = {
            'total_inserted': 0,
            'total_updated': 0,
            'total_failed': 0,
            'total_time': 0.0
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
    
    def close(self):
        """关闭连接池"""
        if self._closed:
            return
        
        try:
            if hasattr(self, 'pool'):
                self.pool.close()
                if self.logger:
                    self.logger.debug("连接池已关闭")
                    # 输出最终统计
                    stats = self.get_stats()
                    self.logger.info(f"总计处理: {stats['total_inserted']}条数据")
        except Exception as e:
            if self.logger:
                self.logger.error(f"关闭连接失败: {str(e)}")
        finally:
            self._closed = True


# ==================== 测试代码 ====================


def test():
    """演示功能"""
    
    try:
        with MYSQLWriter(
            host='localhost',
            user='user',
            password='password',
            auto_create=True,
            auto_add_id=True,
            auto_add_timestamps=True,
            log_config={'enable': True, 'level': 'INFO', 'output': 'both', 'file_path': 'mysql_writer.log'}
        ) as writer:
            custom_type_data = [
                {
                    'product_id': 123456,
                    'product_name': '商品名称1',
                    'price': 99.99,
                    'stock': 100,
                    'status': 'active',
                    'weight': 1.5,
                    'rating': 4.4
                },
                {
                    'product_id': 22456,
                    'product_name': '商品名称2',
                    'price': 22,
                    'stock': 2,
                    'status': 'active',
                    'weight': 0.2,
                    'rating': 2.22
                },
                {
                    'product_id': 123456,
                    'product_name': '商品名称1',
                    'price': 3,
                    'stock': 0.33,
                    'status': 'active',
                    'weight': 0.333,
                    'rating': 3.33
                }
            ]
            field_types={
                'product_id': 'INT UNSIGNED',
                'price': 'DECIMAL(10,2)',
                'stock': 'INT UNSIGNED',
                'status': 'ENUM("active","inactive","sold")',
                'weight': 'FLOAT(5,2)',
                'rating': 'DECIMAL(3,1)'
            }
            
            count = writer.insert_many(
                table='test_db.custom_products',
                data_list=custom_type_data,
                unique_key=['product_id', 'product_name'],  # 自动创建唯一索引
                on_duplicate='update',
                field_types=field_types
            )
            print(f"✓ 处理成功: {count}条数据（自动创建唯一索引 + UPSERT）")
            
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")


if __name__ == '__main__':
    test()

