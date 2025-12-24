# -*- coding: utf-8 -*-
"""
查询并添加商品上市年份
"""

from typing import Dict, List, Optional, Any


def get_item_listing_years(
    cursor,
    item_ids: List[str],
    attribute_database: str = '属性设置3',
    logger: Optional[Any] = None
) -> Dict[str, str]:
    """
    批量获取商品的上市年份
    
    原理说明：
    通过查询"货品年份基准"表，该表存储了商品ID区间的基准数据（按商品ID降序）。
    对于任意商品ID，找到第一个小于等于它的基准ID，该基准ID对应的上市年份即为该商品的上市年份。
    
    例如：
    - 基准表数据: 600000000000 -> "2020年1月", 700000000000 -> "2021年1月"
    - 查询商品ID: 650000000000
    - 匹配逻辑: 650000000000 >= 600000000000，所以匹配到 "2020年1月"
    
    Args:
        cursor: 数据库游标对象
        item_ids: 商品ID列表（字符串格式）
        attribute_database: 属性数据库名称，默认为 '属性设置3'
        logger: 日志记录器（可选）
        
    Returns:
        Dict[str, str]: 商品ID到上市年份的映射字典
        - Key: 商品ID（字符串）
        - Value: 上市年份（如 "2024年8月"）或 "未知"
        
    Example:
        >>> listing_years = get_item_listing_years(
        ...     cursor, 
        ...     ['623456789012', '734567890123'],
        ...     logger=logger
        ... )
        >>> print(listing_years)
        {'623456789012': '2020年3月', '734567890123': '2023年8月'}
    """
    listing_years = {}
    
    # 输入验证
    if not item_ids:
        return listing_years
    
    # 过滤无效的商品ID
    valid_item_ids = [
        item_id for item_id in item_ids 
        if item_id and str(item_id).strip() and str(item_id) != '0'
    ]
    
    if not valid_item_ids:
        return listing_years
    
    try:
        # 从货品年份基准表查询所有区间数据，按商品id降序
        # 降序排列是为了从大到小匹配，找到第一个小于等于目标ID的基准ID
        year_query = f"""
            SELECT 商品id as base_product_id, 上市年份 as listing_year
            FROM `{attribute_database}`.`货品年份基准`
            ORDER BY 商品id DESC
        """
        cursor.execute(year_query)
        base_results = cursor.fetchall()
        
        # 对每个商品ID进行匹配
        for item_id in valid_item_ids:
            try:
                # 淘宝商品ID理论上不会超过14位，如果超过则标记为未知
                if len(str(item_id)) >= 14:
                    listing_years[item_id] = '未知'
                    continue
                
                # 转换为整数进行比较
                item_id_int = int(item_id)
                matched_year = '未知'
                
                # 从大到小遍历基准数据，找到第一个小于等于当前商品ID的基准
                for base_row in base_results:
                    base_id = int(base_row['base_product_id'])
                    if item_id_int >= base_id:
                        matched_year = base_row['listing_year']
                        break
                
                listing_years[item_id] = matched_year
                
            except (ValueError, TypeError) as e:
                # 商品ID转换失败，标记为未知
                listing_years[item_id] = '未知'
                if logger:
                    logger.debug(f'商品ID转换失败: {item_id}, 错误: {str(e)}')
        
    except Exception as e:
        error_msg = f'查询商品上市年份失败: {str(e)}'
        if logger:
            logger.warning(error_msg)
        else:
            print(error_msg)
    
    return listing_years


