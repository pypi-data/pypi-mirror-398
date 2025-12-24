# -*- coding: utf-8 -*-
"""
Redis智能缓存系统

主要功能：
1. Redis缓存的CRUD操作
2. 命名空间隔离
3. 智能TTL策略
4. 专业统计分析并提交到MySQL
5. 缓存健康检查和监控
6. 热点键分析
7. 响应时间分析
8. 业务指标计算
"""

import json
import time
import threading
import socket
import os
import statistics
import enum
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from threading import Event
from collections import defaultdict, deque
import redis
# from mdbq.log import mylogger


# # 全局日志器
# logger = mylogger.MyLogger(
#     logging_mode='file',
#     log_level='info',
#     log_format='json',
#     max_log_size=50,
#     backup_count=5,
#     enable_async=False,
#     sample_rate=1,
#     sensitive_fields=[],
#     enable_metrics=False,
# )


class CacheStatsCollector:
    """缓存统计收集器 """
    
    def __init__(self, enabled: bool = True, mysql_pool=None, config: dict = None):
        self.enabled = enabled
        self.mysql_pool = mysql_pool
        self.config = config or {}
        self.process_id = os.getpid()
        self.instance_name = self.config.get('instance_name', 'default')
        
        # 统计数据
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_operations': 0,
            'start_time': time.time()
        }
        self._lock = threading.RLock()
        self.response_times = deque(maxlen=1000)
        self.namespace_stats = defaultdict(int)
        
        # 定时提交控制
        self.submit_interval = self.config.get('submit_interval', 600)  # 每隔N秒定时提交一次（期间有新操作时）
        self.last_submit_time = time.time()
        self.last_operation_count = 0  # 上次提交时的操作总数
        
        # 后台定时器
        self._timer = None
        self._shutdown_event = threading.Event()
        self._error_count = 0  # 连续错误计数
        self._max_errors = 5   # 最大连续错误次数
        
        # 启动后台定时提交
        if self.enabled and self.mysql_pool:
            self._start_background_timer()

    def record_operation(self, operation: str, response_time: float = 0, namespace: str = ""):
        """记录操作统计"""
        if not self.enabled:
            return
        
        try:
            with self._lock:
                old_total = self.stats['total_operations']
                
                self.stats['total_operations'] += 1
                self.stats[operation] = self.stats.get(operation, 0) + 1
                
                if response_time > 0:
                    self.response_times.append(response_time)
                
                if namespace:
                    self.namespace_stats[namespace] += 1
                
                # 检查是否需要提交统计数据（容错处理）
                try:
                    self._check_and_submit()
                except Exception as submit_error:
                    # 统计提交失败不应影响统计记录
                    # logger.error("统计数据提交检查失败，但统计记录继续", {
                    #     'instance_name': self.instance_name,
                    #     'process_id': self.process_id,
                    #     'operation': operation,
                    #     'submit_error': str(submit_error)
                    # })
                    pass
        except Exception as e:
            # 统计记录失败不应影响缓存操作
            # logger.error("统计记录失败，但缓存操作继续", {
            #     'instance_name': self.instance_name,
            #     'process_id': self.process_id,
            #     'operation': operation,
            #     'error': str(e)
            # })
            pass
    
    def _start_background_timer(self):
        """启动后台定时提交线程"""
        if self._timer is not None:
            return  # 已经启动
        
        self._timer = threading.Timer(self.submit_interval, self._background_submit)
        self._timer.daemon = True  # 设置为守护线程
        self._timer.start()
    
    def _background_submit(self):
        """后台定时提交方法"""
        if self._shutdown_event.is_set():
            return  # 已关闭，不再提交
        
        try:
            # 执行提交检查（强制检查，不受时间间隔限制）
            self._check_and_submit(force_check=True)
            # 成功执行，重置错误计数
            self._error_count = 0
            
        except Exception as e:
            self._error_count += 1
            # logger.error("后台定时提交失败", {
            #     'instance_name': self.instance_name,
            #     'process_id': self.process_id,
            #     'error': str(e),
            #     'error_type': type(e).__name__,
            #     'error_count': self._error_count,
            #     'max_errors': self._max_errors
            # })
            
            # 如果连续错误次数过多，停止定时器
            if self._error_count >= self._max_errors:
                # logger.error("后台定时器连续错误过多，停止定时提交", {
                #     'instance_name': self.instance_name,
                #     'process_id': self.process_id,
                #     'error_count': self._error_count
                # })
                return  # 不再安排下一次定时器
                
        finally:
            # 安排下一次定时提交（仅在未达到最大错误次数时）
            if not self._shutdown_event.is_set() and self._error_count < self._max_errors:
                self._timer = threading.Timer(self.submit_interval, self._background_submit)
                self._timer.daemon = True
                self._timer.start()
    
    def _check_and_submit(self, force_check=False):
        """检查并提交统计数据
        
        Args:
            force_check: 是否强制检查（用于后台定时器）
        """
        if not self.mysql_pool:
            return
            
        current_time = time.time()
        time_since_last_submit = current_time - self.last_submit_time
        
        # 提交逻辑：每隔固定秒数且期间有新操作则提交
        should_check_time = force_check or time_since_last_submit >= self.submit_interval
        
        if should_check_time:
            # 检查是否有新的操作（与上次提交时相比）
            new_operations = self.stats['total_operations'] - self.last_operation_count
            
            if new_operations > 0:
                # 有新操作，提交统计数据
                try:
                    self._submit_to_mysql()
                    self.last_submit_time = current_time
                    self.last_operation_count = self.stats['total_operations']
                    
                    # logger.info("统计数据提交成功", {
                    #     'instance_name': self.instance_name,
                    #     'total_operations': self.stats['total_operations'],
                    #     'new_operations': new_operations,
                    #     'trigger_type': 'background_timer' if force_check else 'operation_triggered'
                    # })
                except Exception as e:
                    # logger.error("统计数据提交失败", {
                    #     'instance_name': self.instance_name,
                    #     'error': str(e),
                    #     'trigger_type': 'background_timer' if force_check else 'operation_triggered'
                    # })
                    pass
            else:
                # 无新操作，跳过提交但更新时间
                self.last_submit_time = current_time
                
    def _submit_to_mysql(self):
        """同步提交统计数据到MySQL"""
        if not self.mysql_pool:
            return
            
        stats_data = self.get_stats()
        if not stats_data.get('enabled'):
            return
        
        db_name = self.config.get('db_name')
        table_name = self.config.get('table_name')
        
        # 如果没有配置数据库名和表名，不提交统计
        if not db_name or not table_name:
            return
            
        try:
            connection = self.mysql_pool.connection()
            with connection.cursor() as cursor:
                # 选择数据库
                cursor.execute(f"USE `{db_name}`")
                
                # 插入统计数据
                insert_sql = f"""
                INSERT INTO `{table_name}` (
                    `日期`, `实例标识`, `主机名`, `进程ID`, `统计时间`,
                    `缓存命中`, `缓存未命中`, `缓存设置`, `缓存删除`, `缓存错误`, `总操作数`,
                    `命中率`, `平均响应时间`, `运行时间`, `命名空间统计`
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                insert_data = (
                    datetime.now().strftime('%Y-%m-%d'),
                    f"{self.instance_name}_pid_{self.process_id}",
                    socket.gethostname(),
                    self.process_id,
                    datetime.now(),
                    stats_data['hits'],
                    stats_data['misses'],
                    stats_data['sets'],
                    stats_data['deletes'],
                    stats_data['errors'],
                    stats_data['total_operations'],
                    stats_data['hit_rate_percent'],
                    stats_data['avg_response_time_ms'],
                    stats_data['uptime_seconds'],
                    json.dumps(stats_data['namespace_stats'], ensure_ascii=False)
                )
                
                cursor.execute(insert_sql, insert_data)
                connection.commit()
                
            connection.close()
            
        except Exception as e:
            # logger.error("MySQL提交失败", {
            #     'instance_name': self.instance_name,
            #     'database': db_name,
            #     'table': table_name,
            #     'error': str(e)
            # })
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        if not self.enabled:
            return {'enabled': False, 'message': '统计功能已禁用'}
        
        with self._lock:
            uptime = time.time() - self.stats['start_time']
            total_cache_ops = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_cache_ops * 100) if total_cache_ops > 0 else 0
            avg_response_time = statistics.mean(self.response_times) if self.response_times else 0
            
            return {
                'enabled': True,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'errors': self.stats['errors'],
                'total_operations': self.stats['total_operations'],
                'hit_rate_percent': round(hit_rate, 2),
                'avg_response_time_ms': round(avg_response_time, 2),
                'uptime_seconds': round(uptime, 2),
                'namespace_stats': dict(self.namespace_stats),
                'last_updated': datetime.now().isoformat(),
                'process_id': self.process_id
            }
    
    def shutdown(self):
        """关闭统计收集器，停止后台定时器"""
        # logger.info("关闭统计收集器", {
        #     'instance_name': self.instance_name
        # })
        
        # 设置关闭标志
        self._shutdown_event.set()
        
        # 取消定时器
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
    
    def reset_stats(self):
        """重置统计数据"""
        if not self.enabled:
            return
            
        with self._lock:
            self.stats = {
                'hits': 0,
                'misses': 0,
                'sets': 0,
                'deletes': 0,
                'errors': 0,
                'total_operations': 0,
                'start_time': time.time()
            }
            self.response_times.clear()
            self.namespace_stats.clear()
            self.last_submit_time = time.time()
            self.last_operation_count = 0


class CacheSystemState(enum.Enum):
    """缓存系统状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    MYSQL_READY = "mysql_ready"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class CacheConfig:
    """缓存配置类"""
    def __init__(self, **kwargs):
        # 基础配置
        self.default_ttl = kwargs.get('default_ttl', 3600)  # 默认过期时间(秒)
        self.stats_submit_interval = kwargs.get('stats_submit_interval', 600)  # 每隔N秒定时提交一次（期间有新操作时）
        self.enable_stats = kwargs.get('enable_stats', True)  # 是否启用统计功能
        self.max_value_size = kwargs.get('max_value_size', 10 * 1024 * 1024)  # 最大值大小(字节)
        self.cache_prefix = kwargs.get('cache_prefix', 'cache')  # 缓存键前缀
        self.enable_compression = kwargs.get('enable_compression', True)
        
        # 数据库配置（如果不传则为 None，不会自动创建数据库）
        self.db_name = kwargs.get('db_name', None)
        self.table_name = kwargs.get('table_name', None)
        
        # 智能TTL策略配置
        self.enable_smart_ttl = kwargs.get('enable_smart_ttl', True)  # 启用智能TTL
        self.ttl_min = kwargs.get('ttl_min', 60)  # 最小TTL(秒)
        self.ttl_max = kwargs.get('ttl_max', 7200)  # 最大TTL(秒)
        self.debug_ttl = kwargs.get('debug_ttl', False)  # TTL调试模式
        
        # 自定义TTL模式
        self.custom_namespace_patterns = kwargs.get('custom_namespace_patterns', {})
        self.custom_key_patterns = kwargs.get('custom_key_patterns', {})


