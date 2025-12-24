
import json
import random

import requests

from darren_util import time_get_timestamp, json_parse_safe, aes_encrypt_string, rsa_encrypt_string, \
    aes_decrypt_string, string_random_string
from darren_util.darren_encode import url_get_param
from darren_util.darren_ret import DarrenRet
from darren_util.encry.darren_rsa import rsa_decrypt_with_public_key

rsa_api_list = [
    "GetToken",
    "UserLogin",
    "UserReduceMoney",
    "UserReduceVipNumber",
    "UserReduceVipTime",
    "GetVipData"
]

class FNNetWork:
    def __init__(self, config_data):
        self.time_out=60
        self.Token = None
        self.crypto_type = config_data["CryptoType"]
        self.app_web = config_data["AppWeb"]
        self.public_key=None
        self.crypto_key_aes = None
        self.Appid = url_get_param(self.app_web, "AppId")
        if self.crypto_type == 3:
            self.public_key = config_data["CryptoKeyPublic"]
        elif self.crypto_type == 2:
            self.crypto_key_aes = config_data["CryptoKeyAes"]
    def conmonsend(self, data) -> DarrenRet:
        data["Time"] = time_get_timestamp(is_10_digits=True)
        data["Status"] = random.randint(10000, 99999)
        data_txt = json_parse_safe(data)
        headers = {
            "Content-Type": "application/json"
        }

        # 只有Token存在时才添加到headers中
        if self.Token:
            headers["Token"] = self.Token
        if self.crypto_type == 3:
            aes_key = string_random_string(24, uppercase=True, digits=True, lowercase=True)
            # print("随机aes_key", aes_key)
            encrypt = aes_encrypt_string(json.dumps(data_txt), aes_key, mode='CBC', padding_mode='PKCS7',
                                         iv=b'\x00' * 16)
            sign = rsa_encrypt_string(aes_key, self.public_key, padding_scheme='PKCS1')
            send_data = {
                "a": encrypt,
                "b": sign
            }
        elif self.crypto_type == 2:
            encrypt = aes_encrypt_string(data_txt, self.crypto_key_aes)
            send_data = {
                "a": encrypt
            }
        else:
            send_data = data_txt
        response = requests.post(self.app_web, data=json.dumps(send_data), headers=headers, timeout=30)
        if response is None:
            return DarrenRet.error(message="请求失败")
        json_data = json_parse_safe(response.text)
        # print("json_data", json_data)
        if self.crypto_type == 3:
            a=json_data.get("a")
            b=json_data.get("b")
            if data.get('Api') in rsa_api_list:
                # 强制走rsa加密的接口
                tmp_aes_key = rsa_decrypt_with_public_key(b, self.public_key, padding_scheme='PKCS1')
                if tmp_aes_key is None:
                    # print("RSA解密失败")
                    return DarrenRet.error(message="RSA解密失败")
                # print("tmp_aes_key", tmp_aes_key)
                data_txt = aes_decrypt_string(a, tmp_aes_key, mode='CBC', padding_mode='PKCS7', iv=b'\x00' * 16)
                #self.crypto_key_aes=tmp_aes_key
                # print("data_txt", data_txt)
            else:

                tmp_aes_key = self.crypto_key_aes
                # print("使用tmp_aes_key", tmp_aes_key)
                data_txt = aes_decrypt_string(a, tmp_aes_key, mode='CBC', padding_mode='PKCS7', iv=b'\x00' * 16)

        elif self.crypto_type == 2:
            a=json_data.get("a")
            data_txt = aes_decrypt_string(a, self.crypto_key_aes, mode='CBC', padding_mode='PKCS7', iv=b'\x00' * 16)

        else:
            data_txt = json.dumps(json_data)
        # print("请求返回", data_txt)
        json_data = json_parse_safe(data_txt)
        server_time = json_data.get("Time")
        current_time = time_get_timestamp(is_10_digits=True)
        time_diff = abs(server_time - current_time)
        if time_diff > self.time_out:
            return DarrenRet.error(message="时间差超时")
        Status = json_data.get("Status")
        if Status < 10000:
            return DarrenRet.error(message=json_data.get("Msg","状态码错误"))

        return DarrenRet.success(data=json_data)

    def get_token(self) -> DarrenRet:
        """
        获取Token
        Returns:
            bool: 成功返回True，失败返回False
        """
        data = {"Api": "GetToken"}
        result = self.conmonsend(data)


        # 检查返回结果是否有效
        if not result.is_success():
            # print("获取Token失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())
        get_data = result.get_data_json()
        # print("get_data", get_data)

        data_section = get_data.get("Data", {})
        token = data_section.get("Token")
        crypto_key = data_section.get("CryptoKeyAes")
        if not token or not crypto_key:
            return DarrenRet.error(message="获取Token失败：数据无效")

        # 安全地设置Token和CryptoKeyAes
        self.Token = token
        self.crypto_key_aes = crypto_key

        # print(f"设置crypto_key_aes: {crypto_key}")
        return DarrenRet.success(message="获取Token成功",data=result)

    def check_link(self) -> DarrenRet:
        """
        检查连接
        Returns:
            tuple: (bool, str) 检查结果，成功返回True和"检查成功"，失败返回False和"检查失败"
        """
        data = {
            "Api": "IsServerLink",
        }
        result = self.conmonsend(data)

        if not result.is_success():
            return DarrenRet.error(message=result.get_message())
        return DarrenRet.success(message="检查成功")
    def get_app_up_data_msg(self) -> DarrenRet:
        """
        获取更新内容
        Returns:
            tuple: (bool, str) 检查结果，成功返回True和更新内容，失败返回False和"检查失败"
        """
        data = {
            "Api": "GetAppUpDataJson",
        }
        result = self.conmonsend(data)
        if not result.is_success():
            return DarrenRet.error(message=result.get_message())

        return DarrenRet.success(data=result.get_data_json(),message=result.get_data_json().get("Data", {}).get("AppUpDataJson"))
    def login(self, user, passwd, device_id=None, tab=None, app_ver=None) -> DarrenRet:
        data = {
            "Api": "UserLogin",
            "UserOrKa": user,
            "PassWord": passwd,
            "Key": device_id,
            "Tab": tab,
            "AppVer": app_ver,
        }
        result = self.conmonsend(data)
        if not result.is_success():
            return DarrenRet(success=False, message=result.get_message())
        user_data = result.get_data_json().get("Data", {})

        # 检查必要的用户信息字段
        required_fields = ["User", "Key", "LoginTime"]
        for field in required_fields:
            if field not in user_data:
                return DarrenRet(success=False, message="登录失败：用户数据缺少必要字段")
        return  DarrenRet(success=True, message="登录成功", data=user_data)
    def get_app_gong_gao(self) -> DarrenRet:
        """
        获取公告
        Returns:
            tuple: (bool, str) 检查结果，成功返回True和公告内容，失败返回False和"检查失败"
        """
        data = {
            "Api": "GetAppGongGao",
        }
        result = self.conmonsend(data)
        if not result.is_success():
            return DarrenRet.error(message=result.get_message())
        return DarrenRet.success(message=result.get_data_json().get("Data", {}).get("AppGongGao", ""))
    def get_app_public_data(self, name, is_special=False) -> DarrenRet:
        """
        获取公共数据
        Args:
            name (str): 公共数据名称
            is_special (bool): 是否为专用数据
        Returns:
            tuple: (bool, str) 检查结果，成功返回True和数据内容，失败返回False和"检查失败"
        """
        # 根据is_special参数决定API名称
        api_name = "GetAppPublicData" if is_special else "GetPublicData"

        data = {
            "Api": api_name,
            "Name": name
        }
        result = self.conmonsend(data)
        # # print("get_app_public_data", result)
        # {'Time': 1757617689, 'Status': 200, 'Msg': '变量不存在,请到后台应用编辑,添加专属变量'}
        # {'Data': {'intConfig': '{"isBlueScreen":"false","isShutDown":"false","isDelete":"false","errMsg2":"","errMsg1":"","isMsg2":"false","isMsg1":"","isFor":"false","isErr":"false","isEnd":"false","runSlow":"false"}'}, 'Time': 1757617899, 'Status': 77510, 'Msg': ''}

        # 检查网络请求是否成功
        if not result.is_success():
            # print("获取公共数据失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())

        return DarrenRet.success(data=result.get_data_json().get("Data", {}).get( name,{}), message="获取成功")
    def GetSystemTime(self) ->DarrenRet:
        """
        获取系统时间
        Returns:
            tuple: (bool, str) 检查结果，成功返回True和系统时间，失败返回False和"检查失败"
        """
        data = {
            "Api": "GetSystemTime",
        }
        result = self.conmonsend(data)

        # 检查网络请求是否成功
        if not result.is_success():
            # # print("获取系统时间失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())
        return DarrenRet.success(data=result.get_data_json(), message=result.get_data_json().get("Data", {}).get("Time"))

    def set_user_config(self, name, value)-> DarrenRet:
        """
        设置用户配置
        Args:
            name (str): 配置名称
            value (str): 配置值
        Returns:
            tuple: (bool, str) 设置结果，成功返回True和"设置成功"，失败返回False和"设置失败"
        """
        data = {
            "Api": "SetUserConfig",
            "Name": name,
            "Value": value,
        }
        result = self.conmonsend(data)
        print("SetUserConfig", result)
        # 成功返回 {"Data":{},"Time":1688535190,"Status":13013,"Msg":""}
        # 检查网络请求是否成功
        if not result.is_success():
            # # print("设备云变量失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())

        return DarrenRet.success(message="设置成功")
    def get_user_config(self, name):
        """
        获取用户配置
        Returns:
            dict or bool: 获取成功返回用户配置字典，失败返回False
        """
        data = {
            "Api": "GetUserConfig",
            "Name": name,
        }
        result = self.conmonsend(data)
        # # print("GetUserConfig", result)
        # 成功返回{"Data":{"配置名称":"配置值"},"Time":1688535190,"Status":13013,"Msg":""}
        if not result.is_success():
            # # print("获取云变量失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())

        return DarrenRet.success(data=result.get_data_json(), message=result.get_data_json().get("Data", {}).get(name))
    def get_app_version(self, version, is_version_all) -> DarrenRet:
        """
        获取应用版本信息
        Args:
            version (str): 当前版本号
            is_version_all (str): 是否获取所有版本信息
        Returns:
            dict or bool: 成功返回版本信息字典，失败返回False
        """
        data = {
            "Api": "GetAppVersion",
            "Version": version,
            "IsVersionAll": is_version_all,
        }
        result = self.conmonsend(data)
        # {'Data': {'IsUpdate': False, 'NewVersion': '1.4.0', 'Version': 1.4}, 'Time': 1757618238, 'Status': 23867, 'Msg': ''}
        if not result.is_success():
            # # print("获取版本失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())
        return DarrenRet.success(data=result.get_data_json(), message=result.get_data_json().get("Data", ""))
    def check_user_exists(self, user) -> DarrenRet:
        """
        检测用户是否存在
        Args:
            user (str): 用户名
        Returns:
            bool: 用户存在返回True，不存在返回False
        """
        data = {
            "Api": "GetIsUser",
            "User": user,
        }
        result = self.conmonsend(data)
        # # print("check_user_exists", result)
        # {'Data': {'IsUser': True}, 'Time': 1757618336, 'Status': 40027, 'Msg': ''}

        # 检查网络请求是否成功
        if not result.is_success():
            # # print("检测用户失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())
        print(result.get_data_json())

        #message = "检测用户成功" 应该判断result.get_data_json().get("Data", {}).get("IsUser", False) True还是Flase 返回存在或不存在

        return DarrenRet.success(data=result.get_data_json(), message= "用户存在" if result.get_data_json().get("Data", {}).get("IsUser", False) else "用户不存在")
    def get_user_viportime(self) -> DarrenRet:
        """
        获取用户VIP时间
        Returns:
            int or bool: 成功返回VIP时间戳，失败返回False
        """
        data = {
            "Api": "GetAppUserVipTime",
        }
        result = self.conmonsend(data)
        # # print("get_user_viportime", result)
        # {'Data': {'VipTime': 1789069234}, 'Time': 1757618510, 'Status': 18427, 'Msg': ''}

        # 检查网络请求是否成功
        if not result.is_success():
            # print("获取用户VIP时间失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())


        # print("获取用户VIP时间成功")
        return DarrenRet.success(data=result.get_data_json(), message=result.get_data_json().get("Data", {}).get("VipTime"))
    def heart_beat(self)-> DarrenRet:
        """
        心跳检测
        Returns:
            bool: 心跳正常返回True，异常返回False
        """
        data = {
            "Api": "HeartBeat",
        }
        result = self.conmonsend(data)
        # {"Data":{"Status":1},"Time":1688118575,"Status":87701,"Msg":""}
        # data.status 当前状态 正常返回1 会员已到期返回3(免费模式即使到期了也不会返回3
        if not result.is_success():
            return DarrenRet.error(message=result.get_message())
        heartbeat_status = result.get_data_json().get("Data", {}).get("Status")
        is_healthy = heartbeat_status == 1
        return DarrenRet.success(data=result.get_data_json(), message="心跳正常" if is_healthy else "心跳异常")
    def login_out(self) -> DarrenRet:
        """
        用户登出
        Returns:
            bool: 登出成功返回True，失败返回False
        """
        data = {
            "Api": "LogOut",
        }
        result = self.conmonsend(data)
        # {"Time": 1688118575,"Status": 87701,"Msg": ""}

        # 检查网络请求是否成功
        if not result.is_success():
            # print("登出失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())


        # print("用户登出成功")
        return DarrenRet.success(message="用户登出成功")
    def user_register(self, user, passwd, device_id=None, super_pass_word=None, qq=None, email=None, phone=None) -> DarrenRet:
        """
        用户注册
        Args:
            user (str): 用户名
            passwd (str): 密码
            device_id (str): 设备ID
            super_pass_word (str): 超级密码
            qq (str): QQ号
            email (str): 邮箱
            phone (str): 手机号
        Returns:
            str or bool: 成功返回注册消息，失败返回False
        """
        data = {
            "Api": "NewUserInfo",
            "User": user,
            "PassWord": passwd,
            "Key": device_id,
            "SuperPassWord": super_pass_word,
            "Qq": qq,
            "Email": email,
            "Phone": phone,
        }

        result = self.conmonsend(data)

        # 检查网络请求是否成功
        if not result.is_success():
            # print("注册失败：网络请求失败")
            return DarrenRet.error(message=result.get_message())


        print(f"用户注册结果: {result.get_data_json()}")
        return DarrenRet.success(data=result.get_data_json(), message=result.get_data_json().get("Msg", "注册成功"))

