# -*- coding:utf-8 -*-
"""
MySQL数据上传
"""
import datetime
import time
import json
import re
import io
from typing import Union, List, Dict, Optional, Any, Tuple, Iterator
from functools import wraps
from decimal import Decimal, InvalidOperation
import math
import pymysql
import pandas as pd
import psutil
import enum
import ipaddress
from dbutils.pooled_db import PooledDB
from mdbq.log import mylogger
# from mdbq.myconf import myconf

# 配置日志
logger = mylogger.MyLogger(
    logging_mode='file',
    log_level='info',
    log_format='json',
    max_log_size=50,
    backup_count=5,
    enable_async=False,
    sample_rate=1,
    sensitive_fields=[],
    enable_metrics=False,
)


class DatabaseConnectionManager:
    """数据库连接管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        self._create_pool()
    
    def _create_pool(self):
        """创建连接池"""
        pool_params = {
            'creator': pymysql,
            'host': self.config['host'],
            'port': self.config['port'],
            'user': self.config['username'],
            'password': self.config['password'],
            'charset': self.config['charset'],
            'cursorclass': pymysql.cursors.DictCursor,
            'maxconnections': self.config['pool_size'],
            'mincached': self.config.get('mincached', 0),
            'maxcached': self.config.get('maxcached', 0),
            'ping': 7,
            'connect_timeout': self.config.get('connect_timeout', 10),
            'read_timeout': self.config.get('read_timeout', 30),
            'write_timeout': self.config.get('write_timeout', 30),
            'autocommit': False
        }
        
        # 设置时区为北京时间，确保时间戳的一致性
        if 'init_command' not in self.config:
            pool_params['init_command'] = "SET time_zone = '+08:00'"
        else:
            # 如果用户已设置init_command，则追加时区设置
            existing_commands = self.config['init_command']
            if 'time_zone' not in existing_commands.lower():
                pool_params['init_command'] = f"{existing_commands}; SET time_zone = '+08:00'"
            else:
                pool_params['init_command'] = existing_commands
        
        if self.config.get('ssl'):
            pool_params['ssl'] = self.config['ssl']
        
        try:
            self.pool = PooledDB(**pool_params)
            logger.debug('数据库连接池创建成功', {'host': self.config['host']})
        except Exception as e:
            logger.error('连接池创建失败', {'error': str(e)})
            raise ConnectionError(f'连接池创建失败: {str(e)}')
    
    def get_connection(self):
        """获取数据库连接"""
        if not self.pool:
            self._create_pool()
        return self.pool.connection()
    
    def close(self):
        """关闭连接池"""
        if self.pool:
            self.pool = None
            logger.debug('数据库连接池已关闭')


class DataTypeInferrer:
    """数据类型推断器"""
    
    # 自定义类型映射注册表
    _custom_type_handlers = {}
    
    @classmethod
    def register_type_handler(cls, type_name: str, handler_func):
        """
        注册自定义类型处理器
        
        :param type_name: 类型名称
        :param handler_func: 处理函数，接收value参数，返回MySQL类型字符串或None
        """
        cls._custom_type_handlers[type_name] = handler_func
    
    @staticmethod
    def infer_mysql_type(value: Any) -> str:
        """推断MySQL数据类型"""
        if value is None or str(value).lower() in ['', 'none', 'nan']:
            return 'VARCHAR(255)'
        
        # 检查自定义类型处理器
        for type_name, handler in DataTypeInferrer._custom_type_handlers.items():
            try:
                result = handler(value)
                if result:
                    return result
            except Exception:
                continue
        
        # Python基本类型
        if isinstance(value, bool):
            return 'TINYINT(1)'
        elif isinstance(value, int):
            if -2147483648 <= value <= 2147483647:
                return 'INT'
            else:
                return 'BIGINT'
        elif isinstance(value, float):
            return 'DECIMAL(20,6)'
        elif isinstance(value, (datetime.datetime, pd.Timestamp)):
            return 'DATETIME'
        elif isinstance(value, datetime.date):
            return 'DATE'
        elif isinstance(value, (list, dict)):
            return 'JSON'
        elif isinstance(value, str):
            return DataTypeInferrer._infer_string_type(value)
        
        # 处理枚举类型
        if hasattr(value, '__class__') and hasattr(value.__class__, '__bases__'):
            # 检查是否是枚举类型
            if isinstance(value, enum.Enum):
                # 根据枚举值的类型决定MySQL类型
                enum_value = value.value
                if isinstance(enum_value, int):
                    return 'INT'
                elif isinstance(enum_value, str):
                    max_len = max(len(str(item.value)) for item in value.__class__)
                    return f'VARCHAR({min(max_len * 2, 255)})'
                else:
                    return 'VARCHAR(255)'
        
        # 处理其他特殊类型
        value_str = str(value)
        
        # UUID检测
        if DataTypeInferrer._is_uuid(value_str):
            return 'CHAR(36)'
        
        # IP地址检测
        if DataTypeInferrer._is_ip_address(value_str):
            return 'VARCHAR(45)'  # 支持IPv6
        
        # 邮箱检测
        if DataTypeInferrer._is_email(value_str):
            return 'VARCHAR(255)'
        
        # URL检测
        if DataTypeInferrer._is_url(value_str):
            return 'TEXT'
        
        # 默认字符串处理
        return DataTypeInferrer._infer_string_type(value_str)
    
    @staticmethod
    def _infer_string_type(value: str) -> str:
        """推断字符串类型"""
        # 尝试判断是否是日期时间
        if DataValidator.is_datetime_string(value):
            return 'DATETIME'
        
        # 数值字符串检测
        if DataTypeInferrer._is_numeric_string(value):
            if '.' in value or 'e' in value.lower():
                return 'DECIMAL(20,6)'
            else:
                try:
                    int_val = int(value)
                    if -2147483648 <= int_val <= 2147483647:
                        return 'INT'
                    else:
                        return 'BIGINT'
                except ValueError:
                    pass
        
        # 根据字符串长度选择类型
        length = len(value)
        if length <= 255:
            return 'VARCHAR(255)'
        elif length <= 65535:
            return 'TEXT'
        else:
            return 'LONGTEXT'
    
    @staticmethod
    def _is_uuid(value: str) -> bool:
        """检测是否是UUID格式"""
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
        return bool(re.match(uuid_pattern, value.lower()))
    
    @staticmethod
    def _is_ip_address(value: str) -> bool:
        """检测是否是IP地址"""
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_email(value: str) -> bool:
        """检测是否是邮箱地址"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, value))
    
    @staticmethod
    def _is_url(value: str) -> bool:
        """检测是否是URL"""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, value, re.IGNORECASE))
    
    @staticmethod
    def _is_numeric_string(value: str) -> bool:
        """检测是否是数值字符串"""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def infer_types_from_data(data: List[Dict], sample_size: int = 100) -> Dict[str, str]:
        """
        从数据中推断所有列的类型
        
        :param data: 数据列表
        :param sample_size: 采样大小，避免检查过多数据
        """
        if not data:
            return {}
        
        type_map = {}
        type_candidates = {}  # 存储每列的候选类型
        
        # 采样数据进行类型推断
        sample_data = data[:sample_size] if len(data) > sample_size else data
        
        # 首先收集所有列名
        all_columns = set()
        for row in sample_data:
            for col in row.keys():
                if col.lower() not in ['id', 'create_at', 'update_at']:
                    all_columns.add(col)
        
        # 为每个列初始化候选类型列表
        for col in all_columns:
            type_candidates[col] = []
        
        for row in sample_data:
            for col, value in row.items():
                # 跳过系统列
                if col.lower() in ['id', 'create_at', 'update_at']:
                    continue
                
                # 即使值为空，也要推断类型
                mysql_type = DataTypeInferrer.infer_mysql_type(value)
                type_candidates[col].append(mysql_type)
        
        # 为每列选择最合适的类型
        for col, types in type_candidates.items():
            type_map[col] = DataTypeInferrer._select_best_type(types)
        
        # 自动添加系统列类型定义（id列只在新建表时添加）
        type_map['id'] = 'BIGINT'
        type_map['create_at'] = 'TIMESTAMP'
        type_map['update_at'] = 'TIMESTAMP'
        
        return type_map
    
    @staticmethod
    def _select_best_type(type_candidates: List[str]) -> str:
        """
        从候选类型中选择最佳类型
        
        优先级：JSON > LONGTEXT > TEXT > VARCHAR > DECIMAL > BIGINT > INT > DATETIME > DATE
        """
        if not type_candidates:
            return 'VARCHAR(255)'
        
        # 类型优先级映射
        type_priority = {
            'JSON': 10,
            'LONGTEXT': 9,
            'TEXT': 8,
            'VARCHAR': 7,
            'DECIMAL': 6,
            'BIGINT': 5,
            'INT': 4,
            'DATETIME': 3,
            'DATE': 2,
            'TINYINT': 1
        }
        
        # 找到优先级最高的类型
        best_type = 'VARCHAR(255)'
        best_priority = 0
        
        for candidate in set(type_candidates):
            # 提取基础类型名
            base_type = candidate.split('(')[0].upper()
            priority = type_priority.get(base_type, 0)
            
            if priority > best_priority:
                best_priority = priority
                best_type = candidate
        
        return best_type


