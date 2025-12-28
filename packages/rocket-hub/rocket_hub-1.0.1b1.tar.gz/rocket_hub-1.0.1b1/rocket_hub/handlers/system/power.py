"""
:Author: wang kui
:Date: 2020-03-24 16:32:52
:LastEditTime: 2025-08-26 18:46:41
:LastEditors: ChenXiaolei
:Description: power 用户权限相关接口
"""
from rocket_hub.handlers.rocket_base import *
from rocket_hub.utils.dict import *

from rocket_hub.models.db_models.product.product_info_model import *
from rocket_hub.models.db_models.product.product_user_model import *
from rocket_hub.models.db_models.role.role_power_model_ex import *
from rocket_hub.models.db_models.role.role_user_model import *
from rocket_hub.models.db_models.role.role_info_model import *
from rocket_hub.models.db_models.user.user_info_model_ex import *

from rocket_hub.models.hub_model import InvokeResult
from rocket_hub.models.power_model import *


class GetUserInfoHandler(RocketBaseHandler):
    """
    :description: 获取当前用户信息
    """
    @login_filter(True)
    def get_async(self):
        """
        :description: 获取当前用户信息
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        user_info = self.get_curr_user_info()
        curr_info = {}
        if user_info:
            curr_info["Account"] = user_info.Account
            curr_info["IsSuper"] = user_info.IsSuper
            curr_info["UserName"] = user_info.UserName
            curr_info["NickName"] = user_info.NickName
            curr_info["JobNo"] = user_info.JobNo
            curr_info["Avatar"] = user_info.Avatar
            curr_info["Phone"] = user_info.Phone
            curr_info["Email"] = user_info.Email
            curr_info["PersonalitySignature"] = user_info.PersonalitySignature

        return self.response_json_success(curr_info)


class GetUserProductListHandler(RocketBaseHandler):
    """
    :description: 获取用户产品列表
    """
    @login_filter(True)
    def get_async(self):
        """
        :description: 获取用户产品列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        user_id = self.request_user_id()
        product_id = self.request_product_id()
        base_manage_context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
        product_info_model = ProductInfoModel(base_manage_context_key)
        product_user_model = ProductUserModel(base_manage_context_key)
        product_data = []
        product_infos = []
        home_info = {"Title": "平台管理", "ImageUrl": "", "ManageUrl": "", "WebUrl": "", "ProductID": 0}
        is_super = self.get_is_super()

        if is_super:
            product_infos = product_info_model.get_list("IsRelease=1")
            if product_id > 0 and self.__has_home_platform_power(self.get_curr_user_info()).ResultCode == "0":
                product_data.append(home_info)
        else:
            if self.__has_home_platform_power(self.get_curr_user_info()).ResultCode == "0":
                product_data.append(home_info)

            product_user_list = product_user_model.get_list("UserID=%s", params=user_id)

            if product_user_list:
                list_str = str([i.ProductID for i in product_user_list if i.ProductID > 0 or product_id == 0]).strip('[').strip(']')
                condition = f"IsRelease=1 AND ProductID IN({list_str})"
                product_infos = product_info_model.get_list(condition)
            elif not product_data:
                return self.response_common("NoData", "没有其他平台权限")

        for product_info in product_infos:
            product_data.append(self.__to_user_product_data(user_id, product_info, is_super))

        return self.response_json_success(product_data)

    def __to_user_product_data(self, user_id, product_info, is_super):
        """
        :description: 判断该用户是否有用户管理和角色管理权限
        :param user_id: 用户id
        :param product_info: 产品信息
        :param is_super: 是否超管
        :return: 
        :last_editors: ChenXiaolei
        """
        has_user_manage = False
        has_role_manage = False
        if is_super:
            has_user_manage = True
            has_role_manage = True
        else:
            role_user_list = RoleUserModel(product_info.ManageContextKey).get_list("UserID=%s", params=user_id)
            role_power_list = RolePowerModelEx(product_info.ManageContextKey).get_role_power_list([i.RoleID for i in role_user_list])
            # 用户管理
            if [i for i in role_power_list if i.MenuID == config.get_value("menu_id_user", "80ce2364-368f-47ac-98c8-819fcb521bab")]:
                has_user_manage = True
            # 角色管理
            if [i for i in role_power_list if i.MenuID == config.get_value("menu_id_role", "47a90fe3-012b-49b6-af27-5293124ce827")]:
                has_role_manage = True

        return {
            "Title": product_info.ProductName,
            "SubTitle": product_info.ProductSubName,
            "ImageUrl": product_info.ImageUrl,
            "ManageUrl": product_info.ManageUrl,
            "PowerUrl": product_info.PowerUrl,
            "ProductID": product_info.ProductID,
            "HasUserManage": has_user_manage,
            "HasRoleManage": has_role_manage,
            "IsBrank": product_info.IsBrank,
        }

    def __has_home_platform_power(self, user_info):
        """
        :description: 获取该账号是否有平台管理权限
        :param user_info：用户信息
        :return: 
        :last_editors: ChenXiaolei
        """
        invoke_result = InvokeResult()
        invoke_result.ResultCode = "AccountLock"
        invoke_result.ResultMessage = "对不起该账号没有平台管理权限"
        context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
        user_info_model_ex = UserInfoModel(context_key)
        base_user_info = user_info_model_ex.get_entity_by_id(user_info.UserID)
        if not base_user_info:
            return invoke_result
        if base_user_info.IsSuper == 1:
            return InvokeResult()
        role_user_list = RoleUserModel(context_key).get_list("UserID=%s", params=self.request_user_id())
        if not role_user_list:
            return invoke_result
        role_power_list = RolePowerModelEx(context_key).get_role_power_list([i.RoleID for i in role_user_list])
        role_power_info = [i for i in role_power_list if i.MenuID == config.get_value("menu_id_platform", "03E5D2A0-DB59-47F6-8F10-1ACDEFE9BDDD")]

        return InvokeResult() if role_power_info else invoke_result


