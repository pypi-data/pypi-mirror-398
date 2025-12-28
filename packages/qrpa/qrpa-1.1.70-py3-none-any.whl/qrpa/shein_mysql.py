import json

from . import TimeUtils
from .mysql_module.shein_return_order_model import SheinReturnOrderManager
from .mysql_module.shein_product_model import SheinProductManager
from .mysql_module.shein_ledger_model import SheinLedgerManager
from .mysql_module.shein_ledger_month_report_model import SheinLedgerMonthReportManager
from .mysql_module.new_product_analysis_model import NewProductAnalysisManager
from .fun_base import log

import os

class SheinMysql:
    def __init__(self, config):
        self.config = config

    def upsert_shein_ledger(self, json_file):
        log(f'当前使用的数据库: {self.config.db.database_url}')
        manager = SheinLedgerManager(self.config.db.database_url)
        manager.create_tables()
        manager.import_from_json_file(json_file)

    def upsert_shein_ledger_month_report(self, json_file):
        """
        插入或更新希音台账月报数据

        Args:
            json_file: JSON文件路径
        """
        log(f'当前使用的数据库: {self.config.db.database_url}')
        manager = SheinLedgerMonthReportManager(self.config.db.database_url)
        manager.create_tables()
        manager.import_from_json_file(json_file)

    def upsert_shein_return_order(self, json_file):
        database_url = 'mysql+pymysql://root:123wyk@47.83.212.3:3306/lz'
        # database_url = 'mysql+pymysql://root:123wyk@127.0.0.1:3306/lz'
        log(f'当前使用的数据库: {database_url}')
        # 创建管理器实例
        manager = SheinReturnOrderManager(database_url)
        # 创建数据表
        manager.create_tables()
        # 读取JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            dict = json.load(f)
            for store_username, data_list in dict.items():
                manager.upsert_return_order_data(store_username, data_list)

    def upsert_shein_product(self, json_file):
        log(f'当前使用的数据库: {self.config.db.database_url}')
        # 创建管理器实例
        manager = SheinProductManager(self.config.db.database_url)
        # 创建数据表
        manager.create_tables()
        with open(json_file, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
            for store_username, store_skc_list_file in file_list.items():
                with open(store_skc_list_file, 'r', encoding='utf-8') as f:
                    dict_store_skc_list = json.load(f)
                    for store_username, data_list in dict_store_skc_list.items():
                        manager.upsert_product_data(data_list)

    def upsert_shein_product_info(self, json_file):
        log(f'当前使用的数据库: {self.config.db.database_url}')
        # 创建管理器实例
        manager = SheinProductManager(self.config.db.database_url)
        # 创建数据表
        manager.create_tables()
        with open(json_file, 'r', encoding='utf-8') as f:
            file_list = json.load(f)
            for store_username, store_spu_list in file_list.items():
                for spu in store_spu_list:
                    product_detail_file = f'{self.config.auto_dir}/shein/product_detail/product_detail_{spu}.json'
                    attribute_file = f'{self.config.auto_dir}/shein/attribute/attribute_template_{spu}.json'
                    if os.path.exists(product_detail_file):
                        with open(product_detail_file, 'r', encoding='utf-8') as f:
                            data_list = json.load(f)
                            manager.upsert_product_detail(spu, 'product_detail', data_list)
                    else:
                        log(f'文件不存在: {product_detail_file}')
                    if os.path.exists(attribute_file):
                        with open(attribute_file, 'r', encoding='utf-8') as f:
                            data_list = json.load(f)
                            manager.upsert_product_detail(spu, 'attribute_template', data_list)
                    else:
                        log(f'文件不存在: {attribute_file}')

    def upsert_shein_new_product_analysis(self, stat_date):
        log(f'当前使用的数据库: {self.config.db.database_url}')
        # 创建管理器实例
        manager = NewProductAnalysisManager(self.config.db.database_url)
        # 创建数据表
        manager.create_table()
        src_directory = f'{self.config.auto_dir}/shein/product_analysis'
        for file in os.listdir(src_directory):
            # 检查是否为文件且符合命名模式
            if file.startswith(f"skc_model_") and file.endswith(f"_{stat_date}.json"):
                file_path = os.path.join(src_directory, file)
                filename = os.path.basename(file_path)  # 获取 "tool.py"
                name = os.path.splitext(filename)[0]
                store_username = name.split('_')[2]
                # 读取JSON文件
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                count = manager.import_from_json(json_data)
                print(f"成功导入 {store_username} {count} 条记录")
