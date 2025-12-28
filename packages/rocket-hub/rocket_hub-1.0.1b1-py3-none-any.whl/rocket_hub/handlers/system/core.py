"""
:Author: ChenXiaolei
:Date: 2020-03-24 19:48:05
:LastEditTime: 2025-08-28 10:00:46
:LastEditors: ChenXiaolei
:Description: 
"""
from rocket_hub.handlers.rocket_base import *
from rocket_hub.libs.geetest import *

from rocket_hub.models.db_models.user.user_info_model_ex import *
from rocket_hub.models.db_models.role.role_power_model_ex import *
from rocket_hub.models.db_models.role.role_user_model import *
from rocket_hub.models.db_models.user.user_login_model import *
from rocket_hub.models.hub_model import InvokeResult
from rocket_hub.libs.file.upload import *


class CoreHandler(RocketBaseHandler):
    def get_async(self):
        result = "后台接口站"
        self.write(result)


class VerifyCodeHandler(RocketBaseHandler):
    def mask_phone_number(self, mobile):
        return mobile[:3] + mobile[3:-4].replace(mobile[3:-4], '*'*len(mobile[3:-4])) + mobile[-4:]

    @filter_check_params("account")
    def get_async(self):
        """
        :description: 判断用户是否配置手机号，前端配合显示手机验证码框
        :param account: 用户账号
        :return : 是否需要验证码
        :last_editors: ChenXiaolei
        """

        account = self.request_params["account"]
        
        user_info = UserInfoModelEx().get_dict(
            "Account=%s or Phone=%s", field="UserID,Phone", params=[account, account])
        
        if not user_info:
            return self.response_common("Check Password", "密码验证模式")
        
        login_key = user_info["UserID"].replace("-","")
        
        check_level = config.get_value("check_level", "safety")

        if check_level == "password":
            return self.response_common("Check Password", "密码验证模式",login_key)
        elif check_level in ["verify_code", "safety", "safety_strong"]:
            # 默认模式，白名单无需手机验证
            if check_level == "safety" and self.get_remote_ip() in self.get_group_ip():
                return self.response_common("Check Password", "密码验证模式",login_key)

        user_info = UserInfoModelEx().get_dict(
            "Account=%s or Phone=%s", field="Phone", params=[account, account])
        
        if user_info and user_info["Phone"]:
            if check_level == "verify_code":
                return self.response_common("Check VerifyCode", "验证码验证模式",login_key)
            elif check_level == "safety" or check_level == "safety_strong":
                return self.response_common("Check All", f"安全验证模式 ip:[{self.get_remote_ip()}]",login_key)

        return self.response_common("Check Password", "密码验证模式",login_key)

    @filter_check_params()
    def post_async(self):
        """
        :description: 发送验证码
        :param account: 用户账号
        :return : 发送结果
        :last_editors: ChenXiaolei
        """
        account = self.request_params.get("account", None)
        mobile = self.request_params.get("mobile", None)
        if account:
            # 如果account是11位的，就优先正则判断手机号
            if re.match(r'^1[3456789]\d{9}$', account):
                user_info = UserInfoModelEx().get_dict(
                    "Phone=%s", field="Account,Phone", params=[account])
            else:
                user_info = UserInfoModelEx().get_dict(
                    "Account=%s", field="Account,Phone", params=[account])

            if not user_info or not user_info["Phone"]:
                return self.response_common("Phone number not set", "用户未设置手机号")

            phone = user_info["Phone"]
        elif mobile:
            phone = mobile

        request_data = {
            "mobile": phone,
            "project_name": config.get_value("project_name")
        }

        resposne = HTTPHelper.post("https://ps.gao7.com/verify_code/sms",
                                   request_data, headers={'Content-Type': 'application/json'})

        if resposne:
            verify_json = json.loads(resposne.text)
            if verify_json["result"] == 0:
                return self.response_common("Send Fail", verify_json["desc"], data={"mobile": self.mask_phone_number(phone)})
            else:
                return self.response_common("0", "发送验证码成功", data={"mobile": self.mask_phone_number(phone)})


class GeetestCodeHandler(RocketBaseHandler):
    """
    :description: 获取极验证的验证码
    """

    def get_async(self):
        user_id = 'test'
        gt = GeetestLib(config.get_value("pc_geetest_id", "5993a5801d01dd43a07452be135a7381"),
                        config.get_value("pc_geetest_key", "e5bd10f056d92ee46d2ac7cd0356a979"))
        status = gt.pre_process(user_id, JSON_FORMAT=0, ip_address="127.0.0.1")
        if not status:
            status = 2
        response_str = gt.get_response_str()

        return self.response_json_success(response_str)