class FocusPasswordHandler(RocketBaseHandler):
    """
    :description: 强制修改密码弹窗
    """
    @login_filter(True)
    def get_async(self):
        """
        :description: 强制修改密码弹窗
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        invoke_result = InvokeResult()
        is_force_password = UserInfoModelEx().is_force_password(self.get_curr_user_info())

        is_force_mobile = True
        if self.get_curr_user_info().Phone:
            is_force_mobile = False
        
        if is_force_password and is_force_mobile:
            invoke_result.ResultCode = "Upgrade Security"
            invoke_result.ResultMessage = "需要提升安全等级"
        elif is_force_password:
            invoke_result.ResultCode = "Change Password"
            invoke_result.ResultMessage = "需要修改密码"
        elif is_force_mobile:
            invoke_result.ResultCode = "Update Mobile"
            invoke_result.ResultMessage = "需要修改手机号"
        else:
            invoke_result.ResultCode = "Has Change Password"
            invoke_result.ResultMessage = "核验正常"

        return self.response_custom(invoke_result)


class FocusChangeUserPwHandler(RocketBaseHandler):
    """
    :description: 强制安全升级
    """
    @login_filter(True)
    def post_async(self):
        """
        :description: 强制安全升级
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 密码
        password = self.get_param("password")
        # 手机号
        mobile = self.get_param("mobile")
        # 验证码
        verify_code = self.get_param("verify_code")

        invoke_result = InvokeResult()
        user_info_model_ex = UserInfoModel(config.get_value("base_manage_context_key", "db_rocket_hub"))
        user_info_ex = UserInfoModelEx()
        base_user_info = self.get_base_user_info()

        user_id = base_user_info.UserID if base_user_info else ""
        # 先判断
        if password:
            is_sturdy,message = self.check_password_strength(password)

            if not is_sturdy:
                return self.response_common("Error", message)
            
            is_force_password = user_info_ex.is_force_password(base_user_info)
            if not is_force_password:
                return self.response_common("Error", "无需强制更改密码")
        if mobile:
            if user_info_ex.is_exist_phone(mobile,user_id):
                return self.response_common("Exist Phone", "手机号已存在")
            # 验证用户验证码
            resposne = HTTPHelper.get(f"https://ps.gao7.com/verify_code/sms?mobile={mobile}&project_name={config.get_value('project_name')}")

            if resposne:
                verify_json = json.loads(resposne.text)
                if verify_json["result"]==0:
                    return self.response_common("VerifyCodeExpired", verify_json["desc"])
                elif verify_json["data"]["verify_code"]!=verify_code:
                    return self.response_common("VerifyCodeError", "验证码输入错误")
        # 后更改
        if password:
            sign_password = user_info_ex.sign_password(password, user_id)
            user_info_model_ex.update_table("Password=%s", "UserID=%s", [sign_password, user_id])
        if mobile:
            user_info_model_ex.update_table("Phone=%s", "UserID=%s", [mobile, user_id])
            
        self.logout(user_id)

        invoke_result.ResultCode="UserExpire"
        invoke_result.ResultMessage = "已更新登录凭证，请重新登录"

        return self.response_custom(invoke_result)


