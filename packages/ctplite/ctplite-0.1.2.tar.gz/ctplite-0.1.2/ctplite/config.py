"""
配置管理模块
提供统一的配置接口
支持token认证和密码认证两种方式
"""

import os
from typing import Optional, Tuple


def _load_dotenv_if_available():
    """尝试加载 .env 文件（如果 python-dotenv 已安装）"""
    try:
        from dotenv import load_dotenv
        # 尝试加载 .env 文件，如果文件不存在也不会报错
        load_dotenv(override=False)  # override=False 表示不覆盖已存在的环境变量
    except ImportError:
        # python-dotenv 未安装，忽略
        pass


class Config:
    """配置类"""
    
    def __init__(self):
        """初始化配置，从环境变量读取"""
        # 在读取环境变量之前，先尝试加载 .env 文件
        _load_dotenv_if_available()
        
        # gRPC服务器配置
        self.GRPC_HOST: str = os.getenv('CTPLITE_GRPC_HOST', 'localhost')
        self.GRPC_PORT: int = int(os.getenv('CTPLITE_GRPC_PORT', '50051'))
        
        # REST服务器配置
        self.REST_HOST: str = os.getenv('CTPLITE_REST_HOST', 'localhost')
        self.REST_PORT: int = int(os.getenv('CTPLITE_REST_PORT', '8080'))
        
        # CTP认证信息（用于登录获取token）
        self.CTP_BROKER_ID: Optional[str] = os.getenv('CTP_BROKER_ID')
        self.CTP_USER_ID: Optional[str] = os.getenv('CTP_USER_ID')
        self.CTP_PASSWORD: Optional[str] = os.getenv('CTP_PASSWORD')
        self.CTP_APP_ID: Optional[str] = os.getenv('CTP_APP_ID')
        self.CTP_AUTH_CODE: Optional[str] = os.getenv('CTP_AUTH_CODE')
        self.CTP_INVESTOR_ID: Optional[str] = os.getenv('CTP_INVESTOR_ID')
        
        # Token认证（优先使用token，如果设置了token则不需要密码）
        self.TOKEN: Optional[str] = os.getenv('CTPLITE_TOKEN')
    
    @property
    def grpc_address(self) -> str:
        """gRPC服务器地址"""
        return f"{self.GRPC_HOST}:{self.GRPC_PORT}"
    
    @property
    def rest_base_url(self) -> str:
        """REST服务器基础URL"""
        return f"http://{self.REST_HOST}:{self.REST_PORT}"
    
    def get_auth_request(self, use_token: bool = True) -> dict:
        """
        获取认证请求字典（用于REST API）
        
        Args:
            use_token: 如果为True且TOKEN已设置，则使用token认证；否则使用密码认证
        
        Returns:
            认证信息字典
        """
        auth = {}
        
        # 优先使用token认证
        if use_token and self.TOKEN:
            auth['token'] = self.TOKEN
            # token认证时，broker_id和user_id可选（服务器可以从token中获取）
            if self.CTP_BROKER_ID:
                auth['broker_id'] = self.CTP_BROKER_ID
            if self.CTP_USER_ID:
                auth['user_id'] = self.CTP_USER_ID
        else:
            # 使用密码认证（向后兼容）
            if not self.CTP_BROKER_ID or not self.CTP_USER_ID or not self.CTP_PASSWORD:
                raise ValueError(
                    "缺少必需的CTP认证信息: CTP_BROKER_ID, CTP_USER_ID, CTP_PASSWORD "
                    "(请设置环境变量，或使用token认证)"
                )
            
            auth['broker_id'] = self.CTP_BROKER_ID
            auth['user_id'] = self.CTP_USER_ID
            auth['password'] = self.CTP_PASSWORD
            
            if self.CTP_APP_ID:
                auth['app_id'] = self.CTP_APP_ID
            if self.CTP_AUTH_CODE:
                auth['auth_code'] = self.CTP_AUTH_CODE
        
        if self.CTP_INVESTOR_ID:
            auth['investor_id'] = self.CTP_INVESTOR_ID
        
        return auth
    
    def set_token(self, token: str):
        """设置token（用于登录后保存token）"""
        self.TOKEN = token
        # 可选：更新环境变量（但不会影响当前进程）
        os.environ['CTPLITE_TOKEN'] = token
    
    def clear_token(self):
        """清除token（用于登出）"""
        self.TOKEN = None
        # 可选：清除环境变量
        if 'CTPLITE_TOKEN' in os.environ:
            del os.environ['CTPLITE_TOKEN']
    
    def validate(self, require_password: bool = False) -> Tuple[bool, Optional[str]]:
        """
        验证配置是否完整
        
        Args:
            require_password: 如果为True，要求必须设置密码（即使有token）
        
        Returns:
            (是否有效, 错误消息)
        """
        # 如果设置了token，不需要密码
        if self.TOKEN and not require_password:
            return True, None
        
        # 否则需要密码认证信息
        if not self.CTP_BROKER_ID:
            return False, "缺少CTP_BROKER_ID配置（请设置环境变量CTP_BROKER_ID）"
        if not self.CTP_USER_ID:
            return False, "缺少CTP_USER_ID配置（请设置环境变量CTP_USER_ID）"
        if not self.CTP_PASSWORD:
            return False, "缺少CTP_PASSWORD配置（请设置环境变量CTP_PASSWORD，或使用token认证）"
        return True, None


# 全局配置实例
config = Config()