# 注册一些常用的自定义类型处理器
def register_common_type_handlers():
    """注册常用的自定义类型处理器"""
    
    def handle_phone_number(value):
        """处理电话号码"""
        if isinstance(value, str):
            # 中国手机号码格式
            if re.match(r'^1[3-9]\d{9}$', value):
                return 'VARCHAR(11)'
            # 国际电话号码格式
            if re.match(r'^\+?[1-9]\d{1,14}$', value):
                return 'VARCHAR(20)'
        return None
    
    def handle_id_card(value):
        """处理身份证号"""
        if isinstance(value, str):
            # 中国身份证号码
            if re.match(r'^\d{17}[\dXx]$', value):
                return 'CHAR(18)'
        return None
    
    def handle_json_string(value):
        """处理JSON字符串"""
        if isinstance(value, str):
            try:
                json.loads(value)
                return 'JSON'
            except (ValueError, TypeError):
                pass
        return None
    
    # 注册处理器
    DataTypeInferrer.register_type_handler('phone', handle_phone_number)
    DataTypeInferrer.register_type_handler('id_card', handle_id_card)
    DataTypeInferrer.register_type_handler('json_string', handle_json_string)

# 自动注册常用类型处理器
register_common_type_handlers()


class DataValidator:
    """数据验证器"""
    
    @staticmethod
    def is_datetime_string(value: str) -> bool:
        """检查字符串是否为日期时间格式"""
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y%m%d',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                datetime.datetime.strptime(value, fmt)
                return True
            except ValueError:
                continue
        return False
    
    @staticmethod
    def validate_and_convert_value(value: Any, mysql_type: str, allow_null: bool = False) -> Any:
        """验证并转换数据值"""
        mysql_type_lower = mysql_type.lower()
        
        # 处理空值
        if value is None or (isinstance(value, str) and value.strip() == ''):
            if allow_null:
                return None
            # 对于日期时间类型，直接返回默认的日期时间值
            if 'datetime' in mysql_type_lower or 'timestamp' in mysql_type_lower:
                return '2000-01-01 00:00:00'
            elif 'date' in mysql_type_lower:
                return '2000-01-01'
            return DataValidator._get_default_value(mysql_type)
        
        # 处理pandas的NaN值
        if not isinstance(value, (list, dict)):
            try:
                if pd.isna(value) or (isinstance(value, float) and math.isinf(value)):
                    if allow_null:
                        return None
                    # 对于日期时间类型，直接返回默认的日期时间值
                    if 'datetime' in mysql_type_lower or 'timestamp' in mysql_type_lower:
                        return '2000-01-01 00:00:00'
                    elif 'date' in mysql_type_lower:
                        return '2000-01-01'
                    return DataValidator._get_default_value(mysql_type)
            except (ValueError, TypeError):
                pass
        
        # JSON类型
        if 'json' in mysql_type_lower:
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False)
            elif isinstance(value, str):
                try:
                    json.loads(value)
                    return value
                except (TypeError, ValueError):
                    raise ValueError(f"无效的JSON字符串: {value}")
            else:
                return str(value)
        
        # 日期时间类型
        if 'datetime' in mysql_type_lower or 'timestamp' in mysql_type_lower:
            return DataValidator._convert_to_datetime(value)
        elif 'date' in mysql_type_lower:
            return DataValidator._convert_to_date(value)
        
        # 数值类型
        elif 'int' in mysql_type_lower:
            return DataValidator._convert_to_int(value)
        elif any(t in mysql_type_lower for t in ['decimal', 'float', 'double']):
            return DataValidator._convert_to_decimal(value)
        
        # 字符串类型
        elif 'varchar' in mysql_type_lower:
            str_value = str(value)
            # 检查长度限制
            match = re.search(r'\((\d+)\)', mysql_type)
            if match:
                max_len = int(match.group(1))
                if len(str_value.encode('utf-8')) > max_len:
                    return str_value.encode('utf-8')[:max_len].decode('utf-8', 'ignore')
            return str_value
        
        # 默认转为字符串
        return str(value)
    
    @staticmethod
    def _get_default_value(mysql_type: str) -> Any:
        """获取MySQL类型的默认值"""
        mysql_type_lower = mysql_type.lower()
        
        if any(t in mysql_type_lower for t in ['int', 'bigint', 'tinyint', 'smallint']):
            return 0
        elif any(t in mysql_type_lower for t in ['decimal', 'float', 'double']):
            return 0.0
        elif any(t in mysql_type_lower for t in ['varchar', 'text', 'char']):
            return 'none'
        elif 'date' in mysql_type_lower:
            if 'datetime' in mysql_type_lower:
                return '2000-01-01 00:00:00'
            else:
                return '2000-01-01'
        elif 'json' in mysql_type_lower:
            return '{}'
        else:
            return 'none'
    
    @staticmethod
    def _convert_to_datetime(value: Any) -> str:
        """转换为datetime格式"""
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        
        value_str = str(value).strip()
        
        # 处理特殊的无效值
        if value_str.lower() in ['none', 'null', 'nan', '', 'nat']:
            return '2000-01-01 00:00:00'
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
            '%Y%m%d',
            '%Y-%m-%dT%H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.datetime.strptime(value_str, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        # 如果所有格式都无法解析，返回默认值而不是抛出异常
        return '2000-01-01 00:00:00'
    
    @staticmethod
    def _convert_to_date(value: Any) -> str:
        """转换为date格式"""
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        
        # 先转为datetime再提取日期部分
        datetime_str = DataValidator._convert_to_datetime(value)
        return datetime_str.split(' ')[0]
    
    @staticmethod
    def _convert_to_int(value: Any) -> int:
        """转换为整数"""
        if hasattr(value, 'item'):
            try:
                value = value.item()
            except Exception:
                pass
        
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                raise ValueError(f"无法转换为整数: {value}")
    
    @staticmethod
    def _convert_to_decimal(value: Any) -> Decimal:
        """转换为Decimal"""
        if hasattr(value, 'item'):
            try:
                value = value.item()
            except Exception:
                pass
        
        # 处理百分比字符串
        if isinstance(value, str) and '%' in value:
            if re.match(r'^-?\d+(\.\d+)?%$', value.strip()):
                value = float(value.strip().replace('%', '')) / 100
        
        try:
            return Decimal(str(value))
        except (ValueError, TypeError, InvalidOperation):
            raise ValueError(f"无法转换为数值: {value}")