class ChangeCurrUserPwHandler(RocketBaseHandler):
    """
    :description: 修改密码
    """
    @login_filter(True)
    def post_async(self):
        """
        :description: 修改密码
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 旧密码
        password = self.get_param("Password")
        # 新密码
        new_password = self.get_param("NewPassword")

        is_sturdy,message = self.check_password_strength(new_password)

        if not is_sturdy:
            return self.response_common("ErrorPassword", message)
        
        invoke_result = InvokeResult()
        user_info_model_ex = UserInfoModelEx(config.get_value("base_manage_context_key", "db_rocket_hub"))
        base_user_info = self.get_base_user_info()

        user_id = base_user_info.UserID if base_user_info else ""
        if not user_info_model_ex.verify_password(password, base_user_info.Password, user_id):
            return self.response_common("ErrorPassword", "旧密码错误，请重新输入")

        sign_password = user_info_model_ex.sign_password(new_password, user_id)
        user_info_model_ex.update_table("Password=%s", "UserID=%s", [sign_password, user_id])

        self.logout(user_id)

        return self.response_custom(invoke_result)


class GetRoleListHandler(RocketBaseHandler):
    """
    :description: 角色列表
    """
    @login_filter(True)
    def get_async(self):
        """
        :description: 角色列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        manage_context_key = self.get_manage_context_key()
        user_id = self.request_user_id()
        is_super = self.get_is_super()

        condition = "" if is_super else f"ChiefUserID='{user_id}'"
        role_dict_list = RoleInfoModel(manage_context_key).get_dict_list(condition, field="RoleID,RoleName")

        return self.response_json_success(role_dict_list)


