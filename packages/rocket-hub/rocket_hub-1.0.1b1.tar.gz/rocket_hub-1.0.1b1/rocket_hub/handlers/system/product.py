# -*- coding: utf-8 -*-
"""
:Author: ChenXiaolei
:Date: 2020-04-22 14:32:40
:LastEditTime: 2025-08-26 18:47:23
:LastEditors: ChenXiaolei
:Description: 产品相关Handler
"""

from rocket_hub.handlers.rocket_base import *
from rocket_hub.models.db_models.product.product_info_model import *
from rocket_hub.models.db_models.product.product_user_model import *


class GetProductListHandler(RocketBaseHandler):
    """
    :description: 产品列表
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 产品列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 数据库连接串
        product_info_model = ProductInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub"))
        # 页索引
        page_index = self.get_page_index()
        # 页大小
        page_size = self.get_page_size()
        # 查询条件,排序字段
        condition, order = self.get_condition_by_body()

        source_dict_list = product_info_model.get_dict_list(condition, "", order)
        if len(source_dict_list) > 0:
            merge_dict_list = UserInfoModel(self.get_manage_context_key()).get_dict_list(field="UserID,UserName")
            source_dict_list = DictUtil.merge_dict_list(source_dict_list, "SuperID", merge_dict_list, "UserID", "UserID,UserName")
        page_dict = self.get_dict_page_info_list(page_index, page_size, source_dict_list)

        return self.response_json_success(page_dict)


class GetAllProductListHandler(RocketBaseHandler):
    """
    :description: 全部产品列表
    """
    @login_filter(True)
    @power_filter(True)
    def get_async(self):
        """
        :description: 全部产品列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        product_info_model = ProductInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub"))
        source_dict_list = product_info_model.get_dict_list()

        return self.response_json_success(source_dict_list)


class SaveProductHandler(RocketBaseHandler):
    """
    :description: 保存产品
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 保存产品
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 数据库连接串
        base_manage_context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
        # 产品id
        product_id = int(self.get_param("ProductID", "0"))
        # 产品名称
        product_name = self.get_param("ProductName")
        # 产品子名称
        product_sub_name = self.get_param("ProductSubName")
        # 业务地址
        manage_url = self.get_param("ManageUrl")
        # 权限地址
        power_url = self.get_param("PowerUrl")
        # 说明
        summary = self.get_param("Summary")
        # 图片地址
        image_url = self.get_param("ImageUrl")
        # 超管ID
        super_id = self.get_param("SuperID")
        # 文件上下文配置
        file_context_key = self.get_param("FileContextKey")
        # 权限上下文配置
        manage_context_key = self.get_param("ManageContextKey")
        # 日志上下文配置
        log_context_key = self.get_param("LogContextKey")
        # 作业上下文配置
        plug_work_context_key = self.get_param("PlugWorkContextKey")
        # 是否发布
        is_release = int(self.get_param("IsRelease", "0"))
        # 是否新页面打开
        is_brank = int(self.get_param("IsBrank", "0"))

        # 验证数据
        if product_name == "":
            return self.response_common("ProductNameEmpty", "产品名称为空")

        if not config.get_value(manage_context_key):
            return self.response_common("HasExit", "ManageContentKey链接字符串未配置")

        product_info_model = ProductInfoModel(base_manage_context_key)
        product_info = ProductInfo()
        if product_id > 0:
            product_info = product_info_model.get_entity_by_id(product_id)
            if not product_info:
                return self.response_common("NoExit", "产品不存在")
            if manage_url != "" or power_url != "":
                product_info_c = product_info_model.get_entity("(ManageUrl=%s OR PowerUrl=%s) AND ProductID<>%s", params=[manage_url, power_url, product_id])
                if product_info_c:
                    return self.response_common("HasExit", "WebUrl或ApiUrl已存在")
        elif manage_url != "" or power_url != "":
            product_info_c = product_info_model.get_entity("ManageUrl=%s OR PowerUrl=%s", params=[manage_url, power_url])
            if product_info_c:
                return self.response_common("HasExit", "WebUrl或ApiUrl已存在")

        # 赋值
        product_info.ProductName = product_name
        product_info.ProductSubName = product_sub_name
        product_info.ManageUrl = manage_url
        product_info.PowerUrl = power_url
        product_info.Summary = summary
        product_info.ImageUrl = image_url
        product_info.SuperID = super_id
        product_info.Summary = summary
        product_info.FileContextKey = file_context_key
        product_info.ManageContextKey = manage_context_key
        product_info.LogContextKey = log_context_key
        product_info.PlugWorkContextKey = plug_work_context_key
        product_info.IsRelease = is_release
        product_info.IsBrank = is_brank
        if product_id > 0:
            product_info_model.update_entity(product_info)
        else:
            product_id = product_info_model.add_entity(product_info)
            product_info.ProductID = product_id

        user_info_model = UserInfoModel(manage_context_key)

        user_info_model.update_table("IsSuper=0", "Account<>'seven'")
        user_info_model.update_table("IsSuper=1", "UserID=%s", params=[super_id])

        return self.response_json_success(product_info)


class DeleteProductHandler(RocketBaseHandler):
    """
    :description: 删除产品
    """
    @login_filter(True)
    @power_filter(True)
    def get_async(self):
        """
        :description: 删除产品
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        product_id = int(self.get_param("ProductID", 0))

        if product_id <= 0:
            return self.response_json_error_params()

        product_info_model = ProductInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub"))

        product_info_model.del_entity("ProductID=%s", product_id)

        return self.response_json_success()