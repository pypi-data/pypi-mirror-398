#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHEIN台账月报数据模型
使用SQLAlchemy定义台账月报表结构
"""

from sqlalchemy import create_engine, Column, String, DateTime, Integer, DECIMAL, Date, Index
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import json

# 创建基类
Base = declarative_base()

class SheinLedgerMonthReport(Base):
    """
    SHEIN台账月报表
    存储供应商维度的月度台账汇总数据
    """
    __tablename__ = 'shein_ledger_month_report'

    # 主键ID (自增)
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 供应商信息
    supplier_id = Column(Integer, nullable=False, comment='供应商ID')
    supplier_name = Column(String(200), nullable=False, comment='供应商名称')

    # 报表日期（月份的第一天）
    report_date = Column(Date, nullable=False, comment='报表月份（如2025-05-01）')

    # === 期初期末库存 ===
    begin_balance_cnt = Column(Integer, nullable=True, default=0, comment='期初库存数量')
    begin_balance_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='期初库存金额')
    end_balance_cnt = Column(Integer, nullable=True, default=0, comment='期末库存数量')
    end_balance_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='期末库存金额')

    # === 入库数据 ===
    # 紧急订单入库
    urgent_order_entry_cnt = Column(Integer, nullable=True, default=0, comment='紧急订单入库数量')
    urgent_order_entry_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='紧急订单入库金额')

    # 备货订单入库
    prepare_order_entry_cnt = Column(Integer, nullable=True, default=0, comment='备货订单入库数量')
    prepare_order_entry_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='备货订单入库金额')

    # 收益入库
    in_gain_cnt = Column(Integer, nullable=True, default=0, comment='收益入库数量')
    in_gain_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='收益入库金额')

    # 退货入库
    in_return_cnt = Column(Integer, nullable=True, default=0, comment='退货入库数量')
    in_return_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='退货入库金额')

    # 供应变更入库
    supply_change_in_cnt = Column(Integer, nullable=True, default=0, comment='供应变更入库数量')
    in_supply_change_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='供应变更入库金额')

    # 调整入库
    adjust_in_cnt = Column(Integer, nullable=True, default=0, comment='调整入库数量')
    adjust_in_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='调整入库金额')

    # 总入库
    in_cnt = Column(Integer, nullable=True, default=0, comment='总入库数量')
    in_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='总入库金额')

    # === 出库数据（核心字段） ===
    # 总出库（最重要）
    total_customer_cnt = Column(Integer, nullable=True, default=0, comment='总出库数量')
    total_customer_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='总出库金额')

    # 客户出库
    customer_cnt = Column(Integer, nullable=True, default=0, comment='客户出库数量')
    customer_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='客户出库金额')

    # 平台客户出库
    platform_customer_cnt = Column(Integer, nullable=True, default=0, comment='平台客户出库数量')
    platform_customer_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='平台客户出库金额')

    # 亏损出库
    out_loss_cnt = Column(Integer, nullable=True, default=0, comment='亏损出库数量')
    out_loss_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='亏损出库金额')

    # 供应商出库
    out_supplier_cnt = Column(Integer, nullable=True, default=0, comment='供应商出库数量')
    out_supplier_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='供应商出库金额')

    # 库存清理
    inventory_clear_cnt = Column(Integer, nullable=True, default=0, comment='库存清理数量')
    inventory_clear_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='库存清理金额')

    # 报表清理
    report_clear_cnt = Column(Integer, nullable=True, default=0, comment='报表清理数量')
    report_clear_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='报表清理金额')

    # 报废
    scrap_cnt = Column(Integer, nullable=True, default=0, comment='报废数量')
    scrap_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='报废金额')

    # 供应变更出库
    supply_change_out_cnt = Column(Integer, nullable=True, default=0, comment='供应变更出库数量')
    out_supply_change_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='供应变更出库金额')

    # 调整出库
    adjust_out_cnt = Column(Integer, nullable=True, default=0, comment='调整出库数量')
    adjust_out_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='调整出库金额')

    # 客户损失
    customer_lose_cnt = Column(Integer, nullable=True, default=0, comment='客户损失数量')
    customer_lose_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='客户损失金额')

    # 总出库
    out_cnt = Column(Integer, nullable=True, default=0, comment='总出库数量')
    out_amount = Column(DECIMAL(12, 2), nullable=True, default=0, comment='总出库金额')

    # === 扩展字段（用于后续关联店铺信息） ===
    store_username = Column(String(100), nullable=True, comment='店铺账号（预留）')
    store_name = Column(String(200), nullable=True, comment='店铺名称（预留）')
    store_manager = Column(String(100), nullable=True, comment='店长（预留）')

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 定义索引和唯一约束
    __table_args__ = (
        Index('ix_supplier_id', 'supplier_id'),
        Index('ix_report_date', 'report_date'),
        Index('ix_supplier_report', 'supplier_id', 'report_date', unique=True),  # 联合唯一索引
        Index('ix_store_username', 'store_username'),
    )

    def __repr__(self):
        return f"<SheinLedgerMonthReport(id={self.id}, supplier_id={self.supplier_id}, supplier_name='{self.supplier_name}', report_date='{self.report_date}')>"


class SheinLedgerMonthReportManager:
    """
    SHEIN台账月报数据管理器
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
        print("台账月报数据表创建成功！")

    def drop_tables(self):
        """
        删除数据表
        """
        Base.metadata.drop_all(self.engine)
        print("台账月报数据表删除成功！")

    def _parse_date(self, date_str):
        """
        解析日期字符串（格式：YYYY-MM-DD）
        """
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            return None

    def _parse_decimal(self, value):
        """
        解析decimal值，如果为None则返回0
        """
        if value is None:
            return 0
        try:
            return float(value)
        except:
            return 0

    def _parse_int(self, value):
        """
        解析整数值，如果为None则返回0
        """
        if value is None:
            return 0
        try:
            return int(value)
        except:
            return 0

    def upsert_month_report_data(self, data_list):
        """
        从JSON数据中执行upsert操作（插入或更新）

        Args:
            data_list (list): 月报数据列表
        """
        session = self.Session()
        try:
            insert_count = 0
            update_count = 0

            for data in data_list:
                supplier_id = data.get('supplierId')
                report_date = self._parse_date(data.get('reportDate'))

                if not supplier_id or not report_date:
                    print(f"警告：跳过无效数据（supplierId={supplier_id}, reportDate={report_date}）")
                    continue

                # 查找是否存在记录
                existing_record = session.query(SheinLedgerMonthReport).filter_by(
                    supplier_id=supplier_id,
                    report_date=report_date
                ).first()

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
            print(f"成功处理 {len(data_list)} 条月报数据")
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
        return SheinLedgerMonthReport(
            supplier_id=data.get('supplierId'),
            supplier_name=data.get('supplierName'),
            report_date=self._parse_date(data.get('reportDate')),

            # 期初期末库存
            begin_balance_cnt=self._parse_int(data.get('beginBalanceCnt')),
            begin_balance_amount=self._parse_decimal(data.get('beginBalanceAmount')),
            end_balance_cnt=self._parse_int(data.get('endBalanceCnt')),
            end_balance_amount=self._parse_decimal(data.get('endBalanceAmount')),

            # 入库数据
            urgent_order_entry_cnt=self._parse_int(data.get('urgentOrderEntryCnt')),
            urgent_order_entry_amount=self._parse_decimal(data.get('urgentOrderEntryAmount')),
            prepare_order_entry_cnt=self._parse_int(data.get('prepareOrderEntryCnt')),
            prepare_order_entry_amount=self._parse_decimal(data.get('prepareOrderEntryAmount')),
            in_gain_cnt=self._parse_int(data.get('inGainCnt')),
            in_gain_amount=self._parse_decimal(data.get('inGainAmount')),
            in_return_cnt=self._parse_int(data.get('inReturnCnt')),
            in_return_amount=self._parse_decimal(data.get('inReturnAmount')),
            supply_change_in_cnt=self._parse_int(data.get('supplyChangeInCnt')),
            in_supply_change_amount=self._parse_decimal(data.get('inSupplyChangeAmount')),
            adjust_in_cnt=self._parse_int(data.get('adjustInCnt')),
            adjust_in_amount=self._parse_decimal(data.get('adjustInAmount')),
            in_cnt=self._parse_int(data.get('inCnt')),
            in_amount=self._parse_decimal(data.get('inAmount')),

            # 出库数据
            total_customer_cnt=self._parse_int(data.get('totalCustomerCnt')),
            total_customer_amount=self._parse_decimal(data.get('totalCustomerAmount')),
            customer_cnt=self._parse_int(data.get('customerCnt')),
            customer_amount=self._parse_decimal(data.get('customerAmount')),
            platform_customer_cnt=self._parse_int(data.get('platformCustomerCnt')),
            platform_customer_amount=self._parse_decimal(data.get('platformCustomerAmount')),
            out_loss_cnt=self._parse_int(data.get('outLossCnt')),
            out_loss_amount=self._parse_decimal(data.get('outLossAmount')),
            out_supplier_cnt=self._parse_int(data.get('outSupplierCnt')),
            out_supplier_amount=self._parse_decimal(data.get('outSupplierAmount')),
            inventory_clear_cnt=self._parse_int(data.get('inventoryClearCnt')),
            inventory_clear_amount=self._parse_decimal(data.get('inventoryClearAmount')),
            report_clear_cnt=self._parse_int(data.get('reportClearCnt')),
            report_clear_amount=self._parse_decimal(data.get('reportClearAmount')),
            scrap_cnt=self._parse_int(data.get('scrapCnt')),
            scrap_amount=self._parse_decimal(data.get('scrapAmount')),
            supply_change_out_cnt=self._parse_int(data.get('supplyChangeOutCnt')),
            out_supply_change_amount=self._parse_decimal(data.get('outSupplyChangeAmount')),
            adjust_out_cnt=self._parse_int(data.get('adjustOutCnt')),
            adjust_out_amount=self._parse_decimal(data.get('adjustOutAmount')),
            customer_lose_cnt=self._parse_int(data.get('customerLoseCnt')),
            customer_lose_amount=self._parse_decimal(data.get('customerLoseAmount')),
            out_cnt=self._parse_int(data.get('outCnt')),
            out_amount=self._parse_decimal(data.get('outAmount')),

            # 扩展字段
            store_username=data.get('store_username'),
            store_name=data.get('store_name'),
            store_manager=data.get('store_manager')
        )

    def _update_record_from_data(self, record, data):
        """
        使用JSON数据更新现有记录
        """
        record.supplier_name = data.get('supplierName')

        # 期初期末库存
        record.begin_balance_cnt = self._parse_int(data.get('beginBalanceCnt'))
        record.begin_balance_amount = self._parse_decimal(data.get('beginBalanceAmount'))
        record.end_balance_cnt = self._parse_int(data.get('endBalanceCnt'))
        record.end_balance_amount = self._parse_decimal(data.get('endBalanceAmount'))

        # 入库数据
        record.urgent_order_entry_cnt = self._parse_int(data.get('urgentOrderEntryCnt'))
        record.urgent_order_entry_amount = self._parse_decimal(data.get('urgentOrderEntryAmount'))
        record.prepare_order_entry_cnt = self._parse_int(data.get('prepareOrderEntryCnt'))
        record.prepare_order_entry_amount = self._parse_decimal(data.get('prepareOrderEntryAmount'))
        record.in_gain_cnt = self._parse_int(data.get('inGainCnt'))
        record.in_gain_amount = self._parse_decimal(data.get('inGainAmount'))
        record.in_return_cnt = self._parse_int(data.get('inReturnCnt'))
        record.in_return_amount = self._parse_decimal(data.get('inReturnAmount'))
        record.supply_change_in_cnt = self._parse_int(data.get('supplyChangeInCnt'))
        record.in_supply_change_amount = self._parse_decimal(data.get('inSupplyChangeAmount'))
        record.adjust_in_cnt = self._parse_int(data.get('adjustInCnt'))
        record.adjust_in_amount = self._parse_decimal(data.get('adjustInAmount'))
        record.in_cnt = self._parse_int(data.get('inCnt'))
        record.in_amount = self._parse_decimal(data.get('inAmount'))

        # 出库数据
        record.total_customer_cnt = self._parse_int(data.get('totalCustomerCnt'))
        record.total_customer_amount = self._parse_decimal(data.get('totalCustomerAmount'))
        record.customer_cnt = self._parse_int(data.get('customerCnt'))
        record.customer_amount = self._parse_decimal(data.get('customerAmount'))
        record.platform_customer_cnt = self._parse_int(data.get('platformCustomerCnt'))
        record.platform_customer_amount = self._parse_decimal(data.get('platformCustomerAmount'))
        record.out_loss_cnt = self._parse_int(data.get('outLossCnt'))
        record.out_loss_amount = self._parse_decimal(data.get('outLossAmount'))
        record.out_supplier_cnt = self._parse_int(data.get('outSupplierCnt'))
        record.out_supplier_amount = self._parse_decimal(data.get('outSupplierAmount'))
        record.inventory_clear_cnt = self._parse_int(data.get('inventoryClearCnt'))
        record.inventory_clear_amount = self._parse_decimal(data.get('inventoryClearAmount'))
        record.report_clear_cnt = self._parse_int(data.get('reportClearCnt'))
        record.report_clear_amount = self._parse_decimal(data.get('reportClearAmount'))
        record.scrap_cnt = self._parse_int(data.get('scrapCnt'))
        record.scrap_amount = self._parse_decimal(data.get('scrapAmount'))
        record.supply_change_out_cnt = self._parse_int(data.get('supplyChangeOutCnt'))
        record.out_supply_change_amount = self._parse_decimal(data.get('outSupplyChangeAmount'))
        record.adjust_out_cnt = self._parse_int(data.get('adjustOutCnt'))
        record.adjust_out_amount = self._parse_decimal(data.get('adjustOutAmount'))
        record.customer_lose_cnt = self._parse_int(data.get('customerLoseCnt'))
        record.customer_lose_amount = self._parse_decimal(data.get('customerLoseAmount'))
        record.out_cnt = self._parse_int(data.get('outCnt'))
        record.out_amount = self._parse_decimal(data.get('outAmount'))

        # 扩展字段
        record.store_username = data.get('store_username')
        record.store_name = data.get('store_name')
        record.store_manager = data.get('store_manager')

        record.updated_at = datetime.now()

    def get_month_reports(self, supplier_id=None, report_date=None, year=None, month=None, limit=None, offset=None):
        """
        查询月报记录列表

        Args:
            supplier_id (int): 供应商ID
            report_date (str): 报表日期（格式：YYYY-MM-DD）
            year (int): 年份
            month (int): 月份
            limit (int): 限制返回数量
            offset (int): 偏移量

        Returns:
            list: 月报记录列表
        """
        session = self.Session()
        try:
            query = session.query(SheinLedgerMonthReport)

            if supplier_id:
                query = query.filter(SheinLedgerMonthReport.supplier_id == supplier_id)

            if report_date:
                query = query.filter(SheinLedgerMonthReport.report_date == report_date)

            if year and month:
                # 按年月查询
                date_str = f"{year}-{month:02d}-01"
                query = query.filter(SheinLedgerMonthReport.report_date == date_str)

            # 默认按报表日期降序排列
            query = query.order_by(SheinLedgerMonthReport.report_date.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()
        finally:
            session.close()

    def get_statistics_by_supplier(self, supplier_id, start_date=None, end_date=None):
        """
        按供应商统计多个月的汇总数据

        Args:
            supplier_id (int): 供应商ID
            start_date (str): 开始日期（格式：YYYY-MM-DD）
            end_date (str): 结束日期（格式：YYYY-MM-DD）

        Returns:
            dict: 统计结果
        """
        session = self.Session()
        try:
            query = session.query(SheinLedgerMonthReport).filter(
                SheinLedgerMonthReport.supplier_id == supplier_id
            )

            if start_date:
                query = query.filter(SheinLedgerMonthReport.report_date >= start_date)
            if end_date:
                query = query.filter(SheinLedgerMonthReport.report_date <= end_date)

            records = query.all()

            # 统计信息
            total_in_cnt = sum([r.in_cnt for r in records])
            total_in_amount = sum([r.in_amount for r in records])
            total_out_cnt = sum([r.out_cnt for r in records])
            total_out_amount = sum([r.out_amount for r in records])
            total_customer_cnt = sum([r.total_customer_cnt for r in records])
            total_customer_amount = sum([r.total_customer_amount for r in records])

            return {
                'supplier_id'            : supplier_id,
                'month_count'            : len(records),
                'total_in_cnt'           : total_in_cnt,
                'total_in_amount'        : float(total_in_amount),
                'total_out_cnt'          : total_out_cnt,
                'total_out_amount'       : float(total_out_amount),
                'total_customer_cnt'     : total_customer_cnt,
                'total_customer_amount'  : float(total_customer_amount)
            }
        finally:
            session.close()

    def get_statistics_by_month(self, report_date):
        """
        按月份统计所有供应商的汇总数据

        Args:
            report_date (str): 报表日期（格式：YYYY-MM-DD）

        Returns:
            dict: 统计结果
        """
        session = self.Session()
        try:
            records = session.query(SheinLedgerMonthReport).filter(
                SheinLedgerMonthReport.report_date == report_date
            ).all()

            # 统计信息
            supplier_count = len(records)
            total_in_amount = sum([r.in_amount for r in records])
            total_out_amount = sum([r.out_amount for r in records])
            total_customer_amount = sum([r.total_customer_amount for r in records])

            return {
                'report_date'            : report_date,
                'supplier_count'         : supplier_count,
                'total_in_amount'        : float(total_in_amount),
                'total_out_amount'       : float(total_out_amount),
                'total_customer_amount'  : float(total_customer_amount)
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
            self.upsert_month_report_data(data_list)

    def get_store_month_summary(self, start_date, end_date):
        """
        按店铺+月份汇总出库数据（用于Excel导出）

        Args:
            start_date (str): 开始日期（格式：YYYY-MM-DD）
            end_date (str): 结束日期（格式：YYYY-MM-DD）

        Returns:
            dict: 按店铺分组的月度数据
                  {
                      'store_name': {
                          'store_username': 'xxx',
                          'store_manager': 'xxx',
                          'months': {
                              1: {'cnt': xxx, 'amount': xxx},  # 1月
                              2: {'cnt': xxx, 'amount': xxx},  # 2月
                              ...
                              12: {'cnt': xxx, 'amount': xxx}  # 12月
                          }
                      }
                  }
        """
        from collections import defaultdict

        session = self.Session()
        try:
            # 查询日期范围内的数据
            records = session.query(SheinLedgerMonthReport).filter(
                SheinLedgerMonthReport.report_date >= start_date,
                SheinLedgerMonthReport.report_date <= end_date
            ).order_by(
                SheinLedgerMonthReport.store_username,
                SheinLedgerMonthReport.report_date
            ).all()

            # 按店铺+月份组织数据
            store_data = defaultdict(lambda: {
                'store_username': '',
                'store_manager': '',
                'months': defaultdict(lambda: {'cnt': 0, 'amount': 0})
            })

            for record in records:
                store_key = record.store_name or record.store_username
                month = int(record.report_date.strftime('%m'))  # 1-12

                # 保存店铺账号和店长信息（取第一条记录的值）
                if not store_data[store_key]['store_username']:
                    store_data[store_key]['store_username'] = record.store_username or ''
                    store_data[store_key]['store_manager'] = record.store_manager or ''

                # 累加月度数据
                store_data[store_key]['months'][month]['cnt'] += record.total_customer_cnt or 0
                store_data[store_key]['months'][month]['amount'] += float(record.total_customer_amount or 0)

            return dict(store_data)

        finally:
            session.close()


def example_usage():
    """
    使用示例
    """
    # 数据库连接URL（请根据实际情况修改）
    database_url = "mysql+pymysql://root:123wyk@localhost:3306/lz"

    # 创建管理器实例
    manager = SheinLedgerMonthReportManager(database_url)

    # 创建数据表
    manager.create_tables()

    # 从JSON文件导入数据
    json_file = "ledger_month_GS0365305_2025-01-01_2025-12-31.json"
    manager.import_from_json_file(json_file)

    # 查询示例
    reports = manager.get_month_reports(limit=10)
    for report in reports:
        print(f"供应商: {report.supplier_name}, 月份: {report.report_date}, 出库金额: {report.total_customer_amount}")

    # 按供应商统计
    stats = manager.get_statistics_by_supplier(supplier_id=5230023)
    print(f"供应商统计: {stats}")

    # 按月份统计
    month_stats = manager.get_statistics_by_month("2025-05-01")
    print(f"月份统计: {month_stats}")


if __name__ == "__main__":
    pass
    # example_usage()