class GetRoleUserListHandler(RocketBaseHandler):
    """
    :description: 角色用户列表
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 角色用户列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 数据库db
        manage_context_key = self.get_manage_context_key()
        # 用户id
        user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()
        # 页索引
        page_index = self.get_page_index()
        # 页大小
        page_size = self.get_page_size()
        # 查询条件、排序字段
        condition, order = self.get_condition_by_body()

        page_data = PageInfo()
        role_user_dto_list = []
        role_info_model = RoleInfoModel(manage_context_key)

        if not is_super:
            if condition:
                condition += " AND "
            condition += f"ChiefUserID='{user_id}'"

        page_list, total = role_info_model.get_page_list("*", page_index, page_size, condition, "", order)
        if not page_list:
            return self.response_json_success(page_data)

        user_ids_list = [i.ModifyUserID for i in page_list]
        user_ids_str = str(user_ids_list).strip('[').strip(']')
        user_info_list = UserInfoModel(manage_context_key).get_list(f"UserID IN({user_ids_str})")

        role_ids_list = [i.RoleID for i in page_list]
        role_ids_str = str(role_ids_list).strip('[').strip(']')
        role_info_list = RoleUserModel(manage_context_key).get_list(f"RoleID IN({role_ids_str})")

        role_power_list = RolePowerModel(manage_context_key).get_list(f"RoleID IN({role_ids_str})")
        role_power_list = RolePowerEx().get_list_by_role_power_list(role_power_list)

        for curr_role_info in page_list:
            curr_role_user_dto = DictUtil.auto_mapper(RoleUserDto(), curr_role_info.__dict__)
            curr_user_info = [i for i in user_info_list if curr_role_info.ModifyUserID != "" and i.UserID == curr_role_info.ModifyUserID]
            curr_role_user_dto.ModifyUser = curr_user_info[0].UserName if curr_user_info else ""
            curr_role_user_dto.RoleUserIds = [i.UserID for i in role_info_list if i.RoleID == curr_role_info.RoleID]
            curr_role_user_dto.RoleMenuIds = [i.MenuCoteID for i in role_power_list if i.RoleID == curr_role_info.RoleID]
            if curr_role_info.ModifyDate == "1900-01-01 00:00:00":
                curr_role_user_dto.ModifyDate = ""
            role_user_dto_list.append(curr_role_user_dto.__dict__)

        page_data.Data = role_user_dto_list
        page_data.RecordCount = total
        page_data.PageSize = page_size
        page_data.PageIndex = page_index

        return self.response_json_success(page_data)


class GetUserRoleListHandler(RocketBaseHandler):
    """
    :description: 用户角色列表
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 用户角色列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 数据库db
        manage_context_key = self.get_manage_context_key()
        # 用户id
        user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()
        # 页索引
        page_index = self.get_page_index()
        # 页大小
        page_size = self.get_page_size()
        # 查询条件、排序字段
        condition, order = self.get_condition_by_body()
        # 产品id
        product_id = config.get_value("product_id")

        page_data = PageInfo()
        user_role_dto_list = []
        user_info_model = UserInfoModel(manage_context_key)

        if not is_super:
            if condition:
                condition += " AND "
            condition += f"ChiefUserID='{user_id}'"

        page_list, total = user_info_model.get_page_list("*", page_index, page_size, condition, "", order)
        if not page_list:
            return self.response_json_success(page_data)

        chief_user_ids_list = [i.ChiefUserID for i in page_list]
        chief_user_ids_str = str(chief_user_ids_list).strip('[').strip(']')
        chief_user_info_list = user_info_model.get_list(f"UserID IN({chief_user_ids_str})")

        user_ids_list = [i.UserID for i in page_list]
        user_ids_str = str(user_ids_list).strip('[').strip(']')
        role_user_list = RoleUserModel(manage_context_key).get_list(f"UserID IN({user_ids_str})")

        product_user_list = []
        if product_id == 0:
            product_user_list = ProductUserModel(config.get_value("base_manage_context_key", "db_rocket_hub")).get_list(f"UserID IN({user_ids_str})")

        for curr_user_info in page_list:
            curr_user_role_dto = DictUtil.auto_mapper(UserRoleDto(), curr_user_info.__dict__)
            curr_user_role_dto.UserRoleIds = [i.RoleID for i in role_user_list if i.UserID == curr_user_info.UserID]
            if product_id == 0:
                curr_user_role_dto.UserProductIds = [i.ProductID for i in product_user_list if i.UserID == curr_user_info.UserID]
            chief_user_info = [i for i in chief_user_info_list if curr_user_info.ChiefUserID and i.UserID == curr_user_info.ChiefUserID]
            curr_user_role_dto.ChiefUserName = chief_user_info[0].UserName if chief_user_info else ""
            if curr_user_role_dto.LoginDate == "1900-01-01 00:00:00":
                curr_user_role_dto.LoginDate = ""
            user_role_dto_list.append(curr_user_role_dto.__dict__)

        page_data.Data = user_role_dto_list
        page_data.RecordCount = total
        page_data.PageSize = page_size
        page_data.PageIndex = page_index

        return self.response_json_success(page_data)