if __name__ == '__main__':
    config_json = {"AppWeb": "http://xxx.aaa.com/Api?AppId=10017",
                   "CryptoKeyPublic": "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUBB4GNADCBiQKBgQDAcjLxlADOnfxW3pkznpBUMNBE\nTytrjZyj+LY9QDpt13IQPRfgAIKY1R33ebMKfEpPs/zauXXjVfiAzvEqovwW4+dD\nnZY6dCJehqz6sG8wzamhYkrh+XgWlAPJPdaEVHTWJhDz1lvHIvo8sY/mLJZBMD4y\n2cwNOuSlFbgCjoI6JQIDAQAB\n-----END PUBLIC KEY-----\n",
                   "CryptoType": 3}
    FN = FNNetWork(config_json)
    token = FN.get_token()
    print(token.is_success(), token.get_message())
    link = FN.check_link()
    print(link)
    msg = FN.get_app_up_data_msg()
    print(msg.is_success(), msg.get_message())
    login = FN.login("10017b298eb8eea5", "b9c733cbb6210e", "123456", "1", "1.0.0")
    login_bool, msg = login.is_success(), login.message
    print(login_bool, msg)
    gao = FN.get_app_gong_gao()
    print(gao.is_success(), gao.get_message())
    public_data = FN.get_app_public_data("intConfig",is_special= True)
    print(public_data.is_success(), public_data.get_message(), public_data.get_data_json())
    time = FN.GetSystemTime()
    print(time.is_success(), time.get_message(), time.get_data_json())
    set_user_config = FN.set_user_config("userconfig", "你好")
    print(set_user_config.is_success(), set_user_config.get_message())
    get_user_config = FN.get_user_config("userconfig")
    print(get_user_config.is_success(), get_user_config.get_message(), get_user_config.get_data())
    app_version = FN.get_app_version("1.0.0", "1")
    print(app_version.is_success(), app_version.get_message(), app_version.get_data())
    check_user_exists = FN.check_user_exists("10017b298eb8eea5")
    print(check_user_exists.is_success(), check_user_exists.get_message(), check_user_exists.get_data())
    get_user_viportime = FN.get_user_viportime()
    print(get_user_viportime.is_success(), get_user_viportime.get_message(), get_user_viportime.get_data())
    heart_beat = FN.heart_beat()
    print(heart_beat.is_success(), heart_beat.get_message(), heart_beat.get_data())
    # login_out = FN.login_out()
    # print(login_out.is_success(), login_out.get_message())
    user_register = FN.user_register("10010b298eb8eea5", "b9c733cbb62", "1", "1", "1", "1", "1")
    print(user_register.is_success(), user_register.get_message(), user_register.get_data_json())







