"""
gRPC客户端
用于连接pq-futures项目的gRPC服务
"""

import grpc
import threading
import queue
from typing import Optional, Iterator, List

from .config import config
from .proto import common_pb2
from .proto import market_data_pb2
from .proto import market_data_pb2_grpc
from .proto import trading_pb2
from .proto import trading_pb2_grpc

# 尝试导入auth相关代码（如果已生成）
try:
    from .proto import auth_pb2
    from .proto import auth_pb2_grpc
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False


class GrpcClient:
    """gRPC客户端类"""
    
    def __init__(self, address: Optional[str] = None):
        """
        初始化gRPC客户端
        
        Args:
            address: gRPC服务器地址，默认使用config中的地址
        """
        self.address = address or config.grpc_address
        self.channel = None
        self.md_stub = None
        self.td_stub = None
        self.auth_stub = None  # 认证服务stub
        self.md_stream = None  # 保存市场数据流引用，用于取消
        self.td_stream = None  # 保存交易数据流引用，用于取消
        self.token = config.TOKEN  # 当前token
        self._running = True  # 内部运行标志
    
    def connect(self):
        """连接到gRPC服务器"""
        try:
            self.channel = grpc.insecure_channel(self.address)
            grpc.channel_ready_future(self.channel).result(timeout=5)
            
            # 创建服务stub
            self.md_stub = market_data_pb2_grpc.MarketDataServiceStub(self.channel)
            self.td_stub = trading_pb2_grpc.TradingServiceStub(self.channel)
            
            # 创建认证服务stub（如果可用）
            if AUTH_AVAILABLE:
                self.auth_stub = auth_pb2_grpc.AuthServiceStub(self.channel)
            
            return True
        except grpc.FutureTimeoutError:
            raise ConnectionError(f"连接超时: 无法连接到 {self.address}")
        except Exception as e:
            raise ConnectionError(f"连接失败: {e}")
    
    def close(self):
        """关闭连接"""
        self._running = False
        
        # 取消活跃的流
        if self.md_stream:
            try:
                self.md_stream.cancel()
            except:
                pass
            self.md_stream = None
        
        if self.td_stream:
            try:
                self.td_stream.cancel()
            except:
                pass
            self.td_stream = None
        
        if self.channel:
            self.channel.close()
    
    def create_auth_request(self, use_token: bool = True) -> common_pb2.AuthRequest:
        """
        创建认证请求
        
        Args:
            use_token: 如果为True且token已设置，则使用token认证；否则使用密码认证
        
        Returns:
            AuthRequest对象
        """
        auth = common_pb2.AuthRequest()
        
        # 优先使用token认证
        if use_token and self.token:
            auth.token = self.token
            # token认证时，broker_id和user_id可选
            if config.CTP_BROKER_ID:
                auth.broker_id = config.CTP_BROKER_ID
            if config.CTP_USER_ID:
                auth.user_id = config.CTP_USER_ID
        else:
            # 使用密码认证
            if not config.CTP_BROKER_ID or not config.CTP_USER_ID or not config.CTP_PASSWORD:
                raise ValueError(
                    "缺少必需的CTP认证信息: CTP_BROKER_ID, CTP_USER_ID, CTP_PASSWORD "
                    "(请设置环境变量，或使用token认证)"
                )
            
            auth.broker_id = config.CTP_BROKER_ID
            auth.user_id = config.CTP_USER_ID
            auth.password = config.CTP_PASSWORD
            if config.CTP_APP_ID:
                auth.app_id = config.CTP_APP_ID
            if config.CTP_AUTH_CODE:
                auth.auth_code = config.CTP_AUTH_CODE
        
        if config.CTP_INVESTOR_ID:
            auth.investor_id = config.CTP_INVESTOR_ID
        
        return auth
    
    def login(self) -> bool:
        """
        登录并获取token
        
        Returns:
            是否登录成功
        """
        if not AUTH_AVAILABLE:
            raise RuntimeError("认证服务不可用，请确保auth_pb2和auth_pb2_grpc已生成")
        
        if not self.auth_stub:
            raise RuntimeError("未连接到服务器")
        
        # 验证配置
        ok, msg = config.validate(require_password=True)
        if not ok:
            raise ValueError(f"配置错误: {msg}")
        
        try:
            request = auth_pb2.LoginRequest()
            request.broker_id = config.CTP_BROKER_ID
            request.user_id = config.CTP_USER_ID
            request.password = config.CTP_PASSWORD
            if config.CTP_APP_ID:
                request.app_id = config.CTP_APP_ID
            if config.CTP_AUTH_CODE:
                request.auth_code = config.CTP_AUTH_CODE
            if config.CTP_INVESTOR_ID:
                request.investor_id = config.CTP_INVESTOR_ID
            
            response = self.auth_stub.Login(request)
            
            if response.error_code == 0:
                self.token = response.token
                config.set_token(response.token)
                return True
            else:
                raise RuntimeError(
                    f"登录失败: {response.error_message} (错误码: {response.error_code})"
                )
                
        except grpc.RpcError as e:
            raise ConnectionError(f"登录失败: {e.code()} - {e.details()}")
        except Exception as e:
            if isinstance(e, (RuntimeError, ConnectionError)):
                raise
            raise RuntimeError(f"登录出错: {e}")
    
    def logout(self) -> bool:
        """
        登出并清除token
        
        Returns:
            是否登出成功
        """
        if not AUTH_AVAILABLE:
            raise RuntimeError("认证服务不可用")
        
        if not self.auth_stub:
            raise RuntimeError("未连接到服务器")
        
        if not self.token:
            return True  # 未登录，无需登出
        
        try:
            request = auth_pb2.LogoutRequest()
            request.token = self.token
            
            response = self.auth_stub.Logout(request)
            
            if response.error_code == 0:
                self.token = None
                config.clear_token()
                return True
            else:
                raise RuntimeError(
                    f"登出失败: {response.error_message} (错误码: {response.error_code})"
                )
                
        except grpc.RpcError as e:
            raise ConnectionError(f"登出失败: {e.code()} - {e.details()}")
        except Exception as e:
            if isinstance(e, (RuntimeError, ConnectionError)):
                raise
            raise RuntimeError(f"登出出错: {e}")
    
    def refresh_token(self) -> bool:
        """
        刷新token（延长过期时间）
        
        Returns:
            是否刷新成功
        """
        if not AUTH_AVAILABLE:
            raise RuntimeError("认证服务不可用")
        
        if not self.auth_stub:
            raise RuntimeError("未连接到服务器")
        
        if not self.token:
            raise RuntimeError("未登录，请先登录")
        
        try:
            request = auth_pb2.RefreshTokenRequest()
            request.token = self.token
            
            response = self.auth_stub.RefreshToken(request)
            
            if response.error_code == 0:
                return True
            else:
                raise RuntimeError(
                    f"Token刷新失败: {response.error_message} (错误码: {response.error_code})"
                )
                
        except grpc.RpcError as e:
            raise ConnectionError(f"Token刷新失败: {e.code()} - {e.details()}")
        except Exception as e:
            if isinstance(e, (RuntimeError, ConnectionError)):
                raise
            raise RuntimeError(f"Token刷新出错: {e}")
    
    def subscribe_market_data(self, symbols: List[str]) -> Iterator[market_data_pb2.MarketDataStream]:
        """
        订阅行情数据（流式）
        
        Args:
            symbols: 合约代码列表
            
        Yields:
            MarketDataStream消息
        """
        if not self.md_stub:
            raise RuntimeError("未连接到服务器")
        
        request = market_data_pb2.SubscribeRequest()
        request.symbols.extend(symbols)
        request.auth.CopyFrom(self.create_auth_request())
        
        # 使用队列和线程来处理流式数据，以便能够响应取消信号
        data_queue = queue.Queue()
        exception_queue = queue.Queue()
        stream_done = threading.Event()
        stream_ready = threading.Event()
        
        def stream_reader():
            """在单独线程中读取流数据"""
            try:
                self.md_stream = self.md_stub.SubscribeMarketData(request)
                stream_ready.set()  # 标记流已创建
                for response in self.md_stream:
                    if not self._running:
                        # 如果 _running 变为 False，停止读取
                        break
                    data_queue.put(response)
                stream_done.set()
            except grpc.RpcError as e:
                # 如果是取消操作，这是正常的
                if e.code() != grpc.StatusCode.CANCELLED:
                    exception_queue.put(e)
                stream_done.set()
            except Exception as e:
                exception_queue.put(e)
                stream_done.set()
        
        # 启动读取线程
        reader_thread = threading.Thread(target=stream_reader, daemon=True)
        reader_thread.start()
        
        # 等待流创建完成
        stream_ready.wait(timeout=5)
        
        try:
            while self._running and not stream_done.is_set():
                try:
                    # 使用超时以便定期检查 _running 标志
                    response = data_queue.get(timeout=0.1)
                    yield response
                except queue.Empty:
                    # 检查是否有异常
                    if not exception_queue.empty():
                        e = exception_queue.get()
                        raise e
                    continue
            
            # 如果因为 _running=False 退出，取消流
            if not self._running and self.md_stream:
                try:
                    self.md_stream.cancel()
                except:
                    pass
                    
        except grpc.RpcError as e:
            # 取消操作是正常的，不需要抛出异常
            if e.code() != grpc.StatusCode.CANCELLED:
                raise
        except Exception as e:
            raise
    
    def place_order(
        self,
        symbol: str,
        exchange: str,
        direction: trading_pb2.Direction,
        offset: trading_pb2.Offset,
        price: float,
        volume: int,
        order_type: trading_pb2.OrderType = trading_pb2.OrderType.LIMIT
    ) -> trading_pb2.OrderResponse:
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
            
        Returns:
            OrderResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.OrderRequest()
        request.symbol = symbol
        request.exchange = exchange
        request.direction = direction
        request.offset = offset
        request.price = price
        request.volume = volume
        request.order_type = order_type
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.PlaceOrder(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"下单失败: {e.code()} - {e.details()}")
    
    def cancel_order(
        self,
        order_id: str,
        symbol: str,
        exchange: str
    ) -> trading_pb2.OrderResponse:
        """
        撤单
        
        Args:
            order_id: 订单编号
            symbol: 合约代码
            exchange: 交易所代码
            
        Returns:
            OrderResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.CancelRequest()
        request.order_id = order_id
        request.symbol = symbol
        request.exchange = exchange
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.CancelOrder(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"撤单失败: {e.code()} - {e.details()}")
    
    def query_position(
        self,
        symbol: str = "",
        exchange: str = ""
    ) -> trading_pb2.PositionResponse:
        """
        查询持仓
        
        Args:
            symbol: 合约代码（空字符串表示查询所有持仓）
            exchange: 交易所代码（可选）
            
        Returns:
            PositionResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.PositionQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryPosition(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询持仓失败: {e.code()} - {e.details()}")
    
    def stream_order_status(self) -> Iterator[trading_pb2.OrderStatusUpdate]:
        """
        流式接收订单状态更新
        
        Yields:
            OrderStatusUpdate消息
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = self.create_auth_request()
        
        # 使用队列和线程来处理流式数据，以便能够响应取消信号
        data_queue = queue.Queue()
        exception_queue = queue.Queue()
        stream_done = threading.Event()
        stream_ready = threading.Event()
        
        def stream_reader():
            """在单独线程中读取流数据"""
            try:
                self.td_stream = self.td_stub.StreamOrderStatus(request)
                stream_ready.set()  # 标记流已创建
                for update in self.td_stream:
                    if not self._running:
                        # 如果 _running 变为 False，停止读取
                        break
                    data_queue.put(update)
                stream_done.set()
            except grpc.RpcError as e:
                # 如果是取消操作，这是正常的
                if e.code() != grpc.StatusCode.CANCELLED:
                    exception_queue.put(e)
                stream_done.set()
            except Exception as e:
                exception_queue.put(e)
                stream_done.set()
        
        # 启动读取线程
        reader_thread = threading.Thread(target=stream_reader, daemon=True)
        reader_thread.start()
        
        # 等待流创建完成
        stream_ready.wait(timeout=5)
        
        try:
            while self._running and not stream_done.is_set():
                try:
                    # 使用超时以便定期检查 _running 标志
                    update = data_queue.get(timeout=0.1)
                    yield update
                except queue.Empty:
                    # 检查是否有异常
                    if not exception_queue.empty():
                        e = exception_queue.get()
                        raise e
                    continue
            
            # 如果因为 _running=False 退出，取消流
            if not self._running and self.td_stream:
                try:
                    self.td_stream.cancel()
                except:
                    pass
                    
        except grpc.RpcError as e:
            # 取消操作是正常的，不需要抛出异常
            if e.code() != grpc.StatusCode.CANCELLED:
                raise
        except Exception as e:
            raise
    
    def query_trading_account(self) -> trading_pb2.TradingAccountResponse:
        """
        查询资金账户
        
        Returns:
            TradingAccountResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.TradingAccountQuery()
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryTradingAccount(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询资金账户失败: {e.code()} - {e.details()}")
    
    def query_order(
        self,
        symbol: str = "",
        exchange: str = "",
        order_sys_id: str = ""
    ) -> trading_pb2.OrderQueryResponse:
        """
        查询订单
        
        Args:
            symbol: 合约代码（空字符串表示查询所有订单）
            exchange: 交易所代码（可选）
            order_sys_id: 系统订单号（可选，CTP API仅支持通过系统订单号查询）
            
        Returns:
            OrderQueryResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.OrderQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        if order_sys_id:
            request.order_sys_id = order_sys_id
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryOrder(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询订单失败: {e.code()} - {e.details()}")
    
    def query_trade(
        self,
        symbol: str = "",
        exchange: str = "",
        trade_id: str = ""
    ) -> trading_pb2.TradeQueryResponse:
        """
        查询成交
        
        Args:
            symbol: 合约代码（空字符串表示查询所有成交）
            exchange: 交易所代码（可选）
            trade_id: 成交编号（可选）
            
        Returns:
            TradeQueryResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.TradeQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        if trade_id:
            request.trade_id = trade_id
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryTrade(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询成交失败: {e.code()} - {e.details()}")
    
    def confirm_settlement_info(self) -> trading_pb2.SettlementConfirmResponse:
        """
        结算确认
        
        Returns:
            SettlementConfirmResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.SettlementConfirmRequest()
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.ConfirmSettlementInfo(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"结算确认失败: {e.code()} - {e.details()}")
    
    def query_instrument(
        self,
        symbol: str = "",
        exchange: str = ""
    ) -> trading_pb2.InstrumentQueryResponse:
        """
        查询合约信息
        
        Args:
            symbol: 合约代码（空字符串表示查询所有合约）
            exchange: 交易所代码（可选）
            
        Returns:
            InstrumentQueryResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.InstrumentQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryInstrument(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询合约信息失败: {e.code()} - {e.details()}")
    
    def query_instrument_margin_rate(
        self,
        symbol: str = "",
        exchange: Optional[str] = None,
        hedge_flag: str = "1"
    ) -> trading_pb2.InstrumentMarginRateResponse:
        """
        查询合约保证金率
        
        Args:
            symbol: 合约代码（空字符串表示查询所有）
            exchange: 交易所代码（可选）
            hedge_flag: 投机套保标志（可选，默认值为"1"=投机）
            
        Returns:
            InstrumentMarginRateResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.InstrumentMarginRateQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        if hedge_flag:
            request.hedge_flag = hedge_flag
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryInstrumentMarginRate(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询保证金率失败: {e.code()} - {e.details()}")
    
    def query_instrument_commission_rate(
        self,
        symbol: str = "",
        exchange: str = ""
    ) -> trading_pb2.InstrumentCommissionRateResponse:
        """
        查询合约手续费率
        
        Args:
            symbol: 合约代码（空字符串表示查询所有）
            exchange: 交易所代码（可选）
            
        Returns:
            InstrumentCommissionRateResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.InstrumentCommissionRateQuery()
        request.symbol = symbol
        if exchange:
            request.exchange = exchange
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryInstrumentCommissionRate(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询手续费率失败: {e.code()} - {e.details()}")
    
    def query_settlement_info(
        self,
        trading_day: str = ""
    ) -> trading_pb2.SettlementInfoResponse:
        """
        查询结算信息
        
        Args:
            trading_day: 交易日（空字符串表示查询所有）
            
        Returns:
            SettlementInfoResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.SettlementInfoQuery()
        request.trading_day = trading_day
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QuerySettlementInfo(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询结算信息失败: {e.code()} - {e.details()}")
    
    def trading_logout(self) -> trading_pb2.TradingLogoutResponse:
        """
        CTP交易登出
        
        Returns:
            TradingLogoutResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.TradingLogoutRequest()
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.TradingLogout(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"交易登出失败: {e.code()} - {e.details()}")
    
    def query_max_order_volume(
        self,
        symbol: str,
        exchange: str,
        direction: trading_pb2.Direction,
        offset: trading_pb2.Offset,
        hedge_flag: str = ""
    ) -> trading_pb2.MaxOrderVolumeResponse:
        """
        查询最大报单量
        
        Args:
            symbol: 合约代码（必需）
            exchange: 交易所代码（必需）
            direction: 买卖方向
            offset: 开平标志
            hedge_flag: 投机套保标志（可选）
            
        Returns:
            MaxOrderVolumeResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.MaxOrderVolumeQuery()
        request.symbol = symbol
        request.exchange = exchange
        request.direction = direction
        request.offset = offset
        if hedge_flag:
            request.hedge_flag = hedge_flag
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryMaxOrderVolume(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询最大报单量失败: {e.code()} - {e.details()}")
    
    def query_exchange(
        self,
        exchange_id: str = ""
    ) -> trading_pb2.ExchangeResponse:
        """
        查询交易所
        
        Args:
            exchange_id: 交易所代码（空字符串表示查询所有）
            
        Returns:
            ExchangeResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.ExchangeQuery()
        request.exchange_id = exchange_id
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryExchange(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询交易所失败: {e.code()} - {e.details()}")
    
    def query_investor(self) -> trading_pb2.InvestorResponse:
        """
        查询投资者
        
        Returns:
            InvestorResponse
        """
        if not self.td_stub:
            raise RuntimeError("未连接到服务器")
        
        request = trading_pb2.InvestorQuery()
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.td_stub.QueryInvestor(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"查询投资者失败: {e.code()} - {e.details()}")