class SaveUserHandler(RocketBaseHandler):
    """
    :description: 保存用户
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 保存用户
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 用户id（空为新增）
        user_id = self.get_param("UserID")
        # 账号
        account = self.get_param("Account")
        # 密码
        password = self.get_param("Password")
        # 电子邮箱
        email = self.get_param("Email")
        # 用户真实名称
        user_name = self.get_param("UserName")
        # 用户昵称
        nick_name = self.get_param("NickName")
        # 工号
        job_no = self.get_param("JobNo")
        # 用户电话
        phone = self.get_param("Phone")
        # 用户头像
        avatar = self.get_param("Avatar")
        # 用户角色列表（多个角色逗号分隔）
        user_role_id_str = self.get_param("UserRoleIdStr")
        # 用户产品列表（多个产品逗号分隔）
        user_product_id_str = self.get_param("UserProductIdStr")
        # 是否修改密码
        change_pw = bool(self.get_param("ChangePw", False))

        manage_context_key = self.get_manage_context_key()
        is_super = self.get_is_super()
        curr_user_id = self.request_user_id()
        product_id = self.request_product_id()

        # 验证数据
        if account == "":
            return self.response_common("AccountEmpty", "账号为空")

        user_info_model = UserInfoModelEx(self.get_manage_context_key())
        user_info = UserInfo()
        if user_id != "":
            user_info = user_info_model.get_entity_by_id(user_id)
            if not user_info:
                return self.response_common("NoExit", "用户不存在")
            user_info_c = user_info_model.get_entity("Account=%s AND UserID!=%s", params=[account, user_id])
        else:
            user_info_c = user_info_model.get_entity("Account=%s", params=account)

        if user_info_c:
            return self.response_common("Exit", "账号已存在")

        if user_info_model.is_exist_phone(phone,user_id):
            return self.response_common("Exit", "手机号已存在")
        
        # 检查密码强度
        if password:
            is_sturdy,message = self.check_password_strength(password)

            if not is_sturdy:
                return self.response_common("ErrorPassword", message)
        
        user_info.Account = account
        user_info.Email = email
        user_info.UserName = user_name
        user_info.NickName = nick_name
        user_info.JobNo = job_no
        user_info.Phone = phone
        user_info.Avatar = avatar
        if not self.get_is_super():
            user_info.ChiefUserID = self.request_user_id()

        power_model = PowerModel(manage_context_key, is_super, curr_user_id, product_id)
        is_add = user_id == ""
        result = power_model.set_user(user_info, user_role_id_str.split(","), user_product_id_str.split(","), password, change_pw, is_add)

        return self.response_json_success(result)


class SaveCurrUserHandler(RocketBaseHandler):
    """
    :description: 保存用户
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 保存用户
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 用户id
        user_id = self.request_user_id()
        # 电子邮箱
        email = self.get_param("Email")
        # 用户昵称
        nick_name = self.get_param("NickName")
        # 用户电话
        phone = self.get_param("Phone")
        # 用户头像
        avatar = self.get_param("Avatar")
        # 个性签名
        personality_signature = self.get_param("PersonalitySignature")

        user_info_model = UserInfoModelEx(self.get_manage_context_key())
        user_info = user_info_model.get_entity_by_id(user_id)
        if user_id == "" or not user_info:
            return self.response_common("Exit", "账号不存在")

        if user_info_model.is_exist_phone(phone,user_id):
            return self.response_common("Exit", "手机号已存在")
        
        user_info.Email = email
        user_info.NickName = nick_name
        user_info.Phone = phone
        user_info.Avatar = avatar
        user_info.PersonalitySignature = personality_signature

        user_info_model.update_entity(user_info, field_list=["Email", "NickName", "Phone", "Avatar", "PersonalitySignature"])

        return self.response_json_success(user_info)