class LoginPlatformHandler(RocketBaseHandler):
    """
    :description: 登陆
    """

    def get_async(self):
        # 账号
        account = self.get_param("account")
        # 密码
        password = self.get_param("password")
        # 验证码，配置中需要开启
        verify_code = self.get_param("verify_code")
        # 极验证参数challenge
        challenge = self.get_param("challenge")
        # 极验证参数validate
        validate = self.get_param("validate")
        # 极验证参数seccode
        seccode = self.get_param("seccode")

        if account == "":
            return self.response_common("EmptyAccount", "对不起，请你输入账号")

        # 滑动验证码
        if config.get_value("is_captcha_check", True):
            if challenge == "" or validate == "" or seccode == "":
                return self.response_common("CaptchaError", "对不起，请先校验验证码")

            result = self.check_code(challenge, validate, seccode)
            if not result:
                return self.response_common("CaptchaError", "对不起，验证码验证失败")

        # 如果配置中未开启验证码校验，则必需输入密码，
        check_level = config.get_value("check_level", "safety")

        if check_level in ["safety", "safety_strong"]:
            if not password:
                return self.response_common("EmptyPassword", "请您输入密码")

            user_info = UserInfoModelEx().get_dict("Account=%s or Phone=%s", field="Phone", params=[account, account])
            
            if not user_info:
                return self.response_common("AccountNotExist", "用户名或密码错误")

            # 默认模式，白名单无需手机验证
            if (check_level == "safety" and self.get_remote_ip() in self.get_group_ip()) or not user_info["Phone"]:
                invoke_result = self.login(account, password)
            else:
                if not verify_code:
                    return self.response_common("EmptyVerifyCode", "请输入验证码")

                invoke_result = self.login(account, password, verify_code=verify_code)
                
        elif check_level == "verify_code":
            # 验证码
            if not verify_code:
                return self.response_common("EmptyVerifyCode", "请输入验证码")
            invoke_result = self.login(account, verify_code=verify_code)
        else:
            # 密码
            invoke_result = self.login(account, password)

        # if check_level=="safety":
        #     if password == "":
        #         return self.response_common("EmptyPassword", "对不起，请您输入密码")
        #     invoke_result = self.login(account, password)
        # else:
        #     # 如果配置中开启验证码校验，则可通过verify_code校验登录，但是存在可通过初始密码登录的情况。
        #     if verify_code == "" and password=="":
        #         return self.response_common("EmptyPassword", "登录失败，请输入密码及验证码")
        #     elif password:
        #         invoke_result = self.login(account, password)
        #     elif verify_code:
        #         invoke_result = self.login(account, verify_code=verify_code )

        # invoke_result = self.login(account, password)

        if invoke_result.ResultCode == "0":
            invoke_result_user = self.check_login_user(
                invoke_result.Data['UserID'], invoke_result.Data['UserToken'])
            if invoke_result_user.ResultCode != "0":
                invoke_result = invoke_result_user

        return self.response_custom(invoke_result)

    def check_code(self, challenge="", validate="", seccode=""):
        """
        :description: 验证码校验
        :param challenge：极验证参数challenge
        :param validate：极验证参数validate
        :param seccode：极验证参数seccode
        :return: true or false
        :last_editors: ChenXiaolei
        """
        gt = GeetestLib(config.get_value("pc_geetest_id", "5993a5801d01dd43a07452be135a7381"),
                        config.get_value("pc_geetest_key", "e5bd10f056d92ee46d2ac7cd0356a979"))
        result = gt.success_validate(
            challenge, validate, seccode, JSON_FORMAT=0)
        return result == 1

    def login(self, account="", password="", verify_code=""):
        """
        :description: 登录验证
        :param account：账号
        :param password：密码
        :param verify_code：验证码
        :return: invoke_result
        :last_editors: ChenXiaolei
        """
        manage_context_key = config.get_value(
            "manage_context_key", "db_rocket_hub")
        base_manage_context_key = config.get_value(
            "base_manage_context_key", "db_rocket_hub")
        invoke_result = InvokeResult()
        user_info_model = UserInfoModel(base_manage_context_key)
        user_info = user_info_model.get_entity(
            "Account=%s or Phone=%s", params=[account, account])
        if not user_info:
            invoke_result.ResultCode = "NoExistAccount"
            invoke_result.ResultMessage = "用户名或密码错误"
            return invoke_result

        if user_info.FaildLoginCount > 4:
            invoke_result.ResultCode = "FaildLoginCountLimit"
            invoke_result.ResultMessage = "异常登录错误限制，请联系管理员解除限制"
            return invoke_result

        verify = True

        if password:
            verify = UserInfoModelEx().verify_password(
                password, user_info.Password, user_info.UserID)
            if not verify:
                user_info.FaildLoginCount += 1
                invoke_result.ResultCode = "ErrorPassword"
                invoke_result.ResultMessage = f"用户名或密码错误,尝试次数：{str(user_info.FaildLoginCount)}"
        if verify == True and verify_code:
            # 验证用户验证码
            resposne = HTTPHelper.get(
                f"https://ps.gao7.com/verify_code/sms?mobile={user_info.Phone}&project_name={config.get_value('project_name')}")

            if resposne:
                verify_json = json.loads(resposne.text)
                if verify_json["result"] == 0:
                    invoke_result.ResultCode = "VerifyCodeExpired"
                    invoke_result.ResultMessage = f"验证码已过期,请重新发送。"
                    verify = False
                elif verify_json["data"]["verify_code"] != verify_code:
                    user_info.FaildLoginCount += 1
                    invoke_result.ResultCode = "VerifyCodeError"
                    invoke_result.ResultMessage = f"验证码错误,尝试次数：{str(user_info.FaildLoginCount)}"
                    verify = False
                else:
                    verify = True
        if not verify:
            user_info_model.update_table("FaildLoginCount=%s", "UserID=%s", [
                                         user_info.FaildLoginCount, user_info.UserID])

            return invoke_result

        if user_info.IsLock == 1:
            invoke_result.ResultCode = "AccountLock"
            invoke_result.ResultMessage = "对不起你的帐号已经被锁定，请联系管理员解除限制"
            return invoke_result

        # is_super = user_info.IsSuper == 1

        if manage_context_key != base_manage_context_key:
            user_info_model_part = UserInfoModel(manage_context_key)
            user_info_curr = user_info_model_part.get_entity(
                "Account=%s", params=account)
            if not user_info_curr:
                invoke_result.ResultCode = "NoExistAccount"
                invoke_result.ResultMessage = "用户名或密码错误"
                return invoke_result
            if user_info_curr.IsLock == 1:
                invoke_result.ResultCode = "AccountLock"
                invoke_result.ResultMessage = "对不起你的帐号已经被锁定，请联系管理员解除限制"
                return invoke_result

            # is_super = user_info_curr.IsSuper == 1 or user_info.IsSuper == 1

        # if is_platform and not is_super:
        #     role_user_list = RoleUserModel(manage_context_key).get_list("UserID=%s", params=user_info.UserID)
        #     if len(role_user_list) == 0:
        #         invoke_result.ResultCode = "AccountLock"
        #         invoke_result.ResultMessage = "对不起该账号没有平台管理权限"
        #         return invoke_result

        #     role_power_list = RolePowerModelEx(manage_context_key).get_role_power_list([i.RoleID for i in role_user_list])
        #     if not [i for i in role_power_list if i.MenuID == config.get_value("menu_id_platform", "03E5D2A0-DB59-47F6-8F10-1ACDEFE9BDDD")]:
        #         invoke_result.ResultCode = "AccountLock"
        #         invoke_result.ResultMessage = "对不起该账号没有平台管理权限"
        #         return invoke_result

        user_info.FaildLoginCount = 0
        user_info.LoginDate = TimeHelper.get_now_datetime()
        user_info.LoginIP = self.get_remote_ip()
        user_info_model.update_table("FaildLoginCount=%s,LoginDate=%s,LoginIP=%s", "UserID=%s", [
                                     user_info.FaildLoginCount, user_info.LoginDate, user_info.LoginIP, user_info.UserID])

        invoke_result.ResultCode = "0"
        invoke_result.ResultMessage = "调用成功"
        invoke_result.Data = self.set_user_info_login_status(
            user_info).__dict__

        return invoke_result

    def set_user_info_login_status(self, user_info):
        """
        :description: 登录状态设置
        :param user_info：当前登录用户信息
        :return: user_login
        :last_editors: ChenXiaolei
        """
        user_login = UserLogin()
        user_login.UserID = user_info.UserID
        user_login.UserIDMD5 = CryptoHelper.md5_encrypt(user_info.UserID, config.get_value(
            "login_encrypt_key", "7C34A5212F7845CB85D4BBB589502D9B"))
        user_login.UserToken = UUIDHelper.get_uuid()
        user_login.ExpireTime = TimeHelper.add_hours_by_format_time(
            hour=config.get_value("login_expire", 10))

        self.login_cookie(user_login)

        return user_login


class LogoutHandler(RocketBaseHandler):
    """
    :description: 注销
    """

    def post_async(self):
        """
        :description: 注销用户
        :param {type} 
        :return: 
        :last_editors: ChenXiaolei
        """
        self.logout(self.request_user_id())

        return self.response_json_success()


class UploadFilesHandler(RocketBaseHandler):
    """
    :description: 上传图片
    """

    def post_async(self):
        """
        :description: 上传图片
        :param resourceCode：resourceCode
        :param resourceCode：restrictCode
        :return: json
        :last_editors: ChenXiaolei
        """
        # 获取参数
        resource_code = self.get_param("resourceCode")
        restrict_code = self.get_param("restrictCode")

        # 验证数据
        if resource_code == "":
            return self.response_common("ResourceCodeEmpty", "资源代码不能为空")
        if restrict_code == "":
            return self.response_common("RestrictCodeEmpty", "资源限制码不能为空")

        invoke_result = FileUpload(self.get_file_context_key()).upload(
            resource_code, restrict_code, self.request.files)

        if invoke_result.ResultCode == "0":
            return self.response_json_success(invoke_result.Data)
        else:
            return self.response_custom(invoke_result)
