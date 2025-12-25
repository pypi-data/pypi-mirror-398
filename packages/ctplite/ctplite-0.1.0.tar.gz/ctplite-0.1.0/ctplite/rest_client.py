"""
REST客户端
用于连接pq-futures项目的REST服务
"""

import requests
from typing import Optional, Dict, Any, List

from .config import config


class RestClient:
    """REST客户端类"""
    
    def __init__(self, base_url: Optional[str] = None):
        """
        初始化REST客户端
        
        Args:
            base_url: REST服务器基础URL，默认使用config中的URL
        """
        self.base_url = base_url or config.rest_base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.token = config.TOKEN  # 当前token
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> requests.Response:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法（GET, POST等）
            endpoint: API端点路径
            data: 请求体数据（字典）
            params: URL参数
            
        Returns:
            Response对象
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            return response
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"请求失败: {e}")
    
    def login(self, use_token: bool = True) -> Dict[str, Any]:
        """
        登录并获取token
        
        Args:
            use_token: 如果为True且已有token，则直接返回成功（不重复登录）
        
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        # 如果已有token且use_token为True，跳过登录
        if use_token and self.token:
            return {
                'success': True,
                'code': 0,
                'msg': 'Already logged in',
                'data': {'token': self.token}
            }
        
        # 验证配置
        ok, msg = config.validate(require_password=True)
        if not ok:
            raise ValueError(f"配置错误: {msg}")
        
        auth = config.get_auth_request(use_token=False)
        data = {'auth': auth}
        
        response = self._request('POST', '/api/v1/auth/login', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"登录失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        # 保存token
        if 'data' in result and 'token' in result['data']:
            self.token = result['data']['token']
            config.set_token(self.token)
        
        return result
    
    def logout(self) -> Dict[str, Any]:
        """
        登出并清除token
        
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        if not self.token:
            return {
                'success': True,
                'code': 0,
                'msg': 'Not logged in',
                'data': {}
            }
        
        data = {'auth': {'token': self.token}}
        
        response = self._request('POST', '/api/v1/auth/logout', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 清除token
        self.token = None
        config.clear_token()
        
        return result
    
    def subscribe_market_data(
        self, 
        symbols: List[str], 
        kafka_topic: Optional[str] = None,
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        订阅行情数据
        
        Args:
            symbols: 合约代码列表
            kafka_topic: Kafka topic（可选，不指定则使用环境变量KAFKA_TOPIC或默认值"mkt_ctp_ticks"）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {
            'symbols': symbols,
            'auth': auth
        }
        
        # 如果指定了kafka_topic，添加到请求中
        if kafka_topic:
            data['kafka_topic'] = kafka_topic
        
        response = self._request('POST', '/api/v1/market/subscribe', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"订阅失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def unsubscribe_market_data(self, symbols: List[str], use_token: bool = True) -> Dict[str, Any]:
        """
        取消订阅行情数据
        
        Args:
            symbols: 要取消订阅的合约代码列表
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {
            'symbols': symbols,
            'auth': auth
        }
        
        response = self._request('POST', '/api/v1/market/unsubscribe', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"取消订阅失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def place_order(
        self,
        symbol: str,
        exchange: str,
        direction: str,  # 'BUY' or 'SELL'
        offset: str,     # 'OPEN', 'CLOSE', 'CLOSE_TODAY', 'CLOSE_YESTERDAY'
        price: float,
        volume: int,
        order_type: str = 'LIMIT',  # 'LIMIT', 'MARKET', 'FAK', 'FOK'
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        下单
        
        Args:
            symbol: 合约代码
            exchange: 交易所代码
            direction: 买卖方向
            offset: 开平标志
            price: 价格（市价单为0）
            volume: 数量
            order_type: 订单类型
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {
            'symbol': symbol,
            'exchange': exchange,
            'direction': direction,
            'offset': offset,
            'price': price,
            'volume': volume,
            'order_type': order_type,
            'auth': auth
        }
        
        response = self._request('POST', '/api/v1/trading/order', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误（即使HTTP状态码是200，也可能有业务错误）
        if not result.get('success', False):
            error_msg = f"下单失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def cancel_order(
        self,
        order_id: str,
        symbol: str,
        exchange: str,
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        撤单
        
        Args:
            order_id: 订单编号
            symbol: 合约代码
            exchange: 交易所代码
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {
            'order_id': order_id,
            'symbol': symbol,
            'exchange': exchange,
            'auth': auth
        }
        
        response = self._request('POST', '/api/v1/trading/cancel', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"撤单失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_position(
        self,
        symbol: str = "",
        exchange: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询持仓
        
        Args:
            symbol: 合约代码（空字符串表示查询所有持仓）
            exchange: 交易所代码（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/position', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询持仓失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_trading_account(self, use_token: bool = True) -> Dict[str, Any]:
        """
        查询资金账户
        
        Args:
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {**auth}  # 将认证信息作为URL参数
        
        response = self._request('GET', '/api/v1/trading/account', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询资金账户失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_order(
        self,
        symbol: str = "",
        exchange: str = "",
        order_sys_id: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询订单
        
        Args:
            symbol: 合约代码（空字符串表示查询所有订单）
            exchange: 交易所代码（可选）
            order_sys_id: 系统订单号（可选，CTP API仅支持通过系统订单号查询）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            'order_sys_id': order_sys_id,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/order/query', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询订单失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_trade(
        self,
        symbol: str = "",
        exchange: str = "",
        trade_id: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询成交
        
        Args:
            symbol: 合约代码（空字符串表示查询所有成交）
            exchange: 交易所代码（可选）
            trade_id: 成交编号（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            'trade_id': trade_id,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/trade/query', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询成交失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def confirm_settlement_info(self, use_token: bool = True) -> Dict[str, Any]:
        """
        结算确认
        
        Args:
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {'auth': auth}
        
        response = self._request('POST', '/api/v1/trading/settlement/confirm', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"结算确认失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_instrument(
        self,
        symbol: str = "",
        exchange: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询合约信息
        
        Args:
            symbol: 合约代码（空字符串表示查询所有合约）
            exchange: 交易所代码（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/instrument', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询合约信息失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_instrument_margin_rate(
        self,
        symbol: str = "",
        exchange: str = "",
        hedge_flag: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询合约保证金率
        
        Args:
            symbol: 合约代码（空字符串表示查询所有）
            exchange: 交易所代码（可选）
            hedge_flag: 投机套保标志（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            **auth  # 将认证信息作为URL参数
        }
        if hedge_flag:
            params['hedge_flag'] = hedge_flag
        
        response = self._request('GET', '/api/v1/trading/instrument/margin-rate', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询保证金率失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_instrument_commission_rate(
        self,
        symbol: str = "",
        exchange: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询合约手续费率
        
        Args:
            symbol: 合约代码（空字符串表示查询所有）
            exchange: 交易所代码（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/instrument/commission-rate', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询手续费率失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_settlement_info(
        self,
        trading_day: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询结算信息
        
        Args:
            trading_day: 交易日（空字符串表示查询所有）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'trading_day': trading_day,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/settlement/info', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询结算信息失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def trading_logout(self, use_token: bool = True) -> Dict[str, Any]:
        """
        CTP交易登出
        
        Args:
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        data = {'auth': auth}
        
        response = self._request('POST', '/api/v1/trading/logout', data=data)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"交易登出失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_max_order_volume(
        self,
        symbol: str,
        exchange: str,
        direction: str,  # 'BUY' or 'SELL'
        offset: str,     # 'OPEN', 'CLOSE', 'CLOSE_TODAY', 'CLOSE_YESTERDAY'
        hedge_flag: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询最大报单量
        
        Args:
            symbol: 合约代码（必需）
            exchange: 交易所代码（必需）
            direction: 买卖方向（'BUY' or 'SELL'）
            offset: 开平标志（'OPEN', 'CLOSE', 'CLOSE_TODAY', 'CLOSE_YESTERDAY'）
            hedge_flag: 投机套保标志（可选）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'symbol': symbol,
            'exchange': exchange,
            'direction': direction,
            'offset': offset,
            **auth  # 将认证信息作为URL参数
        }
        if hedge_flag:
            params['hedge_flag'] = hedge_flag
        
        response = self._request('GET', '/api/v1/trading/max-order-volume', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询最大报单量失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_exchange(
        self,
        exchange_id: str = "",
        use_token: bool = True
    ) -> Dict[str, Any]:
        """
        查询交易所
        
        Args:
            exchange_id: 交易所代码（空字符串表示查询所有）
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {
            'exchange_id': exchange_id,
            **auth  # 将认证信息作为URL参数
        }
        
        response = self._request('GET', '/api/v1/trading/exchange', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查错误
        if not result.get('success', False):
            error_msg = f"查询交易所失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result
    
    def query_investor(self, use_token: bool = True) -> Dict[str, Any]:
        """
        查询投资者
        
        Args:
            use_token: 是否使用token认证（如果已登录）
            
        Returns:
            响应数据字典（标准格式：code, msg, success, time, data）
        """
        auth = config.get_auth_request(use_token=use_token)
        params = {**auth}  # 将认证信息作为URL参数
        
        response = self._request('GET', '/api/v1/trading/investor', params=params)
        response.raise_for_status()
        result = response.json()
        
        # 检查业务错误
        if not result.get('success', False):
            error_msg = f"查询投资者失败: {result.get('msg', '未知错误')} (code: {result.get('code', 'N/A')})"
            raise requests.exceptions.HTTPError(error_msg, response=response)
        
        return result

