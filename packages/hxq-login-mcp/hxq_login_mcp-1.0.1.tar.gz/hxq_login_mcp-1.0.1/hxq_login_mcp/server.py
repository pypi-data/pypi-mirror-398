import json
from typing import Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
import httpx
from pydantic import BaseModel
import hashlib


# 创建MCP实例
mcp = FastMCP("HXQ Login API")

def md5_encrypt(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()



# 定义请求参数模型
class LoginRequest(BaseModel):
    account: str
    password: Optional[str] = None
    verifyCode: Optional[str] = None
    loginType: str  # "0" 或 "1"


class DeviceInfo(BaseModel):
    appSource: str = "hxq"
    clientType: str
    clientVersion: str
    channel: str
    imei: str
    manufacturer: str
    model: str
    osVersion: str
    deviceId: str
    osImage: str
    storageSpace: str
    wifiSsid: str
    systemLanguage: str = "zh"
    providersName: str
    cpuArchitecture: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    pushId: Optional[str] = None
    registerId: Optional[str] = None
    signature: str
    timestamp: str
    userAgent: str


class VersionConfig(BaseModel):
    content: str
    apkUrl: str
    fileSize: str
    fileMD5: str
    force: str
    version: str


class AreaUpdateInfo(BaseModel):
    moduleKey: str
    moduleId: str
    updateId: str


class BottomConfig(BaseModel):
    clickImgUrl: str
    unclickImgUrl: str
    buttonName: str
    skipUrl: str


class LoginResponse(BaseModel):
    resultCode: str
    errorCode: Optional[str] = None
    errorDesc: Optional[str] = None
    userId: Optional[str] = None
    memberId: Optional[int] = None
    mchtNo: Optional[str] = None
    mchtStatus: Optional[str] = None
    selfRegisterUrl: Optional[str] = None
    userToken: Optional[str] = None
    accessExpiration: Optional[str] = None
    refreshToken: Optional[str] = None
    kindName: Optional[str] = None
    source: Optional[str] = None
    channelKind: Optional[str] = None
    account: Optional[str] = None
    isMainMerchant: Optional[str] = None
    userName: Optional[str] = None
    userPrimary: Optional[str] = None
    name: Optional[str] = None
    brhNo: Optional[str] = None
    mchtSingleName: Optional[str] = None
    mchtAreaNo: Optional[str] = None
    merchantType: Optional[str] = None
    activeState: Optional[str] = None
    legalPersonName: Optional[str] = None
    boxList: Optional[str] = None
    logoUrl: Optional[str] = None
    spStatus: Optional[str] = None
    cbxSource: Optional[str] = None
    ipCountry: Optional[str] = None
    cancelAccountName: Optional[str] = None
    cancelAccountUrl: Optional[str] = None
    mchtNum: Optional[int] = None
    accountValidateStatus: Optional[str] = None
    isShowVerifyCode: Optional[str] = None
    needWeakPwdCheck: Optional[str] = None
    versionConfig: Optional[VersionConfig] = None
    areaUpdateInfosList: Optional[List[AreaUpdateInfo]] = None
    bottomConfigList: Optional[List[BottomConfig]] = None


@mcp.tool()
async def hxq_login(
        account: str,
        login_type: str,
        password: Optional[str] = None,
        verify_code: Optional[str] = None,
        # 设备信息参数
        client_type: str = "android",
        client_version: str = "1.0.0",
        channel: str = "official",
        imei: str = "",
        manufacturer: str = "",
        model: str = "",
        os_version: str = "",
        device_id: str = "",
        os_image: str = "",
        storage_space: str = "",
        wifi_ssid: str = "",
        providers_name: str = "",
        cpu_architecture: str = "",
        latitude: Optional[str] = None,
        longitude: Optional[str] = None,
        push_id: Optional[str] = None,
        register_id: Optional[str] = None,
        signature: Optional[str] = None,
        timestamp: Optional[str] = None,
        user_agent: str = "HXQ App"
) -> Dict[str, Any]:
    """
    盒小圈APP登录接口

    Args:
        account: 用户账号（手机号码）
        login_type: 登录类型，"0"=密码登录，"1"=验证码登录
        password: 密码（密码和验证码必传一个）
        verify_code: 验证码（密码和验证码必传一个）
        client_type: 客户端类型
        client_version: 客户端版本
        channel: 客户端渠道
        imei: 移动设备ID
        manufacturer: 移动设备制造商
        model: 移动设备型号
        os_version: 移动设备系统版本
        device_id: 设备ID
        os_image: 屏幕分辨率
        storage_space: 内存大小
        wifi_ssid: WiFi名称
        providers_name: 移动运营商
        cpu_architecture: 设备CPU架构
        latitude: 登录经度
        longitude: 登录纬度
        push_id: 个推deviceId
        register_id: 个推cid
        signature: 加密串
        timestamp: 时间戳
        user_agent: 用户代理

    Returns:
        登录响应数据，包含用户信息和token等
    """

    # 验证必填参数
    if login_type == "0" and not password:
        return {"resultCode": "0", "errorCode": "PARAM_ERROR", "errorDesc": "密码登录必须提供密码"}
    if login_type == "1" and not verify_code:
        return {"resultCode": "0", "errorCode": "PARAM_ERROR", "errorDesc": "验证码登录必须提供验证码"}

    # 准备请求数据

    encrypted_password = None
    if login_type == "0" and password:
        encrypted_password = md5_encrypt(password)

    login_data = LoginRequest(
        account=account,
        password=encrypted_password,
        verifyCode=verify_code,
        loginType=login_type
    )

    # 准备设备信息
    if not timestamp:
        import time
        timestamp = str(int(time.time()))

    device_info = DeviceInfo(
        clientType=client_type,
        clientVersion=client_version,
        channel=channel,
        imei=imei,
        manufacturer=manufacturer,
        model=model,
        osVersion=os_version,
        deviceId=device_id,
        osImage=os_image,
        storageSpace=storage_space,
        wifiSsid=wifi_ssid,
        providersName=providers_name,
        cpuArchitecture=cpu_architecture,
        latitude=latitude,
        longitude=longitude,
        pushId=push_id,
        registerId=register_id,
        signature=signature or f"sign_{timestamp}",
        timestamp=timestamp,
        userAgent=user_agent
    )

    # 构建请求头
    headers = {
        "Content-Type": "application/json",

        "appSource": "hxq",
        "clientType": "android",
        "clientVersion": "1.2.4",
        "channel": "official",

        "imei": "866174030123456",
        "manufacturer": "Xiaomi",
        "model": "M2102J2SC",
        "osVersion": "Android 12",
        "deviceId": "a3f1c8e9b2d44a1c",

        "osImage": "2400*1080",
        "storageSpace": "128GB",
        "wifiSsid": "ChinaNet-5G",

        "systemLanguage": "zh",
        "providersName": "China Mobile",
        "cpuArchitecture": "arm64-v8a",

        "signature": device_info.signature,
        "timestamp": device_info.timestamp,

        "userAgent": "HXQ/1.2.4 (Android 12; Xiaomi M2102J2SC)"
    }


    # 添加可选的头信息
    if device_info.latitude:
        headers["latitude"] = device_info.latitude
    if device_info.longitude:
        headers["longitude"] = device_info.longitude
    if device_info.pushId:
        headers["pushId"] = device_info.pushId
    if device_info.registerId:
        headers["registerId"] = device_info.registerId

    # 构建请求体
    request_body = {
        "requestBody": json.dumps(login_data.dict(exclude_none=True))
    }

    try:
        # 发送登录请求
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://ccasheasy.iboxpay.com/hxq-gateway/hxqBusiness/app/v104/login.json",  # 替换为实际API地址
                headers=headers,
                json=request_body,
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()

                # 处理错误码
                error_codes = {
                    "HXQ-G-99992": "弱密码",
                    "HXQ-G-99993": "账号或密码错误",
                    "HXQ-G-99994": "账号锁定"
                }

                if result.get("errorCode") in error_codes:
                    result["errorDesc"] = error_codes[result["errorCode"]]

                return result
            else:
                return {
                    "resultCode": "0",
                    "errorCode": f"HTTP_{response.status_code}",
                    "errorDesc": f"请求失败，状态码: {response.status_code}"
                }

    except Exception as e:
        return {
            "resultCode": "0",
            "errorCode": "REQUEST_ERROR",
            "errorDesc": f"请求异常: {str(e)}"
        }


@mcp.tool()
async def check_login_status(user_token: str) -> Dict[str, Any]:
    """
    检查用户登录状态

    Args:
        user_token: 用户token

    Returns:
        登录状态信息
    """
    # 这里可以实现token验证逻辑
    return {
        "resultCode": "1",
        "isValid": True,
        "message": "Token有效"
    }


@mcp.tool()
async def refresh_token(refresh_token: str) -> Dict[str, Any]:
    """
    刷新用户token

    Args:
        refresh_token: 刷新token

    Returns:
        新的token信息
    """
    # 这里可以实现token刷新逻辑
    return {
        "resultCode": "1",
        "userToken": "new_token_123456",
        "accessExpiration": "3600",
        "refreshToken": "new_refresh_token_123456"
    }


# 资源定义
@mcp.resource("config://login_error_codes")
async def get_login_error_codes() -> str:
    """获取登录错误码说明"""
    error_codes = {
        "HXQ-G-99992": "弱密码",
        "HXQ-G-99993": "账号或密码错误",
        "HXQ-G-99994": "账号锁定"
    }
    return json.dumps(error_codes, ensure_ascii=False, indent=2)


# 提示模板
@mcp.prompt()
async def login_help_prompt() -> str:
    """登录帮助提示"""
    return """盒小圈APP登录接口使用说明：

登录类型：
- 密码登录：login_type = "0"，需要提供password参数
- 验证码登录：login_type = "1"，需要提供verify_code参数

常见错误码：
- HXQ-G-99992: 弱密码，需要修改密码
- HXQ-G-99993: 账号或密码错误
- HXQ-G-99994: 账号锁定

使用示例：
await hxq_login(account="13800138000", login_type="0", password="123456")
"""


if __name__ == "__main__":
    # 运行MCP服务器
    mcp.run(transport='stdio')