class TableManager:
    """表管理器"""
    
    def __init__(self, connection_manager: DatabaseConnectionManager, collation: str):
        self.conn_mgr = connection_manager
        self.collation = collation
    
    def ensure_database_exists(self, db_name: str):
        """确保数据库存在"""
        db_name = self._sanitize_identifier(db_name)
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                    (db_name,)
                )
                if not cursor.fetchone():
                    charset = self.conn_mgr.config['charset']
                    sql = f"CREATE DATABASE `{db_name}` CHARACTER SET {charset} COLLATE {self.collation}"
                    cursor.execute(sql)
                    conn.commit()
                    logger.debug('数据库已创建', {'database': db_name})
    
    def table_exists(self, db_name: str, table_name: str) -> bool:
        """检查表是否存在"""
        db_name = self._sanitize_identifier(db_name)
        table_name = self._sanitize_identifier(table_name)
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
                    (db_name, table_name)
                )
                return bool(cursor.fetchone())
    
    def get_table_columns(self, db_name: str, table_name: str) -> Dict[str, str]:
        """获取表的列信息"""
        db_name = self._sanitize_identifier(db_name)
        table_name = self._sanitize_identifier(table_name)
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COLUMN_NAME, COLUMN_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                """, (db_name, table_name))
                
                columns = {}
                for row in cursor.fetchall():
                    columns[row['COLUMN_NAME']] = row['COLUMN_TYPE']
                return columns
    
    def get_table_primary_key(self, db_name: str, table_name: str) -> Optional[str]:
        """获取表的主键列名"""
        db_name = self._sanitize_identifier(db_name)
        table_name = self._sanitize_identifier(table_name)
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COLUMN_NAME 
                    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
                    AND CONSTRAINT_NAME = 'PRIMARY'
                """, (db_name, table_name))
                
                result = cursor.fetchone()
                return result['COLUMN_NAME'] if result else None
    
    def ensure_system_columns(self, db_name: str, table_name: str):
        """确保表有系统列，如果没有则添加（保持原有主键结构）"""
        existing_columns = self.get_table_columns(db_name, table_name)
        existing_primary_key = self.get_table_primary_key(db_name, table_name)
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                # 只有在表没有主键且没有id列时，才添加id主键
                if existing_primary_key is None and 'id' not in existing_columns:
                    cursor.execute(f"""
                        ALTER TABLE `{db_name}`.`{table_name}` 
                        ADD COLUMN `id` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY FIRST
                    """)
                    logger.info('自动添加id主键列', {'database': db_name, 'table': table_name})
                elif existing_primary_key is not None:
                    logger.debug('表已有主键，保持原有结构', {
                        'database': db_name, 
                        'table': table_name, 
                        'primary_key': existing_primary_key
                    })
                
                # 检查并添加create_at列
                if 'create_at' not in existing_columns:
                    cursor.execute(f"""
                        ALTER TABLE `{db_name}`.`{table_name}` 
                        ADD COLUMN `create_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    """)
                    logger.info('自动添加create_at列', {'database': db_name, 'table': table_name})
                
                # 检查并添加update_at列
                if 'update_at' not in existing_columns:
                    cursor.execute(f"""
                        ALTER TABLE `{db_name}`.`{table_name}` 
                        ADD COLUMN `update_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    """)
                    logger.info('自动添加update_at列', {'database': db_name, 'table': table_name})
                
                conn.commit()
    
    def create_table(self, db_name: str, table_name: str, columns: Dict[str, str], 
                    primary_keys: Optional[List[str]] = None, 
                    unique_keys: Optional[List[List[str]]] = None,
                    allow_null: bool = False):
        """创建表"""
        db_name = self._sanitize_identifier(db_name)
        table_name = self._sanitize_identifier(table_name)
        
        # 验证columns不为空
        if not columns:
            raise ValueError(f"创建表失败：columns不能为空。数据库: {db_name}, 表: {table_name}")
        
        # 验证unique_keys中的列是否存在于columns中
        if unique_keys:
            business_columns = {k.lower(): k for k in columns.keys() if k.lower() not in ['id', 'create_at', 'update_at']}
            for i, uk in enumerate(unique_keys):
                for col in uk:
                    col_lower = col.lower()
                    if col_lower not in business_columns and col not in columns:
                        raise ValueError(f"唯一约束中的列 '{col}' 不存在于表定义中。可用列: {list(business_columns.keys())}")
        
        # 构建列定义
        column_defs = []
        
        # 始终添加自增ID列作为主键
        column_defs.append("`id` BIGINT NOT NULL AUTO_INCREMENT")
        
        # 添加业务列
        for col_name, col_type in columns.items():
            if col_name.lower() in ['id', 'create_at', 'update_at']:
                continue
            safe_col_name = self._sanitize_identifier(col_name)
            null_constraint = "" if allow_null else " NOT NULL"
            column_defs.append(f"`{safe_col_name}` {col_type}{null_constraint}")
        
        # 添加时间戳列
        column_defs.append("`create_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP")
        column_defs.append("`update_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        
        # 主键定义（始终使用id作为主键）
        primary_key_def = "PRIMARY KEY (`id`)"
        
        # 唯一约束定义 - 使用前缀索引处理超长字段
        unique_defs = []
        if unique_keys:
            for i, uk in enumerate(unique_keys):
                # 过滤掉系统列
                filtered_uk = [col for col in uk if col.lower() not in ['id', 'create_at', 'update_at']]
                if filtered_uk:
                    # 先清理列名标识符，再应用前缀索引
                    safe_uk_parts = []
                    for col in filtered_uk:
                        safe_col_name = self._sanitize_identifier(col)
                        # 检查是否需要前缀索引 - 优先使用原始列名，然后尝试小写
                        col_lower = col.lower()
                        if col in columns:
                            col_type = columns[col].lower()
                        elif col_lower in columns:
                            col_type = columns[col_lower].lower()
                        else:
                            col_type = 'varchar(255)'
                        
                        if 'varchar' in col_type:
                            # 提取varchar长度
                            match = re.search(r'varchar\((\d+)\)', col_type)
                            if match:
                                length = int(match.group(1))
                                # 如果varchar长度超过191字符，使用前缀索引
                                if length > 191:
                                    prefix_length = 191
                                    safe_uk_parts.append(f"`{safe_col_name}`({prefix_length})")
                                else:
                                    safe_uk_parts.append(f"`{safe_col_name}`")
                            else:
                                # 如果没有指定长度，默认使用前缀索引
                                safe_uk_parts.append(f"`{safe_col_name}`(191)")
                        else:
                            # 非varchar字段保持原样
                            safe_uk_parts.append(f"`{safe_col_name}`")
                    
                    unique_name = f"uniq_{i}"
                    unique_defs.append(f"UNIQUE KEY `{unique_name}` ({','.join(safe_uk_parts)})")
        
        # 组合所有定义
        all_defs = column_defs + [primary_key_def] + unique_defs
        
        charset = self.conn_mgr.config['charset']
        sql = f"""
        CREATE TABLE `{db_name}`.`{table_name}` (
            {','.join(all_defs)}
        ) ENGINE=InnoDB DEFAULT CHARSET={charset} COLLATE={self.collation}
        """
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql)
                    conn.commit()
                    logger.debug('表已创建', {'database': db_name, 'table': table_name})
                except Exception as e:
                    logger.error('创建表失败', {
                        'database': db_name,
                        'table': table_name,
                        'error': str(e)
                    })
                    raise
    
    def get_partition_table_name(self, base_name: str, date_value: str, partition_by: str) -> str:
        """获取分表名称"""
        try:
            if isinstance(date_value, str):
                date_obj = pd.to_datetime(date_value)
            else:
                date_obj = date_value
            
            if partition_by == 'year':
                return f"{base_name}_{date_obj.year}"
            elif partition_by == 'month':
                return f"{base_name}_{date_obj.year}_{date_obj.month:02d}"
            else:
                raise ValueError("partition_by必须是'year'或'month'")
        except Exception as e:
            raise ValueError(f"无效的日期值: {date_value}, 错误: {str(e)}")
    
    def _sanitize_identifier(self, identifier: str) -> str:
        """清理标识符"""
        if not identifier or not isinstance(identifier, str):
            raise ValueError(f"无效的标识符: {identifier}")
        
        # 清理特殊字符
        cleaned = re.sub(r'[^\w\u4e00-\u9fff$]', '_', identifier)
        cleaned = re.sub(r'_+', '_', cleaned).strip('_')
        
        if not cleaned:
            raise ValueError(f"标识符清理后为空: {identifier}")
        
        # # 检查MySQL关键字
        # mysql_keywords = {
        #     'select', 'insert', 'update', 'delete', 'from', 'where', 'and', 'or',
        #     'not', 'like', 'in', 'is', 'null', 'true', 'false', 'between'
        # }
        
        if len(cleaned) > 64:
            cleaned = cleaned[:64]
        
        # 不在这里添加反引号，让调用者决定是否需要
        return cleaned
    