class SmartCacheSystem:
    """智能缓存系统 - 单线程"""
    
    def __init__(self, redis_client: redis.Redis, mysql_pool=None, instance_name: str = "default", **config):
        self.redis_client = redis_client
        self.mysql_pool = mysql_pool
        self.instance_name = instance_name
        self.config = CacheConfig(**config)
        
        # 系统状态管理
        self._state = CacheSystemState.INITIALIZING
        self._ready_event = Event()
        
        # 直接初始化统计系统
        self.stats_collector = None
        if self.config.enable_stats:
            self.stats_collector = CacheStatsCollector(
                enabled=True,
                mysql_pool=self.mysql_pool,
                config={
                    'instance_name': self.instance_name,
                    'submit_interval': self.config.stats_submit_interval,  # 每隔N秒定时提交一次（期间有新操作时）
                    'table_name': self.config.table_name,
                    'db_name': self.config.db_name
                }
            )
        
        # 初始化系统
        self._initialize()
    
    def _initialize(self):
        """初始化缓存系统"""
        # 测试Redis连接
        if self._test_redis_connection():
            self._state = CacheSystemState.READY
            self._ready_event.set()
            
            # 如果启用统计且有MySQL连接和数据库配置，创建统计表
            if self.config.enable_stats and self.mysql_pool and self.config.db_name:
                try:
                    self._create_simple_stats_table()
                    self._state = CacheSystemState.MYSQL_READY
                    # logger.info("统计功能已启用", {
                    #     'instance_name': self.instance_name,
                    #     'process_id': os.getpid()
                    # })
                except Exception as e:
                    # logger.error("统计表创建失败", {
                    #     'instance_name': self.instance_name,
                    #     'error': str(e)
                    # })
                    pass
        else:
            self._state = CacheSystemState.ERROR
            # logger.error("Redis连接失败", {'instance_name': self.instance_name})
    
    def _test_redis_connection(self) -> bool:
        """测试Redis连接"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            # logger.error("Redis连接测试失败", {'error': str(e)})
            return False
    
    def _create_simple_stats_table(self):
        """创建统计表"""
        if not self.mysql_pool:
            return
        
        # 如果没有配置数据库名，不创建统计表
        if not self.config.db_name or not self.config.table_name:
            return
        
        try:
            connection = self.mysql_pool.connection()
            with connection.cursor() as cursor:
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.config.db_name}` DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci")
                cursor.execute(f"USE `{self.config.db_name}`")
                
                # 创建统计表
                create_table_sql = f"""
                CREATE TABLE IF NOT EXISTS `{self.config.table_name}` (
                    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
                    `日期` date NOT NULL COMMENT '统计日期',
                    `实例标识` varchar(64) NOT NULL COMMENT '缓存实例标识',
                    `主机名` varchar(100) NOT NULL COMMENT '服务器主机名',
                    `进程ID` int NOT NULL COMMENT '进程ID',
                    `统计时间` timestamp NOT NULL COMMENT '统计时间',
                    
                    -- 基础操作统计
                    `缓存命中` bigint DEFAULT 0 COMMENT '缓存命中次数',
                    `缓存未命中` bigint DEFAULT 0 COMMENT '缓存未命中次数',
                    `缓存设置` bigint DEFAULT 0 COMMENT '缓存设置次数',
                    `缓存删除` bigint DEFAULT 0 COMMENT '缓存删除次数',
                    `缓存错误` bigint DEFAULT 0 COMMENT '缓存错误次数',
                    `总操作数` bigint DEFAULT 0 COMMENT '总操作次数',
                    
                    -- 性能指标
                    `命中率` decimal(5,2) DEFAULT 0.00 COMMENT '命中率百分比',
                    `平均响应时间` decimal(10,2) DEFAULT 0.00 COMMENT '平均响应时间(毫秒)',
                    `运行时间` bigint DEFAULT 0 COMMENT '运行时间(秒)',
                    
                    -- 命名空间统计
                    `命名空间统计` json COMMENT '命名空间统计详情',
                    
                    -- 时间戳
                    `创建时间` timestamp DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                    
                    PRIMARY KEY (`id`),
                    KEY `idx_日期` (`日期`),
                    KEY `idx_实例时间` (`实例标识`, `统计时间`),
                    KEY `idx_创建时间` (`创建时间`)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Redis缓存统计表'
                """
                
                cursor.execute(create_table_sql)
                connection.commit()
                
            connection.close()
            
        except Exception as e:
            # logger.error("统计表初始化失败", {'error': str(e)})
            raise
    
    @property
    def is_ready(self) -> bool:
        """检查系统是否就绪"""
        return self._ready_event.is_set()
    
    @property
    def is_mysql_ready(self) -> bool:
        """检查MySQL是否就绪"""
        return self._state == CacheSystemState.MYSQL_READY
    
    def get(self, key: str, namespace: str = "", default=None) -> Any:
        """获取缓存值"""
        return self._get_with_stats(key, namespace, default)
    
    def _get_with_stats(self, key: str, namespace: str = "", default=None) -> Any:
        """带统计的获取缓存值"""
        if not self.is_ready:
            return default
        
        start_time = time.time()
        try:
            cache_key = self._generate_cache_key(key, namespace)
            value = self.redis_client.get(cache_key)
            response_time = (time.time() - start_time) * 1000
            
            if value is not None:
                # 缓存命中
                if self.stats_collector:
                    self.stats_collector.record_operation('hits', response_time, namespace)
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return value.decode('utf-8')
            else:
                # 缓存未命中
                if self.stats_collector:
                    self.stats_collector.record_operation('misses', response_time, namespace)
                return default
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            if self.stats_collector:
                self.stats_collector.record_operation('errors', response_time, namespace)
            # logger.error("缓存获取失败", {
            #     'key': key,
            #     'namespace': namespace,
            #     'error': str(e)
            # })
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "") -> bool:
        """设置缓存值"""
        return self._set_with_stats(key, value, ttl, namespace)
    
    def _set_with_stats(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "") -> bool:
        """带统计的设置缓存值"""
        if not self.is_ready:
            return False
        
        start_time = time.time()
        try:
            cache_key = self._generate_cache_key(key, namespace)
            
            # 智能TTL策略
            if ttl is None:
                ttl = self._get_smart_ttl(namespace, key, len(json.dumps(value, ensure_ascii=False, default=str)))
            
            # 序列化值
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            else:
                serialized_value = str(value)
            
            # 检查值大小
            value_size = len(serialized_value.encode('utf-8'))
            if value_size > self.config.max_value_size:
                if self.stats_collector:
                    self.stats_collector.record_operation('errors', 0, namespace)
                # logger.warning("缓存值过大，跳过设置", {
                #     'key': key,
                #     'size': len(serialized_value),
                #     'max_size': self.config.max_value_size
                # })
                return False
            
            result = self.redis_client.setex(cache_key, ttl, serialized_value)
            response_time = (time.time() - start_time) * 1000
            
            if self.stats_collector:
                self.stats_collector.record_operation('sets', response_time, namespace)
            return bool(result)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            if self.stats_collector:
                self.stats_collector.record_operation('errors', response_time, namespace)
            # logger.error("缓存设置失败", {
            #     'key': key,
            #     'namespace': namespace,
            #     'error': str(e)
            # })
            return False
    
    def delete(self, key: str, namespace: str = "") -> bool:
        """删除缓存值"""
        return self._delete_with_stats(key, namespace)
    
    def _delete_with_stats(self, key: str, namespace: str = "") -> bool:
        """带统计的删除缓存值"""
        if not self.is_ready:
            return False
        
        start_time = time.time()
        try:
            cache_key = self._generate_cache_key(key, namespace)
            result = self.redis_client.delete(cache_key)
            response_time = (time.time() - start_time) * 1000
            if self.stats_collector:
                self.stats_collector.record_operation('deletes', response_time, namespace)
            return bool(result)
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            if self.stats_collector:
                self.stats_collector.record_operation('errors', response_time, namespace)
            # logger.error("缓存删除失败", {
            #     'key': key,
            #     'namespace': namespace,
            #     'error': str(e)
            # })
            return False
    
    def clear_namespace(self, namespace: str) -> int:
        """清除指定命名空间的所有缓存"""
        if not self.is_ready:
            return 0
        
        try:
            pattern = f"{self.config.cache_prefix}:{namespace}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                return deleted
            return 0
            
        except Exception as e:
            # logger.error("清除命名空间失败", {
            #     'namespace': namespace,
            #     'error': str(e)
            # })
            return 0
    
    def _generate_cache_key(self, key: str, namespace: str = "") -> str:
        """生成缓存键"""
        if namespace:
            return f"{self.config.cache_prefix}:{namespace}:{key}"
        return f"{self.config.cache_prefix}:{key}"
    
    def _get_smart_ttl(self, namespace: str, key: str = "", data_size: int = 0) -> int:
        """智能TTL策略 - 通用版本
        
        基于多种因素智能计算TTL：
        1. 命名空间模式匹配
        2. 数据类型推断
        3. 数据大小考虑
        4. 访问频率预测
        """
        
        # 如果禁用智能TTL，直接返回默认值
        if not self.config.enable_smart_ttl:
            return self.config.default_ttl
        
        # 1. 基于命名空间模式的智能匹配
        namespace_patterns = {
            # 数据库相关 - 变化频率低，TTL较长
            r'.*database.*|.*db.*|.*schema.*': 1800,  # 30分钟
            
            # 表结构相关 - 变化频率低，TTL较长  
            r'.*table.*|.*column.*|.*field.*': 1200,  # 20分钟
            
            # 数据查询相关 - 变化频率中等，TTL中等
            r'.*data.*|.*query.*|.*result.*': 600,    # 10分钟
            
            # 用户会话相关 - 变化频率高，TTL较短
            r'.*session.*|.*user.*|.*auth.*': 900,    # 15分钟
            
            # 配置相关 - 变化频率很低，TTL很长
            r'.*config.*|.*setting.*|.*param.*': 3600, # 1小时
            
            # 统计相关 - 变化频率中等，TTL中等
            r'.*stats.*|.*metric.*|.*count.*': 720,   # 12分钟
            
            # 缓存相关 - 变化频率高，TTL较短
            r'.*cache.*|.*temp.*|.*tmp.*': 180,       # 3分钟
            
            # 列表相关 - 变化频率中等，TTL中等
            r'.*list.*|.*index.*|.*catalog.*': 450,   # 7.5分钟
        }
        
        # 合并用户自定义模式（优先级更高）
        namespace_patterns.update(self.config.custom_namespace_patterns)
        
        # 2. 基于键名模式的智能匹配
        key_patterns = {
            # ID相关 - 相对稳定
            r'.*_id$|^id_.*': 1.2,  # TTL倍数
            
            # 详情相关 - 相对稳定
            r'.*detail.*|.*info.*': 1.1,
            
            # 列表相关 - 变化较频繁
            r'.*list.*|.*items.*': 0.8,
            
            # 计数相关 - 变化频繁
            r'.*count.*|.*num.*|.*total.*': 0.6,
            
            # 状态相关 - 变化很频繁
            r'.*status.*|.*state.*': 0.5,
        }
        
        # 合并用户自定义键模式
        key_patterns.update(self.config.custom_key_patterns)
        
        # 3. 基于数据大小的调整
        size_factor = 1.0
        if data_size > 0:
            if data_size > 100 * 1024 * 1024:  # > 100MB，延长TTL减少重建开销
                size_factor = 10.0
            elif data_size > 20 * 1024 * 1024:  # > 20MB，延长TTL减少重建开销
                size_factor = 8.0
            elif data_size > 10 * 1024 * 1024:  # > 10MB，延长TTL减少重建开销
                size_factor = 6.0
            elif data_size > 5 * 1024 * 1024:  # > 5MB，延长TTL减少重建开销
                size_factor = 4.0
            elif data_size > 1024 * 1024:  # > 1MB，延长TTL减少重建开销
                size_factor = 3.0
            elif data_size > 100 * 1024:  # > 100KB
                size_factor = 2.0
            elif data_size < 1024:  # < 1KB，缩短TTL减少内存占用
                size_factor = 1.0
        
        # 4. 计算基础TTL
        base_ttl = self.config.default_ttl
        
        # 匹配命名空间模式
        for pattern, ttl in namespace_patterns.items():
            if re.match(pattern, namespace.lower()):
                base_ttl = ttl
                break
        
        # 5. 应用键名模式调整
        key_factor = 1.0
        for pattern, factor in key_patterns.items():
            if re.match(pattern, key.lower()):
                key_factor = factor
                break
        
        # 6. 计算最终TTL
        final_ttl = int(base_ttl * key_factor * size_factor)
        
        # 7. TTL边界限制（使用配置值）
        final_ttl = max(self.config.ttl_min, min(self.config.ttl_max, final_ttl))
        
        return final_ttl
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        # 确保统计系统已初始化
        if self.stats_collector:
            return self.stats_collector.get_stats()

        return {
            'enabled': False,
            'message': '统计系统未初始化',
            'process_id': os.getpid()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # Redis连接检查
            redis_latency = time.time()
            self.redis_client.ping()
            redis_latency = (time.time() - redis_latency) * 1000
            
            # 获取Redis信息
            redis_info = self.redis_client.info()
            
            return {
                'status': 'healthy',
                'redis_connected': True,
                'redis_latency_ms': round(redis_latency, 2),
                'mysql_enabled': self.mysql_pool is not None,
                'mysql_ready': self.is_mysql_ready,
                'system_state': self._state.value,
                'uptime_seconds': time.time() - (self.stats_collector.stats['start_time'] if self.stats_collector else time.time()),
                'redis_memory_used': redis_info.get('used_memory', 0),
                'redis_connected_clients': redis_info.get('connected_clients', 0),
                'process_id': os.getpid()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'redis_connected': False,
                'system_state': self._state.value
            }
    
    def _record_operation(self, operation: str, response_time: float = 0, namespace: str = "", key: str = ""):
        """记录操作统计 """
        # 如果禁用统计功能，直接返回
        if not self.config.enable_stats:
            return
            
    def shutdown(self):
        """关闭缓存系统"""
        self._state = CacheSystemState.SHUTDOWN
        
        if self.stats_collector:
            # 关闭统计收集器（包括后台定时器）
            self.stats_collector.shutdown()
        
        # logger.info("缓存系统已关闭", {'instance_name': self.instance_name})


class CacheManager:
    """缓存管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.cache_instance = None
            self._initialized = True
    
    def initialize(self, redis_client: redis.Redis, mysql_pool=None, instance_name: str = "default", **config):
        """初始化缓存系统"""
        if self.cache_instance is not None:
            # logger.warning("缓存系统已初始化，跳过重复初始化", {
            #     'existing_instance': self.cache_instance.instance_name,
            #     'new_instance': instance_name
            # })
            return
        
        self.cache_instance = SmartCacheSystem(
            redis_client=redis_client,
            mysql_pool=mysql_pool,
            instance_name=instance_name,
            **config
        )
    
    def get_cache(self) -> Optional[SmartCacheSystem]:
        """获取缓存实例"""
        return self.cache_instance
    
    def is_available(self) -> bool:
        """检查缓存是否可用"""
        return self.cache_instance is not None and self.cache_instance.is_ready
    
    def get_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        if self.cache_instance is None:
            return {
                'enabled': False,
                'available': False,
                'stats_enabled': False,
                'initialization_error': 'Cache not initialized'
            }
        
        return {
            'enabled': True,
            'available': self.cache_instance.is_ready,
            'mysql_ready': self.cache_instance.is_mysql_ready,
            'stats_enabled': self.cache_instance.config.enable_stats,
            'state': self.cache_instance._state.value,
            'instance_name': self.cache_instance.instance_name
        }


# 全局缓存管理器实例
cache_manager = CacheManager()


# ===== 装饰器功能 =====

def flask_redis_cache(cache_key_func=None, ttl=1200, namespace="default", 
                data_validator=None, skip_cache_on_error=True, cache_empty_data=True):
    """
    Flask路由函数的Redis缓存装饰器
    
    Args:
        cache_key_func: 缓存键生成函数，接收请求数据作为参数，返回缓存键字符串
                       如果为None，则使用默认的键生成策略
        ttl: 缓存过期时间（秒），默认20分钟
        namespace: 缓存命名空间，默认为"default"
        data_validator: 数据验证函数，用于验证数据是否应该被缓存
        skip_cache_on_error: 当缓存操作出错时是否跳过缓存，默认True
        cache_empty_data: 是否缓存空数据（None, {}, [], "", 0等），默认True（向后兼容）
    
    Usage:
        @flask_redis_cache(
            cache_key_func=lambda data: f"tables_{data.get('database', 'unknown')}",
            ttl=1200,
            namespace="sycm_tables",
            cache_empty_data=False  # 不缓存空数据
        )
        def my_flask_route():
            pass
    """
    def decorator(func):
        import functools
        import hashlib
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 导入Flask相关模块（延迟导入避免依赖问题）
            try:
                from flask import request, jsonify, g
            except ImportError:
                # 如果没有Flask环境，直接执行原函数
                return func(*args, **kwargs)
            
            # OPTIONS 预检请求特殊处理：直接跳过缓存逻辑
            if request.method == 'OPTIONS':
                g.data_source = 'preflight'  # 标记为预检请求
                g.cache_hit = False
                return func(*args, **kwargs)
            
            # 初始化数据源标记（仅非 OPTIONS 请求）
            g.data_source = 'mysql'
            g.cache_hit = False
            
            # 获取缓存系统
            cache_system = cache_manager.get_cache()
            
            # 如果缓存系统不可用，直接执行原函数
            if not cache_system:
                # 直接查询数据库（无缓存系统）
                return func(*args, **kwargs)
            
            try:
                # 获取请求数据用于生成缓存键
                request_data = {}
                if request.method == 'POST':
                    try:
                        request_data = request.get_json() or {}
                    except Exception:
                        request_data = {}
                elif request.method == 'GET':
                    request_data = dict(request.args)
                
                # 生成缓存键
                if cache_key_func:
                    cache_key = cache_key_func(request_data)
                else:
                    # 默认缓存键生成策略
                    func_name = func.__name__
                    # 将请求数据转换为字符串并生成哈希
                    data_str = str(sorted(request_data.items()))
                    data_hash = hashlib.md5(data_str.encode()).hexdigest()[:8]
                    cache_key = f"{func_name}_{data_hash}"
                
                # 尝试从缓存获取数据
                try:
                    cached_result = cache_system.get(cache_key, namespace)
                    if cached_result is not None:
                        # 缓存命中：标记为 redis
                        g.data_source = 'redis'
                        g.cache_hit = True
                        return jsonify(cached_result)
                except Exception as e:
                    if not skip_cache_on_error:
                        raise
                
                # 缓存未命中，执行原函数
                result = func(*args, **kwargs)
                
                # 如果结果是Flask Response对象，提取JSON数据进行缓存
                if hasattr(result, 'get_json'):
                    try:
                        response_data = result.get_json()
                        if response_data:
                            # 使用安全缓存写入
                            _safe_cache_set(
                                cache_system=cache_system,
                                cache_key=cache_key,
                                response_data=response_data,
                                ttl=ttl,
                                namespace=namespace,
                                data_validator=data_validator,
                                cache_empty_data=cache_empty_data
                            )
                    except Exception as e:
                        if not skip_cache_on_error:
                            raise
                elif isinstance(result, tuple) and len(result) == 2:
                    # 处理 (response, status_code) 格式的返回值
                    try:
                        response_data, status_code = result
                        if hasattr(response_data, 'get_json'):
                            json_data = response_data.get_json()
                        elif isinstance(response_data, dict):
                            json_data = response_data
                        else:
                            json_data = None
                            
                        if json_data and status_code == 200:
                            _safe_cache_set(
                                cache_system=cache_system,
                                cache_key=cache_key,
                                response_data=json_data,
                                ttl=ttl,
                                namespace=namespace,
                                data_validator=data_validator,
                                cache_empty_data=cache_empty_data
                            )
                    except Exception as e:
                        if not skip_cache_on_error:
                            raise
                
                return result
                
            except Exception as e:
                if not skip_cache_on_error:
                    raise
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def function_redis_cache(cache_key_func=None, ttl=1800, namespace="default", 
                        skip_cache_on_error=True, cache_empty_data=True):
    """
    普通函数的Redis缓存装饰器
    
    Args:
        cache_key_func: 缓存键生成函数，接收函数参数作为输入，返回缓存键字符串
                       如果为None，则使用默认的键生成策略
        ttl: 缓存过期时间（秒），默认30分钟
        namespace: 缓存命名空间，默认为"default"
        skip_cache_on_error: 当缓存操作出错时是否跳过缓存，默认True
        cache_empty_data: 是否缓存空数据（None, {}, [], "", 0等），默认True（向后兼容）
    
    Usage:
        @function_redis_cache(
            cache_key_func=lambda _key, shop_name: f"cookies_{_key}_{shop_name}",
            ttl=1800,
            namespace="cookies_cache",
            cache_empty_data=False  # 不缓存空数据
        )
        def my_function(_key, shop_name):
            pass
    """
    def decorator(func):
        import functools
        import inspect
        import hashlib
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取缓存系统
            cache_system = cache_manager.get_cache()
            
            # 如果缓存系统不可用，直接执行原函数
            if not cache_system:
                return func(*args, **kwargs)
            
            try:
                # 获取函数签名和参数
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # 生成缓存键
                if cache_key_func:
                    cache_key = cache_key_func(*args, **kwargs)
                else:
                    # 默认缓存键生成策略
                    func_name = func.__name__
                    # 将参数转换为字符串并生成哈希
                    args_str = str(args) + str(sorted(kwargs.items()))
                    args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                    cache_key = f"{func_name}_{args_hash}"
                
                # 尝试从缓存获取数据
                try:
                    cached_result = cache_system.get(cache_key, namespace)
                    if cached_result is not None:
                        return cached_result
                except Exception as e:
                    if not skip_cache_on_error:
                        raise
                
                # 缓存未命中，执行原函数
                result = func(*args, **kwargs)
                
                # 检查是否需要缓存空数据
                if not cache_empty_data and _is_empty_data(result):
                    # 不缓存空数据，直接返回结果
                    return result
                
                # 缓存结果（只缓存非空结果或cache_empty_data=True时缓存所有结果）
                if result is not None and result != {} and result != []:
                    try:
                        cache_system.set(cache_key, result, ttl=ttl, namespace=namespace)
                    except Exception as e:
                        if not skip_cache_on_error:
                            raise
                
                return result
                
            except Exception as e:
                if not skip_cache_on_error:
                    raise
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def _safe_cache_set(cache_system, cache_key, response_data, ttl, namespace, 
                   data_validator=None, cache_empty_data=True):
    """
    安全的缓存写入函数，只有数据有效时才写入缓存。
    
    Args:
        cache_system: 缓存系统实例
        cache_key: 缓存键
        response_data: 要缓存的响应数据
        ttl: 缓存过期时间
        namespace: 缓存命名空间
        data_validator: 数据验证函数，返回True表示数据有效
        cache_empty_data: 是否缓存空数据，默认True
    
    Returns:
        bool: 是否成功写入缓存
    """
    if not cache_system:
        return False
    
    # 检查是否需要缓存空数据
    if not cache_empty_data and _is_empty_data(response_data):
        return False
    
    # 默认验证逻辑：检查响应数据结构
    if data_validator is None:
        def default_validator(data):
            if not isinstance(data, dict):
                return False
            
            # 更宽松的验证逻辑，支持多种响应格式
            # 检查状态字段（支持多种成功状态格式）
            status_ok = (
                data.get('status') == 'success' or  # 新格式
                data.get('code') == 0 or            # 旧格式
                data.get('code') == 200             # HTTP状态码格式
            )
            
            if not status_ok:
                return False
            
            # 检查 message 字段是否包含"失败"字样，如果包含则跳过缓存
            message = data.get('message', '')
            if isinstance(message, str) and ('失败' in message or 'error' in message or 'fail' in message):
                return False
            
            # 检查数据部分（不仅要有字段，还要有有效的非空值）
            def is_valid_value(value):
                """判断值是否有效（非None、非空列表、非空字典）"""
                if value is None:
                    return False
                if isinstance(value, (list, dict)) and len(value) == 0:
                    return False
                return True
            
            # 检查各种数据字段
            has_valid_data = (
                ('data' in data and is_valid_value(data.get('data'))) or
                ('logs' in data and is_valid_value(data.get('logs'))) or
                ('announcements' in data and is_valid_value(data.get('announcements'))) or
                ('databases' in data and is_valid_value(data.get('databases'))) or
                ('tables' in data and is_valid_value(data.get('tables'))) or
                ('rows' in data and is_valid_value(data.get('rows'))) or
                # message 单独判断：只有在其他字段都不存在时，才检查 message
                (not any(key in data for key in ['data', 'logs', 'announcements', 'databases', 'tables', 'rows']) 
                 and 'message' in data 
                 and data.get('message') 
                 and data.get('message') not in ['', 'ok', 'success'])
            )
            
            # 返回是否有有效数据
            return has_valid_data
        
        data_validator = default_validator
    
    # 验证数据
    try:
        is_valid = data_validator(response_data)
    except Exception:
        return False
    
    if is_valid:
        try:
            cache_system.set(cache_key, response_data, ttl=ttl, namespace=namespace)
            return True
        except Exception:
            return False
    else:
        return False


def _is_empty_data(data):
    """
    检查数据是否为空
    
    Args:
        data: 要检查的数据
        
    Returns:
        bool: True表示数据为空，False表示数据非空
    """
    # None 视为空
    if data is None:
        return True
    
    # 空容器视为空
    if isinstance(data, (list, dict, tuple, set, str)) and len(data) == 0:
        return True
    
    # 数字0视为空（可选，根据业务需求调整）
    # if isinstance(data, (int, float)) and data == 0:
    #     return True
    
    # False 不视为空（布尔值有意义）
    if isinstance(data, bool):
        return False
    
    return False

