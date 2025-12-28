#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新品分析数据模型
使用SQLAlchemy定义shein_new_product_analysis表结构
"""

from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, Date, BigInteger, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 创建基类
Base = declarative_base()

class SheinNewProductAnalysis(Base):
    """
    希音新品分析表
    存储SKC新品分析相关数据
    """
    __tablename__ = 'shein_new_product_analysis'

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 店铺信息
    store_username = Column(String(100), nullable=False, comment='店铺账号')
    store_name = Column(String(200), nullable=True, comment='店铺名称')

    # 日期信息
    stat_date = Column(Date, nullable=False, comment='统计日期')
    shelf_date = Column(Date, nullable=True, comment='上架日期')

    # SKC信息
    skc = Column(String(100), nullable=False, comment='平台SKC')
    sku_supplier_no = Column(String(100), nullable=True, comment='商家SKC')
    layer_nm = Column(String(100), nullable=True, comment='商品层级')
    
    # 品类信息
    new_cate1_nm = Column(String(200), nullable=True, comment='一级品类名称')
    new_cate2_nm = Column(String(200), nullable=True, comment='二级品类名称')
    new_cate3_nm = Column(String(200), nullable=True, comment='三级品类名称')
    new_cate4_nm = Column(String(200), nullable=True, comment='四级品类名称')
    
    goods_name = Column(String(500), nullable=True, comment='商品标题')
    img_url = Column(String(500), nullable=True, comment='SKC图片URL')

    # 状态标识
    onsale_flag = Column(Integer, nullable=True, default=0, comment='在售标识(0-否,1-是)')
    sale_flag = Column(Integer, nullable=True, default=0, comment='上架标识(0-否,1-是)')
    new_goods_tag = Column(Integer, nullable=True, comment='新品标签(1-新品爆款,2-新品畅销,3-潜力新品,4-新品)')

    # 销售数据
    sale_cnt = Column(Integer, nullable=True, default=0, comment='销量')
    pay_order_cnt = Column(Integer, nullable=True, default=0, comment='支付订单数')
    goods_uv = Column(Integer, nullable=True, default=0, comment='商品访客数')
    cart_uv_idx = Column(Integer, nullable=True, default=0, comment='加车访客')
    eps_uv_idx = Column(Integer, nullable=True, default=0, comment='曝光人数')

    # 转化率数据
    eps_gds_ctr_idx = Column(DECIMAL(10, 4), nullable=True, comment='点击率')
    gds_pay_ctr_idx = Column(DECIMAL(10, 4), nullable=True, comment='转化率')
    bad_comment_rate = Column(DECIMAL(10, 4), nullable=True, comment='差评率')

    # 促销活动信息(JSON格式)
    prom_inf_ing = Column(Text, nullable=True, comment='活动中的促销活动(JSON)')
    prom_inf_ready = Column(Text, nullable=True, comment='即将开始的促销活动(JSON)')

    # AB测试信息(JSON格式)
    ab_test = Column(Text, nullable=True, comment='AB测试数据(JSON)')

    # 分析字段（不参与更新）
    front_price = Column(DECIMAL(10, 2), nullable=True, comment='前台价格')
    reason_analysis = Column(Text, nullable=True, comment='原因分析')
    optimization_action = Column(Text, nullable=True, comment='优化动作')

    # 备注
    remark = Column(String(500), nullable=True, comment='备注')

    # 时间戳
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 创建联合唯一索引
    __table_args__ = (
        Index('idx_date_skc', 'stat_date', 'skc', unique=True),
        Index('idx_stat_date', 'stat_date'),
        Index('idx_skc', 'skc'),
        Index('idx_store_username', 'store_username'),
    )

    def __repr__(self):
        return f"<SheinNewProductAnalysis(id={self.id}, store_username='{self.store_username}', skc='{self.skc}', stat_date={self.stat_date})>"

    @property
    def new_goods_tag_name(self):
        """
        获取新品标签的文本描述
        
        Returns:
            str: 新品标签文本描述
        """
        return self.get_new_goods_tag_name(self.new_goods_tag)
    
    @staticmethod
    def get_new_goods_tag_name(tag):
        """
        将新品标签代码转换为文本描述
        
        Args:
            tag (str): 新品标签代码
            
        Returns:
            str: 新品标签文本描述
        """
        tag_map = {
            '1': '新品爆款',
            '2': '新品畅销',
            '3': '潜力新品',
            '4': '新品'
        }
        return tag_map.get(str(tag), '') if tag else ''

class NewProductAnalysisManager:
    """
    新品分析数据管理器
    提供数据库操作相关方法
    """

    # database_url = f"mysql+pymysql://{config.mysql_username}:{config.mysql_password}@{config.mysql_host}:{config.mysql_port}/{config.mysql_database}"

    @classmethod
    def __init__(self, database_url=None):
        """
        初始化数据库连接

        Args:
            database_url (str): 数据库连接URL
        """
        # if database_url is None:
        #     database_url = self.database_url
        print(f"{self.__name__} 连接数据库: {database_url}")
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_table(self):
        """
        创建数据表
        """
        Base.metadata.create_all(self.engine)
        print("数据表创建成功")

    def insert_data(self, data_list):
        """
        批量插入数据

        Args:
            data_list (list): 数据字典列表

        Returns:
            int: 成功插入的记录数
        """
        session = self.Session()
        try:
            insert_count = 0
            for data in data_list:
                # 检查是否存在（根据唯一索引：stat_date + skc）
                existing = session.query(SheinNewProductAnalysis).filter(
                    SheinNewProductAnalysis.stat_date == data.get('stat_date'),
                    SheinNewProductAnalysis.skc == data.get('skc')
                ).first()

                # 先处理JSON字段转换（无论是新增还是更新都需要）
                # 使用 'in' 判断而不是 'and'，确保空列表[]和空字典{}也能被转换
                if 'prom_inf_ing' in data and isinstance(data['prom_inf_ing'], (dict, list)):
                    data['prom_inf_ing'] = json.dumps(data['prom_inf_ing'], ensure_ascii=False)
                if 'prom_inf_ready' in data and isinstance(data['prom_inf_ready'], (dict, list)):
                    data['prom_inf_ready'] = json.dumps(data['prom_inf_ready'], ensure_ascii=False)
                if 'ab_test' in data and isinstance(data['ab_test'], (dict, list)):
                    data['ab_test'] = json.dumps(data['ab_test'], ensure_ascii=False)

                if existing:
                    # 更新现有记录（排除不更新的分析字段）
                    exclude_fields = {'front_price', 'reason_analysis', 'optimization_action'}
                    for key, value in data.items():
                        if key not in exclude_fields:
                            setattr(existing, key, value)
                    setattr(existing, 'updated_at', datetime.now())
                else:
                    # 插入新记录
                    new_record = SheinNewProductAnalysis(**data)
                    session.add(new_record)
                    insert_count += 1

            session.commit()
            print(f"成功插入/更新 {insert_count} 条记录")
            return insert_count
        except Exception as e:
            session.rollback()
            print(f"插入数据失败: {e}")
            raise
        finally:
            session.close()

    def get_records_by_date_range(self, store_username, start_date, end_date):
        """
        根据日期范围查询记录

        Args:
            store_username (str): 店铺账号
            start_date (str): 开始日期
            end_date (str): 结束日期

        Returns:
            list: 记录列表
        """
        session = self.Session()
        try:
            records = session.query(SheinNewProductAnalysis).filter(
                SheinNewProductAnalysis.store_username == store_username,
                SheinNewProductAnalysis.stat_date >= start_date,
                SheinNewProductAnalysis.stat_date <= end_date
            ).all()
            return records
        finally:
            session.close()

    def get_records_by_skc(self, store_username, skc):
        """
        根据SKC查询记录

        Args:
            store_username (str): 店铺账号
            skc (str): 平台SKC

        Returns:
            list: 记录列表
        """
        session = self.Session()
        try:
            records = session.query(SheinNewProductAnalysis).filter(
                SheinNewProductAnalysis.store_username == store_username,
                SheinNewProductAnalysis.skc == skc
            ).order_by(SheinNewProductAnalysis.stat_date.desc()).all()
            return records
        finally:
            session.close()

    def _extract_prom_info(self, prom_list, current_skc=None):
        """
        提取促销活动信息
        
        Args:
            prom_list (list): 促销活动列表
            current_skc (str): 当前SKC，用于从promDetail中筛选匹配的记录
            
        Returns:
            list: 提取后的促销活动信息列表
        """
        if not prom_list:
            return []

        result = []
        for prom in prom_list:
            prom_info = {
                'promNm'   : prom.get('promNm'),
                'promId'   : prom.get('promId'),
                'startDate': prom.get('startDate'),
                'endDate'  : prom.get('endDate')
            }

            prom_id = prom.get('promId', '')
            prom_detail = prom.get('promDetail', [])

            # 如果提供了current_skc，从promDetail中筛选匹配的记录
            if current_skc and prom_detail and isinstance(prom_detail, list):
                # 查找匹配当前SKC的detail记录
                matched_detail = None
                for detail in prom_detail:
                    if isinstance(detail, dict) and detail.get('skc') == current_skc:
                        matched_detail = detail
                        break
                
                # 如果找到匹配的记录，使用它；否则使用第一个
                if matched_detail:
                    prom_detail = [matched_detail]
                # 如果没找到匹配的，保持原样（使用第一个）

            # 根据promId长度判断取哪些字段
            if len(str(prom_id)) >= 11 and prom_detail:
                # 营销工具：取第一个detail的数据
                detail = prom_detail[0] if isinstance(prom_detail, list) else prom_detail
                if isinstance(detail, dict):
                    prom_info['attend_num_sum'] = detail.get('act_stock_num') or detail.get('attend_num_sum')
                    prom_info['supply_price'] = detail.get('sku_price') or detail.get('supply_price')
                    prom_info['product_act_price'] = detail.get('act_sku_price') or detail.get('product_act_price')
            elif len(str(prom_id)) >= 8 and prom_detail:
                # 营销工具：取第一个detail的数据
                detail = prom_detail[0] if isinstance(prom_detail, list) else prom_detail
                if isinstance(detail, dict):
                    prom_info['attend_num_sum'] = detail.get('attend_num_sum')
                    prom_info['supply_price'] = detail.get('supply_price')
                    prom_info['product_act_price'] = detail.get('product_act_price')
            elif prom_detail:
                # 营销活动：取第一个detail的数据
                detail = prom_detail[0] if isinstance(prom_detail, list) else prom_detail
                if isinstance(detail, dict):
                    prom_info['attend_num'] = detail.get('attend_num')
                    prom_info['goods_cost'] = detail.get('goods_cost')
                    prom_info['attend_cost'] = detail.get('attend_cost')

            result.append(prom_info)

        return result

    def import_from_json(self, json_data_list):
        """
        从JSON数据导入到数据库
        
        Args:
            json_data_list (list): JSON数据列表
            
        Returns:
            int: 成功导入的记录数
        """
        print(f"开始处理 {len(json_data_list)} 条JSON数据")
        data_list = []
        skipped_count = 0

        for idx, item in enumerate(json_data_list, 1):
            # 验证必填字段
            stat_date = item.get('stat_date')
            skc = item.get('skc')

            if not stat_date:
                print(f"⚠️ 警告: 第 {idx} 条记录缺少必填字段 stat_date (统计日期)，跳过该记录")
                skipped_count += 1
                continue

            if not skc:
                print(f"⚠️ 警告: 第 {idx} 条记录缺少必填字段 skc，跳过该记录")
                skipped_count += 1
                continue

            # 提取促销活动信息（传入当前SKC以筛选匹配的促销信息）
            prom_campaign = item.get('promCampaign', {})
            prom_inf_ing = self._extract_prom_info(prom_campaign.get('promInfIng'), current_skc=skc)
            prom_inf_ready = self._extract_prom_info(prom_campaign.get('promInfReady'), current_skc=skc)

            # 提取AB测试信息（去掉product_name字段）
            ab_test = item.get('ab_test', {})
            if ab_test and isinstance(ab_test, dict):
                ab_test_copy = ab_test.copy()
                ab_test_copy.pop('product_name', None)
                ab_test = ab_test_copy

            # 构建数据库记录
            record = {
                'store_username'  : item.get('store_username'),
                'store_name'      : item.get('store_name'),
                'stat_date'       : stat_date,
                'shelf_date'      : item.get('shelf_date'),
                'skc'             : skc,
                'sku_supplier_no' : item.get('skuSupplierNo'),
                'layer_nm'        : item.get('layerNm'),
                'new_cate1_nm'    : item.get('newCate1Nm'),
                'new_cate2_nm'    : item.get('newCate2Nm'),
                'new_cate3_nm'    : item.get('newCate3Nm'),
                'new_cate4_nm'    : item.get('newCate4Nm'),
                'goods_name'      : item.get('goodsName'),
                'img_url'         : item.get('imgUrl'),
                'onsale_flag'     : int(item.get('onsaleFlag', 0)),
                'sale_flag'       : int(item.get('saleFlag', 0)),
                'new_goods_tag'   : item.get('newGoodsTag'),
                'sale_cnt'        : item.get('saleCnt', 0),
                'pay_order_cnt'   : item.get('payOrderCnt', 0),
                'goods_uv'        : item.get('goodsUv', 0),
                'cart_uv_idx'     : item.get('cartUvIdx', 0),
                'eps_uv_idx'      : item.get('epsUvIdx', 0),
                'eps_gds_ctr_idx' : item.get('epsGdsCtrIdx', 0),
                'gds_pay_ctr_idx' : item.get('gdsPayCtrIdx', 0),
                'bad_comment_rate': item.get('badCommentRate', 0),
                'prom_inf_ing'    : prom_inf_ing,
                'prom_inf_ready'  : prom_inf_ready,
                'ab_test'         : ab_test
            }

            print(f"✓ 处理第 {idx} 条: SKC={record['skc']}, stat_date={stat_date}")
            data_list.append(record)

        if skipped_count > 0:
            print(f"⚠️ 共跳过 {skipped_count} 条记录（缺少必填字段）")

        # 调用insert_data方法插入数据
        return self.insert_data(data_list)

    def update_front_price(self, stat_date, skc, front_price):
        """
        更新指定SKC的前台价格
        
        Args:
            stat_date (str): 统计日期
            skc (str): 平台SKC
            front_price (float): 前台价格
            
        Returns:
            bool: 是否成功
        """
        session = self.Session()
        try:
            record = session.query(SheinNewProductAnalysis).filter(
                SheinNewProductAnalysis.stat_date == stat_date,
                SheinNewProductAnalysis.skc == skc
            ).first()
            
            if record:
                record.front_price = front_price
                setattr(record, 'updated_at', datetime.now())
                session.commit()
                print(f"成功更新前台价格: {skc} ({stat_date}) -> {front_price}")
                return True
            else:
                print(f"未找到记录: SKC={skc}, 日期={stat_date}")
                return False
        except Exception as e:
            session.rollback()
            print(f"更新前台价格失败: {e}")
            raise
        finally:
            session.close()

    def delete_records_by_date(self, store_username, stat_date):
        """
        删除指定日期的记录

        Args:
            store_username (str): 店铺账号
            stat_date (str): 统计日期

        Returns:
            int: 删除的记录数
        """
        session = self.Session()
        try:
            delete_count = session.query(SheinNewProductAnalysis).filter(
                SheinNewProductAnalysis.store_username == store_username,
                SheinNewProductAnalysis.stat_date == stat_date
            ).delete()
            session.commit()
            print(f"成功删除 {delete_count} 条记录")
            return delete_count
        except Exception as e:
            session.rollback()
            print(f"删除数据失败: {e}")
            raise
        finally:
            session.close()

# 创建全局实例，用于快速访问
_new_product_analysis_manager = None

def get_new_product_analysis_manager():
    """
    获取新品分析管理器实例

    Returns:
        NewProductAnalysisManager: 新品分析管理器实例
    """
    global _new_product_analysis_manager
    if _new_product_analysis_manager is None:
        _new_product_analysis_manager = NewProductAnalysisManager()
    return _new_product_analysis_manager

def insert_analysis_data(data_list):
    """
    插入分析数据的便捷函数

    Args:
        data_list (list): 数据字典列表

    Returns:
        int: 成功插入的记录数
    """
    manager = get_new_product_analysis_manager()
    return manager.insert_data(data_list)

def import_from_json(json_data_list):
    """
    从JSON数据导入的便捷函数

    Args:
        json_data_list (list): JSON数据列表

    Returns:
        int: 成功导入的记录数
    """
    manager = get_new_product_analysis_manager()
    return manager.import_from_json(json_data_list)

def get_records_by_skc(store_username, skc):
    """
    根据SKC查询记录的便捷函数

    Args:
        store_username (str): 店铺账号
        skc (str): 平台SKC

    Returns:
        list: 记录列表
    """
    manager = get_new_product_analysis_manager()
    return manager.get_records_by_skc(store_username, skc)


def update_front_price(stat_date, skc, front_price):
    """
    更新前台价格的便捷函数

    Args:
        stat_date (str): 统计日期
        skc (str): 平台SKC
        front_price (float): 前台价格

    Returns:
        bool: 是否成功
    """
    manager = get_new_product_analysis_manager()
    return manager.update_front_price(stat_date, skc, front_price)


if __name__ == '__main__':
    database_url = "mysql+pymysql://root:123wyk@127.0.0.1:3306/lz"

    # 测试代码
    manager = NewProductAnalysisManager(database_url)

    # 创建表
    manager.create_table()

    # 读取JSON文件
    with open('../../docs/skc_model_GS9740414_2025-10-22.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    count = manager.import_from_json(json_data)
    print(f"成功导入 {count} 条记录")

    # with open('../../docs/skc_model_S19118100_2025-10-15.json', 'r', encoding='utf-8') as f:
    #     json_data = json.load(f)
    # count = manager.import_from_json(json_data)
    # print(f"成功导入 {count} 条记录")
    
    # 更新前台价格（手动设置，后续导入不会覆盖）
    # manager.update_front_price('2025-10-15', 'si2409238815318914', 19.99)
    
    # 或使用便捷函数
    # update_front_price('2025-10-15', 'si2409238815318914', 19.99)
