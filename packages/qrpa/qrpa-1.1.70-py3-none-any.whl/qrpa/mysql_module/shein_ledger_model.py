#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHEIN账本记录数据模型
使用SQLAlchemy定义账本记录表结构
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, DECIMAL, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 创建基类
Base = declarative_base()

class SheinLedgerRecord(Base):
    """
    SHEIN账本记录表
    存储来自接口的账本记录数据
    """
    __tablename__ = 'shein_ledger_records'

    # 主键ID (自增)
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 原始数据中的ID作为ledger_id
    ledger_id = Column(String(50), nullable=False, unique=True, comment='账本记录ID(原始数据中的id字段)')

    # 变更类型相关字段
    display_change_type = Column(Integer, nullable=True, comment='显示变更类型编码')
    display_change_type_name = Column(String(100), nullable=True, comment='显示变更类型名称')
    change_type = Column(Integer, nullable=True, comment='变更类型编码')

    # 结算类型相关字段
    settle_type = Column(Integer, nullable=True, comment='结算类型编码')
    settle_type_name = Column(String(100), nullable=True, comment='结算类型名称')

    # 业务单号相关字段
    business_no = Column(String(100), nullable=True, comment='业务单号')
    bill_no = Column(String(100), nullable=True, comment='账单编号')
    uniq_key = Column(String(100), nullable=True, comment='唯一键')

    # 时间相关字段
    happen_time = Column(DateTime, nullable=True, comment='发生时间')
    add_time = Column(DateTime, nullable=True, comment='添加时间')

    # 供应商相关字段
    supplier_id = Column(Integer, nullable=True, comment='供应商ID')
    supplier_name = Column(String(200), nullable=True, comment='供应商名称')
    supplier_code = Column(String(100), nullable=True, comment='供应商编码')

    # 商品相关字段
    skc = Column(String(100), nullable=True, comment='SKC编码')
    sku = Column(String(100), nullable=True, comment='SKU编码')
    supplier_sku = Column(String(200), nullable=True, comment='供应商SKU')
    suffix_zh = Column(String(100), nullable=True, comment='商品属性(中文)')

    # 数量和金额相关字段
    quantity = Column(Integer, nullable=True, comment='数量')
    cost = Column(DECIMAL(10, 2), nullable=True, comment='成本')
    amount = Column(DECIMAL(10, 2), nullable=True, comment='金额')
    currency = Column(String(10), nullable=True, comment='货币类型')

    # 备注
    remark = Column(Text, nullable=True, comment='备注')

    # 前后关联字段
    before_inventory_id = Column(String(50), nullable=True, comment='前库存ID')
    after_inventory_id = Column(String(50), nullable=True, comment='后库存ID')
    before_business_no = Column(String(100), nullable=True, comment='前业务单号')
    after_business_no = Column(String(100), nullable=True, comment='后业务单号')
    before_bill_no = Column(String(100), nullable=True, comment='前账单号')
    after_bill_no = Column(String(100), nullable=True, comment='后账单号')
    after_change_type_name = Column(String(100), nullable=True, comment='后变更类型名称')

    # 业务标签
    business_no_tags = Column(String(500), nullable=True, comment='业务单号标签')

    # 来源系统
    source_system = Column(String(50), nullable=True, comment='来源系统')

    # 促销相关
    show_promotion = Column(Integer, nullable=True, comment='显示促销')

    # 销售相关字段
    sales_seller_id = Column(Integer, nullable=True, comment='销售卖家ID')
    sales_seller_name = Column(String(200), nullable=True, comment='销售卖家名称')

    # 店铺相关字段
    store_username = Column(String(100), nullable=True, comment='店铺用户名')
    store_name = Column(String(200), nullable=True, comment='店铺名称')
    store_manager = Column(String(100), nullable=True, comment='店铺经理')

    # 成本价格和SKU图片
    cost_price = Column(DECIMAL(10, 2), nullable=True, comment='成本价格')
    sku_img = Column(Text, nullable=True, comment='SKU图片URL')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 定义索引
    __table_args__ = (
        Index('ix_ledger_id', 'ledger_id'),
        Index('ix_business_no', 'business_no'),
        Index('ix_bill_no', 'bill_no'),
        Index('ix_supplier_id', 'supplier_id'),
        Index('ix_skc', 'skc'),
        Index('ix_sku', 'sku'),
        Index('ix_store_username', 'store_username'),
        Index('ix_happen_time', 'happen_time'),
        Index('ix_add_time', 'add_time'),
        Index('ix_change_type', 'change_type'),
        Index('ix_display_change_type', 'display_change_type'),
    )

    def __repr__(self):
        return f"<SheinLedgerRecord(id={self.id}, ledger_id='{self.ledger_id}', business_no='{self.business_no}')>"