class DataProcessor:
    """数据处理器"""
    
    @staticmethod
    def normalize_data(data: Union[Dict, List[Dict], pd.DataFrame], 
                      chunk_size: int = 5000, 
                      memory_limit_mb: int = 100) -> Iterator[List[Dict]]:
        """
        标准化数据格式为分块迭代器
        
        :param data: 输入数据
        :param chunk_size: 每个chunk的大小
        :param memory_limit_mb: 内存限制(MB)，超过时自动调整chunk_size
        """
        # 动态调整chunk_size基于可用内存
        available_memory_mb = psutil.virtual_memory().available / 1024 / 1024
        if available_memory_mb < memory_limit_mb * 2:
            chunk_size = min(chunk_size, 1000)  # 内存紧张时减小chunk
        
        if isinstance(data, pd.DataFrame):
            # 统一将DataFrame的列名转为小写
            data = data.copy()
            data.columns = [col.lower() for col in data.columns]
            
            # 对于大DataFrame，使用更高效的分块方式
            if len(data) > 50000:
                # 大数据集使用pandas的分块读取
                for chunk in pd.read_csv(io.StringIO(data.to_csv(index=False)), chunksize=chunk_size):
                    yield chunk.to_dict('records')
            else:
                for i in range(0, len(data), chunk_size):
                    chunk = data.iloc[i:i + chunk_size]
                    yield chunk.to_dict('records')
        elif isinstance(data, dict):
            # 统一将字典的键转为小写
            normalized_dict = {}
            for key, value in data.items():
                normalized_dict[key.lower()] = value
            yield [normalized_dict]
        elif isinstance(data, list):
            if all(isinstance(item, dict) for item in data):
                # 统一将列表中字典的键转为小写
                normalized_data = []
                for item in data:
                    normalized_item = {}
                    for key, value in item.items():
                        normalized_item[key.lower()] = value
                    normalized_data.append(normalized_item)
                
                for i in range(0, len(normalized_data), chunk_size):
                    yield normalized_data[i:i + chunk_size]
            else:
                raise ValueError("列表中必须全部是字典")
        else:
            raise ValueError("数据格式必须是字典、字典列表或DataFrame")
    
    @staticmethod
    def prepare_data_for_insert(data_chunk: List[Dict], set_typ: Dict[str, str], 
                               allow_null: bool = False) -> List[Dict]:
        """准备插入数据"""
        prepared_data = []
        
        for row_idx, row in enumerate(data_chunk, 1):
            prepared_row = {}
            
            for col_name, col_type in set_typ.items():
                # 跳过系统列（id, create_at, update_at由MySQL自动处理）
                if col_name.lower() in ['id', 'create_at', 'update_at']:
                    continue
                
                value = row.get(col_name)
                try:
                    prepared_row[col_name] = DataValidator.validate_and_convert_value(
                        value, col_type, allow_null
                    )
                except ValueError as e:
                    logger.error('数据验证失败', {
                        '行号': row_idx,
                        '列名': col_name,
                        '原始值': value,
                        '错误': str(e)
                    })
                    raise ValueError(f"行{row_idx}列{col_name}验证失败: {str(e)}")
            
            prepared_data.append(prepared_row)
        
        return prepared_data
    
    @staticmethod
    def partition_data_by_date(data_chunk: List[Dict], date_column: str, 
                              partition_by: str) -> Dict[str, List[Dict]]:
        """按日期分区数据块"""
        partitioned = {}
        table_manager = TableManager(None, None)  # 只用静态方法
        
        for row in data_chunk:
            if date_column not in row:
                logger.warning('缺少分区日期列', {'列名': date_column, '行数据': row})
                continue
            
            try:
                partition_suffix = table_manager.get_partition_table_name(
                    '', row[date_column], partition_by
                ).split('_', 1)[1]  # 获取后缀部分
                
                if partition_suffix not in partitioned:
                    partitioned[partition_suffix] = []
                partitioned[partition_suffix].append(row)
            except Exception as e:
                logger.error('分区处理失败', {'行数据': row, '错误': str(e)})
                continue
        
        return partitioned


class DataInserter:
    """数据插入器"""
    
    def __init__(self, connection_manager: DatabaseConnectionManager, table_manager: TableManager = None):
        self.conn_mgr = connection_manager
        self.table_mgr = table_manager
    
    def insert_data(self, db_name: str, table_name: str, data: List[Dict], 
                   set_typ: Dict[str, str], update_on_duplicate: bool = False) -> Tuple[int, int, int]:
        """插入数据"""
        if not data:
            return 0, 0, 0
        
        # 准备SQL语句（排除系统列）
        columns = [col for col in set_typ.keys() if col.lower() not in ['id', 'create_at', 'update_at']]
        safe_columns = [self.table_mgr._sanitize_identifier(col) if self.table_mgr else col for col in columns]
        placeholders = ','.join(['%s'] * len(columns))
        
        sql = f"""
        INSERT INTO `{db_name}`.`{table_name}` 
        (`{'`,`'.join(safe_columns)}`) 
        VALUES ({placeholders})
        """
        
        if update_on_duplicate:
            # 更新时只更新业务列，不更新create_at，update_at会自动更新
            update_clause = ", ".join([f"`{col}` = VALUES(`{col}`)" for col in safe_columns])
            sql += f" ON DUPLICATE KEY UPDATE {update_clause}"
        
        # 批量插入
        return self._execute_batch_insert(sql, data, columns)
    
    def _execute_batch_insert(self, sql: str, data: List[Dict], 
                             columns: List[str]) -> Tuple[int, int, int]:
        """执行批量插入"""
        # 动态调整批次大小
        estimated_row_size = len(str(data[0])) if data else 100
        max_packet_size = 16 * 1024 * 1024  # 16MB MySQL默认限制
        optimal_batch_size = min(
            max_packet_size // (estimated_row_size * len(columns)),
            2000,  # 最大批次
            len(data)
        )
        batch_size = max(100, optimal_batch_size)  # 最小100条
        
        total_inserted = 0
        total_skipped = 0
        total_failed = 0
        
        with self.conn_mgr.get_connection() as conn:
            with conn.cursor() as cursor:
                # 预处理所有数据，减少循环中的处理开销
                all_values = []
                for row in data:
                    values = [self._ensure_basic_type(row.get(col)) for col in columns]
                    all_values.append(values)
                
                # 分批处理，使用更大的事务批次
                transaction_size = min(5000, len(all_values))  # 每个事务处理的记录数
                
                for tx_start in range(0, len(all_values), transaction_size):
                    tx_end = min(tx_start + transaction_size, len(all_values))
                    tx_values = all_values[tx_start:tx_end]
                    
                    try:
                        # 开始事务
                        conn.begin()
                        
                        # 在事务内分批执行，成功后直接累加
                        for i in range(0, len(tx_values), batch_size):
                            batch_values = tx_values[i:i + batch_size]
                            
                            try:
                                cursor.executemany(sql, batch_values)
                                total_inserted += len(batch_values)
                            except pymysql.err.IntegrityError as e:
                                # 批量插入遇到唯一约束冲突，fallback到逐行插入
                                logger.debug('批量插入唯一约束冲突，尝试逐行插入', {'批次大小': len(batch_values)})
                                
                                # 逐行插入处理冲突
                                for single_value in batch_values:
                                    try:
                                        cursor.execute(sql, single_value)
                                        total_inserted += 1
                                    except pymysql.err.IntegrityError:
                                        total_skipped += 1
                                        logger.debug('单行插入唯一约束冲突，跳过')
                                    except Exception as single_e:
                                        total_failed += 1
                                        logger.error('单行插入失败', {'错误': str(single_e)})
                            except Exception as e:
                                logger.error('批量插入失败', {'错误': str(e), '批次大小': len(batch_values)})
                                raise
                        
                        conn.commit()
                        
                    except Exception as e:
                        conn.rollback()
                        logger.error('事务执行失败，已回滚', {'错误': str(e)})
                        total_failed += len(tx_values)
        
        return total_inserted, total_skipped, total_failed
    
    @staticmethod
    def _ensure_basic_type(value):
        """确保值是基本数据类型"""
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)
        return value


