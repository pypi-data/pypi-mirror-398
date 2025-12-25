"""
gRPC客户端
用于连接pq-futures项目的gRPC服务
"""

import grpc
import threading
import queue
import time
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
        self.expires_at = 0  # token过期时间戳（Unix时间戳，秒）
        self._running = True  # 内部运行标志
        
        # Token自动刷新相关
        self.token_refresh_thread = None  # 后台刷新线程
        self.token_refresh_running = threading.Event()  # 控制线程运行状态
        self.token_refresh_interval = 60  # 检查间隔（秒），默认60秒
        self.token_refresh_threshold = 300  # 提前刷新阈值（秒），默认300秒（5分钟）
    
    def connect(self, max_retries: int = -1, initial_retry_delay: float = 1.0, max_retry_delay: float = 60.0):
        """
        连接到gRPC服务器（带自动重连机制）
        
        Args:
            max_retries: 最大重试次数，-1 表示无限重试
            initial_retry_delay: 初始重试延迟（秒）
            max_retry_delay: 最大重试延迟（秒）
        
        Returns:
            bool: 连接是否成功
        """
        retry_count = 0
        retry_delay = initial_retry_delay
        
        while True:
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
                if max_retries >= 0 and retry_count >= max_retries:
                    raise ConnectionError(f"连接超时: 无法连接到 {self.address}，达到最大重试次数 ({max_retries})")
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)  # 指数退避
                continue
            except Exception as e:
                if max_retries >= 0 and retry_count >= max_retries:
                    raise ConnectionError(f"连接失败: {e}，达到最大重试次数 ({max_retries})")
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)  # 指数退避
                continue
    
    def _reconnect(self) -> bool:
        """
        重新连接到服务器
        
        Returns:
            bool: 重连是否成功
        """
        try:
            # 关闭旧连接
            if self.channel:
                try:
                    self.channel.close()
                except:
                    pass
            
            # 重新连接
            return self.connect()
        except Exception as e:
            return False
    
    def close(self):
        """关闭连接"""
        # 停止自动刷新
        self.stop_auto_refresh()
        
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
                self.expires_at = response.expires_at if response.expires_at > 0 else 0
                # 登录成功后自动启动token刷新机制
                if self.expires_at > 0:
                    self.start_auto_refresh()
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
                self.expires_at = 0
                config.clear_token()
                # 登出时停止自动刷新
                self.stop_auto_refresh()
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
                self.expires_at = response.expires_at if response.expires_at > 0 else 0
                # 刷新成功后，如果自动刷新未启动，则启动它
                if self.expires_at > 0 and not (self.token_refresh_thread and self.token_refresh_thread.is_alive()):
                    self.start_auto_refresh()
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
    
    def _token_refresh_worker(self):
        """
        后台线程工作函数：定期检查token过期时间，在过期前自动刷新
        """
        import datetime
        
        while self.token_refresh_running.is_set():
            try:
                # 检查是否有token和过期时间
                if not self.token or self.expires_at <= 0:
                    # 没有token，等待一段时间后继续检查
                    if not self.token_refresh_running.wait(self.token_refresh_interval):
                        continue  # 超时，继续循环
                    else:
                        break  # 收到停止信号
                
                # 计算剩余时间
                current_time = time.time()
                remaining_time = self.expires_at - current_time
                
                # 如果剩余时间小于阈值，尝试刷新
                if remaining_time <= self.token_refresh_threshold:
                    # 尝试刷新token（静默模式，不打印详细信息）
                    success = self._refresh_token_silent()
                    if not success:
                        # 刷新失败，清除token和过期时间
                        self.token = None
                        self.expires_at = 0
                
                # 等待检查间隔（使用time.sleep，同时检查停止信号）
                elapsed = 0
                check_interval = min(self.token_refresh_interval, 1)  # 每秒检查一次停止信号
                while elapsed < self.token_refresh_interval:
                    if not self.token_refresh_running.is_set():
                        return  # 收到停止信号
                    time.sleep(check_interval)
                    elapsed += check_interval
                    
            except Exception as e:
                # 发生错误时等待一段时间后继续
                if not self.token_refresh_running.wait(self.token_refresh_interval):
                    continue  # 超时，继续循环
                else:
                    break  # 收到停止信号
    
    def _refresh_token_silent(self) -> bool:
        """
        静默刷新token（不打印详细信息，用于自动刷新）
        
        Returns:
            是否刷新成功
        """
        if not AUTH_AVAILABLE or not self.auth_stub or not self.token:
            return False
        
        try:
            request = auth_pb2.RefreshTokenRequest()
            request.token = self.token
            response = self.auth_stub.RefreshToken(request)
            
            if response.error_code == 0:
                self.expires_at = response.expires_at if response.expires_at > 0 else 0
                return True
            return False
        except:
            return False
    
    def start_auto_refresh(self, interval: int = None, threshold: int = None):
        """
        启动token自动刷新机制
        
        Args:
            interval: 检查间隔（秒），默认60秒
            threshold: 提前刷新阈值（秒），默认300秒（5分钟）
        """
        if not AUTH_AVAILABLE:
            return
        
        # 如果没有token，无法启动自动刷新
        if not self.token:
            return
        
        # 设置参数
        if interval is not None:
            self.token_refresh_interval = interval
        if threshold is not None:
            self.token_refresh_threshold = threshold
        
        # 如果线程已经在运行，先停止
        if self.token_refresh_thread and self.token_refresh_thread.is_alive():
            self.stop_auto_refresh()
        
        # 启动后台线程
        self.token_refresh_running.set()
        self.token_refresh_thread = threading.Thread(
            target=self._token_refresh_worker,
            name="TokenRefreshThread",
            daemon=True
        )
        self.token_refresh_thread.start()
    
    def stop_auto_refresh(self):
        """停止token自动刷新机制"""
        if self.token_refresh_running.is_set():
            self.token_refresh_running.clear()
            if self.token_refresh_thread and self.token_refresh_thread.is_alive():
                self.token_refresh_thread.join(timeout=2)
    
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
    
    def stream_order_status(self, max_retries: int = -1, 
                           initial_retry_delay: float = 1.0, max_retry_delay: float = 60.0) -> Iterator[trading_pb2.OrderStatusUpdate]:
        """
        流式接收订单状态更新（带自动重连机制）
        
        Args:
            max_retries: 最大重试次数，-1 表示无限重试
            initial_retry_delay: 初始重试延迟（秒）
            max_retry_delay: 最大重试延迟（秒）
        
        Yields:
            OrderStatusUpdate消息
        """
        retry_count = 0
        retry_delay = initial_retry_delay
        
        while self._running:
            # 检查stub是否存在，如果不存在则尝试重连
            if not self.td_stub:
                if not self._reconnect():
                    if max_retries >= 0 and retry_count >= max_retries:
                        raise RuntimeError(f"达到最大重试次数 ({max_retries})，无法连接到服务器")
                    retry_count += 1
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)  # 指数退避
                    continue
                else:
                    # 重连成功，重置重试计数和延迟
                    retry_count = 0
                    retry_delay = initial_retry_delay
            
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
            if not stream_ready.wait(timeout=5):
                if max_retries >= 0 and retry_count >= max_retries:
                    raise RuntimeError(f"达到最大重试次数 ({max_retries})，无法创建流")
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                continue
            
            # 重置重试计数和延迟（流创建成功）
            retry_count = 0
            retry_delay = initial_retry_delay
            
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
                            # 检查是否是可重试的错误
                            if isinstance(e, grpc.RpcError):
                                error_code = e.code()
                                error_details = e.details()
                                
                                # 可重试的错误码
                                retryable_errors = {
                                    grpc.StatusCode.UNAVAILABLE,
                                    grpc.StatusCode.DEADLINE_EXCEEDED,
                                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                                    grpc.StatusCode.ABORTED,
                                    grpc.StatusCode.INTERNAL,
                                }
                                
                                # 检查错误详情中是否包含连接相关的错误
                                connection_errors = [
                                    "End of TCP stream",
                                    "Connection refused",
                                    "Connection reset",
                                    "Broken pipe",
                                    "Transport closed",
                                ]
                                
                                is_retryable = (
                                    error_code in retryable_errors or
                                    any(err in error_details for err in connection_errors)
                                )
                                
                                if is_retryable:
                                    if max_retries >= 0 and retry_count >= max_retries:
                                        raise e
                                    
                                    retry_count += 1
                                    
                                    # 尝试重连
                                    if self._reconnect():
                                        retry_count = 0
                                        retry_delay = initial_retry_delay
                                        break  # 跳出内层循环，重新建立流
                                    else:
                                        time.sleep(retry_delay)
                                        retry_delay = min(retry_delay * 2, max_retry_delay)
                                        break  # 跳出内层循环，继续外层重试循环
                                else:
                                    # 不可重试的错误，直接抛出
                                    raise e
                            else:
                                # 非gRPC错误，直接抛出
                                raise e
                        continue
                
                # 如果因为 _running=False 退出，取消流
                if not self._running and self.td_stream:
                    try:
                        self.td_stream.cancel()
                    except:
                        pass
                        
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    # 取消操作，正常退出
                    return
                # 其他错误，检查是否可重试
                error_code = e.code()
                error_details = e.details()
                
                retryable_errors = {
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    grpc.StatusCode.ABORTED,
                    grpc.StatusCode.INTERNAL,
                }
                
                connection_errors = [
                    "End of TCP stream",
                    "Connection refused",
                    "Connection reset",
                    "Broken pipe",
                    "Transport closed",
                ]
                
                is_retryable = (
                    error_code in retryable_errors or
                    any(err in error_details for err in connection_errors)
                )
                
                if is_retryable:
                    if max_retries >= 0 and retry_count >= max_retries:
                        raise e
                    retry_count += 1
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                    continue  # 继续外层循环，重新建立连接和流
                else:
                    raise
            except Exception as e:
                if not isinstance(e, grpc.RpcError):
                    raise
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
    
    def stream_connection_status(self, connection_type: str = "TD", max_retries: int = -1, 
                                 initial_retry_delay: float = 1.0, max_retry_delay: float = 60.0) -> Iterator[common_pb2.ConnectionStatusUpdate]:
        """
        流式接收连接状态更新（带自动重连机制）
        
        Args:
            connection_type: 连接类型，"TD" 表示交易连接，"MD" 表示行情连接
            max_retries: 最大重试次数，-1 表示无限重试
            initial_retry_delay: 初始重试延迟（秒）
            max_retry_delay: 最大重试延迟（秒）
        
        Yields:
            ConnectionStatusUpdate消息
        """
        retry_count = 0
        retry_delay = initial_retry_delay
        
        while self._running:
            # 检查stub是否存在，如果不存在则尝试重连
            stub = self.td_stub if connection_type == "TD" else self.md_stub
            if not stub:
                if not self._reconnect():
                    if max_retries >= 0 and retry_count >= max_retries:
                        raise RuntimeError(f"达到最大重试次数 ({max_retries})，无法连接到服务器")
                    retry_count += 1
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)  # 指数退避
                    continue
                else:
                    # 重连成功，重置重试计数和延迟
                    retry_count = 0
                    retry_delay = initial_retry_delay
                    stub = self.td_stub if connection_type == "TD" else self.md_stub
        
            request = self.create_auth_request()
            
            # 使用队列和线程来处理流式数据，以便能够响应取消信号
            data_queue = queue.Queue()
            exception_queue = queue.Queue()
            stream_done = threading.Event()
            stream_ready = threading.Event()
            
            def stream_reader():
                """在单独线程中读取流数据"""
                try:
                    stream = stub.StreamConnectionStatus(request)
                    stream_ready.set()  # 标记流已创建
                    for update in stream:
                        if not self._running:
                            break
                        data_queue.put(update)
                    stream_done.set()
                except grpc.RpcError as e:
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
            if not stream_ready.wait(timeout=5):
                if max_retries >= 0 and retry_count >= max_retries:
                    raise RuntimeError(f"达到最大重试次数 ({max_retries})，无法创建流")
                retry_count += 1
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_retry_delay)
                continue
            
            # 重置重试计数和延迟（流创建成功）
            retry_count = 0
            retry_delay = initial_retry_delay
            
            try:
                while self._running and not stream_done.is_set():
                    try:
                        update = data_queue.get(timeout=0.1)
                        yield update
                    except queue.Empty:
                        if not exception_queue.empty():
                            e = exception_queue.get()
                            # 检查是否是可重试的错误
                            if isinstance(e, grpc.RpcError):
                                error_code = e.code()
                                error_details = e.details()
                                
                                # 可重试的错误码
                                retryable_errors = {
                                    grpc.StatusCode.UNAVAILABLE,
                                    grpc.StatusCode.DEADLINE_EXCEEDED,
                                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                                    grpc.StatusCode.ABORTED,
                                    grpc.StatusCode.INTERNAL,
                                }
                                
                                # 检查错误详情中是否包含连接相关的错误
                                connection_errors = [
                                    "End of TCP stream",
                                    "Connection refused",
                                    "Connection reset",
                                    "Broken pipe",
                                    "Transport closed",
                                ]
                                
                                is_retryable = (
                                    error_code in retryable_errors or
                                    any(err in error_details for err in connection_errors)
                                )
                                
                                if is_retryable:
                                    if max_retries >= 0 and retry_count >= max_retries:
                                        raise e
                                    
                                    retry_count += 1
                                    
                                    # 尝试重连
                                    if self._reconnect():
                                        retry_count = 0
                                        retry_delay = initial_retry_delay
                                        break  # 跳出内层循环，重新建立流
                                    else:
                                        time.sleep(retry_delay)
                                        retry_delay = min(retry_delay * 2, max_retry_delay)
                                        break  # 跳出内层循环，继续外层重试循环
                                else:
                                    # 不可重试的错误，直接抛出
                                    raise e
                            else:
                                # 非gRPC错误，直接抛出
                                raise e
                        continue
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    # 取消操作，正常退出
                    return
                # 其他错误，检查是否可重试
                error_code = e.code()
                error_details = e.details()
                
                retryable_errors = {
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                    grpc.StatusCode.RESOURCE_EXHAUSTED,
                    grpc.StatusCode.ABORTED,
                    grpc.StatusCode.INTERNAL,
                }
                
                connection_errors = [
                    "End of TCP stream",
                    "Connection refused",
                    "Connection reset",
                    "Broken pipe",
                    "Transport closed",
                ]
                
                is_retryable = (
                    error_code in retryable_errors or
                    any(err in error_details for err in connection_errors)
                )
                
                if is_retryable:
                    if max_retries >= 0 and retry_count >= max_retries:
                        raise e
                    retry_count += 1
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, max_retry_delay)
                    continue  # 继续外层循环，重新建立连接和流
                else:
                    raise
            except Exception as e:
                if not isinstance(e, grpc.RpcError):
                    raise
                raise
    
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
    
    def market_data_logout(self) -> market_data_pb2.MarketDataLogoutResponse:
        """
        CTP行情登出
        
        Returns:
            MarketDataLogoutResponse
        """
        if not self.md_stub:
            raise RuntimeError("未连接到服务器")
        
        request = market_data_pb2.MarketDataLogoutRequest()
        request.auth.CopyFrom(self.create_auth_request())
        
        try:
            response = self.md_stub.MarketDataLogout(request)
            return response
        except grpc.RpcError as e:
            raise ConnectionError(f"行情登出失败: {e.code()} - {e.details()}")
    
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


