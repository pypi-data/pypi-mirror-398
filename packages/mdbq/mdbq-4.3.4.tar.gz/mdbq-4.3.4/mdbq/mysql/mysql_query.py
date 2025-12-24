#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据查询、导出、表结构获取等功能

功能特性：
- 连接池管理，高性能
- SSL安全连接支持
- SQL注入防护
- 灵活的日志管理（控制台/文件/禁用）
- 自动资源管理，防止内存泄漏
- 支持with上下文管理器
- 多种数据格式导出（字典、DataFrame、JSON、CSV、Excel）
- 表结构和信息查询

依赖：
    pip install pymysql DBUtils pandas openpyxl

"""

import json
import logging
import re
import time
import weakref
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple, TypedDict, Literal
from datetime import datetime
from contextlib import contextmanager
from functools import wraps
import pymysql
from pymysql.cursors import DictCursor
from dbutils.pooled_db import PooledDB


# ==================== 自定义异常类 ====================


class MySQLQueryError(Exception):
    """MySQL查询异常基类"""
    pass


class ConnectionError(MySQLQueryError):
    """数据库连接错误"""
    pass


class QueryError(MySQLQueryError):
    """查询执行错误"""
    pass


class ValidationError(MySQLQueryError):
    """参数验证错误"""
    pass


class TransactionError(MySQLQueryError):
    """事务处理错误"""
    pass


# ==================== 类型定义 ====================


class TableInfo(TypedDict, total=False):
    """表信息类型定义"""
    table_name: str
    engine: str
    row_count: int
    avg_row_length: int
    data_length: int
    index_length: int
    auto_increment: Optional[int]
    create_time: Optional[datetime]
    update_time: Optional[datetime]
    collation: str
    comment: str


class FieldInfo(TypedDict):
    """字段信息类型定义"""
    Field: str
    Type: str
    Null: str
    Key: str
    Default: Optional[str]
    Extra: str


# ==================== 工具函数 ====================


def validate_identifier(name: str, type_: str = "标识符") -> str:
    """
    验证数据库标识符（表名、库名、字段名等）
    
    参数:
        name: 标识符名称
        type_: 标识符类型（用于错误提示）
        
    返回:
        验证通过的标识符
        
    异常:
        ValidationError: 标识符格式不合法
    """
    if not name:
        raise ValidationError(f"{type_}不能为空")
    
    # 允许：字母、数字、下划线、中文、点号（用于database.table格式）
    if not re.match(r'^[\w\u4e00-\u9fa5.]+$', name):
        raise ValidationError(f"非法的{type_}名称: {name}，只允许字母、数字、下划线和中文")
    
    # 检查长度
    if len(name) > 64:
        raise ValidationError(f"{type_}名称过长（最大64字符）: {name}")
    
    return name


def mask_password(password: str) -> str:
    """
    脱敏密码用于日志显示
    
    参数:
        password: 原始密码
        
    返回:
        脱敏后的密码
    """
    if not password:
        return ''
    if len(password) <= 2:
        return '*' * len(password)
    return password[0] + '*' * (len(password) - 2) + password[-1]


def escape_identifier(identifier: str) -> str:
    """
    转义SQL标识符（反引号转义）
    
    参数:
        identifier: 标识符
        
    返回:
        转义后的标识符
    """
    return identifier.replace('`', '``')


# ==================== 装饰器 ====================


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    查询失败自动重试装饰器
    
    参数:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间倍增系数
        
    示例:
        @retry_on_failure(max_retries=3, delay=1, backoff=2)
        def query():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except (pymysql.OperationalError, pymysql.InterfaceError) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.error(f"重试{max_retries}次后仍然失败: {str(e)}")
                        raise QueryError(f"查询失败（已重试{max_retries}次）: {str(e)}") from e
                    
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.warning(f"查询失败，{current_delay}秒后重试 (第{attempt + 1}/{max_retries}次): {str(e)}")
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
                except Exception as e:
                    # 其他异常不重试
                    raise QueryError(f"查询失败: {str(e)}") from e
            
            # 理论上不会到达这里
            if last_exception:
                raise QueryError(f"查询失败: {str(last_exception)}") from last_exception
                
        return wrapper
    return decorator


# ==================== 查询构建器 ====================


class QueryBuilder:
    """
    链式查询构建器
    
    功能:
        - 链式调用构建SQL
        - 自动参数化防止注入
        - 支持常见的查询操作
        
    示例:
        builder = QueryBuilder(db)
        result = (builder
            .table('users')
            .select('id', 'name', 'email')
            .where('age > %s', 18)
            .where('status = %s', 'active')
            .order_by('created_at DESC')
            .limit(10)
            .execute())
    """
    
    def __init__(self, db: 'MYSQLQuery'):
        """
        初始化查询构建器
        
        参数:
            db: MYSQLQuery实例
        """
        self.db = db
        self._table: Optional[str] = None
        self._database: Optional[str] = None
        self._fields: List[str] = ['*']
        self._where_conditions: List[str] = []
        self._where_params: List[Any] = []
        self._order_by: Optional[str] = None
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
    
    def table(self, name: str, database: Optional[str] = None) -> 'QueryBuilder':
        """
        设置查询表名
        
        参数:
            name: 表名
            database: 数据库名（可选）
            
        返回:
            self（支持链式调用）
        """
        self._table = validate_identifier(name, "表名")
        if database:
            self._database = validate_identifier(database, "数据库名")
        return self
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """
        设置查询字段
        
        参数:
            fields: 字段名列表
            
        返回:
            self（支持链式调用）
        """
        if fields:
            self._fields = [validate_identifier(f, "字段名") for f in fields]
        return self
    
    def where(self, condition: str, *params) -> 'QueryBuilder':
        """
        添加WHERE条件
        
        参数:
            condition: 条件表达式（使用%s作为占位符）
            params: 参数值
            
        返回:
            self（支持链式调用）
        """
        self._where_conditions.append(condition)
        self._where_params.extend(params)
        return self
    
    def order_by(self, order: str) -> 'QueryBuilder':
        """
        设置排序
        
        参数:
            order: 排序表达式（例如: "id DESC" 或 "name ASC, created_at DESC"）
            
        返回:
            self（支持链式调用）
        """
        self._order_by = order
        return self
    
    def limit(self, limit: int) -> 'QueryBuilder':
        """
        设置返回数量限制
        
        参数:
            limit: 限制数量
            
        返回:
            self（支持链式调用）
        """
        if limit < 0:
            raise ValidationError("limit必须大于等于0")
        self._limit_value = limit
        return self
    
    def offset(self, offset: int) -> 'QueryBuilder':
        """
        设置偏移量
        
        参数:
            offset: 偏移量
            
        返回:
            self（支持链式调用）
        """
        if offset < 0:
            raise ValidationError("offset必须大于等于0")
        self._offset_value = offset
        return self
    
    def build(self) -> Tuple[str, Tuple]:
        """
        构建SQL语句和参数
        
        返回:
            (sql语句, 参数元组)
        """
        if not self._table:
            raise ValidationError("必须指定表名")
        
        field_str = '*' if self._fields == ['*'] else ', '.join(f'`{escape_identifier(f)}`' for f in self._fields)
        
        if self._database:
            table_str = f"`{escape_identifier(self._database)}`.`{escape_identifier(self._table)}`"
        elif '.' in self._table:
            parts = self._table.split('.', 1)
            table_str = f"`{escape_identifier(parts[0])}`.`{escape_identifier(parts[1])}`"
        else:
            table_str = f"`{escape_identifier(self._table)}`"
        
        sql = f"SELECT {field_str} FROM {table_str}"
        
        if self._where_conditions:
            sql += f" WHERE {' AND '.join(self._where_conditions)}"
        
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        
        if self._limit_value is not None:
            sql += f" LIMIT {self._limit_value}"
        
        if self._offset_value is not None:
            sql += f" OFFSET {self._offset_value}"
        
        return sql, tuple(self._where_params)
    
    def execute(self) -> List[Dict[str, Any]]:
        """
        执行查询并返回结果
        
        返回:
            查询结果（字典列表）
        """
        sql, params = self.build()
        return self.db.query_to_dict(sql, params)
    
    def execute_one(self) -> Optional[Dict[str, Any]]:
        """
        执行查询并返回第一条记录
        
        返回:
            查询结果（单个字典）或None
        """
        sql, params = self.build()
        return self.db.execute_query(sql, params, fetch_one=True)


# ==================== 主管理类 ====================


class MYSQLQuery:
    """
    MySQL数据库管理器
    
    功能特性：
    - 连接池管理，提高性能
    - SSL安全连接
    - SQL注入防护
    - 灵活的日志管理
    - 自动资源管理，防止内存泄漏
    - 支持with上下文管理器
    - 多种数据格式导出

    """
    
    # 类变量：用于跟踪所有实例
    _instances = []
    
    @classmethod
    def cleanup_all(cls):
        """
        清理所有活动的MYSQLQuery实例
        
        功能:
            - 关闭所有未关闭的实例
            - 清理弱引用列表
            
        使用场景:
            - 应用程序退出前
            - 测试清理
            - 资源紧张时强制释放连接
            
        示例:
            # 在应用退出时
            import atexit
            atexit.register(MYSQLQuery.cleanup_all)
        """
        count = 0
        for ref in cls._instances[:]:  # 使用切片副本遍历
            instance = ref()
            if instance and not instance._closed:
                try:
                    instance.close()
                    count += 1
                except:
                    pass  # 忽略清理过程中的错误
        
        # 清空列表
        cls._instances.clear()
        
        # 这里不记录日志，因为可能在程序关闭时调用
        if count > 0:
            print(f"已清理 {count} 个MySQL连接实例")
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 3306,
        user: str = 'root',
        password: str = '',
        database: str = None,
        charset: str = 'utf8mb4',
        pool_size: int = 2,
        ssl_config: Optional[Dict[str, Any]] = None,
        log_config: Optional[Dict[str, Any]] = None,
        connect_timeout: int = 10,
        read_timeout: int = 30,
        write_timeout: int = 30
    ):
        """
        初始化MySQL管理器
        
        参数:
            host: 数据库主机地址
            port: 数据库端口
            user: 用户名
            password: 密码
            database: 数据库名（可选，None表示不指定默认数据库，可随时切换）
            charset: 字符集（默认utf8mb4支持emoji）
            pool_size: 连接池大小
            ssl_config: SSL配置字典，例如: {
                'ca': '/path/to/ca.pem',
                'cert': '/path/to/client-cert.pem',
                'key': '/path/to/client-key.pem'
            }
            log_config: 日志配置字典（键名和level值均忽略大小写），例如: {
                'enable': True,           # 是否启用日志（默认True）
                                          # 设置为False时，不会输出任何日志，忽略其他配置
                'level': 'INFO',          # 日志级别 debug/info/warning/error（默认INFO）
                'output': 'console',      # 输出位置（默认console）:
                                          #   - 'console' 或 'terminal': 仅输出到终端
                                          #   - 'file': 仅输出到文件
                                          #   - 'both': 同时输出到终端和文件
                'file_path': 'mysql_query.log'  # 日志文件路径（可选）
                                          # 相对路径：存储到用户home目录
                                          # 绝对路径：存储到指定路径
            }
            connect_timeout: 连接超时（秒，默认10）
            read_timeout: 读取超时（秒，默认30）
            write_timeout: 写入超时（秒，默认30）
        
        示例:
            # 指定默认数据库
            db = MYSQLQuery(host='localhost', user='root', password='pwd', database='db1')
            
            # 查询多个数据库（使用 database.table 格式）
            db = MYSQLQuery(host='localhost', user='root', password='pwd')
            db.query_to_dict("SELECT * FROM db1.table1")
            db.query_to_dict("SELECT * FROM db2.table2")
            
            # SSL连接
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd', database='db',
                ssl_config={'ca': '/path/to/ca.pem'}
            )
            
            # 完全禁用日志（enable=False时忽略其他配置）
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd',
                log_config={'enable': False}  # 不会输出任何日志
            )
            
            # 仅输出到终端（默认，适合开发调试）
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd',
                log_config={'output': 'console'}  # 或 'terminal'
            )
            
            # 仅输出到文件（适合生产环境）
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd',
                log_config={
                    'output': 'file',
                    'file_path': '/var/log/mysql_query.log'  # 绝对路径
                }
            )
            
            # 同时输出到终端和文件（适合问题排查）
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd',
                log_config={
                    'level': 'debug',              # 'debug'/'DEBUG' 都可以
                    'output': 'both',              # 同时输出
                    'file_path': 'mysql_query.log' # 相对路径，存到 ~/mysql_query.log
                }
            )
            
            # 自定义超时
            db = MYSQLQuery(
                host='localhost', user='root', password='pwd',
                connect_timeout=5, read_timeout=60
            )
        
        异常:
            ValidationError: 参数验证失败
            ConnectionError: 连接初始化失败
        """
        if not host:
            raise ValidationError("host 不能为空")
        if not user:
            raise ValidationError("user 不能为空")
        if port <= 0 or port > 65535:
            raise ValidationError(f"port 必须在 1-65535 之间，当前值: {port}")
        if pool_size < 1:
            raise ValidationError(f"pool_size 必须大于 0，当前值: {pool_size}")
        if connect_timeout < 1:
            raise ValidationError(f"connect_timeout 必须大于 0，当前值: {connect_timeout}")
        if read_timeout < 1:
            raise ValidationError(f"read_timeout 必须大于 0，当前值: {read_timeout}")
        if write_timeout < 1:
            raise ValidationError(f"write_timeout 必须大于 0，当前值: {write_timeout}")
        
        if database:
            database = validate_identifier(database, "数据库名")
        
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.ssl_config = ssl_config
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self._closed = False
        
        self._setup_logger(log_config or {})
        
        try:
            self._init_pool(pool_size)
        except Exception as e:
            raise ConnectionError(f"连接池初始化失败: {str(e)}") from e
        
        MYSQLQuery._instances.append(weakref.ref(self))
        
        if self.logger:
            masked_pwd = mask_password(password)
            self.logger.debug(f"MySQL管理器初始化: {user}@{host}:{port}, 密码: {masked_pwd}")
            if database:
                self.logger.info(f"默认数据库: {database}")
            if ssl_config:
                self.logger.info("SSL连接已启用")
            self.logger.debug(f"超时配置 - 连接:{connect_timeout}s, 读:{read_timeout}s, 写:{write_timeout}s")
    
    def _setup_logger(self, log_config: Dict[str, Any]):
        """
        配置日志系统
        
        参数:
            log_config: 日志配置字典
        """
        config = {k.lower(): v for k, v in log_config.items()}
        
        enable = config.get('enable', True)
        
        if not enable:
            self.logger = logging.getLogger(f'MYSQLQuery_{id(self)}')
            self.logger.addHandler(logging.NullHandler())
            self.logger.propagate = False
            return
        
        level = str(config.get('level', 'INFO')).upper()
        output = str(config.get('output', 'console')).lower()
        file_path = config.get('file_path')
        
        self.logger = logging.getLogger(f'MYSQLQuery_{id(self)}')
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
                file_path = Path.home() / 'mysql_query.log'
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
    
    def _init_pool(self, pool_size: int):
        """
        初始化数据库连接池
        
        参数:
            pool_size: 连接池大小
        """
        try:
            connection_kwargs = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password,
                'charset': self.charset,
                'cursorclass': DictCursor,
                'autocommit': True,
                'connect_timeout': self.connect_timeout,
                'read_timeout': self.read_timeout,
                'write_timeout': self.write_timeout,
            }
            
            if self.database:
                connection_kwargs['database'] = self.database
            
            if self.ssl_config:
                ssl_dict = {}
                if 'ca' in self.ssl_config:
                    ssl_dict['ca'] = self.ssl_config['ca']
                if 'cert' in self.ssl_config:
                    ssl_dict['cert'] = self.ssl_config['cert']
                if 'key' in self.ssl_config:
                    ssl_dict['key'] = self.ssl_config['key']
                if 'check_hostname' in self.ssl_config:
                    ssl_dict['check_hostname'] = self.ssl_config['check_hostname']
                
                connection_kwargs['ssl'] = ssl_dict
                if self.logger:
                    self.logger.debug(f"SSL配置已应用: {list(ssl_dict.keys())}")
            
            # 创建连接池
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=pool_size,
                mincached=1,
                maxcached=3,
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
        """
        获取数据库连接（上下文管理器）
        自动管理连接的获取和释放
        """
        conn = None
        try:
            conn = self.pool.connection()
            yield conn
        except Exception as e:
            if self.logger:
                self.logger.error(f"数据库连接错误: {str(e)}")
            raise ConnectionError(f"数据库连接错误: {str(e)}") from e
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        功能:
            - 自动开始事务
            - 执行成功时自动提交
            - 发生异常时自动回滚
            - 自动管理连接资源
        
        示例:
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO users (name) VALUES (%s)", ('张三',))
                cursor.execute("UPDATE accounts SET balance = balance - 100 WHERE user_id = 1")
                cursor.execute("UPDATE accounts SET balance = balance + 100 WHERE user_id = 2")
        
        异常:
            TransactionError: 事务处理失败
        """
        conn = None
        cursor = None
        try:
            conn = self.pool.connection()
            conn.begin()
            cursor = conn.cursor()
            
            if self.logger:
                self.logger.debug("事务已开始")
            
            yield cursor
            
            conn.commit()
            if self.logger:
                self.logger.debug("事务已提交")
                
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                    if self.logger:
                        self.logger.warning(f"事务已回滚: {str(e)}")
                except Exception as rollback_error:
                    if self.logger:
                        self.logger.error(f"事务回滚失败: {str(rollback_error)}")
            raise TransactionError(f"事务执行失败: {str(e)}") from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def execute_many(
        self, 
        sql: str, 
        params_list: List[Union[Tuple, Dict]],
        batch_size: int = 1000
    ) -> int:
        """
        批量执行SQL（在事务中执行）
        
        参数:
            sql: SQL语句（INSERT, UPDATE, DELETE等）
            params_list: 参数列表
            batch_size: 批次大小（默认1000，避免一次性提交过多数据）
            
        返回:
            影响的总行数
            
        示例:
            # 批量插入
            sql = "INSERT INTO users (name, age) VALUES (%s, %s)"
            params = [('张三', 20), ('李四', 25), ('王五', 30)]
            affected = db.execute_many(sql, params)
            
        异常:
            TransactionError: 批量执行失败
        """
        if not params_list:
            if self.logger:
                self.logger.warning("参数列表为空，跳过执行")
            return 0
        
        total_affected = 0
        start_time = datetime.now()
        
        try:
            for i in range(0, len(params_list), batch_size):
                batch = params_list[i:i + batch_size]
                
                with self.transaction() as cursor:
                    cursor.executemany(sql, batch)
                    total_affected += cursor.rowcount
                    
                    if self.logger:
                        self.logger.debug(f"批次 {i//batch_size + 1}: 影响 {cursor.rowcount} 行")
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if self.logger:
                self.logger.info(f"批量执行成功: 总计 {total_affected} 行, 耗时 {elapsed:.3f}秒")
            
            return total_affected
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"批量执行失败: {str(e)}")
            raise TransactionError(f"批量执行失败: {str(e)}") from e
    
    def builder(self) -> QueryBuilder:
        """
        获取查询构建器实例
        
        返回:
            QueryBuilder对象
            
        示例:
            result = db.builder() \\
                .table('users') \\
                .select('id', 'name') \\
                .where('age > %s', 18) \\
                .limit(10) \\
                .execute()
        """
        return QueryBuilder(self)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口，自动关闭连接
        
        参数:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪
        """
        self.close()
        return False  # 不抑制异常
    
    def __del__(self):
        """
        析构函数，确保资源被释放
        防止内存泄漏
        """
        if not self._closed and hasattr(self, 'pool'):
            try:
                self.close()
            except:
                # 在析构函数中忽略所有异常
                pass
    
    @retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
    def execute_query(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        fetch_one: bool = False
    ) -> Union[List[Dict], Dict, None]:
        """
        执行SQL查询
        
        参数:
            sql: SQL查询语句（支持参数化查询，使用%s占位符）
            params: 查询参数（元组或字典）
            fetch_one: 是否只返回一条记录
            
        返回:
            查询结果（字典列表或单个字典）
            
        异常:
            QueryError: 查询执行失败
        
        注意:
            网络错误会自动重试最多3次
        """
        start_time = datetime.now()
        
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                    else:
                        result = cursor.fetchall()
                    
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if self.logger:
                        row_count = len(result) if result and not fetch_one else 1 if result else 0
                        self.logger.debug(f"查询成功: {row_count}行, 耗时{elapsed:.3f}秒")
                    
                    return result
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"查询失败: {str(e)}")
                self.logger.debug(f"SQL: {sql}")
            raise
    
    def query_to_dict(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None
    ) -> List[Dict[str, Any]]:
        """
        查询并返回字典列表格式
        
        参数:
            sql: SQL查询语句
            params: 查询参数
            
        返回:
            字典列表 [{'field1': value1, 'field2': value2}, ...]
        """
        return self.execute_query(sql, params, fetch_one=False) or []
    
    def query_to_dataframe(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None
    ):
        """
        查询并返回DataFrame格式
        
        参数:
            sql: SQL查询语句
            params: 查询参数
            
        返回:
            pandas.DataFrame对象
        """
        try:
            import pandas as pd
        except ImportError:
            if self.logger:
                self.logger.error("需要安装pandas库: pip install pandas")
            raise ImportError("请先安装pandas: pip install pandas")
        
        result = self.execute_query(sql, params, fetch_one=False)
        df = pd.DataFrame(result if result else [])
        
        if self.logger:
            self.logger.debug(f"DataFrame: {df.shape}")
        return df
    
    def query_with_fields(
        self,
        table: str,
        fields: Optional[List[str]] = None,
        where: Optional[str] = None,
        params: Optional[Union[Tuple, Dict]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """
        查询指定字段
        
        参数:
            table: 表名（支持 database.table 格式）
            fields: 字段列表（None表示查询所有字段）
            where: WHERE条件（不含WHERE关键字）
            params: WHERE条件参数
            order_by: 排序字段（例如: "id DESC" 或 "name ASC, created_at DESC"）
            limit: 限制返回数量
            database: 数据库名（None表示使用当前数据库或table中指定的数据库）
            
        返回:
            字典列表
        
        示例:
            data = db.query_with_fields(
                table='users',
                fields=["id", "name", "email"],
                where="age > %s",
                params=(18,),
                order_by="created_at DESC",
                limit=10
            )
        """
        field_str = '*' if not fields else ', '.join(f'`{f}`' for f in fields)
        
        if database:
            table_str = f"`{database}`.`{table}`"
        elif '.' in table:
            parts = table.split('.', 1)
            table_str = f"`{parts[0]}`.`{parts[1]}`"
        else:
            table_str = f"`{table}`"
        
        sql = f"SELECT {field_str} FROM {table_str}"
        
        if where:
            sql += f" WHERE {where}"
        
        if order_by:
            sql += f" ORDER BY {order_by}"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        return self.query_to_dict(sql, params)
    
    def get_table_structure(self, table: str) -> List[FieldInfo]:
        """
        获取表结构信息
        
        参数:
            table: 表名
            
        返回:
            表结构信息列表，包含字段名、类型、是否为空、键信息等
            
        异常:
            ValidationError: 表名验证失败
            QueryError: 查询失败
        """
        table = validate_identifier(table, "表名")
        sql = f"DESCRIBE `{escape_identifier(table)}`"
        result = self.execute_query(sql)
        
        if self.logger:
            count = len(result) if result else 0
            self.logger.debug(f"表结构: {table}, {count}个字段")
        return result or []
    
    def get_table_info(self, table: str, database: Optional[str] = None) -> Optional[TableInfo]:
        """
        获取表的详细信息
        
        参数:
            table: 表名
            database: 数据库名（None表示使用当前数据库）
            
        返回:
            表信息字典（包含引擎、字符集、注释等），如果表不存在则返回None
            
        异常:
            ValidationError: 表名或数据库名验证失败
            QueryError: 查询失败
        """
        table = validate_identifier(table, "表名")
        
        target_db = database if database else self.database
        if not target_db:
            raise ValidationError("必须指定数据库名或在初始化时设置默认数据库")
        
        target_db = validate_identifier(target_db, "数据库名")
        
        sql = """
        SELECT 
            TABLE_NAME as table_name,
            ENGINE as engine,
            TABLE_ROWS as row_count,
            AVG_ROW_LENGTH as avg_row_length,
            DATA_LENGTH as data_length,
            INDEX_LENGTH as index_length,
            AUTO_INCREMENT as auto_increment,
            CREATE_TIME as create_time,
            UPDATE_TIME as update_time,
            TABLE_COLLATION as collation,
            TABLE_COMMENT as comment
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        result = self.execute_query(sql, (target_db, table), fetch_one=True)
        
        if self.logger and result:
            self.logger.debug(f"表信息: {target_db}.{table}")
        
        return result
    
    def list_tables(self, database: Optional[str] = None) -> List[str]:
        """
        获取数据库的所有表名
        
        参数:
            database: 数据库名（None表示使用当前数据库）
            
        返回:
            表名列表
            
        异常:
            ValidationError: 数据库名验证失败
            QueryError: 查询失败
        """
        if database:
            database = validate_identifier(database, "数据库名")
            sql = f"SHOW TABLES FROM `{escape_identifier(database)}`"
        else:
            sql = "SHOW TABLES"
        
        result = self.execute_query(sql)
        tables = [list(row.values())[0] for row in result] if result else []
        
        if self.logger:
            db_name = database if database else "当前数据库"
            self.logger.debug(f"{db_name}共{len(tables)}张表")
        return tables
    
    def get_current_database(self) -> Optional[str]:
        """
        获取当前使用的数据库名
        
        返回:
            当前数据库名，如果未选择数据库则返回None
        """
        sql = "SELECT DATABASE() as db"
        result = self.execute_query(sql, fetch_one=True)
        return result.get('db') if result else None
    
    def list_databases(self) -> List[str]:
        """
        获取所有数据库名称列表
        
        返回:
            数据库名称列表
        """
        sql = "SHOW DATABASES"
        result = self.execute_query(sql)
        databases = [list(row.values())[0] for row in result] if result else []
        
        if self.logger:
            self.logger.debug(f"共{len(databases)}个数据库")
        return databases
    
    def export_to_json(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        file_path: Optional[str] = None,
        indent: int = 2,
        fields: Optional[List[str]] = None
    ) -> str:
        """
        查询并导出为JSON文件
        
        参数:
            sql: SQL查询语句
            params: 查询参数
            file_path: 导出文件路径（None则自动生成到home目录）
            indent: JSON缩进空格数
            fields: 要导出的字段列表（None表示导出所有字段）
            
        返回:
            导出文件的完整路径
        """
        # 查询数据
        data = self.query_to_dict(sql, params)
        
        # 过滤字段
        if fields and data:
            data = [{k: v for k, v in row.items() if k in fields} for row in data]
        
        # 确定导出路径
        if not file_path:
            home_dir = Path.home()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = home_dir / f"mysql_export_{timestamp}.json"
        else:
            file_path = Path(file_path)
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
        
        if self.logger:
            self.logger.info(f"导出JSON: {file_path}, {len(data)}行")
        return str(file_path)
    
    def export_to_csv(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        file_path: Optional[str] = None,
        encoding: str = 'utf-8-sig',
        fields: Optional[List[str]] = None
    ) -> str:
        """
        查询并导出为CSV文件
        
        参数:
            sql: SQL查询语句
            params: 查询参数
            file_path: 导出文件路径（None则自动生成到home目录）
            encoding: 文件编码（utf-8-sig支持Excel直接打开）
            fields: 要导出的字段列表（None表示导出所有字段）
            
        返回:
            导出文件的完整路径
        """
        try:
            import pandas as pd
        except ImportError:
            if self.logger:
                self.logger.error("需要安装pandas库: pip install pandas")
            raise ImportError("请先安装pandas: pip install pandas")
        
        # 查询数据
        df = self.query_to_dataframe(sql, params)
        
        # 过滤字段
        if fields and not df.empty:
            df = df[[col for col in fields if col in df.columns]]
        
        # 确定导出路径
        if not file_path:
            home_dir = Path.home()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = home_dir / f"mysql_export_{timestamp}.csv"
        else:
            file_path = Path(file_path)
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入CSV
        df.to_csv(file_path, index=False, encoding=encoding)
        
        if self.logger:
            self.logger.info(f"导出CSV: {file_path}, {len(df)}行")
        return str(file_path)
    
    def export_to_excel(
        self,
        sql: str,
        params: Optional[Union[Tuple, Dict]] = None,
        file_path: Optional[str] = None,
        sheet_name: str = 'Sheet1',
        fields: Optional[List[str]] = None
    ) -> str:
        """
        查询并导出为Excel文件
        
        参数:
            sql: SQL查询语句
            params: 查询参数
            file_path: 导出文件路径（None则自动生成到home目录）
            sheet_name: 工作表名称
            fields: 要导出的字段列表（None表示导出所有字段）
            
        返回:
            导出文件的完整路径
        """
        try:
            import pandas as pd
        except ImportError:
            if self.logger:
                self.logger.error("需要安装pandas和openpyxl库")
            raise ImportError("请先安装: pip install pandas openpyxl")
        
        # 查询数据
        df = self.query_to_dataframe(sql, params)
        
        # 过滤字段
        if fields and not df.empty:
            df = df[[col for col in fields if col in df.columns]]
        
        # 确定导出路径
        if not file_path:
            home_dir = Path.home()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = home_dir / f"mysql_export_{timestamp}.xlsx"
        else:
            file_path = Path(file_path)
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        if self.logger:
            self.logger.info(f"导出Excel: {file_path}, {len(df)}行")
        return str(file_path)
    
    def export_table_structure(
        self,
        table: str,
        file_path: Optional[str] = None,
        format: str = 'json'
    ) -> str:
        """
        导出表结构到文件
        
        参数:
            table: 表名
            file_path: 导出文件路径（None则自动生成到home目录）
            format: 导出格式 (json/csv/excel)
            
        返回:
            导出文件的完整路径
        """
        # 获取表结构
        structure = self.get_table_structure(table)
        
        # 获取表信息
        table_info = self.get_table_info(table)
        
        # 组合数据
        export_data = {
            'table_info': table_info,
            'structure': structure
        }
        
        # 确定导出路径
        if not file_path:
            home_dir = Path.home()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = home_dir / f"table_structure_{table}_{timestamp}.{format}"
        else:
            file_path = Path(file_path)
        
        # 创建目录
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 根据格式导出
        if format == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
        elif format in ['csv', 'excel']:
            try:
                import pandas as pd
                df_structure = pd.DataFrame(structure)
                
                if format == 'csv':
                    df_structure.to_csv(file_path, index=False, encoding='utf-8-sig')
                else:  # excel
                    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                        df_structure.to_excel(writer, sheet_name='Structure', index=False)
                        if table_info:
                            df_info = pd.DataFrame([table_info])
                            df_info.to_excel(writer, sheet_name='Info', index=False)
            except ImportError:
                if self.logger:
                    self.logger.error("需要安装pandas库")
                raise
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        if self.logger:
            self.logger.debug(f"表结构已导出: {file_path}")
        return str(file_path)
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        返回:
            连接是否成功
        """
        try:
            sql = "SELECT VERSION() as version"
            result = self.execute_query(sql, fetch_one=True)
            if result:
                version = result.get('version', 'Unknown')
                if self.logger:
                    self.logger.info(f"连接成功, MySQL {version}")
                return True
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"连接失败: {str(e)}")
            return False
    
    def close(self):
        """
        关闭连接池
        
        注意:
            - 可以重复调用，不会报错
            - 关闭后不能再执行查询
            - 使用with语句会自动调用此方法
        """
        if self._closed:
            return
        
        try:
            if hasattr(self, 'pool'):
                self.pool.close()
                if self.logger:
                    self.logger.debug("连接池已关闭")
        except Exception as e:
            if self.logger:
                self.logger.error(f"关闭连接失败: {str(e)}")
        finally:
            self._closed = True


def test():
    try:
        with MYSQLQuery(
            host='localhost',
            port=3306,
            user='user',
            password='password',
            log_config={'enable': True, 'level': 'INFO', 'output': 'both', 'file_path': 'mysql_query.log'}
        ) as db:
            data = db.query_with_fields(
                table='推广数据_圣积天猫店.营销场景报表_2025',
                fields=['日期', '店铺名称', '花费', '点击量', '展现量', '总成交笔数', '总成交金额'],
                where='花费 > 0 and 日期 >= "2025-09-27"',
            )
            for row in data:
                print(row)
            
    except ValidationError as e:
        print(f"✗ 参数验证失败: {e}")
    except ConnectionError as e:
        print(f"✗ 连接失败: {e}")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

if __name__ == '__main__':
    # 运行测试
    test()