class GetUserListHandler(RocketBaseHandler):
    """
    :description: 用户列表
    """
    @login_filter(True)
    @power_filter(True)
    def get_async(self):
        """
        :description: 用户列表
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        manage_context_key = self.get_manage_context_key()
        user_id = self.request_user_id()
        is_super = self.get_is_super()

        condition = "" if is_super else f"ChiefUserID='{user_id}'"
        user_dict_list = UserInfoModel(manage_context_key).get_dict_list(condition, field="UserID,Account,UserName")

        return self.response_json_success(user_dict_list)


class SaveRoleHandler(RocketBaseHandler):
    """
    :description: 修改角色
    """
    @login_filter(True)
    @power_filter(True)
    def post_async(self):
        """
        :description: 修改角色
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 角色id
        role_id = self.get_param("RoleID")
        # 角色名称
        role_name = self.get_param("RoleName")
        # 备注
        summary = self.get_param("Summary")
        # 角色用户id
        role_user_id_str = self.get_param("RoleUserIdStr")
        # 角色栏目id
        role_menu_id_str = self.get_param("RoleMenuIdStr")
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 是否超管
        is_super = self.get_is_super()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 产品id
        product_id = self.request_product_id()

        # 验证数据
        if role_name == "":
            return self.response_common("RoleNameEmpty", "角色名为空")

        role_info_model = RoleInfoModel(self.get_manage_context_key())
        role_info = RoleInfo()
        if role_id != "":
            role_info = role_info_model.get_entity_by_id(role_id)
            if not role_info:
                return self.response_common("NoExit", "角色不存在")
            role_info_c = role_info_model.get_entity("RoleName=%s and RoleID!=%s", params=[role_name, role_id])
            if role_info_c:
                return self.response_common("NoExit", "角色名已存在")
        else:
            role_info_c = role_info_model.get_entity("RoleName=%s", params=role_name)
            if role_info_c:
                return self.response_common("NoExit", "角色名已存在")
            role_info.RoleID = UUIDHelper.get_uuid()

        if not self.get_is_super():
            role_info.ChiefUserID = curr_user_id

        role_info.RoleName = role_name
        role_info.Summary = summary
        role_info.ModifyDate = TimeHelper.get_now_format_time()
        role_info.ModifyUserID = self.request_user_id()

        power_model = PowerModel(manage_context_key, is_super, curr_user_id, product_id)
        is_add = role_id == ""
        result = power_model.set_role(role_info, role_user_id_str.split(","), role_menu_id_str.split(","), is_add)
        result.ModifyUser = self.get_curr_user_info().UserName

        return self.response_json_success(result.__dict__)


class RemoveRoleUserHandler(RocketBaseHandler):
    """
    :description: 删除用户角色
    """
    @login_filter(True)
    @power_filter(True)
    def get_async(self):
        """
        :description: 删除用户角色
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 是否超管
        is_super = self.get_is_super()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 产品id
        product_id = self.request_product_id()
        # 角色id
        role_id = self.get_param("roleID")
        # 用户id
        user_id = self.get_param("userID")

        if role_id == "":
            return self.response_common("EmptyRoleID", "角色ID为空")
        if user_id == "":
            return self.response_common("EmptyUserID", "用户ID为空")

        power_model = PowerModel(manage_context_key, is_super, curr_user_id, product_id)
        power_model.remove_role_user(role_id, user_id)

        return self.response_json_success()


class DeleteRoleHandler(RocketBaseHandler):
    """
    :description: 删除角色
    """
    @login_filter(True)
    @power_filter(True)
    def get_async(self):
        """
        :description: 删除用户角色
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 角色id
        role_id = self.get_param("RoleID")

        if role_id == "":
            return self.response_common("EmptyRoleID", "角色ID为空")

        manage_context_key = self.get_manage_context_key()

        RoleUserModel(manage_context_key).del_entity("RoleID=%s", role_id)
        RolePowerModel(manage_context_key).del_entity("RoleID=%s", role_id)
        RoleInfoModel(manage_context_key).del_entity("RoleID=%s", role_id)

        return self.response_json_success()


class DeleteUserHandler(RocketBaseHandler):
    """
    :description: 删除用户
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("UserID")
    def get_async(self):
        """
        :description: 删除用户
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 要删除的用户id
        user_id = self.get_param("UserID")
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 产品id
        product_id = self.request_product_id()
        # 是否超管
        is_super = self.get_is_super()

        if user_id == "":
            return self.response_common("EmptyUserID", "用户ID为空")

        if user_id == self.request_user_id():
            return self.response_common("RemoveLimit", "当前账号不能删除")

        power_model = PowerModel(manage_context_key, is_super, curr_user_id, product_id)
        power_model.remove_user(curr_user_id, user_id)

        self.logout(user_id)

        return self.response_json_success()