class SheinLedgerManager:
    """
    SHEIN账本记录数据管理器
    提供数据库操作相关方法
    """

    def __init__(self, database_url):
        """
        初始化数据库连接
        
        Args:
            database_url (str): 数据库连接URL，例如：
                mysql+pymysql://username:password@localhost:3306/database_name
        """
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """
        创建数据表
        """
        Base.metadata.create_all(self.engine)
        print("账本记录数据表创建成功！")

    def drop_tables(self):
        """
        删除数据表
        """
        Base.metadata.drop_all(self.engine)
        print("账本记录数据表删除成功！")

    def _parse_datetime(self, datetime_str):
        """
        解析日期时间字符串
        """
        if not datetime_str:
            return None
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except:
            return None

    def _parse_decimal(self, value):
        """
        解析decimal值
        """
        if value is None:
            return None
        try:
            return float(value)
        except:
            return None

    def _parse_cost_price(self, value):
        """
        解析成本价格，如果是"-"或"未匹配到"等非数字值则返回0
        """
        if value is None:
            return 0.0

        # 转换为字符串处理
        str_value = str(value).strip()

        # 如果是 "-" 或包含 "未匹配到" 等文本，则返回0
        if str_value == "-" or "未匹配到" in str_value or str_value == "":
            return 0.0

        try:
            return float(str_value)
        except:
            return 0.0

    def upsert_ledger_data(self, data_list):
        """
        从JSON数据中执行upsert操作（插入或更新）
        
        Args:
            data_list (list): 账本记录数据列表
        """
        session = self.Session()
        try:
            insert_count = 0
            update_count = 0

            for data in data_list:
                ledger_id = str(data.get('id'))
                existing_record = session.query(SheinLedgerRecord).filter_by(ledger_id=ledger_id).first()

                if existing_record:
                    # 更新现有记录
                    self._update_record_from_data(existing_record, data)
                    update_count += 1
                else:
                    # 插入新记录
                    new_record = self._create_record_from_data(data)
                    session.add(new_record)
                    insert_count += 1

            session.commit()
            print(f"成功处理 {len(data_list)} 条账本记录数据")
            print(f"新增记录: {insert_count} 条，更新记录: {update_count} 条")

        except Exception as e:
            session.rollback()
            print(f"处理数据失败: {e}")
            raise
        finally:
            session.close()

    def _create_record_from_data(self, data):
        """
        从JSON数据创建新的记录对象
        """
        return SheinLedgerRecord(
            ledger_id=str(data.get('id')),
            display_change_type=data.get('displayChangeType'),
            display_change_type_name=data.get('displayChangeTypeName'),
            change_type=data.get('changeType'),
            settle_type=data.get('settleType'),
            settle_type_name=data.get('settleTypeName'),
            business_no=data.get('businessNo'),
            bill_no=data.get('billNo'),
            uniq_key=data.get('uniqKey'),
            happen_time=self._parse_datetime(data.get('happenTime')),
            add_time=self._parse_datetime(data.get('addTime')),
            supplier_id=data.get('supplierId'),
            supplier_name=data.get('supplierName'),
            supplier_code=data.get('supplierCode'),
            skc=data.get('skc'),
            sku=data.get('sku'),
            supplier_sku=data.get('supplierSku'),
            suffix_zh=data.get('suffixZh'),
            quantity=data.get('quantity'),
            cost=self._parse_decimal(data.get('cost')),
            amount=self._parse_decimal(data.get('amount')),
            currency=data.get('currency'),
            remark=data.get('remark'),
            before_inventory_id=data.get('beforeInventoryId'),
            after_inventory_id=data.get('afterInventoryId'),
            before_business_no=data.get('beforeBusinessNo'),
            after_business_no=data.get('afterBusinessNo'),
            before_bill_no=data.get('beforeBillNo'),
            after_bill_no=data.get('afterBillNo'),
            after_change_type_name=data.get('afterChangeTypeName'),
            business_no_tags=data.get('businessNoTags'),
            source_system=data.get('sourceSystem'),
            show_promotion=data.get('showPromotion'),
            sales_seller_id=data.get('salesSellerId'),
            sales_seller_name=data.get('salesSellerName'),
            store_username=data.get('store_username'),
            store_name=data.get('store_name'),
            store_manager=data.get('store_manager'),
            cost_price=self._parse_cost_price(data.get('cost_price')),
            sku_img=data.get('sku_img')
        )

    def _update_record_from_data(self, record, data):
        """
        使用JSON数据更新现有记录
        """
        record.display_change_type = data.get('displayChangeType')
        record.display_change_type_name = data.get('displayChangeTypeName')
        record.change_type = data.get('changeType')
        record.settle_type = data.get('settleType')
        record.settle_type_name = data.get('settleTypeName')
        record.business_no = data.get('businessNo')
        record.bill_no = data.get('billNo')
        record.uniq_key = data.get('uniqKey')
        record.happen_time = self._parse_datetime(data.get('happenTime'))
        record.add_time = self._parse_datetime(data.get('addTime'))
        record.supplier_id = data.get('supplierId')
        record.supplier_name = data.get('supplierName')
        record.supplier_code = data.get('supplierCode')
        record.skc = data.get('skc')
        record.sku = data.get('sku')
        record.supplier_sku = data.get('supplierSku')
        record.suffix_zh = data.get('suffixZh')
        record.quantity = data.get('quantity')
        record.cost = self._parse_decimal(data.get('cost'))
        record.amount = self._parse_decimal(data.get('amount'))
        record.currency = data.get('currency')
        record.remark = data.get('remark')
        record.before_inventory_id = data.get('beforeInventoryId')
        record.after_inventory_id = data.get('afterInventoryId')
        record.before_business_no = data.get('beforeBusinessNo')
        record.after_business_no = data.get('afterBusinessNo')
        record.before_bill_no = data.get('beforeBillNo')
        record.after_bill_no = data.get('afterBillNo')
        record.after_change_type_name = data.get('afterChangeTypeName')
        record.business_no_tags = data.get('businessNoTags')
        record.source_system = data.get('sourceSystem')
        record.show_promotion = data.get('showPromotion')
        record.sales_seller_id = data.get('salesSellerId')
        record.sales_seller_name = data.get('salesSellerName')
        record.store_username = data.get('store_username')
        record.store_name = data.get('store_name')
        record.store_manager = data.get('store_manager')
        record.cost_price = self._parse_cost_price(data.get('cost_price'))
        record.sku_img = data.get('sku_img')
        record.updated_at = datetime.now()

    def get_ledger_records(self, limit=None, offset=None, order_by=None):
        """
        查询账本记录列表
        
        Args:
            limit (int): 限制返回数量
            offset (int): 偏移量
            order_by (str): 排序字段，默认按happen_time降序
            
        Returns:
            list: 账本记录列表
        """
        session = self.Session()
        try:
            query = session.query(SheinLedgerRecord)

            # 默认按发生时间降序排列
            if order_by:
                if hasattr(SheinLedgerRecord, order_by):
                    query = query.order_by(getattr(SheinLedgerRecord, order_by).desc())
            else:
                query = query.order_by(SheinLedgerRecord.happen_time.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        finally:
            session.close()

    def search_records(self, **kwargs):
        """
        根据条件搜索账本记录
        
        Args:
            **kwargs: 搜索条件，如store_username, business_no, sku等
            
        Returns:
            list: 符合条件的记录列表
        """
        session = self.Session()
        try:
            query = session.query(SheinLedgerRecord)

            # 根据传入的条件进行过滤
            for key, value in kwargs.items():
                if hasattr(SheinLedgerRecord, key) and value is not None:
                    if isinstance(value, str) and key in ['business_no', 'bill_no', 'skc', 'sku', 'supplier_name', 'store_name']:
                        # 字符串字段支持模糊搜索
                        query = query.filter(getattr(SheinLedgerRecord, key).like(f'%{value}%'))
                    else:
                        query = query.filter(getattr(SheinLedgerRecord, key) == value)

            return query.order_by(SheinLedgerRecord.happen_time.desc()).all()
        finally:
            session.close()

    def get_statistics_by_store(self, store_username=None):
        """
        按店铺统计数据
        
        Args:
            store_username (str): 店铺用户名，如果不提供则统计所有店铺
            
        Returns:
            dict: 统计结果
        """
        session = self.Session()
        try:
            query = session.query(SheinLedgerRecord)

            if store_username:
                query = query.filter(SheinLedgerRecord.store_username == store_username)

            records = query.all()

            # 统计信息
            total_count = len(records)
            total_amount = sum([r.amount for r in records if r.amount])
            total_cost = sum([r.cost for r in records if r.cost])
            total_quantity = sum([r.quantity for r in records if r.quantity])

            # 按变更类型统计
            change_type_stats = {}
            for record in records:
                change_type = record.display_change_type_name or '未知'
                if change_type not in change_type_stats:
                    change_type_stats[change_type] = {'count': 0, 'amount': 0, 'quantity': 0}
                change_type_stats[change_type]['count'] += 1
                change_type_stats[change_type]['amount'] += record.amount or 0
                change_type_stats[change_type]['quantity'] += record.quantity or 0

            return {
                'total_count'      : total_count,
                'total_amount'     : float(total_amount) if total_amount else 0,
                'total_cost'       : float(total_cost) if total_cost else 0,
                'total_quantity'   : total_quantity,
                'change_type_stats': change_type_stats
            }
        finally:
            session.close()

    def import_from_json_file(self, json_file_path):
        """
        从JSON文件导入数据
        
        Args:
            json_file_path (str): JSON文件路径
        """
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
            self.upsert_ledger_data(data_list)

def example_usage():
    """
    使用示例
    """
    # 数据库连接URL（请根据实际情况修改）
    database_url = "mysql+pymysql://root:123wyk@localhost:3306/lz"

    # 创建管理器实例
    manager = SheinLedgerManager(database_url)

    # 创建数据表
    manager.create_tables()

    # 从JSON文件导入数据
    json_file = "ledger_record_GS0365305_2025-09-24_2025-09-24.json"
    manager.import_from_json_file(json_file)

    # 查询示例
    records = manager.get_ledger_records(limit=10)
    for record in records:
        print(f"记录ID: {record.ledger_id}, 业务单号: {record.business_no}, 金额: {record.amount}")

    # 搜索示例
    search_results = manager.search_records(store_username="GS0365305")
    print(f"店铺 GS0365305 的记录数量: {len(search_results)}")

    # 统计示例
    stats = manager.get_statistics_by_store("GS0365305")
    print(f"统计结果: {stats}")

if __name__ == "__main__":
    pass
    # example_usage()
