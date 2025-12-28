# -*- coding: utf-8 -*-
"""
:Author: ChenXiaolei
:Date: 2020-12-09 19:11:51
:LastEditTime: 2025-08-26 18:18:06
:LastEditors: ChenXiaolei
:Description: 
"""

from rocket_hub.handlers.rocket_base import *
from rocket_hub.models.db_models.settings.settings_base_model import *


class BaseSettingsHandler(RocketBaseHandler):
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 设置站点基础信息
        :return 基础信息
        :last_editors: ChenXiaolei
        """
        # 登录页背景图
        login_background = self.get_param("login_background")
        # 登录页logo
        login_logo = self.get_param("login_logo")
        # 首页顶部logo
        banner_logo = self.get_param("banner_logo")
        # 标题
        title = self.get_param("title")
        # 登录过期时间(小时)
        login_expire = int(self.get_param("login_expire", 2))

        settings_base_model = SettingsBaseModel(config.get_value("manage_context_key", "db_rocket_hub"))

        settings_base = settings_base_model.get_entity()

        if not settings_base:
            settings_base = SettingsBase()

        settings_base.login_background = login_background
        settings_base.login_logo = login_logo
        settings_base.banner_logo = banner_logo
        settings_base.title = title
        settings_base.login_expire = login_expire

        if settings_base.id > 0:
            settings_base_model.update_entity(settings_base)
        else:
            settings_base_model.add_entity(settings_base)

        if config.get_value("login_type", "redis") == "redis":
            redis_init = self.redis_init()
            settings_base = redis_init.delete("settings_base")

        return self.response_json_success(settings_base)

    def get_async(self):
        """
        :description: 获取站点基础信息
        :return 基础信息
        :last_editors: ChenXiaolei
        """
        settings_base_model = SettingsBaseModel(config.get_value("manage_context_key", "db_rocket_hub"))

        settings_base = None
        if config.get_value("login_type", "redis") == "redis":
            redis_init = self.redis_init()
            settings_base = redis_init.get("settings_base")
            if not settings_base:
                settings_base = settings_base_model.get_dict()
                redis_init.set("settings_base", self.json_dumps(settings_base))
            else:
                settings_base = self.json_loads(settings_base)
        else:
            settings_base = settings_base_model.get_dict()

        return self.response_json_success(settings_base)