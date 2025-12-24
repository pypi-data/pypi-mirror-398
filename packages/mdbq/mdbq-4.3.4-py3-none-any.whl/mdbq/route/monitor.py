"""
API 监控装饰器模块

高性能、轻量级的 API 访问监控系统，专注于核心监控指标的收集和分析。

核心特性：
1. 请求监控：记录接口访问的核心信息（耗时、状态、ip 等）
2. 统计分析：提供按时间维度的访问统计和性能分析
3. 高性能：精简字段设计，优化索引策略，最小化性能影响
4. 安全性：自动脱敏敏感信息，支持 ip 风险评估
5. 自动清理：支持历史数据自动归档和清理
"""

import os
import json
import time
import uuid
import threading
import pymysql
import functools
import hashlib
import socket
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dbutils.pooled_db import PooledDB # type: ignore
from flask import request, g


class RouteMonitor:
    """
    路由监控核心类
    
    负责 API 请求的监控、日志记录和统计分析。
    
    Attributes:
        database (str): 监控数据库名称，默认为 'api监控系统'
        pool (PooledDB): 数据库连接池
        
    核心方法:
        - api_monitor: 装饰器，用于监控 API 接口
        - get_statistics_summary: 获取统计摘要数据
        - cleanup_old_data: 清理历史数据
    """
    
    def __init__(self, database: str = 'api监控系统', pool = None, redis_client = None, enable_async: bool = True):
        """
        初始化监控系统
        
        Args:
            database: 数据库名称，默认为 'api监控系统'
            pool: 数据库连接池对象，如果不传则使用默认配置创建
            redis_client: Redis 客户端，用于异步队列（可选，如果不传则同步写入）
            enable_async: 是否启用异步模式（需要 redis_client），默认 True
        """
        self.database = database
        self.pool = pool
        if self.pool is None:
            self.init_database_pool()
        self.init_database_tables()
        
        # Redis 异步队列配置
        self.redis_client = redis_client
        self.enable_async = enable_async and self.redis_client is not None
        # 队列名ASCII化，避免中文带来的跨系统兼容问题
        try:
            db_hash = hashlib.md5(self.database.encode('utf-8')).hexdigest()[:8]
            self.queue_name = f"api_monitor:{db_hash}:tasks"
        except Exception:
            self.queue_name = "api_monitor:tasks"
        
        # 线程锁（用于保护统计数据）
        self._stats_lock = threading.Lock()
        
        # 统计信息
        self._stats = {
            'total_requests': 0,
            'queued_tasks': 0,
            'sync_writes': 0,
            'queue_failures': 0,
        }
        
        if self.enable_async:
            # 使用 Redis 队列模式（适合 uwsgi 多进程）
            pass  # 队列消费者需要单独进程运行
        else:
            # 降级为同步模式
            pass

    def init_database_pool(self):
        """
        初始化数据库连接池
        
        配置说明：
        - 最大连接数：2（监控系统不需要大量连接）
        - 编码：utf8mb4（支持中文和 emoji）
        - 自动重连：开启
        """
        from mdbq.myconf import myconf # type: ignore
        parser = myconf.ConfigParser()
        host, port, username, password = parser.get_section_values(
            file_path=os.path.join(os.path.expanduser("~"), 'spd.txt'),
            section='mysql',
            keys=['host', 'port', 'username', 'password'],
        )
        try:
            self.pool = PooledDB(
                creator=pymysql,
                maxconnections=2,
                mincached=1,
                maxcached=2,
                blocking=True,
                host=host,
                port=int(port),
                user=username,
                password=password,
                ping=1,  # 自动重连
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            # 创建数据库
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                        f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                    )
                    cursor.execute(f"USE `{self.database}`")
            finally:
                connection.close()
                
        except Exception as e:
            # 保持原有行为：抛出异常由上层处理
            raise
    
    def ensure_database_context(self, cursor):
        """
        确保游标处于正确的数据库上下文中
        
        Args:
            cursor: 数据库游标对象
        """
        try:
            cursor.execute(f"USE `{self.database}`")
        except Exception:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
            cursor.execute(f"USE `{self.database}`")
        
    def init_database_tables(self):
        """
        初始化数据库表结构
        
        创建三张核心表：
        1. api_访问日志：记录每次 API 请求的详细信息
        2. api_接口统计：按小时汇总的接口性能统计
        3. api_ip记录：IP 维度的访问统计
        """
        try:
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    # ==================== 表 1：访问日志表 ====================
                    # 设计原则：只保留核心监控字段，移除冗余信息
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS `api_访问日志` (
                            `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键，自增id',
                            `请求id` VARCHAR(64) NOT NULL COMMENT '请求唯一标识（用于追踪）',
                            `请求时间` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '请求时间，精确到毫秒',
                            `请求方法` VARCHAR(10) NOT NULL COMMENT 'HTTP 方法（GET/POST/PUT/DELETE等）',
                            `路由地址` VARCHAR(500) NOT NULL COMMENT 'API 路由地址',
                            `客户端ip` VARCHAR(45) NOT NULL COMMENT '客户端 ip 地址（支持 IPv6）',
                            `主机名` VARCHAR(100) COMMENT '服务器主机名',
                            `请求来源` VARCHAR(500) COMMENT '请求来源（Referer）',
                            `状态码` SMALLINT COMMENT 'HTTP 状态码',
                            `响应耗时` DECIMAL(10,3) COMMENT '请求处理耗时（毫秒）',
                            `数据源` VARCHAR(20) COMMENT '数据源类型：redis/mysql/hybrid/none/preflight',
                            `缓存命中` TINYINT(1) DEFAULT 0 COMMENT '是否命中缓存：1-命中，0-未命中',
                            `用户标识` VARCHAR(64) COMMENT '用户id或标识（如有）',
                            `用户代理` VARCHAR(500) COMMENT '浏览器 User-Agent（精简版）',
                            `请求参数` TEXT COMMENT '请求参数（JSON格式，可选记录）',
                            `错误信息` TEXT COMMENT '错误信息（仅失败请求记录）',
                            `创建时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                            `更新时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                            
                            UNIQUE KEY `uk_请求id` (`请求id`),
                            INDEX `idx_请求时间` (`请求时间`),
                            INDEX `idx_路由地址` (`路由地址`(191)),
                            INDEX `idx_客户端ip` (`客户端ip`),
                            INDEX `idx_主机名` (`主机名`),
                            INDEX `idx_状态码` (`状态码`),
                            INDEX `idx_数据源` (`数据源`),
                            INDEX `idx_缓存命中` (`缓存命中`),
                            INDEX `idx_用户标识` (`用户标识`),
                            INDEX `idx_时间_接口` (`请求时间`, `路由地址`(191)),
                            INDEX `idx_时间_数据源` (`请求时间`, `数据源`),
                            INDEX `idx_时间_主机` (`请求时间`, `主机名`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
                        COMMENT='API 访问日志表 - 记录每次请求的核心信息'
                        ROW_FORMAT=COMPRESSED;
                    """)
                    
                    # ==================== 表 2：接口统计表 ====================
                    # 设计原则：按小时维度汇总，用于性能分析和趋势监控
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS `api_接口统计` (
                            `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键，自增id',
                            `统计日期` DATE NOT NULL COMMENT '统计日期',
                            `统计小时` TINYINT NOT NULL COMMENT '统计小时（0-23）',
                            `路由地址` VARCHAR(500) NOT NULL COMMENT 'API 路由地址',
                            `请求方法` VARCHAR(10) NOT NULL COMMENT 'HTTP 请求方法',
                            `请求总数` INT UNSIGNED DEFAULT 0 COMMENT '总请求次数',
                            `成功次数` INT UNSIGNED DEFAULT 0 COMMENT '成功响应次数（状态码 < 400）',
                            `失败次数` INT UNSIGNED DEFAULT 0 COMMENT '失败响应次数（状态码 >= 400）',
                            `缓存命中次数` INT UNSIGNED DEFAULT 0 COMMENT '缓存命中次数',
                            `数据库查询次数` INT UNSIGNED DEFAULT 0 COMMENT '没有命中缓存，直接查询数据库的次数',
                            `平均耗时` DECIMAL(10,3) DEFAULT 0 COMMENT '平均响应耗时（毫秒）',
                            `最大耗时` DECIMAL(10,3) DEFAULT 0 COMMENT '最大响应耗时（毫秒）',
                            `最小耗时` DECIMAL(10,3) DEFAULT NULL COMMENT '最小响应耗时（毫秒）',
                            `独立ip数` INT UNSIGNED DEFAULT 0 COMMENT '访问的独立 ip 数量',
                            `创建时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                            `更新时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                            
                            UNIQUE KEY `uk_日期_小时_接口_方法` (`统计日期`, `统计小时`, `路由地址`(191), `请求方法`),
                            INDEX `idx_统计日期` (`统计日期`),
                            INDEX `idx_路由地址` (`路由地址`(191)),
                            INDEX `idx_日期_接口` (`统计日期`, `路由地址`(191))
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
                        COMMENT='API 接口统计表 - 按小时汇总的接口性能数据';
                    """)
                    
                    # ==================== 表 3：IP 访问记录表 ====================
                    # 设计原则：按日期汇总 IP 访问情况，用于安全分析和流量监控
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS `api_ip记录` (
                            `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键，自增id',
                            `统计日期` DATE NOT NULL COMMENT '统计日期',
                            `客户端ip` VARCHAR(45) NOT NULL COMMENT '客户端 ip 地址',
                            `请求总数` INT UNSIGNED DEFAULT 0 COMMENT '该 ip 当日总请求数',
                            `成功次数` INT UNSIGNED DEFAULT 0 COMMENT '成功请求次数',
                            `失败次数` INT UNSIGNED DEFAULT 0 COMMENT '失败请求次数',
                            `平均耗时` DECIMAL(10,3) DEFAULT 0 COMMENT '平均响应耗时（毫秒）',
                            `首次访问` DATETIME COMMENT '首次访问时间',
                            `最后访问` DATETIME COMMENT '最后访问时间',
                            `访问接口数` INT UNSIGNED DEFAULT 0 COMMENT '访问的不同接口数量',
                            `风险评分` TINYINT UNSIGNED DEFAULT 0 COMMENT '风险评分（0-100，用于识别异常流量）',
                            `创建时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
                            `更新时间` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
                            
                            UNIQUE KEY `uk_日期_ip` (`统计日期`, `客户端ip`),
                            INDEX `idx_统计日期` (`统计日期`),
                            INDEX `idx_客户端ip` (`客户端ip`),
                            INDEX `idx_风险评分` (`风险评分`),
                            INDEX `idx_请求总数` (`请求总数`)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
                        COMMENT='API ip 访问记录表 - ip 维度的访问统计';
                    """)
                connection.commit()
                
            finally:
                connection.close()
                
        except Exception as e:
            # 保持静默降级行为，不影响主应用启动
            pass
    
    # ==================== Redis 队列方法 ====================
    
    @staticmethod
    def _datetime_converter(obj):
        """
        JSON 序列化时的 datetime 转换器
        
        将 datetime 对象转换为特殊格式的字典，便于反序列化时还原
        """
        if isinstance(obj, datetime):
            return {'__datetime__': True, 'value': obj.isoformat()}
        return str(obj)
    
    @staticmethod
    def _datetime_decoder(dct):
        """
        JSON 反序列化时的 datetime 解码器
        
        将特殊格式的字典还原为 datetime 对象
        """
        if isinstance(dct, dict) and '__datetime__' in dct:
            return datetime.fromisoformat(dct['value'])
        return dct
    
    def _push_to_queue(self, task_data: Dict[str, Any]) -> bool:
        """
        将监控任务推入 Redis 队列（非阻塞，极快）
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            bool: 是否成功推入队列
        """
        if not self.enable_async:
            return False
        
        try:
            # 将任务数据序列化为 JSON（使用 datetime 转换器）
            task_json = json.dumps(task_data, default=self._datetime_converter, ensure_ascii=False)
            
            # 推入 Redis 列表（LPUSH，从左侧推入）
            self.redis_client.lpush(self.queue_name, task_json)
            
            with self._stats_lock:
                self._stats['queued_tasks'] += 1
            return True
            
        except Exception as e:
            # 静默处理错误
            with self._stats_lock:
                self._stats['queue_failures'] += 1
            return False
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """
        获取监控系统统计信息
        
        Returns:
            dict: 统计信息字典
        """
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 添加队列信息
        if self.enable_async:
            try:
                queue_length = self.redis_client.llen(self.queue_name)
                stats['queue_length'] = queue_length
                stats['mode'] = 'async_redis'
            except:
                stats['queue_length'] = -1
                stats['mode'] = 'async_redis_error'
        else:
            stats['queue_length'] = 0
            stats['mode'] = 'sync'
        
        return stats
    
    # ==================== 辅助方法 ====================
    
    def generate_request_id(self) -> str:
        """
        生成唯一的请求 ID

        Returns:
            str: 请求唯一标识符
        """
        # # 纯UUID4
        # return f"req_{uuid.uuid4().hex}"
        
        # 哈希
        timestamp = str(int(time.time() * 1000000))  # 微秒
        random_part = uuid.uuid4().hex
        combined = f"{timestamp}_{random_part}_{os.getpid()}"
        return str(hashlib.sha256(combined.encode()).hexdigest()[:32])
    
    def get_real_ip(self, request) -> str:
        """
        获取真实客户端 IP 地址
        
        优先级顺序：
        1. X-Forwarded-For（代理服务器传递的原始IP）
        2. X-Real-IP（Nginx 等反向代理设置）
        3. CF-Connecting-IP（Cloudflare CDN）
        4. request.remote_addr（直连IP）
        
        Args:
            request: Flask request 对象
            
        Returns:
            str: 客户端真实 IP 地址
        """
        # IP 头优先级列表
        ip_headers = [
            'X-Forwarded-For',
            'X-Real-IP',
            'CF-Connecting-IP',
            'X-Client-IP',
        ]
        
        # 尝试从请求头获取 IP
        for header in ip_headers:
            header_value = request.headers.get(header)
            if header_value:
                # X-Forwarded-For 可能包含多个 IP，取第一个
                ip = header_value.split(',')[0].strip()
                if ip:
                    return ip
        
        # 如果没有代理头，返回直连 IP
        return request.remote_addr or 'unknown'
    
    def sanitize_params(self, params: Dict[str, Any]) -> Optional[str]:
        """
        清理和脱敏请求参数
        
        自动移除敏感字段（如 password、token 等）
        
        Args:
            params: 请求参数字典
            
        Returns:
            str: JSON 格式的参数字符串（已脱敏），或 None
        """
        if not params:
            return None
        
        # 敏感字段列表
        sensitive_keys = ['password', 'passwd', 'pwd', 'token', 'secret', 'key', 'api_key', 'apikey']
        
        # 创建副本并脱敏
        sanitized = {}
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***'
            else:
                # 截断过长的值
                if isinstance(value, str) and len(value) > 500:
                    sanitized[key] = value[:500] + '...'
                else:
                    sanitized[key] = value
        
        try:
            return json.dumps(sanitized, ensure_ascii=False)
        except Exception:
            return None
    
    def calculate_risk_score(self, client_ip: str, date: datetime.date) -> int:
        """
        计算 IP 风险评分（0-100）
        
        风险评分基于以下维度：
        1. 请求频率异常（30分）：单日请求数超过阈值
        2. 失败率异常（25分）：失败请求比例过高
        3. 访问模式异常（20分）：短时间访问大量不同接口
        4. 时间分布异常（15分）：非正常时间段高频访问
        5. 响应时间异常（10分）：平均响应时间过长（可能是攻击）
        
        Args:
            client_ip: 客户端 IP 地址
            date: 统计日期
            
        Returns:
            int: 风险评分（0-100），分数越高风险越大
        """
        risk_score = 0
        
        try:
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    # 获取该 IP 当日的统计数据
                    cursor.execute("""
                        SELECT 
                            `请求总数`, `成功次数`, `失败次数`, 
                            `平均耗时`, `首次访问`, `最后访问`, `访问接口数`
                        FROM `api_ip记录`
                        WHERE `客户端ip` = %s AND `统计日期` = %s
                    """, (client_ip, date))
                    
                    ip_stats = cursor.fetchone()
                    if not ip_stats:
                        return 0  # 无数据，无风险
                    
                    total_requests = ip_stats['请求总数']
                    success_count = ip_stats['成功次数']
                    failure_count = ip_stats['失败次数']
                    avg_time = float(ip_stats['平均耗时']) if ip_stats['平均耗时'] else 0
                    first_access = ip_stats['首次访问']
                    last_access = ip_stats['最后访问']
                    endpoint_count = ip_stats['访问接口数'] or 0
                    
                    # 1. 请求频率异常检测（30分）
                    # 阈值：正常用户单日请求 < 1000，可疑 1000-5000，高风险 > 5000
                    if total_requests > 10000:
                        risk_score += 30  # 极高频率
                    elif total_requests > 5000:
                        risk_score += 25  # 高频率
                    elif total_requests > 2000:
                        risk_score += 18  # 中等频率
                    elif total_requests > 1000:
                        risk_score += 10  # 略高
                    
                    # 2. 失败率异常检测（25分）
                    # 高失败率可能是暴力破解、SQL注入等攻击
                    if total_requests > 0:
                        failure_rate = failure_count / total_requests
                        if failure_rate > 0.8:
                            risk_score += 25  # 80%以上失败
                        elif failure_rate > 0.5:
                            risk_score += 20  # 50%-80%失败
                        elif failure_rate > 0.3:
                            risk_score += 12  # 30%-50%失败
                        elif failure_rate > 0.15:
                            risk_score += 5   # 15%-30%失败
                    
                    # 3. 访问模式异常检测（20分）
                    # 短时间访问大量不同接口可能是扫描行为
                    if endpoint_count > 0:
                        # 计算平均每个接口的访问次数
                        avg_per_endpoint = total_requests / endpoint_count
                        
                        if endpoint_count > 50 and avg_per_endpoint < 5:
                            risk_score += 20  # 访问50+接口，每个接口少于5次（扫描特征）
                        elif endpoint_count > 30 and avg_per_endpoint < 10:
                            risk_score += 15  # 访问30+接口
                        elif endpoint_count > 20 and avg_per_endpoint < 15:
                            risk_score += 10  # 访问20+接口
                        elif endpoint_count > 10 and avg_per_endpoint < 20:
                            risk_score += 5   # 访问10+接口
                    
                    # 4. 时间分布异常检测（15分）
                    # 查询该 IP 的小时分布，检测是否有非正常时间段高频访问
                    cursor.execute("""
                        SELECT 
                            HOUR(`请求时间`) as hour,
                            COUNT(*) as count
                        FROM `api_访问日志`
                        WHERE `客户端ip` = %s 
                        AND DATE(`请求时间`) = %s
                        GROUP BY HOUR(`请求时间`)
                        HAVING count > 100
                        ORDER BY count DESC
                    """, (client_ip, date))
                    
                    hourly_distribution = cursor.fetchall()
                    
                    # 检测是否有凌晨时段（0-5点）的异常高频访问
                    night_requests = sum(h['count'] for h in hourly_distribution if 0 <= h['hour'] <= 5)
                    if night_requests > 500:
                        risk_score += 15  # 凌晨大量请求（可能是爬虫/攻击）
                    elif night_requests > 200:
                        risk_score += 10
                    elif night_requests > 100:
                        risk_score += 5
                    
                    # 5. 响应时间异常检测（10分）
                    # 过长的响应时间可能是 DDoS 攻击或资源耗尽攻击
                    if avg_time > 5000:  # > 5秒
                        risk_score += 10
                    elif avg_time > 3000:  # > 3秒
                        risk_score += 7
                    elif avg_time > 2000:  # > 2秒
                        risk_score += 4
                    
                    # 限制评分范围在 0-100
                    risk_score = min(100, max(0, risk_score))
                    
            finally:
                connection.close()
                
        except Exception as e:
            # 计算失败时返回 0（保守策略）
            return 0
        
        return risk_score
    
    # ==================== 核心数据收集 ====================
    
    def collect_request_data(self, request) -> Dict[str, Any]:
        """
        收集请求核心数据
        
        仅收集必要的监控信息，避免过度记录造成性能和存储压力。
        
        Args:
            request: Flask request 对象
            
        Returns:
            dict: 包含请求核心信息的字典
        """
        request_id = self.generate_request_id()
        g.request_id = request_id  # 保存到全局变量，供后续使用
        
        # 获取客户端 IP
        client_ip = self.get_real_ip(request)
        
        # 获取主机名
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = 'unknown'
        
        # 获取请求来源（Referer）
        referer = request.headers.get('Referer') or request.headers.get('Origin')
        if referer and len(referer) > 500:
            referer = referer[:500]
        
        # 获取 User-Agent（截断过长的）
        user_agent = request.headers.get('User-Agent', '')
        if len(user_agent) > 500:
            user_agent = user_agent[:500]
        
        # 获取用户标识（如果有）
        # 安全获取 user_id，允许为空时使用默认值
        user_id = None
        
        if hasattr(g, 'current_user_id'):
            user_id = str(g.current_user_id) if g.current_user_id else None
        elif hasattr(g, 'user_id'):
            user_id = str(g.user_id) if g.user_id else None
        
        # 如果还是获取不到，尝试从 request.current_user 获取
        if not user_id and hasattr(request, 'current_user'):
            try:
                current_user = request.current_user
                if isinstance(current_user, dict):
                    user_id = current_user.get('user_id') or current_user.get('id')
                    if user_id:
                        user_id = str(user_id)
            except Exception:
                pass
        
        # 兜底：使用默认值，避免 None
        if not user_id:
            user_id = 'anonymous'
        
        # 收集请求参数（GET 参数 + POST 数据）
        request_params = None
        params_dict = {}
        
        # 1. 收集 URL 参数（GET）
        if request.args:
            params_dict.update(dict(request.args))
        
        # 2. 收集 POST/PUT/PATCH 请求体数据
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.is_json:
                    # JSON 数据
                    json_data = request.get_json(silent=True)
                    if json_data:
                        params_dict.update(json_data)
                elif request.form:
                    # 表单数据
                    params_dict.update(dict(request.form))
            except Exception:
                pass
        
        # 3. 脱敏处理
        if params_dict:
            request_params = self.sanitize_params(params_dict)
        
        # 获取数据源信息（从 g 对象中读取，由缓存装饰器 redis_cache 设置）
        # 默认为 mysql（没有使用缓存装饰器的接口直接查询数据库）
        data_source = getattr(g, 'data_source', 'mysql')
        cache_hit = getattr(g, 'cache_hit', False)
        
        # 构建请求数据字典
        request_data = {
            '请求id': request_id,
            '请求时间': datetime.now(),
            '请求方法': request.method,
            '路由地址': request.endpoint or request.path,
            '客户端ip': client_ip,
            '主机名': hostname,
            '请求来源': referer,
            '数据源': data_source,
            '缓存命中': 1 if cache_hit else 0,
            '用户标识': user_id,
            '用户代理': user_agent,
            '请求参数': request_params,
        }
        
        return request_data
    
    # ==================== 数据持久化 ====================
    
    def save_request_log(self, request_data: Dict[str, Any], response_data: Dict[str, Any] = None):
        """
        保存请求日志到数据库
        
        Args:
            request_data: 请求数据字典
            response_data: 响应数据字典（可选）
        """
        request_id = request_data.get('请求id', 'unknown')
        
        try:
            # 合并响应数据
            if response_data:
                request_data.update(response_data)
            
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    # 插入请求日志
                    sql = """
                        INSERT INTO `api_访问日志` (
                            `请求id`, `请求时间`, `请求方法`, `路由地址`, `客户端ip`,
                            `主机名`, `请求来源`,
                            `状态码`, `响应耗时`, `数据源`, `缓存命中`,
                            `用户标识`, `用户代理`, `请求参数`, `错误信息`
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """
                    
                    cursor.execute(sql, (
                        request_data.get('请求id'),
                        request_data.get('请求时间'),
                        request_data.get('请求方法'),
                        request_data.get('路由地址'),
                        request_data.get('客户端ip'),
                        request_data.get('主机名'),
                        request_data.get('请求来源'),
                        request_data.get('状态码'),
                        request_data.get('响应耗时'),
                        request_data.get('数据源', 'none'),
                        request_data.get('缓存命中', 0),
                        request_data.get('用户标识'),
                        request_data.get('用户代理'),
                        request_data.get('请求参数'),
                        request_data.get('错误信息'),
                    ))
                    
                connection.commit()
                
            finally:
                connection.close()
                
        except Exception as e:
            # 静默处理错误，避免影响主业务
            pass
    
    def update_statistics(self, request_data: Dict[str, Any]):
        """
        更新统计数据
        
        包括：
        1. 接口统计：按小时汇总接口性能数据
        2. IP 统计：按日期汇总 IP 访问数据
        
        Args:
            request_data: 包含请求和响应信息的字典
        """
        try:
            # 过滤掉 OPTIONS 预检请求，不参与统计
            data_source = request_data.get('数据源', 'none')
            if data_source == 'preflight':
                return  # 跳过统计
            
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    # 使用请求时间而不是当前时间，避免统计时间不一致
                    request_time = request_data.get('请求时间', datetime.now())
                    date = request_time.date()
                    hour = request_time.hour
                    now = datetime.now()  # 用于IP统计的最后访问时间
                    
                    # 判断是否成功（状态码 < 400）
                    status_code = request_data.get('状态码', 500)
                    is_success = 1 if status_code < 400 else 0
                    is_error = 1 if status_code >= 400 else 0
                    response_time = request_data.get('响应耗时', 0)
                    
                    # 获取数据源信息
                    cache_hit = request_data.get('缓存命中', 0)
                    is_cache_hit = 1 if cache_hit else 0
                    is_db_query = 1 if data_source in ['mysql', 'hybrid'] else 0
                    
                    # 1. 更新接口统计表
                    cursor.execute("""
                        INSERT INTO `api_接口统计` (
                            `统计日期`, `统计小时`, `路由地址`, `请求方法`,
                            `请求总数`, `成功次数`, `失败次数`,
                            `缓存命中次数`, `数据库查询次数`,
                            `平均耗时`, `最大耗时`, `最小耗时`
                        ) VALUES (
                            %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s
                        ) ON DUPLICATE KEY UPDATE
                        `请求总数` = `请求总数` + 1,
                        `成功次数` = `成功次数` + %s,
                        `失败次数` = `失败次数` + %s,
                        `缓存命中次数` = `缓存命中次数` + %s,
                        `数据库查询次数` = `数据库查询次数` + %s,
                        `平均耗时` = (
                            (`平均耗时` * `请求总数` + %s) / (`请求总数` + 1)
                        ),
                        `最大耗时` = GREATEST(`最大耗时`, %s),
                        `最小耗时` = (
                            CASE 
                                WHEN `最小耗时` IS NULL OR `最小耗时` = 0 THEN %s 
                                ELSE LEAST(`最小耗时`, %s) 
                            END
                        )
                    """, (
                        date, hour, 
                        request_data.get('路由地址', ''),
                        request_data.get('请求方法', ''),
                        is_success, is_error, is_cache_hit, is_db_query,
                        response_time, response_time, response_time,
                        is_success, is_error, is_cache_hit, is_db_query,
                        response_time,
                        response_time,
                        response_time,
                        response_time
                    ))
                    
                    # 2. 更新 IP 统计表
                    client_ip = request_data.get('客户端ip', '')
                    
                    # 首先更新基础统计
                    cursor.execute("""
                        INSERT INTO `api_ip记录` (
                            `统计日期`, `客户端ip`, `请求总数`, `成功次数`, `失败次数`,
                            `平均耗时`, `首次访问`, `最后访问`
                        ) VALUES (
                            %s, %s, 1, %s, %s, %s, %s, %s
                        ) ON DUPLICATE KEY UPDATE
                            `请求总数` = `请求总数` + 1,
                            `成功次数` = `成功次数` + %s,
                            `失败次数` = `失败次数` + %s,
                            `平均耗时` = (
                                (`平均耗时` * `请求总数` + %s) / (`请求总数` + 1)
                            ),
                            `最后访问` = %s
                    """, (
                        date,
                        client_ip,
                        is_success, is_error,
                        response_time, now, now,
                        is_success, is_error,
                        response_time,
                        now
                    ))
                    
                    # 计算该 IP 访问的不同接口数量
                    cursor.execute("""
                        SELECT COUNT(DISTINCT `路由地址`) as endpoint_count
                        FROM `api_访问日志`
                        WHERE `客户端ip` = %s AND DATE(`请求时间`) = %s
                    """, (client_ip, date))
                    
                    endpoint_result = cursor.fetchone()
                    endpoint_count = endpoint_result['endpoint_count'] if endpoint_result else 0
                    
                    # 更新访问接口数
                    cursor.execute("""
                        UPDATE `api_ip记录`
                        SET `访问接口数` = %s
                        WHERE `客户端ip` = %s AND `统计日期` = %s
                    """, (endpoint_count, client_ip, date))
                    
                connection.commit()
                
                # 3. 计算并更新风险评分（在事务外执行，避免影响主流程性能）
                try:
                    risk_score = self.calculate_risk_score(client_ip, date)
                    if risk_score > 0:
                        # 重新获取连接更新风险评分
                        connection2 = self.pool.connection()
                        try:
                            with connection2.cursor() as cursor2:
                                self.ensure_database_context(cursor2)
                                cursor2.execute("""
                                    UPDATE `api_ip记录`
                                    SET `风险评分` = %s
                                    WHERE `客户端ip` = %s AND `统计日期` = %s
                                """, (risk_score, client_ip, date))
                            connection2.commit()
                        finally:
                            connection2.close()
                except Exception:
                    # 风险评分计算失败不影响主流程
                    pass
                
            finally:
                connection.close()
                
        except Exception as e:
            # 静默处理错误
            pass
    
    # ==================== 核心装饰器 ====================

    def api_monitor(self, func):
        """
        API 监控装饰器
        
        使用方法：
        ```python
        from mdbq.route.monitor import api_monitor
        
        @app.route('/api/users')
        @api_monitor
        def get_users():
            return {'users': [...]}
        ```
        
        功能：
        1. 自动记录请求的核心信息（IP、耗时、状态等）
        2. 实时更新统计数据
        3. 异常情况也会被记录
        4. 不影响主业务逻辑的执行
        
        Args:
            func: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 记录开始时间
            start_time = time.time()
            g.request_start_time = start_time
            
            # 统计总请求数（线程安全）
            with self._stats_lock:
                self._stats['total_requests'] += 1
            
            try:
                # 执行原函数
                response = func(*args, **kwargs)
                
                # 计算响应时间
                end_time = time.time()
                process_time = round((end_time - start_time) * 1000, 3)  # 毫秒
                
                # 获取状态码
                response_status = 200
                if hasattr(response, 'status_code'):
                    response_status = response.status_code
                elif isinstance(response, tuple) and len(response) > 1:
                    # 处理 (data, status_code) 格式的返回
                    response_status = response[1]
                # 健壮化：支持 '200 OK' 等字符串状态
                if isinstance(response_status, str):
                    try:
                        response_status = int(str(response_status).split()[0])
                    except Exception:
                        response_status = 200
                
                # 在函数执行完成后收集请求数据（此时缓存装饰器已经设置了 g.data_source）
                request_data = self.collect_request_data(request)
                
                # 更新响应数据
                response_data = {
                    '状态码': response_status,
                    '响应耗时': process_time,
                }
                
                # 合并数据
                request_data.update(response_data)
                
                # 优先使用 Redis 队列（非阻塞）
                queued = self._push_to_queue({
                    'type': 'request_log',
                    'data': request_data,
                    'timestamp': time.time()
                })
                
                # 如果队列失败，降级为同步写入
                if not queued:
                    with self._stats_lock:
                        self._stats['sync_writes'] += 1
                    self.save_request_log(request_data, None)
                    self.update_statistics(request_data)
                
                return response
                
            except Exception as e:
                # 记录错误信息
                end_time = time.time()
                process_time = round((end_time - start_time) * 1000, 3)
                
                # 在异常发生后收集请求数据
                request_data = self.collect_request_data(request)
                
                # 构建错误数据
                error_data = {
                    '状态码': 500,
                    '响应耗时': process_time,
                    '错误信息': f"{type(e).__name__}: {str(e)}"
                }
                
                # 合并数据
                request_data.update(error_data)
                
                # 优先使用 Redis 队列（非阻塞）
                queued = self._push_to_queue({
                    'type': 'request_log',
                    'data': request_data,
                    'timestamp': time.time()
                })
                
                # 如果队列失败，降级为同步写入
                if not queued:
                    with self._stats_lock:
                        self._stats['sync_writes'] += 1
                    self.save_request_log(request_data, None)
                    self.update_statistics(request_data)
                
                # 重新抛出异常，不影响原有错误处理逻辑
                raise
                
        return wrapper

    
    # ==================== 数据查询与分析 ====================

    def get_statistics_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        获取统计摘要
        
        提供指定天数内的 API 访问统计概览。
        
        Args:
            days: 统计天数，默认 7 天
            
        Returns:
            dict: 包含以下内容的统计摘要：
                - 统计周期
                - 总体统计（总请求数、成功率、平均耗时等）
                - 热门接口 TOP 10
                - IP 统计
        """
        try:
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days)
                    
                    # 1. 总体统计
                    cursor.execute("""
                        SELECT 
                            SUM(请求总数) as 总请求数,
                            SUM(成功次数) as 成功次数,
                            SUM(失败次数) as 失败次数,
                            ROUND(AVG(平均耗时), 2) as 平均耗时,
                            COUNT(DISTINCT 路由地址) as 接口数量
                        FROM api_接口统计
                        WHERE 统计日期 BETWEEN %s AND %s
                    """, (start_date, end_date))
                    
                    summary = cursor.fetchone() or {}
                    
                    # 2. 热门接口 TOP 10
                    cursor.execute("""
                        SELECT 
                            路由地址,
                            SUM(请求总数) as 请求次数,
                            ROUND(AVG(平均耗时), 2) as 平均耗时
                        FROM api_接口统计
                        WHERE 统计日期 BETWEEN %s AND %s
                        GROUP BY 路由地址
                        ORDER BY 请求次数 DESC
                        LIMIT 10
                    """, (start_date, end_date))
                    
                    top_endpoints = cursor.fetchall()
                    
                    # 3. IP 统计
                    cursor.execute("""
                        SELECT 
                            COUNT(DISTINCT 客户端ip) as 独立ip数,
                            SUM(请求总数) as ip总请求数
                        FROM api_ip记录
                        WHERE 统计日期 BETWEEN %s AND %s
                    """, (start_date, end_date))
                    
                    ip_stats = cursor.fetchone() or {}
                    
                    # 4. 性能最慢的接口 TOP 5
                    cursor.execute("""
                        SELECT 
                            路由地址,
                            ROUND(MAX(最大耗时), 2) as 最大耗时,
                            ROUND(AVG(平均耗时), 2) as 平均耗时
                        FROM api_接口统计
                        WHERE 统计日期 BETWEEN %s AND %s
                        GROUP BY 路由地址
                        ORDER BY 最大耗时 DESC
                        LIMIT 5
                    """, (start_date, end_date))
                    
                    slow_endpoints = cursor.fetchall()
                    
                    # 构建返回结果
                    result = {
                        '统计周期': f'{start_date} 至 {end_date}',
                        '总体统计': summary,
                        '热门接口': top_endpoints,
                        'ip统计': ip_stats,
                        '慢接口': slow_endpoints
                    }
                    
                    return result
                    
            finally:
                connection.close()
                    
        except Exception as e:
            return {'错误': str(e)}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        清理历史数据
        
        删除指定天数之前的访问日志，保留统计数据。
        建议定期执行（如每天凌晨）以控制数据库大小。
        
        Args:
            days_to_keep: 保留最近多少天的数据，默认 30 天
            
        Returns:
            dict: 清理结果，包含删除的记录数
        """
        try:
            connection = self.pool.connection()
            try:
                with connection.cursor() as cursor:
                    self.ensure_database_context(cursor)
                    
                    cutoff_date = datetime.now().date() - timedelta(days=days_to_keep)
                    
                    # 1. 清理访问日志表
                    cursor.execute("""
                        DELETE FROM api_访问日志
                        WHERE 请求时间 < %s
                    """, (cutoff_date,))
                    
                    deleted_logs = cursor.rowcount
                    
                    # 2. 清理 ip 记录表（可选，通常保留更久）
                    cursor.execute("""
                        DELETE FROM api_ip记录
                        WHERE 统计日期 < %s
                    """, (cutoff_date,))
                    
                    deleted_ip_records = cursor.rowcount
                    
                connection.commit()
                
                result = {
                    '删除日志数': deleted_logs,
                    '删除ip记录数': deleted_ip_records,
                    '清理日期': str(cutoff_date)
                }
                
                return result
                
            finally:
                connection.close()
                
        except Exception as e:
            return {'错误': str(e)}
    
    def consume_queue_tasks(self, batch_size: int = 100, timeout: float = 1.0):
        """
        从 Redis 队列中消费任务并写入数据库（用于单独的消费者进程）
        
        这个方法应该在单独的进程中循环调用
        
        Args:
            batch_size: 每次处理的最大任务数
            timeout: 从队列获取任务的超时时间（秒）
            
        Returns:
            int: 处理的任务数量
        """
        if not self.enable_async:
            return 0
        
        processed = 0
        
        try:
            # 批量从队列中取出任务（BRPOP，从右侧阻塞弹出）
            for _ in range(batch_size):
                result = self.redis_client.brpop(self.queue_name, timeout=timeout)
                if not result:
                    break  # 队列为空
                
                _, task_json = result
                
                try:
                    # （Redis 可能返回 bytes）
                    if isinstance(task_json, bytes):
                        task_json = task_json.decode('utf-8')
                    
                    # 解析任务数据，还原 datetime 对象（使用 datetime 解码器）
                    task = json.loads(task_json, object_hook=self._datetime_decoder)
                    task_type = task.get('type')
                    task_data = task.get('data', {})
                    
                    # 处理不同类型的任务
                    if task_type == 'request_log':
                        # 写入日志和统计
                        self.save_request_log(task_data, None)
                        self.update_statistics(task_data)
                        processed += 1
                    
                except Exception as e:
                    # 单个任务失败不影响其他任务
                    pass
            
            return processed
            
        except Exception as e:
            # 静默处理错误
            return processed


# # ==================== 全局实例与导出 ====================

# # 创建全局监控实例
# route_monitor = RouteMonitor()

# # 导出核心装饰器（推荐使用此方式）
# api_monitor = route_monitor.api_monitor


# ==================== 模块导出列表 ====================
__all__ = [
    'RouteMonitor',
    'api_monitor',
    'get_request_id',
    'get_statistics_summary',
    'cleanup_old_data',
    'get_async_stats',
]