class ModifyUserStatusHandler(RocketBaseHandler):
    """
    :description: 更新用户状态
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("UserID,IsLock")
    def get_async(self):
        """
        :description: 更新用户状态
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 用户id
        user_id = self.get_param("UserID")
        # 是否锁定
        is_lock = int(self.get_param("IsLock", -1))
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()

        if user_id == "":
            return self.response_json_error_params()

        if is_lock not in [0, 1]:
            return self.response_json_error_params()

        user_info_model = UserInfoModel(manage_context_key)
        user_info = UserInfoModel(manage_context_key).get_entity_by_id(user_id)
        if not user_info:
            return self.response_common("NoExit", "用户不存在")

        if not is_super and user_info.ChiefUserID != curr_user_id:
            return self.response_common("NoExit", "用户不存在")

        user_info_model.update_table("IsLock=%s", "UserID=%s", [is_lock, user_id])

        return self.response_json_success()


class ResetUserPasswordHandler(RocketBaseHandler):
    """
    :description: 重置密码
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("UserID")
    def get_async(self):
        """
        :description: 重置密码
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        # 用户id
        user_id = self.get_param("UserID")
        # 数据库连接串
        base_manage_context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()

        user_info_model = UserInfoModel(base_manage_context_key)
        user_info = UserInfoModel(base_manage_context_key).get_entity_by_id(user_id)
        if not user_info:
            return self.response_common("NoExit", "用户不存在")

        if not is_super and user_info.ChiefUserID != curr_user_id:
            return self.response_common("NoExit", "用户不存在")

        sign_password = UserInfoModelEx().sign_password("", user_id)

        user_info_model.update_table("FaildLoginCount=0,Password=%s", "UserID=%s", [sign_password, user_id])

        self.logout(user_id)

        return self.response_json_success()


class ResetUserFaildLoginCountHandler(RocketBaseHandler):
    """
    :description: 登录失败重置
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("UserID")
    def get_async(self):
        """
        :description: 登录失败重置
        :param {type}
        :return:
        :last_editors: ChenXiaolei
        """
        user_id = self.get_param("UserID")
        # 数据库连接串
        base_manage_context_key = config.get_value("base_manage_context_key", "db_rocket_hub")
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()

        user_info_model = UserInfoModel(base_manage_context_key)
        user_info = UserInfoModel(base_manage_context_key).get_entity_by_id(user_id)
        if not user_info:
            return self.response_common("NoExit", "用户不存在")

        if not is_super and user_info.ChiefUserID != curr_user_id:
            return self.response_common("NoExit", "用户不存在")

        user_info_model.update_table("FaildLoginCount=0", "UserID=%s", [user_id])

        return self.response_json_success()


class RemoveUserAllRoleHandler(RocketBaseHandler):
    """
    :description: 收回权限
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("UserID")
    def get_async(self):
        """
        :description: 收回权限
        :param {type}
        :return:
        :last_editors: ChenXiaolei
        """
        # 被收回权限的用户id
        user_id = self.get_param("UserID")
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 是否超管
        is_super = self.get_is_super()

        role_user_model = RoleUserModel(manage_context_key)

        if is_super:
            role_user_model.del_entity("UserID=%s", user_id)
        else:
            user_info = role_user_model.get_entity_by_id(user_id)
            if user_info and user_info.ChiefUserID != curr_user_id:
                role_user_model.del_entity("UserID=%s", user_id)

        return self.response_json_success()


class CopyUserRoleHandler(RocketBaseHandler):
    """
    :description: 复制权限
    """
    @login_filter(True)
    @power_filter(True)
    @filter_check_params("userID,copyUserID")
    def get_async(self):
        """
        :description: 复制权限
        :param {type}
        :return:
        :last_editors: ChenXiaolei
        """
        # 复制用户id
        copy_user_id = self.get_param("copyUserID")
        # 用户id
        user_id = self.get_param("userID")
        # 数据库连接串
        manage_context_key = self.get_manage_context_key()
        # 当前用户id
        curr_user_id = self.request_user_id()
        # 产品id
        product_id = self.request_product_id()
        # 是否超管
        is_super = self.get_is_super()

        power_model = PowerModel(manage_context_key, is_super, curr_user_id, product_id)
        power_model.copy_user_role(copy_user_id, user_id)

        return self.response_json_success()