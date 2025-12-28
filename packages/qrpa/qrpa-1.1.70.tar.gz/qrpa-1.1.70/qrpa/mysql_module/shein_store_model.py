#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
店铺信息数据模型
使用SQLAlchemy定义shein_store表结构
"""

from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

# 创建基类
Base = declarative_base()

class SheinStore(Base):
    """
    希音店铺信息表
    存储店铺基础信息
    """
    __tablename__ = 'shein_store'

    # 主键ID
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID')

    # 店铺账号信息（唯一）
    user_name = Column(String(100), nullable=False, unique=True, comment='店铺账号')
    store_username = Column(String(100), nullable=True, comment='店铺用户名')
    store_name = Column(String(200), nullable=True, comment='店铺名称')
    
    # 用户ID信息
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    supplier_id = Column(BigInteger, nullable=True, comment='供应商ID')
    main_user_name = Column(String(100), nullable=True, comment='主账号用户名')
    main_user_id = Column(BigInteger, nullable=True, comment='主账号用户ID')
    
    # ULP信息
    ulp_name = Column(String(200), nullable=True, comment='ULP名称')
    ulp_en_name = Column(String(200), nullable=True, comment='ULP英文名称')
    ulp_emplid = Column(String(100), nullable=True, comment='ULP员工ID')
    is_ulp_login = Column(Integer, nullable=True, comment='是否ULP登录')
    
    # 时区信息
    timezone = Column(String(100), nullable=True, comment='时区')
    timezone_name = Column(String(200), nullable=True, comment='时区名称')
    utc_timezone = Column(String(50), nullable=True, comment='UTC时区')
    area_timezone = Column(String(100), nullable=True, comment='地区时区')
    
    # 系统配置
    switch_new_menu = Column(Integer, nullable=True, comment='是否切换新菜单')
    supplier_user_name = Column(String(100), nullable=True, comment='供应商用户名')
    sso_top_nav = Column(Integer, nullable=True, comment='SSO顶部导航')
    sso_host = Column(String(500), nullable=True, comment='SSO主机地址')
    
    # 类目信息
    category_id = Column(BigInteger, nullable=True, comment='类目ID')
    category_out_id = Column(BigInteger, nullable=True, comment='外部类目ID')
    lv1_category_id = Column(BigInteger, nullable=True, comment='一级类目ID')
    lv1_category_name = Column(String(200), nullable=True, comment='一级类目名称')
    lv2_category_name = Column(String(200), nullable=True, comment='二级类目名称')
    
    # 其他信息
    supplier_source = Column(Integer, nullable=True, comment='供应商来源')
    external_id = Column(BigInteger, nullable=True, comment='外部ID')
    store_code = Column(BigInteger, nullable=True, comment='店铺编码')
    merchant_code = Column(String(100), nullable=True, comment='商户编码')
    schat_id = Column(BigInteger, nullable=True, comment='Schat ID')
    
    # 管理字段（不参与更新）
    store_manager_id = Column(BigInteger, default=0, comment='店长ID(用户表ID)')
    is_deleted = Column(Integer, nullable=True, default=0, comment='软删除标志(0-未删除,1-已删除)')
    
    # 备注
    remark = Column(String(500), nullable=True, comment='备注')
    
    # 时间戳
    created_at = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    updated_at = Column(DateTime, nullable=True, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 创建索引
    __table_args__ = (
        Index('idx_store_username', 'store_username',unique=True),
    )

    def __repr__(self):
        return f"<SheinStore(id={self.id}, user_name='{self.user_name}', store_name='{self.store_name}')>"


class SheinStoreManager:
    """
    店铺信息数据管理器
    提供数据库操作相关方法
    """

    @classmethod
    def __init__(self, database_url):
        """
        初始化数据库连接

        Args:
            database_url (str): 数据库连接URL
        """
        print(f"连接数据库: {database_url}")
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)

    def create_table(self):
        """
        创建数据表
        """
        Base.metadata.create_all(self.engine)
        print("店铺表创建成功")

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
            update_count = 0
            
            for data in data_list:
                # 检查是否存在（根据唯一索引：user_name）
                existing = session.query(SheinStore).filter(
                    SheinStore.user_name == data.get('user_name')
                ).first()

                if existing:
                    # 更新现有记录（排除不更新的字段）
                    exclude_fields = {'store_manager_id', 'is_deleted'}
                    for key, value in data.items():
                        if key not in exclude_fields:
                            setattr(existing, key, value)
                    setattr(existing, 'updated_at', datetime.now())
                    update_count += 1
                else:
                    # 插入新记录
                    new_record = SheinStore(**data)
                    session.add(new_record)
                    insert_count += 1

            session.commit()
            print(f"成功插入 {insert_count} 条记录，更新 {update_count} 条记录")
            return insert_count
        except Exception as e:
            session.rollback()
            print(f"插入数据失败: {e}")
            raise
        finally:
            session.close()

    def import_from_json_dict(self, json_dict):
        """
        从JSON字典数据导入到数据库（JSON格式：{userName: {店铺信息}}）
        
        Args:
            json_dict (dict): JSON字典数据，key为userName，value为店铺信息
            
        Returns:
            int: 成功导入的记录数
        """
        print(f"开始处理 {len(json_dict)} 个店铺数据")
        data_list = []
        skipped_count = 0

        for user_name, item in json_dict.items():
            # 验证必填字段
            if not user_name:
                print(f"⚠️ 警告: 缺少必填字段 user_name，跳过该记录")
                skipped_count += 1
                continue

            # 构建数据库记录（字段名转换：驼峰转下划线）
            record = {
                'user_name': item.get('userName'),
                'store_username': item.get('store_username'),
                'store_name': item.get('store_name'),
                'user_id': item.get('userId'),
                'supplier_id': item.get('supplierId'),
                'main_user_name': item.get('mainUserName'),
                'main_user_id': item.get('mainUserId'),
                'ulp_name': item.get('ulpName'),
                'ulp_en_name': item.get('ulpEnName'),
                'ulp_emplid': item.get('ulpEmplid'),
                'is_ulp_login': item.get('isUlpLogin'),
                'timezone': item.get('timezone'),
                'timezone_name': item.get('timezoneName'),
                'utc_timezone': item.get('utcTimezone'),
                'area_timezone': item.get('areaTimezone'),
                'switch_new_menu': item.get('switchNewMenu'),
                'supplier_user_name': item.get('supplierUserName'),
                'sso_top_nav': item.get('ssoTopNav'),
                'sso_host': item.get('ssoHost'),
                'category_id': item.get('categoryId'),
                'category_out_id': item.get('categoryOutId'),
                'lv1_category_id': item.get('lv1CategoryId'),
                'lv1_category_name': item.get('lv1CategoryName'),
                'lv2_category_name': item.get('lv2CategoryName'),
                'supplier_source': item.get('supplierSource'),
                'external_id': item.get('externalId'),
                'store_code': item.get('storeCode'),
                'merchant_code': item.get('merchantCode'),
                'schat_id': item.get('schatId'),
            }

            print(f"✓ 处理店铺: {record['user_name']} - {record['store_name']}")
            data_list.append(record)

        if skipped_count > 0:
            print(f"⚠️ 共跳过 {skipped_count} 条记录（缺少必填字段）")

        # 调用insert_data方法插入数据
        return self.insert_data(data_list)

    def import_from_json_list(self, json_list):
        """
        从JSON列表数据导入到数据库（JSON格式：[{店铺信息}, {店铺信息}]）
        
        Args:
            json_list (list): JSON列表数据
            
        Returns:
            int: 成功导入的记录数
        """
        # 转换为字典格式，然后调用 import_from_json_dict
        json_dict = {item.get('userName'): item for item in json_list if item.get('userName')}
        return self.import_from_json_dict(json_dict)

    def get_store_by_username(self, user_name, include_deleted=False):
        """
        根据用户名查询店铺信息
        
        Args:
            user_name (str): 店铺账号
            include_deleted (bool): 是否包含已删除的店铺，默认False
            
        Returns:
            SheinStore: 店铺对象
        """
        session = self.Session()
        try:
            query = session.query(SheinStore).filter(
                SheinStore.user_name == user_name
            )
            
            # 默认只查询未删除的
            if not include_deleted:
                query = query.filter(SheinStore.is_deleted == 0)
            
            store = query.first()
            return store
        finally:
            session.close()

    def get_all_stores(self, include_deleted=False):
        """
        获取所有店铺列表
        
        Args:
            include_deleted (bool): 是否包含已删除的店铺，默认False
        
        Returns:
            list: 店铺列表
        """
        session = self.Session()
        try:
            query = session.query(SheinStore)
            
            # 默认只查询未删除的
            if not include_deleted:
                query = query.filter(SheinStore.is_deleted == 0)
            
            stores = query.all()
            return stores
        finally:
            session.close()

    def get_stores_by_category(self, lv1_category_name=None, lv2_category_name=None, include_deleted=False):
        """
        根据类目查询店铺列表
        
        Args:
            lv1_category_name (str): 一级类目名称
            lv2_category_name (str): 二级类目名称
            include_deleted (bool): 是否包含已删除的店铺，默认False
            
        Returns:
            list: 店铺列表
        """
        session = self.Session()
        try:
            query = session.query(SheinStore)
            
            # 默认只查询未删除的
            if not include_deleted:
                query = query.filter(SheinStore.is_deleted == 0)
            
            if lv1_category_name:
                query = query.filter(SheinStore.lv1_category_name == lv1_category_name)
            
            if lv2_category_name:
                query = query.filter(SheinStore.lv2_category_name == lv2_category_name)
            
            stores = query.all()
            return stores
        finally:
            session.close()

    def update_store_manager(self, user_name, manager_id):
        """
        更新店铺的店长ID
        
        Args:
            user_name (str): 店铺账号
            manager_id (int): 店长ID（用户表ID）
            
        Returns:
            bool: 是否成功
        """
        session = self.Session()
        try:
            store = session.query(SheinStore).filter(
                SheinStore.user_name == user_name
            ).first()
            
            if store:
                store.store_manager_id = manager_id
                store.updated_at = datetime.now()
                session.commit()
                print(f"成功更新店长ID: {user_name} -> {manager_id}")
                return True
            else:
                print(f"未找到店铺: {user_name}")
                return False
        except Exception as e:
            session.rollback()
            print(f"更新店长ID失败: {e}")
            raise
        finally:
            session.close()
    
    def soft_delete_store(self, user_name):
        """
        软删除指定店铺（设置is_deleted=1）
        
        Args:
            user_name (str): 店铺账号
            
        Returns:
            bool: 是否成功
        """
        session = self.Session()
        try:
            store = session.query(SheinStore).filter(
                SheinStore.user_name == user_name
            ).first()
            
            if store:
                store.is_deleted = 1
                store.updated_at = datetime.now()
                session.commit()
                print(f"成功软删除店铺: {user_name}")
                return True
            else:
                print(f"未找到店铺: {user_name}")
                return False
        except Exception as e:
            session.rollback()
            print(f"软删除失败: {e}")
            raise
        finally:
            session.close()
    
    def restore_store(self, user_name):
        """
        恢复软删除的店铺（设置is_deleted=0）
        
        Args:
            user_name (str): 店铺账号
            
        Returns:
            bool: 是否成功
        """
        session = self.Session()
        try:
            store = session.query(SheinStore).filter(
                SheinStore.user_name == user_name
            ).first()
            
            if store:
                store.is_deleted = 0
                store.updated_at = datetime.now()
                session.commit()
                print(f"成功恢复店铺: {user_name}")
                return True
            else:
                print(f"未找到店铺: {user_name}")
                return False
        except Exception as e:
            session.rollback()
            print(f"恢复失败: {e}")
            raise
        finally:
            session.close()

    def delete_store(self, user_name):
        """
        物理删除指定店铺（真正从数据库删除，慎用！）
        
        Args:
            user_name (str): 店铺账号
            
        Returns:
            int: 删除的记录数
        """
        session = self.Session()
        try:
            delete_count = session.query(SheinStore).filter(
                SheinStore.user_name == user_name
            ).delete()
            session.commit()
            print(f"成功物理删除 {delete_count} 条记录")
            return delete_count
        except Exception as e:
            session.rollback()
            print(f"删除数据失败: {e}")
            raise
        finally:
            session.close()


# 创建全局实例，用于快速访问
_shein_store_manager = None


def get_shein_store_manager(database_url):
    """
    获取店铺管理器实例

    Args:
        database_url (str): 数据库连接URL

    Returns:
        SheinStoreManager: 店铺管理器实例
    """
    global _shein_store_manager
    if _shein_store_manager is None:
        _shein_store_manager = SheinStoreManager(database_url)
    return _shein_store_manager


def insert_store_data(database_url, data_list):
    """
    插入店铺数据的便捷函数

    Args:
        database_url (str): 数据库连接URL
        data_list (list): 数据字典列表

    Returns:
        int: 成功插入的记录数
    """
    manager = get_shein_store_manager(database_url)
    return manager.insert_data(data_list)


def import_from_json(database_url, json_data):
    """
    从JSON数据导入的便捷函数（自动识别字典或列表格式）

    Args:
        database_url (str): 数据库连接URL
        json_data (dict|list): JSON数据（字典或列表）

    Returns:
        int: 成功导入的记录数
    """
    manager = get_shein_store_manager(database_url)
    
    if isinstance(json_data, dict):
        return manager.import_from_json_dict(json_data)
    elif isinstance(json_data, list):
        return manager.import_from_json_list(json_data)
    else:
        raise ValueError("json_data 必须是字典或列表类型")


def get_store_by_username(database_url, user_name, include_deleted=False):
    """
    根据用户名查询店铺的便捷函数

    Args:
        database_url (str): 数据库连接URL
        user_name (str): 店铺账号
        include_deleted (bool): 是否包含已删除的店铺，默认False

    Returns:
        SheinStore: 店铺对象
    """
    manager = get_shein_store_manager(database_url)
    return manager.get_store_by_username(user_name, include_deleted)


def update_store_manager(database_url, user_name, manager_id):
    """
    更新店长ID的便捷函数

    Args:
        database_url (str): 数据库连接URL
        user_name (str): 店铺账号
        manager_id (int): 店长ID（用户表ID）

    Returns:
        bool: 是否成功
    """
    manager = get_shein_store_manager(database_url)
    return manager.update_store_manager(user_name, manager_id)


def soft_delete_store(database_url, user_name):
    """
    软删除店铺的便捷函数

    Args:
        database_url (str): 数据库连接URL
        user_name (str): 店铺账号

    Returns:
        bool: 是否成功
    """
    manager = get_shein_store_manager(database_url)
    return manager.soft_delete_store(user_name)


def restore_store(database_url, user_name):
    """
    恢复店铺的便捷函数

    Args:
        database_url (str): 数据库连接URL
        user_name (str): 店铺账号

    Returns:
        bool: 是否成功
    """
    manager = get_shein_store_manager(database_url)
    return manager.restore_store(user_name)


if __name__ == '__main__':
    # 测试代码
    # 注意：需要提供数据库连接URL
    # database_url = "mysql+pymysql://root:123wyk@127.0.0.1:3306/lz"
    database_url = "mysql+pymysql://root:123wyk@47.83.212.3:3306/lz"

    manager = SheinStoreManager(database_url)
    
    # 创建表
    manager.create_table()

    # 读取JSON文件
    with open('../../docs/shein_user.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    count = manager.import_from_json_dict(json_data)
    print(f"成功导入 {count} 条店铺记录")
    
    # 更新店长ID（手动设置，后续导入不会覆盖）
    # manager.update_store_manager('GS0628340', 123)  # 123是用户表的ID
    
    # 软删除测试
    # manager.soft_delete_store('GS0628340')
    
    # 查询店铺（默认不包含已删除）
    # store = manager.get_store_by_username('GS0628340')
    # print(f"查询结果: {store}")
    
    # 查询店铺（包含已删除）
    # store = manager.get_store_by_username('GS0628340', include_deleted=True)
    # print(f"查询结果（包含已删除）: {store}")
    
    # 恢复店铺
    # manager.restore_store('GS0628340')
    
    # 按类目查询示例
    # stores = manager.get_stores_by_category(lv2_category_name='全托管-备CN-中国团队-内睡服装')
    # print(f"找到 {len(stores)} 个店铺")