# HXQ Login MCP Server
# 服务介绍
这是一个基于 Model Context Protocol (MCP) 实现的盒小圈 (HXQ) APP 登录服务接口服务器。它通过标准化的 MCP 协议，为 AI 助手或客户端提供了模拟盒小圈用户登录、检查令牌状态以及刷新令牌的能力。

✨ 核心功能
📱 模拟登录：完整模拟盒小圈 APP 的登录流程，支持密码登录 (login_type="0") 和验证码登录 (login_type="1") 两种方式。

🔐 状态与令牌管理：提供检查用户登录状态 (check_login_status) 和刷新访问令牌 (refresh_token) 的工具。

🛡️ 参数验证与加密：自动验证必填参数，并对密码进行 MD5 加密以匹配后端接口要求。

📚 资源与提示：集成了登录错误码说明文档 (get_login_error_codes) 和使用帮助提示 (login_help_prompt) 等 MCP 资源。

⚙️ 高度可配置：支持完整的设备信息模拟，可用于测试不同场景下的登录行为。

🚀 快速开始
前提条件
确保你的 Python 环境版本 >= 3.8。

安装与运行
克隆或下载此 login_server.py 文件到你的项目目录。

安装必要的依赖包：

bash
pip install mcp[cli] httpx pydantic
以标准输入输出 (stdio) 模式启动 MCP 服务器：

bash
python login_server.py
服务器启动后，它将通过 stdio 等待来自 MCP 客户端（如 Claude Desktop、编排工具等）的连接和指令。

📖 使用指南
主要工具（Tools）
本服务器主要暴露了以下工具供 AI 助手调用：

工具名	描述	必填参数
hxq_login	执行用户登录。	account, login_type (以及对应的 password 或 verify_code)
check_login_status	检查给定用户令牌的有效性。	user_token
refresh_token	使用刷新令牌获取新的访问令牌。	refresh_token
调用 hxq_login 的两种模式示例：

密码登录：

python
# AI助手会这样调用
await hxq_login(
    account="13800138000",
    login_type="0",
    password="your_plain_text_password"
)
验证码登录：

python
# AI助手会这样调用
await hxq_login(
    account="13800138000",
    login_type="1",
    verify_code="123456"
)
API 参考（hxq_login 工具）
这是最核心的工具，其参数结构模拟了真实移动 APP 的请求。

登录参数（Login Parameters）

account (str): 必需。用户账号，通常为手机号码。

login_type (str): 必需。登录类型，"0" 表示密码登录，"1" 表示验证码登录。

password (Optional[str]): 当 login_type="0" 时必需。用户的明文密码，函数内部会进行 MD5 加密。

verify_code (Optional[str]): 当 login_type="1" 时必需。短信验证码。

设备信息参数（Device Info Parameters）
这些参数模拟了 APP 收集的设备信息，大多数为可选，并提供了合理的默认值。

client_type, client_version, user_agent 等参数用于构建请求头。

如需模拟特定设备，可以传入 manufacturer, model, os_version 等。

signature 和 timestamp 如不提供，函数会自动生成。

响应格式（Response Format）
工具返回一个字典 (Dict[str, Any])，格式与盒小圈官方接口基本一致。

成功响应示例：

json
{
  "resultCode": "1",
  "userId": "U123456789",
  "userToken": "eyJhbGciOi...",
  "accessExpiration": "3600",
  "refreshToken": "def...",
  "userName": "张三"
}
错误响应示例：

json
{
  "resultCode": "0",
  "errorCode": "HXQ-G-99993",
  "errorDesc": "账号或密码错误"
}
# 🔧 配置与自定义
```
{
  "mcpServers": {
    "test-mcp3": {
      "command": "uvx",
      "args": ["mini_mcp_server@1.0.0"],
      "env": {
        
      }
    }
  }
}
```
修改 API 端点
代码中硬编码了登录请求的 URL。如需指向测试或特定的后端环境，请修改 hxq_login 函数中 client.post 调用的 URL：

python
# 在 login_server.py 中找到此行并修改
response = await client.post(
    "https://your-new-api-endpoint.com/path/to/login.json",
    # ... 其他参数
)
更新错误码映射
服务器内置了一个常见的错误码映射（error_codes）。如果后端返回了新的错误码，你可以在 hxq_login 函数和 get_login_error_codes 资源中更新此映射。

🐛 故障排除
服务器无法启动：请检查 Python 版本和依赖是否安装正确 (pip list | grep mcp)。

登录返回网络错误：检查目标 API 地址是否可访问，以及网络环境。代码中当前为示例地址，必须修改为有效地址。

提示“PARAM_ERROR”：请确认 login_type 与 password/verify_code 参数匹配且已提供。

MCP 客户端无法连接：请确认你是在支持 MCP 的客户端（如配置了 Claude Desktop）中加载此服务器，并以 stdio 模式运行。

🤝 贡献
欢迎提交 Issue 和 Pull Request 来改进此项目。

Fork 本仓库。

创建功能分支 (git checkout -b feat/amazing-feature)。

提交更改 (git commit -m 'Add amazing feature')。

推送分支 (git push origin feat/amazing-feature)。

提交 Pull Request。

📄 许可证
本项目基于 MIT 许可证开源。详情请查看 LICENSE 文件。

注意：此项目仅为协议模拟与接口测试工具。请遵守盒小圈服务条款，仅将其用于合法、授权的测试目的。请勿将其用于任何恶意或未经授权的活动。
