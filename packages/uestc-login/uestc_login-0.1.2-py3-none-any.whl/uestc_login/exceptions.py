# exceptions.py

class LoginError(Exception):
    """登录过程中发生的错误的基类"""
    pass

class CredentialError(LoginError):
    """用户名或密码不正确时引发的异常"""
    pass

class NetworkError(LoginError):
    """网络请求失败时（如连接超时）引发的异常"""
    pass

class ExtractionError(LoginError):
    """无法从登录页面提取必要信息（如 salt 或 execution）时引发的异常"""
    pass

class CookieError(LoginError):
    """Cookie 无效或验证失败时引发的异常"""
    pass