def add_listing_year_to_items(
    cursor,
    items: List[Dict],
    item_id_key: str = 'itemId',
    listing_year_key: str = 'listingYear',
    attribute_database: str = '属性设置3',
    logger: Optional[Any] = None
) -> List[Dict]:
    """
    为商品列表批量添加上市年份字段
    
    这是一个便捷函数，直接修改传入的商品列表，为每个商品添加上市年份字段。
    
    Args:
        cursor: 数据库游标对象
        items: 商品列表，每个商品是一个字典
        item_id_key: 商品ID在字典中的键名，默认为 'itemId'
        listing_year_key: 上市年份要写入的键名，默认为 'listingYear'
        attribute_database: 属性数据库名称，默认为 '属性设置3'
        logger: 日志记录器（可选）
        
    Returns:
        List[Dict]: 添加了上市年份字段的商品列表（原地修改）
        
    Example:
        >>> items = [
        ...     {'itemId': '623456789012', 'itemName': '商品A'},
        ...     {'itemId': '734567890123', 'itemName': '商品B'}
        ... ]
        >>> add_listing_year_to_items(cursor, items, logger=logger)
        >>> print(items[0]['listingYear'])
        '2020年3月'
    """
    if not items:
        return items
    
    # 收集所有唯一的商品ID
    item_ids = list(set(
        str(item.get(item_id_key)) 
        for item in items 
        if item.get(item_id_key)
    ))
    
    # 批量查询上市年份
    listing_years = get_item_listing_years(
        cursor=cursor,
        item_ids=item_ids,
        attribute_database=attribute_database,
        logger=logger
    )
    
    # 将上市年份写回到商品列表
    for item in items:
        item_id = str(item.get(item_id_key, ''))
        item[listing_year_key] = listing_years.get(item_id, '未知')
    
    return items


def is_recent_listing(
    listing_year: str,
    months: int = 6
) -> bool:
    """
    判断商品是否为近期上架的新品
    
    Args:
        listing_year: 上市年份字符串，格式如 "2024年8月" 或 "2024年08月"
        months: 判断阈值（月数），默认为6个月
        
    Returns:
        bool: 如果是近期上架（在指定月数内）返回 True，否则返回 False
        
    Example:
        >>> is_recent_listing("2024年8月", months=6)
        True  # 假设当前是2024年11月
        >>> is_recent_listing("2023年1月", months=6)
        False
    """
    if not listing_year or not isinstance(listing_year, str):
        return False
    
    # 解析上市年份字符串（格式：2024年8月 或 2024年08月）
    import re
    match = re.match(r'(\d{4})年\s*(\d{1,2})月', listing_year)
    if not match:
        return False
    
    try:
        from datetime import datetime
        
        year = int(match.group(1))
        month = int(match.group(2))
        
        # 构建上市日期（取每月1号）
        listing_date = datetime(year, month, 1)
        
        # 计算当前日期与上市日期的月份差
        now = datetime.now()
        diff_months = (now.year - listing_date.year) * 12 + (now.month - listing_date.month)
        
        # 判断是否在指定月数内
        return 0 <= diff_months < months
        
    except (ValueError, TypeError):
        return False


# ============================================================================
# 使用示例
# ============================================================================
"""
# 示例1：在数据管理器类中使用
class SomeDataManager:
    def __init__(self, cursor, logger):
        self.cursor = cursor
        self.logger = logger
    
    def get_items_with_listing_year(self):
        # 查询商品数据
        items = [
            {'itemId': '623456789012', 'itemName': '商品A'},
            {'itemId': '734567890123', 'itemName': '商品B'}
        ]
        
        # 批量添加上市年份
        from route_support.item_utils import add_listing_year_to_items
        add_listing_year_to_items(
            cursor=self.cursor,
            items=items,
            logger=self.logger
        )
        
        return items

# 示例2：直接获取商品ID到上市年份的映射
def some_function(cursor, logger):
    from route_support.item_utils import get_item_listing_years
    
    item_ids = ['623456789012', '734567890123']
    listing_years = get_item_listing_years(
        cursor=cursor,
        item_ids=item_ids,
        logger=logger
    )
    
    for item_id, year in listing_years.items():
        print(f"商品 {item_id} 的上市年份是: {year}")

# 示例3：判断是否为新品
def render_item_badge(item):
    from route_support.item_utils import is_recent_listing
    
    listing_year = item.get('listingYear', '')
    if is_recent_listing(listing_year, months=6):
        return '<span class="badge-new">NEW</span>'
    return ''
"""