def retry_on_failure(max_retries: int = 3, delay: int = 1):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (pymysql.OperationalError, pymysql.InterfaceError) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning('操作失败，准备重试', {
                            '尝试次数': attempt + 1,
                            '错误': str(e)
                        })
                        time.sleep(delay * (attempt + 1))
                        continue
                    logger.error(f'操作重试{max_retries}次后失败', {'错误': str(e)})
                    raise
                except Exception as e:
                    logger.error('操作失败', {'错误': str(e)})
                    raise
            raise last_exception
        return wrapper
    return decorator


class MySQLUploader:
    """
    MySQL数据上传与查询器
    
    特性：
    - 自动为每个表添加id（BIGINT自增主键）、create_at、update_at时间戳列
    - 支持自动建表、分表、数据类型推断
    - 高可用连接池管理和重试机制
    - 流式批量插入优化
    - 自动设置数据库连接时区为北京时间(+08:00)，确保时间戳一致性
    - 完善的数据查询功能：原始SQL查询、条件查询、ID查询、分页查询、统计查询等
    
    时区说明：
    - 所有数据库连接会自动设置为北京时间(+08:00)
    - create_at和update_at列使用CURRENT_TIMESTAMP，会按照连接时区记录时间
    
    查询方法：
    - query(): 执行原始SQL查询
    - query_by_condition(): 基于条件查询数据
    - query_by_id(): 根据ID查询单条记录
    - query_all(): 查询全表数据(支持分页)
    - query_count(): 统计记录数
    - execute_sql(): 执行任意SQL语句
    - query_to_dataframe(): 查询结果转为pandas DataFrame
    """
    
    def __init__(self, username: str, password: str, host: str = 'localhost', 
                 port: int = 3306, charset: str = 'utf8mb4', 
                 collation: str = 'utf8mb4_0900_ai_ci', pool_size: int = 5,
                 max_retries: int = 3, **kwargs):
        """
        初始化MySQL上传器
        
        :param username: 数据库用户名
        :param password: 数据库密码
        :param host: 数据库主机地址
        :param port: 数据库端口
        :param charset: 字符集
        :param collation: 排序规则
        :param pool_size: 连接池大小
        :param max_retries: 最大重试次数
        """
        self.config = {
            'username': username,
            'password': password,
            'host': host,
            'port': port,
            'charset': charset,
            'pool_size': pool_size,
            **kwargs
        }
        self.collation = collation
        self.max_retries = max_retries
        
        # 初始化组件
        self.conn_mgr = DatabaseConnectionManager(self.config)
        self.table_mgr = TableManager(self.conn_mgr, collation)
        self.data_inserter = DataInserter(self.conn_mgr, self.table_mgr)
    
    @retry_on_failure(max_retries=3)
    def upload_data(self, db_name: str, table_name: str, 
                   data: Union[Dict, List[Dict], pd.DataFrame],
                   set_typ: Optional[Dict[str, str]] = None,
                   allow_null: bool = False,
                   partition_by: Optional[str] = None,
                   partition_date_column: str = '日期',
                   update_on_duplicate: bool = False,
                   unique_keys: Optional[List[List[str]]] = None) -> Dict[str, Any]:
        """
        上传数据到MySQL数据库
        
        注意：系统会自动为每个表添加以下系统列：
        - id: BIGINT自增主键
        - create_at: 创建时间戳（插入时自动设置）
        - update_at: 更新时间戳（插入和更新时自动设置）
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param data: 要上传的数据，支持字典、字典列表、DataFrame
        :param set_typ: 列类型定义，如果为None则自动推断（无需包含系统列）
        :param allow_null: 是否允许空值
        :param partition_by: 分表方式('year'或'month')
        :param partition_date_column: 分表日期列名
        :param update_on_duplicate: 遇到重复数据时是否更新
        :param unique_keys: 唯一约束列表（无需包含系统列）
        :return: 上传结果详情
        """
        if db_name is None or table_name is None:
            logger.error('数据库名或表名不能为空', {'db_name': db_name, 'table_name': table_name})
            return {
                'success': False,
                'inserted_rows': 0,
                'skipped_rows': 0,
                'failed_rows': 0,
                'tables_created': []
            }
        db_name = db_name.lower()
        table_name = table_name.lower()
        
        result = {
            'success': False,
            'inserted_rows': 0,
            'skipped_rows': 0,
            'failed_rows': 0,
            'tables_created': []
        }
        
        try:
            
            # 标准化数据为流式迭代器
            normalized_data = DataProcessor.normalize_data(data)
            
            # 推断或验证列类型
            if set_typ is None or not set_typ:
                # 取第一个chunk进行类型推断
                first_chunk = next(iter(normalized_data))
                
                if not first_chunk:
                    raise ValueError("数据为空，无法推断列类型")
                
                set_typ = DataTypeInferrer.infer_types_from_data(first_chunk)
                # 重新创建迭代器
                normalized_data = DataProcessor.normalize_data(data)
                logger.debug('自动推断数据类型', {'类型映射': set_typ})
                
                # 验证推断结果
                if not set_typ or not any(col for col in set_typ.keys() if col.lower() not in ['id', 'create_at', 'update_at']):
                    raise ValueError(f"类型推断失败，无有效业务列。推断结果: {set_typ}")
            
            # 将set_typ的键统一转为小写
            set_typ = self.tran_set_typ_to_lower(set_typ)
            
            # 最终验证：确保有业务列定义
            business_columns = {k: v for k, v in set_typ.items() if k.lower() not in ['id', 'create_at', 'update_at']}
            if not business_columns:
                raise ValueError(f"没有有效的业务列定义。set_typ: {set_typ}")
            
            # 确保数据库存在
            self.table_mgr.ensure_database_exists(db_name)
            
            # 处理分表逻辑
            
            if partition_by:
                upload_result = self._handle_partitioned_upload(
                    db_name, table_name, normalized_data, set_typ,
                    partition_by, partition_date_column, allow_null,
                    update_on_duplicate, unique_keys
                )
            else:
                upload_result = self._handle_single_table_upload(
                    db_name, table_name, normalized_data, set_typ,
                    allow_null, update_on_duplicate, unique_keys
                )
            
            # 合并结果
            result.update(upload_result)
            result['success'] = upload_result.get('failed_rows', 0) == 0
            
        except Exception as e:
            logger.error('数据上传失败', {
                '数据库': db_name,
                '表名': table_name,
                '错误': str(e)
            })
            result['success'] = False
        
        return result
    
    def _handle_single_table_upload(self, db_name: str, table_name: str,
                                   data: Iterator[List[Dict]], 
                                   set_typ: Dict[str, str],
                                   allow_null: bool, update_on_duplicate: bool,
                                   unique_keys: Optional[List[List[str]]]) -> Dict[str, Any]:
        """处理单表上传"""
        result = {
            'inserted_rows': 0,
            'skipped_rows': 0,
            'failed_rows': 0,
            'tables_created': []
        }
        
        # 确保表存在
        if not self.table_mgr.table_exists(db_name, table_name):
            self.table_mgr.create_table(db_name, table_name, set_typ, 
                                       unique_keys=unique_keys, allow_null=allow_null)
            result['tables_created'].append(f"{db_name}.{table_name}")
        else:
            # 表已存在，确保有时间戳列（但保持原有主键结构）
            self.table_mgr.ensure_system_columns(db_name, table_name)
        
        # 流式处理每个数据块
        for chunk in data:
            if not chunk:
                continue
            
            prepared_chunk = DataProcessor.prepare_data_for_insert(
                chunk, set_typ, allow_null
            )
            
            inserted, skipped, failed = self.data_inserter.insert_data(
                db_name, table_name, prepared_chunk, set_typ, update_on_duplicate
            )
            
            result['inserted_rows'] += inserted
            result['skipped_rows'] += skipped
            result['failed_rows'] += failed
        
        logger.info('单表上传完成', {
            '数据库': db_name,
            '表名': table_name,
            '插入': result['inserted_rows'],
            '跳过': result['skipped_rows'],
            '失败': result['failed_rows']
        })
        
        return result
    
    def _handle_partitioned_upload(self, db_name: str, base_table_name: str,
                                  data: Iterator[List[Dict]], 
                                  set_typ: Dict[str, str],
                                  partition_by: str, partition_date_column: str,
                                  allow_null: bool, update_on_duplicate: bool,
                                  unique_keys: Optional[List[List[str]]]) -> Dict[str, Any]:
        """处理分表上传"""
        result = {
            'inserted_rows': 0,
            'skipped_rows': 0,
            'failed_rows': 0,
            'tables_created': []
        }
        
        # 使用更小的缓冲区，更频繁地刷新
        partition_buffers = {}
        buffer_limit = 1000  # 减小缓冲区大小
        
        # 记录已创建的表，避免重复检查
        created_tables = set()
        
        for chunk in data:
            if not chunk:
                continue
            
            # 按日期分区当前chunk
            partitioned_chunk = DataProcessor.partition_data_by_date(
                chunk, partition_date_column, partition_by
            )
            
            # 将数据添加到对应分区缓冲区
            for partition_suffix, partition_data in partitioned_chunk.items():
                if partition_suffix not in partition_buffers:
                    partition_buffers[partition_suffix] = []
                partition_buffers[partition_suffix].extend(partition_data)
                
                # 更频繁地刷新缓冲区
                if len(partition_buffers[partition_suffix]) >= buffer_limit:
                    partition_result = self._process_partition_buffer_optimized(
                        db_name, base_table_name, partition_suffix,
                        partition_buffers[partition_suffix], set_typ,
                        allow_null, update_on_duplicate, unique_keys, created_tables
                    )
                    self._merge_partition_result(result, partition_result)
                    partition_buffers[partition_suffix] = []  # 清空缓冲区
            
            # 定期检查所有缓冲区，防止某些分区数据积累过多
            total_buffered = sum(len(buffer) for buffer in partition_buffers.values())
            if total_buffered > 5000:  # 总缓冲超过5000条时强制刷新
                for partition_suffix in list(partition_buffers.keys()):
                    if partition_buffers[partition_suffix]:
                        partition_result = self._process_partition_buffer_optimized(
                            db_name, base_table_name, partition_suffix,
                            partition_buffers[partition_suffix], set_typ,
                            allow_null, update_on_duplicate, unique_keys, created_tables
                        )
                        self._merge_partition_result(result, partition_result)
                        partition_buffers[partition_suffix] = []
        
        # 处理剩余的缓冲区数据
        for partition_suffix, buffer_data in partition_buffers.items():
            if buffer_data:
                partition_result = self._process_partition_buffer_optimized(
                    db_name, base_table_name, partition_suffix,
                    buffer_data, set_typ, allow_null, update_on_duplicate, unique_keys, created_tables
                )
                self._merge_partition_result(result, partition_result)
        
        logger.info('分表上传完成', {
            '数据库': db_name,
            '基础表名': base_table_name,
            '分区数': len(created_tables),
            '插入': result['inserted_rows'],
            '跳过': result['skipped_rows'],
            '失败': result['failed_rows']
        })
        
        return result
    
    def _process_partition_buffer_optimized(self, db_name: str, base_table_name: str,
                                          partition_suffix: str, partition_data: List[Dict],
                                          set_typ: Dict[str, str], allow_null: bool,
                                          update_on_duplicate: bool, 
                                          unique_keys: Optional[List[List[str]]],
                                          created_tables: set) -> Dict[str, Any]:
        """处理单个分区的缓冲数据"""
        partition_table_name = f"{base_table_name}_{partition_suffix}"
        
        result = {
            'inserted_rows': 0,
            'skipped_rows': 0,
            'failed_rows': 0,
            'tables_created': []
        }
        
        # 优化表存在性检查
        table_key = f"{db_name}.{partition_table_name}"
        if table_key not in created_tables:
            if not self.table_mgr.table_exists(db_name, partition_table_name):
                self.table_mgr.create_table(db_name, partition_table_name, set_typ, 
                                           unique_keys=unique_keys, allow_null=allow_null)
                result['tables_created'].append(table_key)
            else:
                # 表已存在，确保有时间戳列（但保持原有主键结构）
                self.table_mgr.ensure_system_columns(db_name, partition_table_name)
            created_tables.add(table_key)
        
        # 准备并插入数据
        prepared_data = DataProcessor.prepare_data_for_insert(
            partition_data, set_typ, allow_null
        )
        
        inserted, skipped, failed = self.data_inserter.insert_data(
            db_name, partition_table_name, prepared_data, set_typ, update_on_duplicate
        )
        
        result['inserted_rows'] = inserted
        result['skipped_rows'] = skipped
        result['failed_rows'] = failed
        
        return result
    
    def _merge_partition_result(self, main_result: Dict[str, Any], 
                               partition_result: Dict[str, Any]):
        """合并分区处理结果"""
        main_result['inserted_rows'] += partition_result['inserted_rows']
        main_result['skipped_rows'] += partition_result['skipped_rows']
        main_result['failed_rows'] += partition_result['failed_rows']
        main_result['tables_created'].extend(partition_result['tables_created'])
    
    def tran_set_typ_to_lower(self, set_typ: Dict[str, str]) -> Dict[str, str]:
        if not isinstance(set_typ, dict) or set_typ is None:
            return {}

        set_typ_lower = {}
        for key, value in set_typ.items():
            set_typ_lower[key.lower()] = value
            
        return set_typ_lower
    
    # ==================== 数据查询功能 ====================
    
    def _sanitize_order_by(self, order_by: str) -> str:
        """
        清理和验证ORDER BY子句，防止SQL注入
        
        :param order_by: 排序子句，例如 'id DESC' 或 'name ASC, age DESC'
        :return: 安全的排序子句
        :raises ValueError: 如果包含非法字符
        """
        if not order_by or not isinstance(order_by, str):
            raise ValueError("order_by参数必须是非空字符串")
        
        # 移除多余的空格
        order_by = ' '.join(order_by.split())
        
        # 只允许字母、数字、下划线、逗号、空格、点号、ASC、DESC
        # 防止注入分号、注释符等危险字符
        allowed_pattern = r'^[a-zA-Z0-9_,.\s]+$'
        if not re.match(allowed_pattern, order_by):
            raise ValueError(f"order_by包含非法字符: {order_by}")
        
        # 验证每个排序字段
        parts = [p.strip() for p in order_by.split(',')]
        sanitized_parts = []
        
        for part in parts:
            tokens = part.split()
            if len(tokens) == 0:
                continue
            
            # 第一个token是列名
            col_name = tokens[0]
            # 清理列名
            safe_col = self.table_mgr._sanitize_identifier(col_name)
            
            # 第二个token可选，应该是ASC或DESC
            direction = ''
            if len(tokens) == 2:
                direction_upper = tokens[1].upper()
                if direction_upper not in ['ASC', 'DESC']:
                    raise ValueError(f"排序方向必须是ASC或DESC: {tokens[1]}")
                direction = f" {direction_upper}"
            elif len(tokens) > 2:
                raise ValueError(f"排序字段格式错误: {part}")
            
            sanitized_parts.append(f"`{safe_col}`{direction}")
        
        return ', '.join(sanitized_parts)
    
    def _validate_limit_offset(self, limit: Optional[int], offset: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
        """
        验证和清理limit和offset参数
        
        :param limit: 限制条数
        :param offset: 偏移量
        :return: 验证后的(limit, offset)元组
        :raises ValueError: 如果参数无效
        """
        if limit is not None:
            try:
                limit = int(limit)
                if limit < 0:
                    raise ValueError("limit必须是非负整数")
                if limit > 1000000:  # 设置一个合理的上限
                    raise ValueError("limit不能超过1000000")
            except (TypeError, ValueError) as e:
                raise ValueError(f"无效的limit参数: {limit}, 错误: {str(e)}")
        
        if offset is not None:
            try:
                offset = int(offset)
                if offset < 0:
                    raise ValueError("offset必须是非负整数")
            except (TypeError, ValueError) as e:
                raise ValueError(f"无效的offset参数: {offset}, 错误: {str(e)}")
        
        return limit, offset
    
    @retry_on_failure(max_retries=3)
    def query(self, db_name: str, sql: str, params: Optional[Tuple] = None, 
             fetch_one: bool = False) -> Union[List[Dict], Dict, None]:
        """
        执行原始SQL查询
        
        :param db_name: 数据库名
        :param sql: SQL查询语句
        :param params: SQL参数(可选)
        :param fetch_one: 是否只返回一条记录
        :return: 查询结果(字典列表或单个字典)
        
        注意：此方法执行原始SQL，请确保SQL语句的安全性，建议使用参数化查询
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        
        try:
            with self.conn_mgr.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 在SQL中指定数据库，而不是使用USE语句
                    # 这样可以避免连接池中的连接状态污染
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    # 获取结果
                    if fetch_one:
                        result = cursor.fetchone()
                        logger.debug('查询完成(单条)', {'数据库': db_name, 'SQL': sql[:100]})
                        return result
                    else:
                        results = cursor.fetchall()
                        logger.debug('查询完成', {
                            '数据库': db_name, 
                            'SQL': sql[:100], 
                            '记录数': len(results)
                        })
                        return results
                        
        except Exception as e:
            logger.error('查询失败', {
                '数据库': db_name,
                'SQL': sql[:100],
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def query_by_condition(self, db_name: str, table_name: str, 
                          conditions: Optional[Dict[str, Any]] = None,
                          columns: Optional[List[str]] = None,
                          order_by: Optional[str] = None,
                          limit: Optional[int] = None,
                          offset: Optional[int] = None) -> List[Dict]:
        """
        基于条件查询数据
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param conditions: 查询条件字典,例如 {'name': 'Alice', 'age': 25}
        :param columns: 要查询的列名列表,None表示查询所有列
        :param order_by: 排序字段,例如 'id DESC' 或 'name ASC, age DESC'
        :param limit: 限制返回记录数
        :param offset: 偏移量(用于分页)
        :return: 查询结果列表
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        table_name = self.table_mgr._sanitize_identifier(table_name.lower())
        
        # 验证limit和offset
        limit, offset = self._validate_limit_offset(limit, offset)
        
        # 构建查询列
        if columns:
            safe_columns = [f"`{self.table_mgr._sanitize_identifier(col)}`" for col in columns]
            columns_str = ','.join(safe_columns)
        else:
            columns_str = '*'
        
        # 构建SQL - 在SQL中指定数据库
        sql = f"SELECT {columns_str} FROM `{db_name}`.`{table_name}`"
        params = []
        
        # 构建WHERE条件
        if conditions:
            where_clauses = []
            for col, value in conditions.items():
                safe_col = self.table_mgr._sanitize_identifier(col)
                where_clauses.append(f"`{safe_col}` = %s")
                params.append(value)
            
            sql += " WHERE " + " AND ".join(where_clauses)
        
        # 添加排序 - 使用安全的排序处理
        if order_by:
            try:
                safe_order_by = self._sanitize_order_by(order_by)
                sql += f" ORDER BY {safe_order_by}"
            except ValueError as e:
                logger.error('排序参数验证失败', {'order_by': order_by, '错误': str(e)})
                raise
        
        # 添加分页 - 使用参数化查询
        if limit is not None:
            sql += f" LIMIT %s"
            params.append(limit)
            if offset is not None:
                sql += f" OFFSET %s"
                params.append(offset)
        
        try:
            return self.query(db_name, sql, tuple(params) if params else None)
        except Exception as e:
            logger.error('条件查询失败', {
                '数据库': db_name,
                '表名': table_name,
                '条件': conditions,
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def query_by_id(self, db_name: str, table_name: str, record_id: int) -> Optional[Dict]:
        """
        根据ID查询单条记录
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param record_id: 记录ID
        :return: 单条记录或None
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        table_name = self.table_mgr._sanitize_identifier(table_name.lower())
        
        # 验证ID是整数
        try:
            record_id = int(record_id)
        except (TypeError, ValueError):
            raise ValueError(f"记录ID必须是整数: {record_id}")
        
        sql = f"SELECT * FROM `{db_name}`.`{table_name}` WHERE `id` = %s LIMIT 1"
        
        try:
            return self.query(db_name, sql, (record_id,), fetch_one=True)
        except Exception as e:
            logger.error('ID查询失败', {
                '数据库': db_name,
                '表名': table_name,
                'ID': record_id,
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def query_all(self, db_name: str, table_name: str, 
                 page: int = 1, page_size: int = 1000,
                 order_by: str = 'id ASC') -> Dict[str, Any]:
        """
        查询全表数据(支持分页)
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param page: 页码(从1开始)
        :param page_size: 每页记录数
        :param order_by: 排序方式,默认按id升序
        :return: 包含数据和分页信息的字典
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        table_name = self.table_mgr._sanitize_identifier(table_name.lower())
        
        # 验证页码和每页大小
        try:
            page = int(page)
            if page < 1:
                raise ValueError("页码必须从1开始")
        except (TypeError, ValueError) as e:
            raise ValueError(f"无效的页码: {page}, 错误: {str(e)}")
        
        try:
            page_size = int(page_size)
            if page_size < 1:
                raise ValueError("每页记录数必须大于0")
            if page_size > 10000:
                raise ValueError("每页记录数不能超过10000")
        except (TypeError, ValueError) as e:
            raise ValueError(f"无效的每页记录数: {page_size}, 错误: {str(e)}")
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        try:
            # 查询数据
            data = self.query_by_condition(
                db_name, table_name,
                order_by=order_by,
                limit=page_size,
                offset=offset
            )
            
            # 查询总记录数
            total_count = self.query_count(db_name, table_name)
            
            # 计算总页数
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            result = {
                'data': data,
                'pagination': {
                    'current_page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
            logger.debug('分页查询完成', {
                '数据库': db_name,
                '表名': table_name,
                '当前页': page,
                '记录数': len(data),
                '总记录数': total_count
            })
            
            return result
            
        except Exception as e:
            logger.error('全表查询失败', {
                '数据库': db_name,
                '表名': table_name,
                '页码': page,
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def query_count(self, db_name: str, table_name: str, 
                   conditions: Optional[Dict[str, Any]] = None) -> int:
        """
        统计记录数
        
        :param db_name: 数据库名
        :param table_name: 表名
        :param conditions: 查询条件(可选)
        :return: 记录总数
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        table_name = self.table_mgr._sanitize_identifier(table_name.lower())
        
        sql = f"SELECT COUNT(*) as count FROM `{db_name}`.`{table_name}`"
        params = []
        
        # 构建WHERE条件
        if conditions:
            where_clauses = []
            for col, value in conditions.items():
                safe_col = self.table_mgr._sanitize_identifier(col)
                where_clauses.append(f"`{safe_col}` = %s")
                params.append(value)
            
            sql += " WHERE " + " AND ".join(where_clauses)
        
        try:
            result = self.query(db_name, sql, tuple(params) if params else None, fetch_one=True)
            count = result['count'] if result else 0
            
            logger.debug('统计完成', {
                '数据库': db_name,
                '表名': table_name,
                '记录数': count,
                '条件': conditions
            })
            
            return count
            
        except Exception as e:
            logger.error('统计失败', {
                '数据库': db_name,
                '表名': table_name,
                '条件': conditions,
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def execute_sql(self, db_name: str, sql: str, params: Optional[Tuple] = None,
                   fetch_result: bool = False) -> Union[List[Dict], int, None]:
        """
        执行任意SQL语句(包括DML和DDL)
        
        :param db_name: 数据库名
        :param sql: SQL语句
        :param params: SQL参数(可选)
        :param fetch_result: 是否获取查询结果(SELECT语句)
        :return: 查询结果或影响的行数
        
        警告：此方法执行任意SQL，请确保SQL语句的安全性！
        建议使用参数化查询防止SQL注入。
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        
        try:
            with self.conn_mgr.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 执行SQL
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    # 如果是查询语句,获取结果
                    if fetch_result or sql.strip().upper().startswith('SELECT'):
                        results = cursor.fetchall()
                        logger.debug('SQL执行完成(查询)', {
                            '数据库': db_name,
                            'SQL': sql[:100],
                            '记录数': len(results)
                        })
                        return results
                    else:
                        # 对于DML语句,提交事务并返回影响的行数
                        conn.commit()
                        affected_rows = cursor.rowcount
                        logger.info('SQL执行完成', {
                            '数据库': db_name,
                            'SQL': sql[:100],
                            '影响行数': affected_rows
                        })
                        return affected_rows
                        
        except Exception as e:
            logger.error('SQL执行失败', {
                '数据库': db_name,
                'SQL': sql[:100],
                '错误': str(e)
            })
            raise
    
    @retry_on_failure(max_retries=3)
    def query_to_dataframe(self, db_name: str, sql: str, 
                          params: Optional[Tuple] = None) -> pd.DataFrame:
        """
        执行查询并返回pandas DataFrame
        
        :param db_name: 数据库名
        :param sql: SQL查询语句
        :param params: SQL参数(可选)
        :return: pandas DataFrame
        
        注意：此方法执行原始SQL，请确保SQL语句的安全性，建议使用参数化查询
        """
        db_name = self.table_mgr._sanitize_identifier(db_name.lower())
        
        try:
            results = self.query(db_name, sql, params)
            df = pd.DataFrame(results)
            
            logger.debug('查询转DataFrame完成', {
                '数据库': db_name,
                'SQL': sql[:100],
                '行数': len(df),
                '列数': len(df.columns) if not df.empty else 0
            })
            
            return df
            
        except Exception as e:
            logger.error('查询转DataFrame失败', {
                '数据库': db_name,
                'SQL': sql[:100],
                '错误': str(e)
            })
            raise
    
    # ==================== 数据查询功能结束 ====================
    
    def close(self):
        """关闭连接"""
        if self.conn_mgr:
            self.conn_mgr.close()
    
    def __del__(self):
        try:
            self.close()
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# 使用示例
if __name__ == '__main__':
    # 初始化上传器
    uploader = MySQLUploader(
        username='your_username',
        password='your_password',
        host='localhost',
        port=3306
    )
    
    # ========== 数据上传示例 ==========
    sample_data = [
        {'name': 'Alice', 'age': 25, 'salary': 50000.0, '日期': '2023-01-01'},
        {'name': 'Bob', 'age': 30, 'salary': 60000.0, '日期': '2023-01-02'},
        {'name': 'Charlie', 'age': 35, 'salary': 70000.0, '日期': '2023-01-03'},
    ]
    
    # 上传数据（自动推断类型，流式处理）
    result = uploader.upload_data(
        db_name='test_db',
        table_name='test_table',
        data=sample_data,
        update_on_duplicate=True,
        unique_keys=[['name', '日期']]
    )
    print(f"上传结果: {result}")
    
    # ========== 数据查询示例 ==========
    
    # 1. 根据ID查询单条记录
    record = uploader.query_by_id('test_db', 'test_table', 1)
    print(f"\n查询ID=1的记录: {record}")
    
    # 2. 条件查询
    results = uploader.query_by_condition(
        db_name='test_db',
        table_name='test_table',
        conditions={'name': 'Alice'},
        order_by='id DESC'
    )
    print(f"\n查询name='Alice'的记录: {results}")
    
    # 3. 分页查询全表数据
    page_result = uploader.query_all(
        db_name='test_db',
        table_name='test_table',
        page=1,
        page_size=10
    )
    print(f"\n分页查询结果: 共{page_result['pagination']['total_count']}条记录")
    print(f"当前页数据: {page_result['data']}")
    
    # 4. 统计记录数
    total = uploader.query_count('test_db', 'test_table')
    print(f"\n总记录数: {total}")
    
    # 条件统计
    count_by_name = uploader.query_count(
        'test_db', 
        'test_table', 
        conditions={'name': 'Alice'}
    )
    print(f"name='Alice'的记录数: {count_by_name}")
    
    # 5. 原始SQL查询
    custom_results = uploader.query(
        db_name='test_db',
        sql="SELECT name, age, salary FROM test_table WHERE age > %s",
        params=(25,)
    )
    print(f"\n自定义SQL查询结果: {custom_results}")
    
    # 6. 查询结果转为DataFrame
    df = uploader.query_to_dataframe(
        db_name='test_db',
        sql="SELECT * FROM test_table ORDER BY age"
    )
    print(f"\nDataFrame查询结果:\n{df}")
    
    # 7. 执行更新/删除等SQL语句
    affected_rows = uploader.execute_sql(
        db_name='test_db',
        sql="UPDATE test_table SET salary = salary * 1.1 WHERE age > %s",
        params=(30,),
        fetch_result=False
    )
    print(f"\n更新了 {affected_rows} 行记录")
    
    # 关闭连接
    uploader.close()
    print("\n数据库连接已关闭") 