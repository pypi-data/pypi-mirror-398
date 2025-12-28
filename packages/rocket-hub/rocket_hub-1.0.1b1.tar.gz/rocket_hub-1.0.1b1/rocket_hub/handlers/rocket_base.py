"""
:Author: ChenXiaolei
:Date: 2020-03-24 10:42:34
:LastEditTime: 2025-12-25 10:29:29
:LastEditors: ChenXiaolei
:Description: RocketBaseHandler
"""
import ast
from rocket_framework.web_tornado.base_handler.base_cookie_handler import *
from rocket_framework.redis import *

from rocket_hub.models.db_models.product.product_info_model import *
from rocket_hub.models.db_models.user.user_login_model import *
from rocket_hub.models.db_models.user.user_info_model import *
from rocket_hub.models.db_models.menu.menu_info_model_ex import *
from rocket_hub.models.db_models.role.role_user_model import *
from rocket_hub.models.db_models.role.role_power_model_ex import *
from rocket_hub.models.db_models.log.log_action_model import *
from rocket_hub.models.hub_model import *
from rocket_hub.models.enum import *


class RocketBaseHandler(BaseCookieHandler):
    """
    :description: RocketBaseHandler
    :last_editors: ChenXiaolei
    """
    def options_async(self):
        self.response_json_success()

    def check_xsrf_cookie(self):
        return

    def get_group_ip(self):
        """
        :description: 获取集团内部IP白名单
        :return 集团内部IP白名单列表
        :last_editors: ChenXiaolei
        """
        resposne = HTTPHelper.get("https://ps.gao7.com/ip/group_ip")

        if resposne:
            group_ip_json = json.loads(resposne.text)
            if group_ip_json["result"]==0:
                return self.response_common("Get GroupIP Fail", group_ip_json["desc"])
            return group_ip_json["data"]["ip_list"]
        
        return []
    
    def add_action_log(self, module_code, content, record_time=None):
        """
        :description: 添加平台操作行为日志
        :param module_code: 模块标识
        :param content: 日志内容
        :param record_time: 日志时间 默认当前时间
        :return 成功 True 失败 False
        :last_editors: ChenXiaolei
        """
        op_result = False
        try:
            if not record_time:
                record_time = TimeHelper.get_now_timestamp()
            user_id = self.request_user_id()
            client_ip = self.get_remote_ip()
            log_action = LogAction()
            log_action.module_code = module_code
            log_action.user_id = user_id
            log_action.content = content
            log_action.record_time = record_time
            log_action.client_ip = client_ip

            if LogActionModel().add_entity(log_action) > 0:
                op_result = True
            return op_result
        except:
            self.logger_error.error(f"添加平台行为日志时异常:{traceback.format_exc()}")
            return False

    def json_dumps(self, rep_dic):
        """
        :description: 对象编码成Json字符串
        :param rep_dic：字典对象
        :return: str
        :last_editors: HuangJianYi
        """
        try:
            if rep_dic == "":
                return ""
            rep_dic = ast.literal_eval(rep_dic)
        except Exception:
            pass

        if hasattr(rep_dic, '__dict__'):
            rep_dic = rep_dic.__dict__

        return json.dumps(
            rep_dic,
            ensure_ascii=False,
            cls=JsonEncoder,
            default=lambda x: (datetime.datetime.strftime(x, '%Y-%m-%d %H:%M:%S') if isinstance(x, datetime.datetime) else x.__dict__) if not isinstance(x, decimal.Decimal) else float(x),
            sort_keys=False,
            indent=None,
        )

    def json_loads(self, rep_str):
        """
        :description: 将Json字符串解码成python对象
        :param rep_str：str
        :return: dict
        :last_editors: ChenXiaolei
        """
        try:
            return json.loads(rep_str)
        except Exception as ex:
            return json.loads(self.json_dumps(rep_str))

    def response_custom(self, rep_dic):
        """
        :description: 输出公共json模型
        :param rep_dic: 字典类型数据
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: ChenXiaolei
        """
        self.http_reponse(self.json_dumps(rep_dic))

    def response_common(self, result_code, result_message, data=None):
        """
        :description: 输出公共json模型
        :param result_code: 字符串，服务端返回的错误码
        :param result_message: 字符串，服务端返回的错误信息
        :param data: 返回结果对象，即为数组，字典
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: ChenXiaolei
        """
        if hasattr(data, '__dict__'):
            data = data.__dict__
        rep_dic = {
            'ResultCode': result_code,
            'ResultMessage': result_message,
            'Data': data,
        }
        self.http_reponse(self.json_dumps(rep_dic))

    def response_json_success(self, data=None, desc='调用成功'):
        """
        :description: 通用成功返回json结构
        :param data: 返回结果对象，即为数组，字典
        :param desc: 字符串，服务端返回的错误信息
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: ChenXiaolei
        """
        self.response_common("0", desc, data)

    def response_json_error(self, desc='error'):
        """
        :description: 通用错误返回json结构
        :param desc: 字符串，服务端返回的错误信息
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: ChenXiaolei
        """
        self.response_common("1", desc)

    def response_json_error_params(self, desc='params error'):
        """
        :description: 参数错误返回json结构
        :param desc: 字符串，服务端返回的错误信息
        :return: 将dumps后的数据字符串返回给客户端
        :last_editors: ChenXiaolei
        """
        self.response_common("1", desc)

    def redis_init(self, db=None):
        """
        :description: redis初始化
        :return: redis_cli
        :last_editors: ChenXiaolei
        """
        return RedisHelper.redis_init(config_dict=config.get_value("redis"))

    def set_default_headers(self):
        allow_origin_list = config.get_value("allow_origin_list")
        origin = self.request.headers.get("Origin")
        if origin in allow_origin_list:
            self.set_header("Access-Control-Allow-Origin", origin)

        self.set_header("Access-Control-Allow-Headers", "Origin,X-Requested-With,Content-Type,Accept,User-Token,Manage-ProductID,Manage-PageID,PYCKET_ID")
        self.set_header("Access-Control-Allow-Methods", "POST,GET,OPTIONS,PUT,DELETE,PATCH")
        self.set_header("Access-Control-Allow-Credentials", "true")

    def request_header_token(self):
        header_token = {}
        if "User-Token" in self.request.headers:
            reqInfoList = str.split(self.request.headers["User-Token"], ";")
            for info in reqInfoList:
                kv = str.split(info, "=")
                header_token[kv[0]] = kv[1]
        return header_token

    def request_user_id(self):
        header_token = self.request_header_token()
        return header_token["UserID"] if header_token.__contains__("UserID") else ""

    def request_user_id_md5(self):
        header_token = self.request_header_token()
        return (header_token["UserIDMD5"] if header_token.__contains__("UserIDMD5") else "")

    def request_user_token(self):
        header_token = self.request_header_token()
        return (header_token["UserToken"] if header_token.__contains__("UserToken") else "")

    def request_product_id(self):
        header_product_id = ""
        if self.request.headers.__contains__("Manage-Productid"):
            header_product_id = self.request.headers["Manage-Productid"]
        product_id = int(header_product_id) if header_product_id.strip() != "" else 0
        if product_id == 0:
            product_id = int(self.get_param("manage-productid", "0"))
        return product_id

    def request_manage_page_id(self):
        return (self.request.headers["Manage-PageID"] if self.request.headers.__contains__("Manage-PageID") else "")

    def get_product_info(self):
        product_id = self.request_product_id()
        return (ProductInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub")).get_entity_by_id(product_id) if product_id > 0 else None)

    def get_curr_user_info(self):
        user_id = self.request_user_id()
        return (UserInfoModel(self.get_manage_context_key()).get_entity_by_id(user_id) if user_id else None)

    def get_base_user_info(self):
        user_id = self.request_user_id()
        return (UserInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub")).get_entity_by_id(user_id) if user_id else None)

    def get_is_super(self):
        base_user_info = self.get_base_user_info()
        return base_user_info.IsSuper == 1 if base_user_info else False

    def get_manage_context_key(self):
        manage_context_key = config.get_value("manage_context_key", "db_rocket_hub")
        product_info = self.get_product_info()
        if product_info:
            manage_context_key = product_info.ManageContextKey
        return manage_context_key

    def get_file_context_key(self):
        file_context_key = config.get_value("file_context_key", "db_rocket_hub")
        product_info = self.get_product_info()
        if product_info:
            file_context_key = product_info.FileContextKey
        return file_context_key

    def get_log_context_key(self):
        log_context_key = config.get_value("log_context_key", "db_rocket_hub")
        product_info = self.get_product_info()
        if product_info:
            log_context_key = product_info.LogContextKey
        return log_context_key

    def get_page_index(self):
        page_index = 0
        r_page_index = self.get_param("PageIndex", "")
        if r_page_index != "":
            dict_page_index = json.loads(r_page_index)
            if dict_page_index and dict_page_index.__contains__("Value"):
                page_index = dict_page_index["Value"]
        return page_index

    def get_page_size(self):
        page_size = 10
        r_page_size = self.get_param("PageSize", "")
        if r_page_size != "":
            dict_page_size = json.loads(r_page_size)
            if dict_page_size and dict_page_size.__contains__("Value"):
                page_size = dict_page_size["Value"]
        return page_size

    def get_page_cote_id(self):
        page_id = self.request_manage_page_id()
        if page_id != "":
            return page_id.split("$")[1] if page_id.__contains__("$") else ""
        else:
            return ""

    def get_dict_page_info_list(self, page_index, page_size, p_dict, total=0):
        """
        :description: 获取分页信息
        :param page_index：页索引
        :param page_size：页大小
        :param p_dict：字典列表
        :return: 
        :last_editors: ChenXiaolei
        """
        page_info = PageInfo()
        page_info.PageIndex = page_index
        page_info.PageSize = page_size
        page_info.RecordCount = total if total > 0 else len(p_dict)
        page_info.Data = p_dict
        page_info = page_info.get_entity_by_page_info(page_info)
        return page_info.__dict__

    def get_dict_by_keys(self, source_dict, keys):
        """
        :description: 根据key搜索字典，返回key相关字典
        :param source_dict
        :param keys
        :return: 值
        :last_editors: ChenXiaolei
        """
        if isinstance(source_dict, str):
            source_dict = json.loads(source_dict)
        key_list = list(keys.split(","))
        return {i: source_dict[i] for i in key_list if i in source_dict}

    def get_condition_by_body(self):
        """
        :description: 获取页面查询条件
        :param {type} 
        :return: condition, order
        :last_editors: ChenXiaolei
        """
        condition = ""
        order = ""
        body_dict = self.request_body_to_dict()
        for item in body_dict:
            if not item.__contains__("PageIndex") and not item.__contains__("PageSize"):
                # print(body_dict[item])
                query_method = json.loads(body_dict[item]).get("QueryMethod")
                query_Value = json.loads(body_dict[item]).get("Value")
                query_type = json.loads(body_dict[item]).get("QueryType")
                # query_data_type = json.loads(body_dict[item]).get("QueryDataType")
                if query_type == "Query" and query_Value != "":
                    if condition != "":
                        condition += " AND "
                    if query_method == QueryMethod.Contains.value:
                        condition += f"{item} LIKE '%{query_Value}%'"
                    elif query_method == QueryMethod.StartsWith.value:
                        condition += f"{item} LIKE '{query_Value}%'"
                    elif query_method == QueryMethod.EndsWith.value:
                        condition += f"{item} LIKE '%{query_Value}'"
                    elif query_method == QueryMethod.Equal.value:
                        condition += f"{item}={query_Value}"
                    elif query_method == QueryMethod.GreaterThan.value:
                        condition += f"{item}>{query_Value}"
                    elif query_method == QueryMethod.GreaterThanOrEqual.value:
                        condition += f"{item}>={query_Value}"
                    elif query_method == QueryMethod.LessThan.value:
                        condition += f"{item}<{query_Value}"
                    elif query_method == QueryMethod.LessThanOrEqual.value:
                        condition += f"{item}<={query_Value}"
                    elif query_method == QueryMethod.NotEqual.value:
                        condition += f"{item}<>{query_Value}"
                if query_type == "Sort" and query_Value != "":
                    order = f"{item} {query_Value}"

        return condition, order

    def get_system_user_table(self):
        """
        :description: 获取系统用户
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        return UserInfoModel(self.get_manage_context_key()).get_dict_list()

    def logout(self, user_id):
        """
        :description: 用户退出
        :param user_id：用户id
        :return: 
        :last_editors: ChenXiaolei
        """
        if user_id.strip() == "":
            return
        if config.get_value("login_type", "redis") == "redis":
            self.redis_init().hdel(config.get_value("redis_provider_name_user_login", "user_login"), user_id)
        else:
            UserLoginModel(config.get_value("manage_context_key", "db_rocket_hub")).del_entity("UserID=%s", user_id)

        self.clear_user_cookie()

    def clear_user_cookie(self):
        """
        :description: 清理用户登录cookie
        """
        self.clear_cookie("UserID")
        self.clear_cookie("UserIDMD5")
        self.clear_cookie("UserToken")

    def login_cookie(self, user_login):
        """
        :description: 登录状态设置
        :param user_login: 登录信息
        :return: user_login
        :last_editors: ChenXiaolei
        """
        if config.get_value("login_type", "redis") == "redis":
            self.redis_init().hset(config.get_value("redis_provider_name_user_login", "user_login"), user_login.UserID, self.json_dumps(user_login))
        else:
            user_login_base = UserLoginModel(config.get_value("base_manage_context_key", "db_rocket_hub"))
            user_login_base.add_update_entity(user_login, "UserIDMD5=%s,ExpireTime=%s,UserToken=%s", [user_login.UserIDMD5, user_login.ExpireTime, user_login.UserToken])

        cookie_domain = config.get_value("cookie_domain")
        if cookie_domain:
            self.set_cookie("UserID", user_login.UserID, domain=cookie_domain)
            self.set_cookie("UserIDMD5", user_login.UserIDMD5, domain=cookie_domain)
            self.set_cookie("UserToken", user_login.UserToken, domain=cookie_domain)
        else:
            self.set_cookie("UserID", user_login.UserID)
            self.set_cookie("UserIDMD5", user_login.UserIDMD5)
            self.set_cookie("UserToken", user_login.UserToken)

    def check_power_menu(self, api_path, cote_id):
        """
        :description: 权限判断
        :param api_path：路径
        :param cote_id：权限码值
        :return: True or False
        :last_editors: ChenXiaolei
        """
        manage_context_key = self.get_manage_context_key()
        menu_info_list = MenuInfoModel(manage_context_key).get_list(f"ApiPath LIKE '%{api_path}%'")
        if not menu_info_list:
            return False
        if [i for i in menu_info_list if i.IsPower == 0]:
            return True
        role_user_list = RoleUserModel(manage_context_key).get_list("UserID=%s", params=self.request_user_id())
        role_power_list = RolePowerModelEx(manage_context_key).get_role_power_list([i.RoleID for i in role_user_list])
        cote_list = [i for i in role_power_list if i.CoteID == cote_id]
        menu_list = [i.MenuID for i in menu_info_list]
        return bool([i for i in cote_list if menu_list.__contains__(i.MenuID)])

    def auto_mapper(self, s_model, map_dict=None):
        """
        :description: 对象映射（把map_dict值赋值到实体s_model中）
        :param s_model：需要映射的实体对象
        :param map_dict：被映射的实体字典
        :return: 映射后的实体s_model
        """
        if map_dict:
            field_list = s_model.get_field_list()
            for filed in field_list:
                if filed in map_dict:
                    setattr(s_model, filed, map_dict[filed])
        return s_model

    def check_login_user(self, user_id, user_token, is_need_login=True):
        """
        :description: 登录用户检查
        :param user_id：用户id
        :param user_token：用户user_token
        :return: 
        """
        invoke_result = InvokeResult()
        # 登陆日志判断，Redis还是MySQL
        if config.get_value("login_type", "redis") == "redis":
            redis_user_login = self.redis_init().hget(config.get_value("redis_provider_name_user_login", "user_login"), user_id)
            user_login = json.loads(redis_user_login) if redis_user_login else {}
            if not user_login or TimeHelper.format_time_to_datetime(user_login["ExpireTime"]) < TimeHelper.get_now_datetime():
                if not is_need_login:
                    return invoke_result
                self.clear_user_cookie()
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户已过期，请重新登录"
                return invoke_result
            if user_login["UserToken"] != user_token:
                if not is_need_login:
                    return invoke_result
                self.clear_user_cookie()
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户在其他终端登录，请重新登录"
                return invoke_result

            curr_user_info = UserInfoModel(config.get_value("manage_context_key", "db_rocket_hub")).get_entity_by_id(user_id)
            if curr_user_info.IsLock == 1:
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户已被锁，请联系管理员"
                return invoke_result

            user_login["ExpireTime"] = TimeHelper.add_hours_by_format_time(hour=config.get_value("login_expire", 10))
            self.redis_init().hset(config.get_value("redis_provider_name_user_login", "user_login"), user_id, self.json_dumps(user_login))
        else:
            base_manage_context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
            manage_context_key = self.get_manage_context_key()

            user_login_model = UserLoginModel(base_manage_context_key)
            user_login = user_login_model.get_entity_by_id(user_id)

            if not user_login or TimeHelper.format_time_to_datetime(user_login.ExpireTime) < TimeHelper.get_now_datetime():
                if not is_need_login:
                    return invoke_result
                self.clear_user_cookie()
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户已过期，请重新登录"
                return invoke_result
            if user_login.UserToken != user_token:
                if not is_need_login:
                    return invoke_result
                self.clear_user_cookie()
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户在其他终端登录，请重新登录"
                return invoke_result

            curr_user_info = UserInfoModel(manage_context_key).get_entity_by_id(user_id)
            if not curr_user_info:
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户已过期，请重新登录"
                return invoke_result
            if curr_user_info.IsLock == 1:
                invoke_result.ResultCode = "login_expire"
                invoke_result.ResultMessage = "用户已被锁，请联系管理员"
                return invoke_result

            if base_manage_context_key != manage_context_key:
                curr_user_info = UserInfoModel(base_manage_context_key).get_entity_by_id(user_id)
                if not curr_user_info:
                    invoke_result.ResultCode = "login_expire"
                    invoke_result.ResultMessage = "用户已过期，请重新登录"
                    return invoke_result
                if curr_user_info.IsLock == 1:
                    invoke_result.ResultCode = "login_expire"
                    invoke_result.ResultMessage = "用户已被锁，请联系管理员"
                    return invoke_result

            user_login.ExpireTime = TimeHelper.add_hours_by_format_time(hour=config.get_value("login_expire", 10))
            user_login_model.update_table(f"ExpireTime='{user_login.ExpireTime}'", "UserID=%s", user_login.UserID)

        return invoke_result

    def login_filter(self, is_need_login, optional_params):
        """
        :description: 登录过滤器
        :param is_need_login: 是否需要登录（true需要false不需要）
        :param optional_params: 其他参数
        :return: InvokeResult
        """
        invoke_result = InvokeResult()

        if not is_need_login:
            return invoke_result

        # 获取头部信息
        header_token = self.request_header_token()
        user_id = header_token["UserID"] if header_token.__contains__("UserID") else ""
        user_token = header_token["UserToken"] if header_token.__contains__("UserToken") else ""
        user_id_md5 = header_token["UserIDMD5"] if header_token.__contains__("UserIDMD5") else ""
        if user_id.strip() == "" or user_token.strip() == "" or user_id_md5.strip() == "":
            invoke_result.ResultCode = "error"
            invoke_result.ResultMessage = "操作失败，用户未登录"
            return invoke_result
        if CryptoHelper.md5_encrypt(user_id, config.get_value("login_encrypt_key", "7C34A5212F7845CB85D4BBB589502D9B")) != user_id_md5:
            invoke_result.ResultCode = "error"
            invoke_result.ResultMessage = "操作失败，用户未登录"
            return invoke_result

        invoke_result = self.check_login_user(user_id, user_token, is_need_login)

        return invoke_result

    def power_filter(self, is_check_power, optional_params):
        """
        :description: 权限过滤器
        :param is_check_power: 是否需要验证权限（true需要false不需要）
        :param optional_params: 其他参数
        :return: InvokeResult
        """
        invoke_result = InvokeResult()
        user_info = self.get_curr_user_info()
        base_user_info = self.get_base_user_info()
        if not user_info or not base_user_info:
            invoke_result.ResultCode = "login_expire"
            invoke_result.ResultMessage = "用户已过期，请重新登录"
            return invoke_result
        if is_check_power and user_info.IsSuper != 1 and base_user_info.IsSuper != 1:
            api_path = self.request.path
            if api_path.strip() == "":
                invoke_result.ResultCode = "error"
                invoke_result.ResultMessage = "该用户没有权限，请联系管理员"
                return invoke_result
            page_id = self.request_manage_page_id()
            cote_id = page_id.split("$")[1] if page_id.__contains__("$") else ""
            if not self.check_power_menu(api_path, cote_id):
                invoke_result.ResultCode = "error"
                invoke_result.ResultMessage = "该用户没有权限，请联系管理员"
                return invoke_result
        return invoke_result
    
    def check_password_strength(self, password):
        """
        :description: 检查密码强度
        :param password: 密码字符串
        :return 符合强度=True,message 不符合密码强度=False,message
        :last_editors: ChenD
        """
        message = "密码长度要求8~20个字符，且包含大写字母、小写字母、数字和特殊字符中的至少三种。"
        password_len = len(password)

        if password_len<8 or password_len>20:
            return False,message

        n1=0   # 大写字母
        n2=0   # 小写字母
        n3=0   # 数字
        n4=0   # 特殊字符
        for i in range(password_len):
            ch=password[i]
            if "0"<=ch<="9":
                n3=1
            elif "a"<=ch<="z":
                n2=1
            elif "A"<=ch<="Z":
                n1=1
            else:
                n4=1
        x=n1+n2+n3+n4
        return (False, message) if x<3 else (True, str(x))


def login_filter(is_need_login=True, optional_params=None):
    """
    :description: 登陆过滤装饰器 仅限handler使用
    :param is_need_login：是否需要登陆（true需要false不需要）
    :param optional_params：其他参数
    :return: handler
    """
    def check_login(handler):
        def wrapper(self, **args):
            invoke_result = self.login_filter(is_need_login, optional_params)
            if invoke_result.ResultCode != "0":
                return self.response_common(invoke_result.ResultCode, invoke_result.ResultMessage)
            return handler(self, **args)

        return wrapper

    return check_login


def power_filter(is_check_power=True, optional_params=None):
    """ 
    :description: 权限过滤装饰器 仅限handler使用
    :param is_check_power: 是否需要验证权限（true需要false不需要）
    :param optional_params: 其他参数
    :return: handler
    """
    def check_power(handler):
        def wrapper(self, **args):
            invoke_result = self.power_filter(is_check_power, optional_params)
            if invoke_result.ResultCode != "0":
                return self.response_common(invoke_result.ResultCode, invoke_result.ResultMessage)

            return handler(self, **args)

        return wrapper

    return check_power